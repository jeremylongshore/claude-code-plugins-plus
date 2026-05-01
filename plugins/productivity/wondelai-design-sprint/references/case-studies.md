# Design Sprint Case Studies

These case studies illustrate how real teams used the design sprint process to solve critical business problems. Each study follows the five-day structure and highlights what worked, what did not, and what lessons emerged. The companies range from well-funded startups to large enterprises to nonprofits.

## Case Study 1: Slack - Onboarding New Teams

### Company

Slack, the workplace messaging platform. At the time of this sprint, Slack was growing rapidly but facing a critical problem: many teams signed up but never became active users.

### Challenge

New teams would create a Slack workspace, invite a few colleagues, and then go quiet within 48 hours. The data showed that teams who sent 2,000 messages within the first week had a 93% retention rate, but most teams never reached that threshold. The sprint question: "How might we get new teams to their first 2,000 messages faster?"

### Sprint Process

**Monday:** The team mapped the journey from "admin creates workspace" to "team sends 2,000 messages." They identified a critical gap: after the admin invited colleagues, those colleagues received a generic email that did not explain why they should join or what to do first. The target became the first 30 minutes after a team member accepts the invitation.

**Tuesday:** Lightning Demos included how Duolingo gets users to complete their first lesson within 60 seconds and how multiplayer games create immediate social interactions. The team sketched solutions ranging from a guided onboarding wizard to a bot that would prompt conversation topics.

**Wednesday:** The winning sketch was "Slackbot Welcome," a concept where an AI bot would greet each new team member, ask them a fun question, and post their answer in the general channel, creating immediate social activity.

**Thursday:** The team prototyped a click-through showing the invitation email (redesigned with a clear value proposition), the first login experience, and the Slackbot interaction. They used Figma for the app screens and rewrote the email copy to emphasize team connection rather than product features.

**Friday:** 5 participants (team leads at small companies) walked through the prototype. 4 out of 5 said they would respond to the Slackbot question. 3 out of 5 said the redesigned email made them significantly more likely to click through compared to the existing email.

### Results

The redesigned invitation email increased click-through rates by 30% in subsequent A/B testing. The Slackbot conversation starter was refined over several iterations and became part of the default onboarding flow.

### Lessons

- The biggest opportunity was not in the product interface but in the email that brought people to the product
- Social interaction (not feature discovery) was the key driver of early retention
- The team's initial assumption that users needed a "product tour" was wrong; users needed a reason to talk

## Case Study 2: Blue Bottle Coffee - Online Store

### Company

Blue Bottle Coffee, a specialty coffee roaster known for its carefully curated in-store experience. They wanted to translate that experience to e-commerce.

### Challenge

Blue Bottle's existing online store looked and felt like every other e-commerce site: grid of products, add to cart, checkout. It did not communicate their brand's emphasis on freshness, origin, and craft. The sprint question: "Can we create an online buying experience that feels as personal as visiting a Blue Bottle cafe?"

### Sprint Process

**Monday:** The team mapped the in-store experience alongside the online experience. In-store, a barista asks what flavors you like and recommends a coffee. Online, customers stared at 40 bags of coffee with no guidance. The target: the moment a new customer decides which coffee to buy.

**Tuesday:** Lightning Demos included how Stitch Fix uses a style quiz to personalize recommendations, how wine apps describe flavor profiles visually, and how the Blue Bottle barista script actually works in stores. Solution sketches ranged from a "coffee quiz" to a curated subscription to a visual flavor map.

**Wednesday:** The Decider chose a combination: a simple 3-question quiz ("What do you usually drink? How do you brew? What flavors do you like?") followed by a personalized recommendation with tasting notes and origin story.

**Thursday:** The prototype was built in Keynote with linked slides. Each quiz answer led to a different recommendation page. The team wrote detailed copy for 4 different coffee recommendations, including origin stories, roast dates, and brewing tips.

**Friday:** 5 participants (regular online coffee buyers who had never tried Blue Bottle) tested the prototype. All 5 completed the quiz. 4 out of 5 said the recommendation felt personal and trustworthy. 3 out of 5 said they would pay a premium because the quiz made them feel confident in the choice. 1 participant said "This is like having a barista in my phone."

### Results

Blue Bottle launched a version of the coffee quiz on their website. It became one of the highest-converting entry points for new customers and was later adapted for their mobile app.

### Lessons

