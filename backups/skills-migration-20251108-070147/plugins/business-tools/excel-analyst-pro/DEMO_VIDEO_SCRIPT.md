# Excel Analyst Pro - Demo Video Script

**Duration:** 3-5 minutes
**Target Audience:** Investment bankers, financial analysts, data analysts
**Objective:** Show how Skills make Excel automation effortless

---

## 🎬 Video Structure

### Opening (0:00-0:20)
**Scene:** Terminal with Claude Code open

**Voiceover:**
> "What if you could build a professional DCF model in 5 minutes instead of 2 hours? With Excel Analyst Pro for Claude Code, you can."

**Screen Actions:**
- Show Claude Code terminal
- Display plugin name: "Excel Analyst Pro"
- Quick flash of 4 Skills icons/names

---

### Demo 1: DCF Model (0:20-1:30)

#### Setup (0:20-0:30)
**Scene:** Empty terminal prompt

**Voiceover:**
> "Let's value Tesla using a DCF model. No Excel formulas to remember—just natural language."

**Type in terminal:**
```
You: Create a DCF model for Tesla
```

**Screen Actions:**
- Show typing animation
- Hit enter

---

#### Skill Auto-Invocation (0:30-0:40)
**Scene:** Claude responds

**Screen Text:**
```
Claude: I'll build a DCF valuation model for Tesla. Let me gather some inputs.

What base year revenue should we use for Tesla?
(For reference, Tesla's 2023 revenue was approximately $96.8B)
```

**Voiceover:**
> "Notice: Claude automatically detected 'DCF model' and loaded the DCF Modeler Skill. No slash command needed."

**Highlight on screen:**
- Box around "DCF Modeler Skill" text
- Arrow pointing to "auto-invoked"

---

#### Conversation (0:40-1:10)
**Scene:** Back-and-forth Q&A

**Screen Text:**
```
You: $96.8 billion

Claude: Great! What revenue growth rates should we assume for Years 1-5?

You: 25%, 20%, 15%, 12%, 10%

Claude: What EBITDA margin should we assume?

You: 16%

Claude: Perfect! Building your DCF model...
[Loading animation]
```

**Voiceover:**
> "The Skill asks intelligent questions, using industry standards as defaults. It knows what financial analysts need."

---

#### Results (1:10-1:30)
**Scene:** Complete DCF model output

**Screen Text:**
```
✅ DCF Model Complete!

📊 Valuation Results:
- Enterprise Value: $847.3 billion
- Terminal Value: 68% of EV
- Implied equity value per share: $243

📁 Model saved to: Tesla_DCF_Model.xlsx
```

**Screen Actions:**
- Open Tesla_DCF_Model.xlsx in Excel
- Show 4 sheets: Assumptions, Projections, Valuation, Sensitivity
- Quickly scroll through each sheet
- Highlight sensitivity table with conditional formatting

**Voiceover:**
> "In under a minute, we have a professional 4-sheet DCF model with projections, valuation calculations, and sensitivity analysis. This would normally take 2-3 hours."

---

### Demo 2: LBO Model (1:30-2:15)

#### Quick Setup (1:30-1:40)
**Scene:** New terminal prompt

**Voiceover:**
> "Let's try something more complex: a leveraged buyout model."

**Type in terminal:**
```
You: Build an LBO model for a $50M EBITDA software company
```

---

#### Rapid Conversation (1:40-2:00)
**Scene:** Condensed Q&A

**Screen Text:**
```
Claude: I'll create an LBO model. What entry multiple (EV/EBITDA)?

You: 12x

Claude: Revenue growth rates (Years 1-5)?

You: 20%, 18%, 15%, 12%, 10%

Claude: [Builds complete LBO model]
```

**Voiceover:**
> "The LBO Modeler Skill structures the entire transaction automatically."

---

#### LBO Results (2:00-2:15)
**Scene:** LBO output and Excel file

