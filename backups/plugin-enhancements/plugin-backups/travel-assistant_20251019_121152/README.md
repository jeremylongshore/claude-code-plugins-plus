# 🌍 Intelligent Travel Assistant

**Your complete AI-powered travel companion** - Real-time weather, currency conversion, smart itineraries, and expert local tips, all in one plugin.

---

## 🎯 What This Plugin Does

Transform travel planning from hours of research into minutes of AI-powered assistance:
- 🌡️ **Real-time weather** - 7-14 day forecasts with packing recommendations
- 💱 **Currency conversion** - Live exchange rates with budget breakdowns
- 🗺️ **Smart itineraries** - Personalized day-by-day plans
- 🎒 **Packing lists** - Weather and activity-optimized
- 💡 **Local expert tips** - Cultural insights, hidden gems, safety
- 🕐 **Timezone coordination** - Meeting scheduling across time zones

---

## 🚀 Quick Start

### Installation
```bash
/plugin install travel-assistant@claude-code-plugins-plus
```

### Basic Usage
```bash
# Complete travel plan
/travel "Tokyo, Japan" --days 7 --budget 3000

# Quick weather check
/weather Paris

# Currency conversion
/currency 100 USD EUR

# Smart packing list
/pack "Iceland" --days 5

# AI itinerary
/itinerary "Barcelona" --interests "food,architecture"

# Timezone info
/timezone "New York vs London vs Tokyo"
```

---

## 💡 Core Features

### 1. Complete Travel Planning (`/travel`)
One command for comprehensive trip planning:

```bash
/travel "Bali, Indonesia" --days 10 --budget 2500
```

**Includes**:
- ✅ 7-14 day weather forecast
- ✅ Complete budget breakdown
- ✅ Day-by-day itinerary
- ✅ Smart packing list
- ✅ Local tips & cultural insights
- ✅ Safety information
- ✅ Transportation guide

**Multi-city support**:
```bash
/travel "Rome → Florence → Venice" --days 12
```

### 2. Weather Intelligence (`/weather`)
Real-time weather with travel insights:

```bash
/weather Tokyo --days 14
```

**Provides**:
- Current conditions + feels like
- 7-14 day detailed forecast
- Best days for outdoor activities
- Packing recommendations
- Historical comparisons
- UV index & air quality

**Compare destinations**:
```bash
/weather "Barcelona vs Lisbon vs Athens"
```

### 3. Currency Mastery (`/currency`)
Smart currency conversion and budgeting:

```bash
/currency 1000 USD EUR
```

**Features**:
- Real-time exchange rates
- 30-day historical trends
- Budget breakdowns by category
- Exchange tips (best places, avoid fees)
- Multi-currency conversion
- Purchasing power comparison

**Budget planning**:
```bash
/currency 3000 USD JPY --budget
# Shows: per-day spending, category splits, optimization tips
```

### 4. AI Itinerary Generator (`/itinerary`)
Personalized day-by-day travel plans:

```bash
/itinerary "Paris" --days 5 --interests "food,art,history" --pace relaxed
```

**Optimization**:
- Geographic clustering (minimize travel time)
- Weather-based scheduling
- Energy management (intense → relaxed rotation)
- Local dining recommendations
- Hidden gems + must-sees balanced
- Booking requirements noted

**Customization options**:
- `--interests`: food, culture, adventure, nature, art, nightlife
- `--pace`: relaxed, moderate, packed
- `--budget`: budget, mid-range, luxury

### 5. Smart Packing (`/pack`)
Never forget essentials again:

```bash
/pack "Iceland" --days 7 --activities "hiking,northern-lights"
```

**Generates lists based on**:
- Weather forecast (temperature, rain, wind)
- Planned activities
- Trip duration
- Cultural requirements
- Season and destination

**Categories**:
- Clothing (weather-appropriate)
- Electronics & adapters
- Documents & money
- Health & safety
- Activity-specific gear

### 6. Timezone Coordination (`/timezone`)
Time zone mastery for global travelers:

```bash
/timezone "San Francisco vs London vs Tokyo"
```

**Features**:
- Current time in any location
- UTC offsets & DST status
- Meeting scheduler
- Best call times across zones

```bash
/timezone meeting 2pm EST "San Francisco, London, Sydney"
# Shows optimal meeting time for all locations
```

---

## 🤖 AI Agents

### travel-planner
**Master orchestrator** coordinating all travel aspects
- Synthesizes weather, budget, itinerary
- Optimizes scheduling
- Ensures comprehensive planning

### weather-analyst
**Meteorological expert** for travel timing
- Forecast interpretation
- Activity-weather matching
- Seasonal pattern analysis

### local-expert
**Cultural guide** for authentic experiences
- Customs & etiquette
- Hidden gems & local favorites
- Safety tips & scam awareness
- Language essentials

### budget-calculator
**Financial planner** for cost optimization
- Accurate cost estimation
- Budget breakdown by category
- Money-saving strategies
- Currency optimization

---

## 🔗 Command Combinations

### Scenario 1: Planning a Trip
```bash
# Step 1: Get complete plan
/travel "Tokyo" --days 7 --budget 3000

# Step 2: Check detailed weather
/weather Tokyo --days 14

# Step 3: Customize itinerary
/itinerary Tokyo --interests "food,temples,technology"

# Step 4: Finalize packing
/pack Tokyo --days 7
```

### Scenario 2: Budget Optimization
```bash
# Check budget
/currency 2000 USD JPY --budget

# See what it buys
/currency 2000 USD JPY --purchasing-power

# Optimize spending
/travel Tokyo --budget 2000 --optimize
```