- Translating a physical experience to digital requires identifying the core emotional value, not just the functional steps
- A quiz format transforms a passive catalog into an interactive experience
- Customers will pay more when they feel guided rather than overwhelmed by choice

## Case Study 3: Savioke - Robot Hotel Delivery

### Company

Savioke, a robotics startup building autonomous delivery robots for hotels. Their robot, Relay, delivered items like toothbrushes and snacks from the front desk to guest rooms.

### Challenge

The robot worked technically, but hotels were hesitant to adopt it. The sprint question: "Will hotel guests react positively to a robot delivering items to their room, and will hotels see it as a brand enhancer rather than a gimmick?"

### Sprint Process

**Monday:** The team mapped the guest experience from calling the front desk to receiving the item. They identified two critical moments: the guest's first sight of the robot in the hallway and the handoff at the guest room door. The target: the doorway interaction when the robot arrives.

**Tuesday:** Lightning Demos included how Disney designs character interactions at theme parks (anticipation, surprise, delight), how Amazon delivery confirms successful drop-off, and how vending machines provide instant gratification. Sketches explored different robot behaviors: should it make sounds? Display a screen? Wait for the guest to open the door?

**Wednesday:** The winning concept featured a robot that calls the guest's room phone to announce arrival, displays a friendly message on its screen, opens its lid for the guest to retrieve the item, and does a happy wiggle when the lid closes. The team debated the wiggle extensively, but the Decider approved it.

**Thursday:** The team could not prototype a physical robot interaction digitally, so they used a Wizard of Oz approach: they programmed the actual Relay robot with the new behaviors and prepared to have real guests interact with it at a partner hotel.

**Friday:** Instead of a standard screen-based prototype test, the team set up at a hotel. 5 guests who had called the front desk for items were surprised by the robot delivery. The team observed from the security camera feed and debriefed guests immediately after. All 5 guests smiled or laughed when the robot arrived. 4 out of 5 pulled out their phones to take a photo or video. The wiggle generated the strongest positive reaction, with 3 guests saying "That's adorable" or similar. 0 guests expressed discomfort or concern.

### Results

Savioke refined the interaction based on the sprint findings and deployed Relay in multiple hotel chains. The wiggle became a signature behavior. Hotels reported that robot deliveries generated social media posts from guests, providing free marketing.

### Lessons

- Physical product sprints can use Wizard of Oz prototyping instead of screen mockups
- Emotional design details (the wiggle) can be the difference between a gimmick and a beloved experience
- Testing in context (a real hotel, not a lab) provided higher-quality reactions
- The sprint question was answered definitively in one day: guests love robot delivery

## Case Study 4: Flatiron Health - Cancer Research Data

### Company

Flatiron Health, a healthcare technology company building software to organize cancer research data from electronic health records. Their users were oncologists and clinical researchers.

### Challenge

Oncologists needed to find eligible patients for clinical trials, but the process involved manually searching through medical records. Flatiron had the data but the interface was designed for data scientists, not doctors. The sprint question: "Can we build a clinical trial matching tool that oncologists will actually use during patient appointments?"

### Sprint Process

**Monday:** The team included two oncologists, a data scientist, a designer, and a product manager. The expert interviews revealed that oncologists have approximately 15 minutes per patient appointment and will not use any tool that takes more than 30 seconds to deliver a result. The target: the moment when an oncologist wonders "Is there a clinical trial for this patient?"

**Tuesday:** Lightning Demos included how Google Flights shows results instantly with progressive detail, how dating apps use simple yes/no swiping to reduce decision fatigue, and how an existing internal tool (complex but accurate) surfaced matches. Sketches ranged from a fully automated notification system to a single-search-box interface.

**Wednesday:** The winning sketch was a "one-click match" concept: the oncologist clicks a button next to the patient's name in the EHR, and within seconds sees a ranked list of eligible trials with a confidence score and one-line summary for each.

**Thursday:** The team built a Figma prototype with realistic patient data (anonymized). They created 3 patient scenarios with pre-populated trial results. The prototype looked like it was embedded in the existing EHR interface, which was critical for realism.

**Friday:** 5 oncologists tested the prototype between real patient appointments. All 5 understood the interface immediately. 4 out of 5 said they would use it during appointments. The key finding: oncologists cared more about the "why" (why this patient matches this trial) than the "what" (which trials matched). The confidence score was not sufficient; they needed to see the specific matching criteria.