**Screen Text:**
```
✅ LBO Model Complete!

📊 Base Case Returns (5-year hold, 12x exit):
- Exit Equity Value: $1,124M
- Money-on-Money: 4.2x
- IRR: 34.2%

📁 Saved to: Software_LBO_Model.xlsx
```

**Screen Actions:**
- Open Software_LBO_Model.xlsx
- Show 6 sheets (Transaction, Sources & Uses, Operating, Debt Schedule, Returns, Covenants)
- Zoom into debt schedule showing paydown
- Show IRR sensitivity table

**Voiceover:**
> "Complete 6-sheet LBO model with debt schedules, IRR calculations, and covenant tracking. Normally a full day's work—done in minutes."

---

### Demo 3: Variance Analysis (2:15-3:00)

#### Setup (2:15-2:25)
**Scene:** Terminal with data paste

**Voiceover:**
> "Finance managers can automate monthly variance reports."

**Type in terminal:**
```
You: Analyze Q1 budget vs actual

[User pastes budget and actual data table]
```

---

#### Quick Analysis (2:25-2:45)
**Scene:** Variance output

**Screen Text:**
```
✅ Variance Analysis Complete!

🔴 CRITICAL VARIANCES:
- EBITDA: $270K vs $450K (-40.0%) - $180K under
- Operating Expenses: $840K vs $750K (+12.0%) - $90K over

💡 Primary Driver: Marketing campaign +$65K over budget

📁 Saved to: Q1_2025_Variance_Analysis.xlsx
```

**Screen Actions:**
- Open variance report
- Show color-coded flags (🔴⚠️✅)
- Highlight executive summary
- Show automated commentary

**Voiceover:**
> "Automated flagging, commentary, and executive summaries. No more manual variance reports."

---

### Demo 4: Pivot Tables (3:00-3:30)

#### Natural Language Pivot (3:00-3:20)
**Scene:** Terminal with simple request

**Type in terminal:**
```
You: Show sales by region and product category
```

**Screen Text:**
```
Claude: [Creates pivot table]

✅ Pivot Table Created!

Top Insights:
1. West region leads with $1.45M (30.3%)
2. Electronics is #1 category at $1.70M

📁 With column chart visualization
```

**Screen Actions:**
- Open Excel with pivot table
- Show professional formatting
- Show chart
- Show slicers

**Voiceover:**
> "Pivot tables from natural language. No need to remember Excel syntax."

---

### Key Features Highlight (3:30-3:50)

**Scene:** Feature list appears on screen

**Screen Text:**
```
🎯 Auto-Invoked Skills
   No slash commands needed

🏦 Investment Banking Grade
   Professional templates & formatting

🔒 Local Processing
   No cloud upload required

⚡ Token Efficient
   50% cheaper than MCP-only

🆓 Free & Open Source
   MIT License
```

**Voiceover:**
> "Excel Analyst Pro features auto-invoked Skills that load exactly when you need them. Investment banking-grade templates, local processing for security, and it's completely free and open source."

---

### Comparison (3:50-4:10)

**Scene:** Comparison table

**Screen Text:**
```
                    Excel Analyst Pro | Claude for Excel | Microsoft Copilot
Price               Free              | Enterprise       | $30/month
Processing          Local ✅          | Cloud           | Cloud
Skills              4 (auto)          | Limited         | Basic
Financial Models    IB-grade ✅       | Basic           | Basic
```

**Voiceover:**
> "Unlike cloud-based solutions, Excel Analyst Pro processes everything locally. And unlike Microsoft Copilot, it includes investment banking-grade financial modeling."

---

### Installation (4:10-4:30)

**Scene:** Terminal showing installation

**Screen Text:**
```bash
/plugin install excel-analyst-pro@claude-code-plugins
```

**Screen Actions:**
- Show installation progress
- Show "✅ Installation complete" message
- Show "Skills loaded: 4" confirmation

**Voiceover:**
> "Installation is one command. The plugin automatically configures the Excel MCP server and loads all four Skills."

---

### Closing (4:30-4:50)

**Scene:** GitHub repo and website