### Scenario 3: Multi-City Europe Trip
```bash
# Plan route
/travel "Paris → Amsterdam → Berlin" --days 15

# Check each city's weather
/weather "Paris vs Amsterdam vs Berlin"

# Calculate total budget
/currency 5000 USD EUR

# Create detailed itinerary
/itinerary Paris --days 5
/itinerary Amsterdam --days 4
/itinerary Berlin --days 5
```

---

## ⚙️ Configuration

### API Keys (Optional)
For real-time data, set up free API keys:

```bash
# OpenWeatherMap (weather data)
export OPENWEATHER_API_KEY="your_key_here"

# ExchangeRate-API (currency data)
export EXCHANGERATE_API_KEY="your_key_here"
```

**Get free keys**:
- Weather: https://openweathermap.org/api (1000 calls/day free)
- Currency: https://www.exchangerate-api.com (1500 calls/month free)
- Timezone: WorldTimeAPI (no key needed, unlimited)

**Without keys**: Plugin uses mock data and seasonal averages.

---

## 📊 Real-World Examples

### Example 1: Solo Backpacker
```bash
/travel "Thailand" --days 21 --budget 1500 --interests "beaches,temples,food"

Output:
- Budget breakdown: $70/day (hostels, street food, local transport)
- Best islands: Phi Phi, Koh Samui, Railay
- Must-try: Pad Thai, Mango Sticky Rice, Tom Yum
- Money-saving tips: Night markets, free walking tours
- Packing: Light, breathable clothes, reef-safe sunscreen
```

### Example 2: Luxury Couple's Trip
```bash
/travel "Maldives" --days 10 --budget 15000 --pace relaxed

Output:
- Overwater villa recommendations
- Private island experiences
- Fine dining reservations
- Spa and wellness
- Sunset cruise options
- Photography tips for perfect shots
```

### Example 3: Family Vacation
```bash
/travel "Orlando, Florida" --days 7 --group "2 adults, 2 kids (ages 6,9)"

Output:
- Theme park strategy (avoid crowds)
- Kid-friendly restaurants
- Rest day scheduling
- Pool time + park balance
- Packing for kids (extra clothes, snacks, entertainment)
```

### Example 4: Digital Nomad
```bash
/travel "Lisbon" --days 30 --work-remote

Output:
- Coworking spaces (wifi speed, prices)
- Apartment recommendations (monthly rates)
- Cafe culture for remote work
- Time zone considerations (US/EU hours)
- Long-stay visa requirements
```

---

## 🎯 Pro Tips

### Maximize Value
1. **Use context**: `/travel Tokyo` then `/weather` auto-uses Tokyo
2. **Compare destinations**: Find the best weather/budget combo
3. **Flexible dates**: Get better prices and weather
4. **Local insights**: Hidden gems beat tourist traps

### Save Money
- Book flights 6-8 weeks in advance
- Stay outside tourist centers
- Eat where locals eat (ask agents!)
- Free walking tours for orientation
- City passes for multiple attractions

### Pack Smart
- Roll clothes (saves 30% space)
- Wear bulkiest items on plane
- Leave 20% space for souvenirs
- Packing cubes for organization
- Check weather day before departure

---

## 🔧 Troubleshooting

### Weather not showing?
- Set `OPENWEATHER_API_KEY` environment variable
- Or plugin will use seasonal averages

### Currency not converting?
- Check internet connection
- Verify currency codes (USD, EUR, GBP, etc.)
- Plugin falls back to last known rates

### Itinerary too packed?
- Add `--pace relaxed` flag
- Reduce daily activities
- Include rest days for longer trips

---

## 📈 Performance

**Time Savings**:
- Manual planning: 4-6 hours
- With Travel Assistant: 5-10 minutes
- **Saves**: ~5 hours per trip

**Cost Optimization**:
- Budget recommendations: Save 20-30%
- Currency tips: Save 5-10% on exchange
- Hidden gems: Authentic + cheaper experiences

---

## 🤝 Integration

Works great with:
- **overnight-dev**: Plan trips while Claude codes overnight
- **ai-commit-gen**: Commit travel plans to git
- **devops-automation-pack**: Automate trip documentation

---

## 📚 Command Reference

| Command | Purpose | Example |
|---------|---------|---------|
| `/travel` | Complete travel plan | `/travel Paris --days 5` |
| `/weather` | Weather forecast | `/weather Tokyo --days 14` |
| `/currency` | Currency conversion | `/currency 100 USD EUR` |
| `/timezone` | Timezone info | `/timezone "NY vs London"` |
| `/itinerary` | AI itinerary | `/itinerary Rome --interests food` |
| `/pack` | Packing list | `/pack Iceland --days 7` |

---

## 🌟 Why Travel Assistant?

**Before**: Hours of research across multiple sites
- Weather.com for forecast
- XE.com for currency
- TripAdvisor for attractions
- Random blogs for tips
- Manual itinerary planning

**After**: One plugin, complete planning
- All data in one place
- AI-optimized itineraries
- Context-aware recommendations
- Instant updates
- Expert local knowledge

---

## 🚀 Get Started Now

```bash
# Install
/plugin install travel-assistant@claude-code-plugins-plus

# Plan your next trip
/travel "Your Dream Destination" --days X --budget Y

# Done! 🎉
```

---

**Version**: 1.0.0
**License**: MIT
**Author**: Jeremy Longshore

**Transform travel planning. One command at a time.** ✈️🌍