### Results

Flatiron redesigned the matching display to show specific eligibility criteria alongside each trial recommendation. The tool was launched as part of their clinical platform and increased clinical trial enrollment rates at partner hospitals.

### Lessons

- Domain experts (oncologists) on the sprint team prevented the designers from building something technically elegant but clinically useless
- The constraint of 30 seconds per interaction forced ruthless simplicity
- The sprint revealed a critical insight (show "why" not just "what") that would have taken months to discover through traditional development

## Case Study 5: Harvest - Time Tracking for Freelancers

### Company

Harvest, a time tracking and invoicing tool. They noticed that freelancers signed up but abandoned the product before sending their first invoice.

### Challenge

Freelancers found time tracking tedious and rarely did it consistently. Without tracked time, they could not generate invoices, which was the product's core value. The sprint question: "Can we make time tracking effortless enough that freelancers actually do it every day?"

### Sprint Process

**Monday:** The team mapped the freelancer's day from waking up to sending an end-of-month invoice. They discovered that freelancers did not think in terms of "projects" and "time entries" (Harvest's mental model) but in terms of "clients" and "what I did today." The target: the daily habit of recording time.

**Tuesday:** Lightning Demos included how fitness apps use daily streaks to build habits, how Uber shows a trip summary after each ride (passive time tracking), and how journaling apps prompt reflection at the end of the day. The team sketched solutions including an end-of-day prompt, automatic time detection from calendar events, and a simplified mobile interface.

**Wednesday:** The Decider chose a "daily digest" concept: at 5 PM, Harvest sends a notification that says "What did you work on today?" The freelancer taps to see their calendar events pre-filled as time entries. They confirm, adjust, or add entries in under 60 seconds.

**Thursday:** The prototype was a series of mobile screens in Figma showing the notification, the pre-filled daily digest, and the one-tap confirmation flow. The Writer created realistic calendar data for a fictional freelance designer.

**Friday:** 5 freelancers tested the prototype. All 5 said the end-of-day prompt was significantly better than opening the app and manually starting timers. 3 out of 5 said the pre-filled entries from calendar data would save them the most time. The biggest complaint: 2 out of 5 did not use a calendar for all their work, so the pre-fill was incomplete.

### Results

Harvest launched a simplified end-of-day tracking feature that reduced the average time-tracking effort from 5 minutes per day to under 1 minute. Calendar integration became a premium feature.

### Lessons

- The product's mental model (projects, time entries) did not match the user's mental model (clients, what I did today)
- Passive data collection (calendar events) dramatically reduced user effort
- The sprint revealed that the core problem was not the interface but the workflow: users needed a prompt, not a better stopwatch

## Case Study 6: Code for America - Government Benefits Application

### Company

Code for America, a nonprofit that works with government agencies to improve public services through technology. They were redesigning the application process for government benefits (food assistance, healthcare, childcare subsidies).

### Challenge

The existing application form was 40 pages long, required documentation that applicants often did not have, and took an average of 3 hours to complete. Many eligible people abandoned the application. The sprint question: "Can we reduce the application from 3 hours to under 20 minutes while still collecting the information the government needs?"

### Sprint Process

**Monday:** The team included a benefits caseworker, a policy expert, two designers, and a developer. Expert interviews revealed that 60% of form fields were either redundant, rarely used for eligibility determination, or could be verified through existing government databases. The target: the first 10 minutes of the application, which had the highest abandonment rate.

**Tuesday:** Lightning Demos included how TurboTax turns a complex tax form into a conversational Q&A, how UK.gov reduced government forms to plain language, and how mobile banking apps use progressive disclosure. Sketches included a chatbot-style application, a "tell us about yourself" conversational form, and a staged approach that collects only essential information first.

**Wednesday:** The winning concept was a staged application: Stage 1 collects only what is needed for a preliminary eligibility check (5 questions), Stage 2 completes the full application only if the applicant qualifies. This meant applicants who were not eligible learned within 2 minutes instead of investing 3 hours.

**Thursday:** The team built a mobile-first prototype with clear, plain-language questions, large buttons, and a progress indicator. They included a Spanish language option for 3 of the 5 screens.

**Friday:** 5 participants were recruited from a community center that assists benefits applicants. 4 out of 5 completed Stage 1 in under 3 minutes. All 5 said the language was clearer than the existing form. 3 out of 5 expressed relief at learning their eligibility early: "I wish all government forms started by telling you if you qualify." 1 participant who was not tech-savvy needed help navigating the mobile interface.