**Screen Text:**
```
Excel Analyst Pro
↓
github.com/jeremylongshore/claude-code-plugins

ClaudeCodePlugins.io
↓
Browse 220+ plugins
```

**Voiceover:**
> "Excel Analyst Pro is part of the Claude Code Plugins marketplace. Browse over 220 plugins for development, automation, and productivity. Link in the description."

---

### Call to Action (4:50-5:00)

**Scene:** End card

**Screen Text:**
```
Try Excel Analyst Pro Today

/plugin install excel-analyst-pro@claude-code-plugins

⭐ Star on GitHub
🌐 claudecodeplugins.io
💬 Questions? github.com/issues
```

**Voiceover:**
> "Try Excel Analyst Pro today. Install with one command, and start building professional financial models in minutes."

---

## 🎥 Recording Instructions

### Equipment Needed
- Screen recording software (OBS Studio, QuickTime, Loom)
- High-quality microphone
- 1920x1080 resolution (minimum)

### Terminal Setup
```bash
# Use a clean terminal
# Font: 18-20pt for readability
# Theme: Dark theme with good contrast
# Claude Code: Latest version
```

### Recording Tips

1. **Pre-record Claude responses**
   - Since you can't control Claude's exact output, pre-write the ideal responses
   - Edit the demo to show "ideal" flow

2. **Use screen annotations**
   - Highlight important text with boxes/arrows
   - Use callouts for "auto-invoked" moments
   - Add icons for Skills

3. **Pace yourself**
   - Speak slowly and clearly
   - Pause 1-2 seconds between sections
   - Leave time for viewers to read screen text

4. **Music**
   - Use light, professional background music (low volume)
   - No music during voiceover (distracting)
   - Fade music in/out smoothly

5. **Graphics**
   - Add animated transitions between demos
   - Use brand colors (Charcoal Slate theme)
   - Include plugin logo if available

---

## 📝 Voiceover Script (Full Text)

**Opening:**
> "What if you could build a professional DCF model in 5 minutes instead of 2 hours? With Excel Analyst Pro for Claude Code, you can."

**DCF Demo:**
> "Let's value Tesla using a DCF model. No Excel formulas to remember—just natural language."

> "Notice: Claude automatically detected 'DCF model' and loaded the DCF Modeler Skill. No slash command needed."

> "The Skill asks intelligent questions, using industry standards as defaults. It knows what financial analysts need."

> "In under a minute, we have a professional 4-sheet DCF model with projections, valuation calculations, and sensitivity analysis. This would normally take 2-3 hours."

**LBO Demo:**
> "Let's try something more complex: a leveraged buyout model."

> "The LBO Modeler Skill structures the entire transaction automatically."

> "Complete 6-sheet LBO model with debt schedules, IRR calculations, and covenant tracking. Normally a full day's work—done in minutes."

**Variance Demo:**
> "Finance managers can automate monthly variance reports."

> "Automated flagging, commentary, and executive summaries. No more manual variance reports."

**Pivot Demo:**
> "Pivot tables from natural language. No need to remember Excel syntax."

**Features:**
> "Excel Analyst Pro features auto-invoked Skills that load exactly when you need them. Investment banking-grade templates, local processing for security, and it's completely free and open source."

**Comparison:**
> "Unlike cloud-based solutions, Excel Analyst Pro processes everything locally. And unlike Microsoft Copilot, it includes investment banking-grade financial modeling."

**Installation:**
> "Installation is one command. The plugin automatically configures the Excel MCP server and loads all four Skills."

**Closing:**
> "Excel Analyst Pro is part of the Claude Code Plugins marketplace. Browse over 220 plugins for development, automation, and productivity. Link in the description."

**CTA:**
> "Try Excel Analyst Pro today. Install with one command, and start building professional financial models in minutes."

---

## 🎨 Visual Elements

