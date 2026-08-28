#!/usr/bin/env node
/**
 * Web Analyzer v4 - Full business research
 * Analyzes entire website + navigates internal pages
 * 
 * The agent should complement with web_search for competitors
 */

const { chromium } = require('playwright');
const fs = require('fs');

const CAROUSEL_DIR = '/tmp/carousel';

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function analyzeWebsite(url) {
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`🔍 FULL RESEARCH: ${url}`);
  console.log('═══════════════════════════════════════════════════════════════\n');
  
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ 
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });
  const page = await context.newPage();
  
  fs.mkdirSync(CAROUSEL_DIR, { recursive: true });
  
  const data = {
    url,
    brand: {},
    content: { features: [], testimonials: [], stats: [], pricing: [], ctas: [] },
    pages: {},
    storytelling: {},
    visualContext: {},
    searchQueries: [] // Para que el agente busque
  };

  try {
    // ═══════════════════════════════════════════════════════════════
    // 1. HOMEPAGE - Full analysis
    // ═══════════════════════════════════════════════════════════════
    console.log('📌 1. ANALYZING HOMEPAGE...');
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    await delay(2000);
    
    // Screenshot
    await page.screenshot({ path: `${CAROUSEL_DIR}/homepage.png`, fullPage: false });
    
    // Full scroll to load all content
    await page.evaluate(async () => {
      for (let i = 0; i < 5; i++) {
        window.scrollTo(0, document.body.scrollHeight * (i / 5));
        await new Promise(r => setTimeout(r, 500));
      }
      window.scrollTo(0, 0);
    });
    await delay(1000);
    
    // Extract ALL info from homepage
    const homeData = await page.evaluate(() => {
      // Brand
      const h1 = document.querySelector('h1')?.textContent?.trim() || '';
      const title = document.title || '';
      const metaDesc = document.querySelector('meta[name="description"]')?.content || '';
      const logo = document.querySelector('header img, [class*="logo"] img, img[alt*="logo"]')?.src;
      
      // Colores
      const colors = [];
      const buttons = document.querySelectorAll('button, a[class*="btn"], [class*="cta"]');
      buttons.forEach(btn => {
        const bg = getComputedStyle(btn).backgroundColor;
        if (bg && bg !== 'rgba(0, 0, 0, 0)' && !colors.includes(bg)) {
          colors.push(bg);
        }
      });
      
      // Typography
      const bodyFont = getComputedStyle(document.body).fontFamily.split(',')[0].replace(/['"]/g, '');
      const h1El = document.querySelector('h1');
      const headingFont = h1El ? getComputedStyle(h1El).fontFamily.split(',')[0].replace(/['"]/g, '') : bodyFont;
      
      // Tagline/subtitle
      const heroSection = document.querySelector('[class*="hero"], main > section:first-child, header + section, header + div');
      let tagline = '';
      if (heroSection) {
        const p = heroSection.querySelector('p');
        const h2 = heroSection.querySelector('h2');
        tagline = p?.textContent?.trim() || h2?.textContent?.trim() || '';
      }
      if (!tagline) tagline = metaDesc;
      
      // Todos los headings
      const headings = [];
      document.querySelectorAll('h1, h2, h3').forEach(h => {
        const text = h.textContent?.trim();
        if (text && text.length > 3 && text.length < 150 && !headings.find(x => x.text === text)) {
          headings.push({ level: h.tagName, text });
        }
      });
      
      // Features - search in multiple formats
      const features = [];
      const featureSelectors = [
        '[class*="feature"]', '[class*="benefit"]', '[class*="card"]',
        '[class*="service"]', '[class*="advantage"]', '[class*="why"]',
        'section ul li', '.grid > div', '[class*="item"]'
      ];
      featureSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
          const title = el.querySelector('h2, h3, h4, strong, b')?.textContent?.trim();
          const desc = el.querySelector('p')?.textContent?.trim();
          if (title && title.length > 3 && title.length < 100 && features.length < 12) {
            if (!features.find(f => f.title === title)) {
              features.push({ title, description: desc?.substring(0, 200) || '' });
            }
          }
        });
      });
      
      // Testimonials
      const testimonials = [];
      const testimonialSelectors = [
        '[class*="testimonial"]', '[class*="review"]', '[class*="quote"]',
        'blockquote', '[class*="customer"]', '[class*="feedback"]'
      ];
      testimonialSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
          const text = el.querySelector('p, .text, .content')?.textContent?.trim() || el.textContent?.trim();
          const author = el.querySelector('[class*="author"], [class*="name"], cite, strong')?.textContent?.trim();
          if (text && text.length > 30 && text.length < 500 && testimonials.length < 5) {
            if (!testimonials.find(t => t.text === text)) {
              testimonials.push({ text: text.substring(0, 300), author: author || 'Usuario' });
            }
          }
        });
      });
      
      // Stats/numbers
      const stats = [];
      const statSelectors = [
        '[class*="stat"]', '[class*="number"]', '[class*="metric"]',
        '[class*="counter"]', '[class*="data"]', '[class*="kpi"]'
      ];
      statSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
          const text = el.textContent?.trim();
          // Buscar patrones como "30k+", "1M", "99%", "$50"
          const match = text.match(/[\d,]+[kKmM%+]?|\$[\d,]+/);
          if (match && stats.length < 6) {
            const label = el.querySelector('span, p, small')?.textContent?.trim() || '';
            if (!stats.find(s => s.value === match[0])) {
              stats.push({ value: match[0], label: label.substring(0, 50) });
            }
          }
        });
      });
      
      // CTAs
      const ctas = [];
      document.querySelectorAll('a[class*="btn"], a[class*="cta"], button').forEach(el => {
        const text = el.textContent?.trim();
        if (text && text.length > 2 && text.length < 50 && !ctas.includes(text)) {
          ctas.push(text);
        }
      });
      
      // Important internal links
      const internalLinks = [];
      const importantPages = ['pricing', 'features', 'about', 'testimonials', 'reviews', 'customers', 'case', 'demo', 'contact'];
      document.querySelectorAll('a[href]').forEach(a => {
        const href = a.href.toLowerCase();
        const text = a.textContent?.trim();
        importantPages.forEach(page => {
          if (href.includes(page) && !internalLinks.find(l => l.url === a.href)) {
            internalLinks.push({ url: a.href, text, type: page });
          }
        });
      });
      
      return {
        title, headline: h1, tagline, metaDesc, logo,
        colors, bodyFont, headingFont,
        headings, features, testimonials, stats, ctas,
        internalLinks: internalLinks.slice(0, 8)
      };
    });
    
    // Extract brand name (prioritize domain over generic title)
    let brandName = homeData.title.split('|')[0].split('-')[0].trim();
    const domain = url.replace(/https?:\/\//, '').replace('www.', '').split('.')[0];
    // If title name is generic, use the domain
    if (brandName.toLowerCase().includes('api') || brandName.toLowerCase().includes('tool') || brandName.length > 30) {
      brandName = domain.charAt(0).toUpperCase() + domain.slice(1);
    }
    
    data.brand = {
      name: brandName,
      headline: homeData.headline,
      tagline: homeData.tagline,
      logo: homeData.logo,
      colors: homeData.colors,
      typography: { body: homeData.bodyFont, heading: homeData.headingFont }
    };
    data.content = {
      headline: homeData.headline,
      tagline: homeData.tagline,
      metaDescription: homeData.metaDesc,
      headings: homeData.headings,
      features: homeData.features,
      testimonials: homeData.testimonials,
      stats: homeData.stats,
      ctas: homeData.ctas.slice(0, 5),
      pricing: []
    };
    
    console.log(`   ✓ Brand: ${data.brand.name}`);
    console.log(`   ✓ Headline: "${homeData.headline?.substring(0, 50)}..."`);
    console.log(`   ✓ Features: ${homeData.features.length}`);
    console.log(`   ✓ Testimonials: ${homeData.testimonials.length}`);
    console.log(`   ✓ Stats: ${homeData.stats.length}`);
    console.log(`   ✓ CTAs: ${homeData.ctas.length}`);
    console.log(`   ✓ Internal links: ${homeData.internalLinks.length}`);

    // ═══════════════════════════════════════════════════════════════
    // 2. INTERNAL PAGES
    // ═══════════════════════════════════════════════════════════════
    console.log('\n📌 2. NAVIGATING INTERNAL PAGES...');
    
    for (const link of homeData.internalLinks.slice(0, 5)) {
      try {
        console.log(`   → ${link.type}: ${link.url.substring(0, 60)}...`);
        await page.goto(link.url, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await delay(1500);
        
        const pageData = await page.evaluate((pageType) => {
          const content = { type: pageType, items: [] };
          
          if (pageType === 'pricing') {
            // Extract pricing plans
            document.querySelectorAll('[class*="plan"], [class*="tier"], [class*="price"]').forEach(el => {
              const name = el.querySelector('h2, h3, h4, [class*="name"]')?.textContent?.trim();
              const price = el.querySelector('[class*="amount"], [class*="price"], .price')?.textContent?.trim();
              const features = [];
              el.querySelectorAll('li, [class*="feature"]').forEach(f => {
                const t = f.textContent?.trim();
                if (t && t.length < 100) features.push(t);
              });
              if (name || price) {
                content.items.push({ name, price, features: features.slice(0, 5) });
              }
            });
          } else if (pageType === 'testimonials' || pageType === 'reviews' || pageType === 'customers') {
            // Extract more testimonials
            document.querySelectorAll('[class*="testimonial"], [class*="review"], blockquote, [class*="quote"]').forEach(el => {
              const text = el.querySelector('p')?.textContent?.trim() || el.textContent?.trim();
              const author = el.querySelector('[class*="author"], [class*="name"]')?.textContent?.trim();
              if (text && text.length > 20 && text.length < 500) {
                content.items.push({ text: text.substring(0, 300), author });
              }
            });
          } else if (pageType === 'features') {
            // Extract more features
            document.querySelectorAll('[class*="feature"], [class*="card"], section > div').forEach(el => {
              const title = el.querySelector('h2, h3, h4')?.textContent?.trim();
              const desc = el.querySelector('p')?.textContent?.trim();
              if (title && title.length > 3 && title.length < 100) {
                content.items.push({ title, description: desc?.substring(0, 200) });
              }
            });
          }
          
          return content;
        }, link.type);
        
        data.pages[link.type] = pageData;
        
        // Merge data
        if (link.type === 'pricing' && pageData.items.length > 0) {
          data.content.pricing = pageData.items;
          console.log(`      ✓ Planes: ${pageData.items.length}`);
        }
        if ((link.type === 'testimonials' || link.type === 'reviews') && pageData.items.length > 0) {
          data.content.testimonials.push(...pageData.items);
          console.log(`      ✓ Testimonials: +${pageData.items.length}`);
        }
        if (link.type === 'features' && pageData.items.length > 0) {
          pageData.items.forEach(f => {
            if (!data.content.features.find(x => x.title === f.title)) {
              data.content.features.push(f);
            }
          });
          console.log(`      ✓ Features: +${pageData.items.length}`);
        }
        
      } catch (e) {
        console.log(`      ⚠️ Error: ${e.message.substring(0, 50)}`);
      }
    }

    // ═══════════════════════════════════════════════════════════════
    // 3. DETECTAR COMPETIDORES EN EL CONTENIDO
    // ═══════════════════════════════════════════════════════════════
    console.log('\n📌 3. DETECTING COMPETITORS...');
    
    // Buscar menciones de competidores conocidos en el contenido
    const knownCompetitors = [
      'buffer', 'hootsuite', 'later', 'sprout social', 'socialbee', 
      'publer', 'metricool', 'ayrshare', 'socialbu', 'postiz',
      'sendible', 'loomly', 'planable', 'sprinklr', 'falcon.io',
      'brandwatch', 'hubspot', 'zoho social', 'tailwind', 'planoly'
    ];
    
    const pageText = await page.evaluate(() => document.body.innerText.toLowerCase());
    const detectedCompetitors = knownCompetitors.filter(c => pageText.includes(c.toLowerCase()));
    
    // Buscar secciones "vs", "alternative", "compare"
    const comparisonData = await page.evaluate(() => {
      const comparisons = [];
      document.querySelectorAll('a[href*="vs"], a[href*="alternative"], a[href*="compare"], [class*="compare"]').forEach(el => {
        const text = el.textContent?.trim();
        if (text && text.length < 100) comparisons.push(text);
      });
      return comparisons;
    });
    
    data.competitors = detectedCompetitors;
    data.comparisons = comparisonData;
    
    console.log(`   ✓ Competitors detected: ${detectedCompetitors.length > 0 ? detectedCompetitors.join(', ') : 'none in content'}`);
    
    // Nombre del producto
    let productName = data.brand.name || url.replace(/https?:\/\//, '').split('.')[0];
    if (productName.toLowerCase().includes('social media')) {
      productName = url.replace(/https?:\/\//, '').replace('www.', '').split('.')[0];
    }
    productName = productName.charAt(0).toUpperCase() + productName.slice(1);

    // ═══════════════════════════════════════════════════════════════
    // 4. STORYTELLING
    // ═══════════════════════════════════════════════════════════════
    console.log('\n📌 4. GENERATING STORYTELLING...');
    
    // Detect niche
    const allText = JSON.stringify(data.content).toLowerCase();
    let businessType = 'saas';
    let niche = 'business';
    
    if (/social media|instagram|tiktok|post|publish|schedule|content creator/i.test(allText)) {
      niche = 'social-media-tools';
    } else if (/api|developer|sdk|integration|code|github/i.test(allText)) {
      niche = 'developer-tools';
    } else if (/ecommerce|shop|store|cart|checkout|product catalog/i.test(allText)) {
      businessType = 'ecommerce';
      niche = 'ecommerce';
    } else if (/app|mobile|ios|android|download/i.test(allText)) {
      businessType = 'app';
      niche = 'mobile-app';
    } else if (/design|interior|architect|room|furniture|decor/i.test(allText)) {
      niche = 'design';
    } else if (/marketing|ads|campaign|seo|growth|funnel/i.test(allText)) {
      niche = 'marketing';
    } else if (/finance|banking|invest|payment|fintech/i.test(allText)) {
      niche = 'finance';
    } else if (/education|learn|course|student|teaching/i.test(allText)) {
      niche = 'education';
    } else if (/health|fitness|wellness|medical|workout/i.test(allText)) {
      niche = 'health';
    }
    
    // Generate hooks based on niche
    const hooks = [];
    if (niche === 'social-media-tools') {
      hooks.push(
        'Still posting to social media ONE BY ONE? 😩',
        'The trick creators use to be on ALL platforms at once',
        'You\'re wasting HOURS every week doing this...',
        'Why your competition is growing faster than you'
      );
    } else if (niche === 'developer-tools') {
      hooks.push(
        'Your code still does THIS? 💀',
        'The API devs can\'t stop recommending',
        'Stop wasting time on integrations'
      );
    } else if (niche === 'ecommerce') {
      hooks.push(
        'The product TikTok won\'t stop recommending',
        'Why your online store is losing sales',
        'Still managing inventory MANUALLY?'
      );
    } else if (niche === 'design') {
      hooks.push(
        'I showed my landlord what AI thinks our room should look like',
        'Good taste but no budget? Try this',
        'Wait... this is actually the same room??'
      );
    } else if (niche === 'health') {
      hooks.push(
        'The app I wish I discovered sooner',
        'My trainer said I\'d never look like this',
        'Still tracking your workouts on paper?'
      );
    } else if (niche === 'education') {
      hooks.push(
        'I learned more in 30 days than in 4 years of college',
        'Why traditional learning is broken',
        'The tool that made studying actually fun'
      );
    } else {
      hooks.push(
        'Still doing this MANUALLY?',
        'The tool that\'s about to change your business',
        'Why 90% of people are doing it WRONG'
      );
    }
    
    data.storytelling = {
      businessType,
      niche,
      productName,
      uvp: data.content.tagline || data.content.metaDescription,
      hooks,
      painPoints: data.content.features.slice(0, 3).map(f => f.title),
      socialProof: data.content.stats.length > 0 
        ? `${data.content.stats[0].value} ${data.content.stats[0].label}`
        : data.content.testimonials.length > 0
          ? `"${data.content.testimonials[0].text.substring(0, 100)}..."`
          : null
    };
    
    console.log(`   ✓ Type: ${businessType} / ${niche}`);
    console.log(`   ✓ Hooks: ${hooks.length}`);

    // ═══════════════════════════════════════════════════════════════
    // 5. CONTEXTO VISUAL
    // ═══════════════════════════════════════════════════════════════
    console.log('\n📌 5. DEFINING VISUAL CONTEXT...');
    
    const imageThemes = {
      'social-media-tools': ['content creator at desk with multiple screens', 'social media icons floating', 'person frustrated with phones', 'successful influencer celebrating'],
      'developer-tools': ['code on screen', 'developer workspace', 'API connections visualization', 'clean tech interface'],
      'ecommerce': ['online shopping', 'product showcase', 'happy customer unboxing', 'mobile shopping'],
      'mobile-app': ['smartphone with app', 'person using phone', 'app interface mockup', 'mobile lifestyle']
    };
    
    data.visualContext = {
      brandColors: data.brand.colors,
      colorDescription: data.brand.colors.length > 0 
        ? data.brand.colors.slice(0, 2).join(', ')
        : 'purple and blue gradient, modern tech',
      typography: data.brand.typography,
      mood: 'professional, modern, vibrant',
      imageThemes: imageThemes[niche] || imageThemes['social-media-tools'],
      styleGuide: `Use ${data.brand.typography.heading || 'bold sans-serif'} font. Modern, clean aesthetic.`
    };
    
    console.log(`   ✓ Visual themes: ${data.visualContext.imageThemes.length}`);

    // ═══════════════════════════════════════════════════════════════
    // GUARDAR
    // ═══════════════════════════════════════════════════════════════
    fs.writeFileSync(`${CAROUSEL_DIR}/analysis.json`, JSON.stringify(data, null, 2));
    
    console.log('\n═══════════════════════════════════════════════════════════════');
    console.log('✅ ANALYSIS COMPLETED');
    console.log('═══════════════════════════════════════════════════════════════');
    console.log(`\n📁 Saved to: ${CAROUSEL_DIR}/analysis.json`);
    console.log(`\n📊 SUMMARY:`);
    console.log(`   Brand: ${data.brand.name}`);
    console.log(`   Type: ${businessType} / ${niche}`);
    console.log(`   Features: ${data.content.features.length}`);
    console.log(`   Testimonials: ${data.content.testimonials.length}`);
    console.log(`   Stats: ${data.content.stats.length}`);
    console.log(`   Pricing: ${data.content.pricing.length} plans`);
    console.log(`   Hooks: ${data.storytelling.hooks.length}`);
    
    if (data.searchQueries.length > 0) {
      console.log(`\n⚠️  PENDING: The agent should run web_search for:`);
      data.searchQueries.forEach(q => console.log(`   → "${q}"`));
    }
    
    return data;
    
  } finally {
    await browser.close();
  }
}

const url = process.argv[2];
if (!url) {
  console.error('Usage: node analyze-web.js <URL>');
  process.exit(1);
}

analyzeWebsite(url).catch(console.error);