### Results

The staged application approach was adopted by several counties in California. Initial data showed a 40% reduction in application abandonment and a 25% increase in completed applications.

### Lessons

- Government services benefit enormously from design sprints because the user experience is often decades behind the private sector
- Involving a policy expert on the sprint team prevented the designers from cutting fields that were legally required
- The biggest insight was structural (staged vs. linear) not visual (better buttons or colors)
- Testing with actual benefits applicants (not proxies) was essential for realistic feedback

## Case Study 7: Grind Coffee - Subscription Model

### Company

Grind, a London-based coffee company with physical cafes exploring a direct-to-consumer subscription for home coffee delivery.

### Challenge

Grind had strong brand recognition from their cafes but no online subscription presence. They did not know if their cafe customers would pay for a home delivery subscription or what the subscription experience should look like. The sprint question: "Will Grind cafe customers subscribe to home coffee delivery, and what do they need to see to commit?"

### Sprint Process

**Monday:** The team mapped two journeys: the existing cafe visit and the hypothetical subscription sign-up. They discovered that cafe loyalty was emotional (community, baristas, atmosphere) while subscription would need to be practical (convenience, freshness, value). The target: the subscription landing page where a cafe customer decides whether to subscribe.

**Tuesday:** Lightning Demos included Dollar Shave Club's viral landing page, how Nespresso creates a luxury unboxing experience, and how HelloFresh explains subscription flexibility (skip, pause, cancel). Solution sketches explored different value propositions: freshness guarantee, exclusive blends, customization, and environmental impact.

**Wednesday:** The Decider chose a landing page concept that led with freshness ("Roasted on Monday, at your door by Wednesday") combined with a simple quiz to match the customer's taste profile. The key differentiator: each delivery would include a handwritten-style note from the roaster.

**Thursday:** The team built a Keynote click-through prototype of the landing page, taste quiz, subscription configuration (frequency, grind type, quantity), and confirmation page. They used real product photography from Grind's existing marketing materials.

**Friday:** 5 Grind cafe regulars tested the prototype. All 5 understood the value proposition immediately. 4 out of 5 said they would subscribe. The freshness angle ("roasted on Monday") was the most compelling element, cited by all 5 participants. The roaster's note was cited by 3 out of 5 as a differentiator from generic subscriptions. Pricing was the main concern: 2 participants said they would need to see a clear comparison to their current cafe spending.

### Results

Grind launched their subscription service using the freshness-first messaging and taste quiz validated in the sprint. The subscription business grew to become a significant revenue stream alongside their physical cafes.

### Lessons

- Existing customers are the best first audience for a new product line, but their motivations may differ from what the team assumes
- A concrete detail ("roasted on Monday, at your door by Wednesday") is more persuasive than an abstract claim ("fresh coffee delivered")
- The sprint identified a gap (pricing comparison) that the team had not considered, leading them to add a "cost per cup" calculator to the final landing page

## Cross-Cutting Patterns

Looking across all seven case studies, several patterns emerge:

### The Target Is Rarely Where You Expect

In 5 out of 7 cases, the Monday target ended up in a different part of the journey than the team initially expected. Slack thought the problem was in-app onboarding; it was in the invitation email. Harvest thought the problem was the timer UI; it was the daily workflow.

### Simplicity Wins

Every successful sprint prototype was simpler than the team's initial instinct. Flatiron went from a complex dashboard to a one-click button. Code for America went from a 40-page form to 5 questions. The design sprint's time constraint forces simplicity.

### Friday Reveals Surprises

In every case, at least one significant Friday finding was unexpected. Savioke did not expect the wiggle to be the standout feature. Flatiron did not expect oncologists to prioritize "why" over "what." Blue Bottle did not expect customers to pay a premium based on quiz-driven confidence.

### Domain Experts Are Essential

The most successful sprints (Flatiron, Code for America) included domain experts as full team members, not just Monday interviewees. Their constraints and insights prevented the team from designing solutions that were technically elegant but practically useless.

### Real Users, Real Context

Savioke tested in a real hotel. Code for America recruited from a community center. The closer the test environment matches reality, the more reliable the results.

### One Week Is Enough

Every team started the sprint week doubting they could prototype and test in 5 days. Every team ended the week with actionable insights they would not have had for months under a normal development process.