### Title Cards
```
[0:00] Excel Analyst Pro
       Professional Financial Modeling for Claude Code

[0:20] Demo 1: DCF Valuation Model
       Build enterprise valuations in minutes

[1:30] Demo 2: Leveraged Buyout Model
       Private equity analysis made simple

[2:15] Demo 3: Variance Analysis
       Automate budget reporting

[3:00] Demo 4: Pivot Tables
       Natural language data analysis

[3:30] Key Features

[3:50] Comparison

[4:10] Installation

[4:50] Try It Today
```

### Annotations
- **Yellow box**: Highlight auto-invoked Skills
- **Green checkmark**: Completed tasks
- **Blue arrow**: Point to important features
- **Red underline**: Critical information

---

## 📊 YouTube Description Template

```
Excel Analyst Pro - Professional Financial Modeling for Claude Code

Build DCF models, LBO analysis, variance reports, and pivot tables using natural language. No Excel formulas to remember. Investment banking-grade templates with auto-invoked Skills.

⏱️ TIMESTAMPS
0:00 - Introduction
0:20 - DCF Valuation Model Demo
1:30 - Leveraged Buyout Model Demo
2:15 - Variance Analysis Demo
3:00 - Pivot Tables Demo
3:30 - Key Features
3:50 - Comparison vs Competitors
4:10 - Installation
4:50 - Call to Action

🚀 INSTALL NOW
/plugin install excel-analyst-pro@claude-code-plugins

✨ FEATURES
✅ Auto-invoked Skills (no manual commands)
✅ Investment banking-grade templates
✅ Local processing (no cloud upload)
✅ Free & open source (MIT License)
✅ 4 specialized Skills:
   • DCF Modeler
   • LBO Modeler
   • Variance Analyzer
   • Pivot Wizard

🔗 LINKS
📚 Documentation: https://claudecodeplugins.io/plugins/excel-analyst-pro
💻 GitHub: https://github.com/jeremylongshore/claude-code-plugins
🌐 Marketplace: https://claudecodeplugins.io
💬 Issues/Support: https://github.com/jeremylongshore/claude-code-plugins/issues

#ClaudeCode #Excel #FinancialModeling #DCF #LBO #InvestmentBanking #PrivateEquity #Automation #OpenSource
```

---

## 📱 Social Media Clips

### LinkedIn (30 seconds)
**Focus:** Professional financial modeling
**Show:** DCF demo only
**CTA:** "Link to full demo in comments"

### X/Twitter (60 seconds)
**Focus:** Speed and efficiency
**Show:** DCF + LBO demos (fast-paced)
**CTA:** "Full demo: [link]"

### Instagram Reel (60 seconds)
**Focus:** Visual impact
**Show:** Excel models opening, formatted outputs
**CTA:** "Link in bio"

---

## 🎬 Production Checklist

### Pre-Production
- [ ] Install Excel Analyst Pro locally
- [ ] Test all Skills work correctly
- [ ] Prepare sample data (Tesla financials, LBO targets, variance data)
- [ ] Set up terminal with good font size and theme
- [ ] Write exact prompts to use

### Production
- [ ] Record screen at 1920x1080 minimum
- [ ] Record voiceover separately (easier to edit)
- [ ] Capture each demo 2-3 times (pick best take)
- [ ] Record Excel screens showing outputs
- [ ] Get 10 seconds of "B-roll" (Excel sheets scrolling)

### Post-Production
- [ ] Edit video to 3-5 minutes
- [ ] Add title cards and transitions
- [ ] Overlay voiceover audio
- [ ] Add background music (low volume)
- [ ] Add screen annotations (boxes, arrows, callouts)
- [ ] Color grade for consistency
- [ ] Add end card with CTA

### Distribution
- [ ] Upload to YouTube
- [ ] Add to GitHub README
- [ ] Share on LinkedIn, X, Reddit
- [ ] Embed on claudecodeplugins.io
- [ ] Create short clips for social media

---

**Status:** ✅ Demo script ready for recording
**Duration:** 5 minutes (can be edited to 3 minutes if needed)
**Next Step:** Record screen demos following this script
