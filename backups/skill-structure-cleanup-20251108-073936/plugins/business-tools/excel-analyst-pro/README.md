# Excel Analyst Pro

**Professional financial modeling toolkit for Claude Code with auto-invoked Skills and Excel MCP integration.**

Build DCF models, LBO analysis, variance reports, and pivot tables using natural language. No formulas to remember, no manual Excel work—just describe what you need.

---

## 🚀 Features

### Auto-Invoked Skills
- **DCF Modeler**: Build discounted cash flow valuation models with projections, WACC, and sensitivity analysis
- **LBO Modeler**: Create leveraged buyout models with debt schedules, cash flow waterfalls, and IRR calculations
- **Variance Analyzer**: Automate budget vs actual analysis with flagging, commentary, and executive summaries
- **Pivot Wizard**: Generate pivot tables and charts from raw data using natural language

### Key Benefits
- ✅ **Natural Language**: Just describe what you want—no Excel formulas to remember
- ✅ **Auto-Invoked**: Claude automatically detects when to use each Skill
- ✅ **Investment Banking Grade**: Follows IB best practices and standards
- ✅ **Local Processing**: No cloud upload—all Excel work happens locally
- ✅ **Token Efficient**: Skills load only when relevant (50% cheaper than MCP alone)
- ✅ **Team Standardization**: Everyone uses the same best practices

---

## 📦 Installation

### Prerequisites
- Claude Code 1.0+
- Node.js 18+

### Quick Install

```bash
/plugin install excel-analyst-pro@claude-code-plugins
```

This will automatically:
1. Install the plugin
2. Configure @negokaz/excel-mcp-server
3. Load all 4 Skills into Claude Code
4. Add slash commands

---

## 🎯 Usage

### DCF Valuation Model

Just ask in natural language:

```
You: "Create a DCF model for Tesla"

Claude: I'll build a DCF valuation model for Tesla. Let me gather some inputs.

What base year revenue should we use for Tesla?
(For reference, Tesla's 2023 revenue was approximately $96.8B)

You: $96.8 billion

Claude: Great! What revenue growth rates should we assume for Years 1-5?

You: 25%, 20%, 15%, 12%, 10%

Claude: [Builds complete DCF model with 4 sheets]

✅ DCF Model Complete!

📊 Valuation Results:
- Enterprise Value: $847.3 billion
- Implied equity value per share: $243

📁 Model saved to: Tesla_DCF_Model.xlsx
```

**That's it!** No Excel formulas, no manual work.

---

### LBO Analysis

```
You: "Build an LBO model for a $50M EBITDA software company"

Claude: I'll create an LBO model. What entry multiple should we assume?
(Software companies typically trade at 10-15x EBITDA)

You: 12x

Claude: [Builds complete LBO model with 6 sheets]

✅ LBO Model Complete!

📊 Base Case Returns (5-year hold, 12x exit):
- Exit Equity Value: $1,124M
- Money-on-Money: 4.2x
- IRR: 34.2%

📁 Model saved to: Software_LBO_Model.xlsx
```

---

### Variance Analysis

```
You: "Analyze Q1 budget vs actual"

Claude: [Analyzes data and generates report]

✅ Variance Analysis Complete!

🔴 CRITICAL VARIANCES:
- EBITDA: $270K vs $450K (-40.0%) - $180K under
- Operating Expenses: $840K vs $750K (+12.0%) - $90K over

📁 Report saved to: Q1_2025_Variance_Analysis.xlsx
```

---

### Pivot Tables

```
You: "Show sales by region and product category"

Claude: [Creates pivot table and visualization]

✅ Pivot Table Created!

Top Insights:
1. West region leads with $1.45M (30.3% of total)
2. Electronics is #1 category at $1.70M (35.6%)
3. Northeast + Electronics = $400K (highest cell)

Visualization: Added column chart comparing regions
```

---

## 📚 Skills Documentation

Each Skill has detailed documentation in its `SKILL.md` file:

### 1. DCF Modeler
**File:** `skills/excel-dcf-modeler/SKILL.md`

**Triggers:**
- "Create a DCF model"
- "Build a valuation model"
- "Calculate enterprise value"
- "Value [company]"

**Outputs:**
- 4-sheet Excel model (Assumptions, FCF Projections, Valuation, Sensitivity)
- Enterprise value calculation
- Sensitivity analysis (WACC vs terminal growth)

---

### 2. LBO Modeler
**File:** `skills/excel-lbo-modeler/SKILL.md`

**Triggers:**
- "Create an LBO model"
- "Build a leveraged buyout model"
- "Private equity analysis"
- "Calculate IRR for acquisition"

**Outputs:**
- 6-sheet Excel model (Transaction, Sources & Uses, Operating, Debt Schedule, Returns, Covenants)
- IRR and money-on-money calculations
- Multiple sensitivity tables

---

### 3. Variance Analyzer
**File:** `skills/excel-variance-analyzer/SKILL.md`

**Triggers:**
- "Analyze budget variance"
- "Compare actual vs forecast"
- "Create variance report"
- "Why are we over/under budget?"

**Outputs:**
- 3-sheet Excel report (Variance Summary, Executive Summary, Trend Analysis)
- Automated flagging (🔴 critical, ⚠️ warning, ✅ on track)
- Commentary and recommendations

---

### 4. Pivot Wizard
**File:** `skills/excel-pivot-wizard/SKILL.md`

**Triggers:**
- "Create a pivot table"
- "Analyze [data] by [dimension]"
- "Summarize sales by region"
- "Show revenue breakdown"

**Outputs:**
- Pivot tables with professional formatting
- Charts and visualizations
- Slicers and filters
- Calculated fields

---

## 🛠️ Technical Details

### Plugin Architecture

```
excel-analyst-pro/
├── plugin.json                    # Plugin configuration
├── README.md                      # This file
├── skills/                        # Auto-invoked Skills
│   ├── excel-dcf-modeler/
│   │   ├── SKILL.md              # DCF modeling instructions
│   │   └── resources/
│   │       └── dcf-template.xlsx
│   ├── excel-lbo-modeler/
│   ├── excel-variance-analyzer/
│   └── excel-pivot-wizard/
├── mcp/                          # MCP server config
│   └── excel-config.json
├── slash-commands/               # Manual triggers (optional)
│   ├── build-dcf.md
│   ├── build-lbo.md
│   └── analyze-variance.md
└── examples/                     # Example files
```

### MCP Server Integration

This plugin uses `@negokaz/excel-mcp-server` for Excel operations:

**Configuration:**
```json
{
  "command": "npx",
  "args": ["--yes", "@negokaz/excel-mcp-server"],
  "env": {
    "EXCEL_MCP_PAGING_CELLS_LIMIT": "4000"
  }
}
```

**Capabilities:**
- Read and write Excel (.xlsx) files
- Create sheets and workbooks
- Write formulas
- Format cells
- No Microsoft Excel installation required

---

## 💡 How It Works

### Skills + MCP Server = Complete Solution

**MCP Server (Low-Level):**
- Provides Excel file operations
- Read cells, write formulas, create sheets
- Like having a toolbox 🧰

**Skills (High-Level):**
- Provide domain expertise
- Financial modeling patterns, best practices
- Like having an expert consultant 👔

**Together:**
- Professional results with zero effort 🚀

### Example Flow

```
User: "Create a DCF model"
        ↓
Claude detects "DCF model" in request
        ↓
Auto-loads excel-dcf-modeler Skill
        ↓
Skill provides instructions:
  - Ask for company and assumptions
  - Build 4-sheet model structure
  - Calculate enterprise value
  - Create sensitivity tables
        ↓
Skill calls MCP server to:
  - create_workbook()
  - add_sheet()
  - write_formula()
  - format_cells()
        ↓
Output: Professional DCF model
```

**No manual invocation needed!** Just natural language.

---

## 📈 Use Cases

### Investment Banking Analysts
- **Before**: 2-3 hours to build DCF from scratch
- **After**: 5 minutes with professional results
- **Time Saved**: 2-3 hours per model

### Private Equity Associates
- **Before**: Full day to build LBO model
- **After**: 10 minutes with complete analysis
- **Time Saved**: 7-8 hours per deal

### Finance Managers
- **Before**: 2 hours for monthly variance analysis
- **After**: 5 minutes with automated commentary
- **Time Saved**: 1 hour 55 minutes per month

### Data Analysts
- **Before**: 55 minutes to clean data, create pivots, format charts
- **After**: 3 minutes end-to-end
- **Time Saved**: 52 minutes per report

---

## 🎓 Best Practices

### 1. Start with Defaults

Don't have all assumptions? No problem:

```
You: "Build a DCF but I don't have all the numbers"

Claude: No problem! I can build with industry-average assumptions.
What company are you valuing?

You: Amazon

Claude: I'll use standard assumptions for large-cap tech:
- Revenue growth: 15%, 12%, 10%, 8%, 6%
- EBITDA margin: 25%
- WACC: 9%

You can adjust the "Assumptions" sheet later.
```

### 2. Ask for Explanations

```
You: "Explain the DCF model you built"

Claude: Sure! Let me walk through the DCF model:

📊 What is a DCF?
A DCF values a company based on its future cash flows...

[Detailed explanation provided]
```

### 3. Iterate and Refine

```
You: "The WACC seems high—can we try 8% instead of 10%?"

Claude: Absolutely! Updating WACC from 10% to 8%...

New Enterprise Value: $924B (was $847B)
Change: +$77B (+9.1%)

Lower discount rate increases value as expected.
```

### 4. Request Variations

```
You: "Add a dividend recap in Year 3 to the LBO model"

Claude: I'll add a dividend recapitalization to the model.

In Year 3, after debt paydown:
- Refi to 5.0x EBITDA (from 3.8x)
- Distribute ~$150M to equity sponsors

This boosts IRR by ~300bps with partial liquidity.
```

---

## ⚠️ Limitations

### What This Plugin Does Well
- Initial valuation analysis ✅
- Pitch decks and presentations ✅
- Academic exercises ✅
- Quick "back of envelope" valuations ✅
- Team standardization ✅

### What Requires Manual Work
- Official fairness opinions ❌
- Detailed IC presentations (need scenario planning) ❌
- Quarterly debt schedules (annual only) ❌
- Complex waterfall structures ❌
- Third-party data validation ❌

**Recommendation:** Use this plugin for initial analysis (80% of use cases), then refine manually for high-stakes decisions.

---

## 🔒 Security & Privacy

### Local Processing
- ✅ All Excel work happens locally
- ✅ No cloud upload required
- ✅ Works offline
- ✅ Full control over data

**vs Claude for Excel (cloud-based):**
- ❌ Uploads data to Anthropic cloud
- ❌ Requires Max/Enterprise/Teams subscription
- ❌ Subject to data retention policies

**Recommendation:** For sensitive financial data or regulated industries, use this plugin (local processing) instead of cloud-based solutions.

---

## 🆚 Comparison

| Feature | Excel Analyst Pro | Claude for Excel | Microsoft Copilot |
|---------|------------------|------------------|-------------------|
| **Price** | Free (open-source) | Max/Enterprise subscription | $30/user/month |
| **Processing** | Local | Cloud | Cloud |
| **Skills Included** | 4 (DCF, LBO, Variance, Pivot) | Limited beta | General assistance |
| **Customizable** | ✅ Fully | ❌ No | ❌ No |
| **Team Sharing** | ✅ Copy/paste Skills | ❌ Cloud only | ❌ Cloud only |
| **Financial Models** | ✅ IB-grade templates | ✅ (beta) | ❌ Basic |
| **Token Efficient** | ✅ Skills on-demand | ❌ Always loaded | N/A |

---

## 🐛 Troubleshooting

### Plugin Not Loading

```bash
# Check Claude Code version
claude --version

# Reinstall plugin
/plugin uninstall excel-analyst-pro
/plugin install excel-analyst-pro@claude-code-plugins
```

### MCP Server Not Working

```bash
# Verify Node.js version
node --version  # Should be 18+

# Manually test MCP server
npx --yes @negokaz/excel-mcp-server
```

### Skill Not Triggering

**Problem:** You said "create DCF" but the Skill didn't load.

**Solution:** Be more explicit:
```
❌ "create DCF"
✅ "Create a DCF model for Apple"
```

Skills trigger on description matching—provide enough context.

---

## 🤝 Contributing

Want to add more Skills or improve existing ones?

1. Fork the repository
2. Create a new Skill in `skills/`
3. Follow the SKILL.md format (see existing Skills)
4. Test with real Excel workflows
5. Submit a pull request

**Ideas for new Skills:**
- Comparable company analysis (comps)
- M&A accretion/dilution model
- Three-statement financial model
- Portfolio performance tracker
- Budget template generator

---

## 📄 License

MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- **Anthropic** for Claude Code and Skills system
- **@negokaz** for excel-mcp-server
- **Investment banking community** for modeling best practices

---

## 📞 Support

- **Issues**: https://github.com/jeremylongshore/claude-code-plugins/issues
- **Discussions**: https://github.com/jeremylongshore/claude-code-plugins/discussions
- **Website**: https://claudecodeplugins.io

---

## 🚀 What's Next

### Roadmap
- [ ] Comparable company analysis Skill
- [ ] M&A accretion/dilution Skill
- [ ] Three-statement model builder
- [ ] Chart generation Skill
- [ ] VBA macro assistant
- [ ] Excel → Database migration tools

### Version History
- **v1.0.0** (2025-10-27): Initial release with 4 core Skills

---

**Made with ❤️ for the Claude Code community**

**Star this repo** if you find it useful! ⭐
