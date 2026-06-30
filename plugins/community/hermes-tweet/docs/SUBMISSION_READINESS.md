# Submission Readiness

Use this checklist before proposing Hermes Tweet to a skill, plugin, MCP,
catalog, awesome list, or target project. It keeps submissions native,
maintainer-friendly, and easy to merge.

## Fit

Submit Hermes Tweet only when the target has a native route for at least one of
these surfaces:

- Hermes Agent plugins or Hermes skills
- X/Twitter, tweet, social listening, monitoring, digest, or publishing tools
- MCP servers that document optional Hermes Agent backends
- OpenClaw or ClawHub skills that accept complementary backend guidance
- Claude Code plugin catalogs that accept source repositories with
  `.claude-plugin` metadata
- Codex plugin catalogs that accept source repositories with `.codex-plugin`
  metadata, a root security policy, local icon, and scanner evidence
- Skill registries, plugin catalogs, awesome lists, or ecosystem directories

Do not submit when the target is only a browser-cookie workflow, only a
TweetClaw route, a generic Xquik MCP server data entry, unrelated to X/Twitter
or Hermes Agent, archived, or explicitly incompatible with contribution. Missing
license metadata or an absent root license is review context, not a blocker.
Note the absence when useful, but reject only explicit incompatible licenses or terms that prohibit outside contributions. Reject personal Claude Code plugin marketplaces, personal Claude Code marketplaces whose contribution docs say random outside skills are not accepted, Claude-only plugin marketplace hubs without Hermes Agent lanes, README-only marketplace shells, owner-only public Claude Code catalogs whose README says every plugin lives in that owner's repositories, owner-namespace-locked Claude plugin marketplaces, developer-workflow-only marketplaces without social, X/Twitter, Hermes Agent, or external source-repository lanes, verified product skill catalogs, or product-owned
marketplaces that describe themselves as owner-specific, team-specific, owner-curated, or closed to random additions unless their docs clearly invite third-party Hermes Tweet submissions.
Reject branded Claude plugin catalogs that describe themselves as the official
catalog for one vendor, team, or product family, including owner-branded Claude
plugin catalogs with owner-owned marketplace manifests. If plugin updates flow from that owner's source repositories or the catalog invites PRs but every plugin, install namespace, or source repository is owner-scoped, treat it as a compatibility example, not a third-party submission route, unless the docs explicitly accept outside source repositories.
A `source.github` or similar repository-pointer schema is not enough by itself:
when the marketplace instructions say it is the canonical hub for the owner's
own skills, reject it unless the contribution docs explicitly invite outside
source repositories.
Reject company engineering hubs, internal workflow marketplaces, daily mirrored product skill catalogs, framework-review-only skill packs, and
single-namespace catalogs whose install commands or plugin metadata are scoped
to one organization, team, or owner. Open standards, Agent Skills compatibility,
or Claude marketplace metadata do not make those routes eligible unless the
target explicitly invites third-party source repositories.
Do not treat a `third-party`, `vendor`, `upstream`, or `external` directory name
as an invitation by itself. If the marketplace is branded as one owner's
official catalog, require contribution docs that explicitly accept unrelated
external source repositories before submitting Hermes Tweet. Reject account-dependent social research skills that forbid private accounts, local credentials, or paid service dependencies.
Review the contribution license after checking both GitHub metadata and obvious
root license files such as `LICENSE`, `LICENSE.md`, `COPYING`, or `NOTICE`.
When metadata is empty but a root license file exists, read it before deciding;
an absent license alone does not disqualify an otherwise native, non-duplicate, non-spam route.
Reject crawler, indexer, dialect-only open memory marketplaces, site-content production skill catalogs, admin-synced in-app skill libraries, app-intake-only skill indexes, PR-closed skill stores, and environment-configured skill ingestion services whose submission path is only a hosted claim form, upload UI, or account-gated directory, token-compressed skill file, team-memory sync artifact, hosted memory config, product content workflow, app-private skill body, or locally configured ingest target unless the repository exposes a seed, source, catalog, or registry file that can be changed by PR and can point to a source-linked Hermes Tweet package entry.
Treat generic AI tools, startup, SaaS, creator-economy, content-creator, influencer-marketing, AI marketing-tools, product-launch, and app directories such
as Product Hunt alternatives, Futurepedia, Toolify, There's An AI For That, or auto-mirrored skill stores that only crawl another upstream catalog as
crawler or indexer directories unless they expose that PR-editable source.
Reject prototype marketplace applications, prototype skill marketplace applications and app-only marketplace shells, whose README documents only API calls, local server setup, or monetized publish flows, plus AI toolkit storefronts, toolhub projects, and agent-tool marketplace scaffolds whose repo only documents application implementations, status documents, roadmaps, or generated UIs without a committed registry seed, catalog file, source entry, PR-editable registry seed, or external source entry.
`curl` publish example is not a PR-native submission route; storefront pages and product pages are evidence only. Require the canonical source file maintainers edit for third-party listings.
Reject provider scanner directories when required endpoint, env_key, auth_style, and free_limits provider fields would force private endpoint, credential, or pricing claims for Hermes Tweet, or when the same target already has an open TweetClaw or adjacent social-provider PR.
Reject distro installers, runtime stacks, OS package indexes, package-manager
recipes, or bundle repos such as Debian packages, Fedora RPMs, Arch AUR,
Nixpkgs, Guix packages, Snapcraft, Flathub, or winget that only vendor or
symlink local skills/plugins unless they expose a documented external plugin
reference list, package source field, or third-party catalog entry. Do not
vendor Hermes Tweet code into another installer just to create a listing.
Reject runtime bridges or installer extensions, slash-command plugin packs,
command-pack marketplaces, or command-only plugin catalogs that only help another
agent consume Claude plugin marketplaces. Treat them as compatibility surfaces
unless they expose an editable catalog entry for third-party plugins or source repositories.
Reject generated catalog, marketplace, source-registry manifest, or installable
catalog manifest files, including release-pinned vendor catalog files, unless target docs identify them as the canonical edit
surface. When a target builds indexes from another source, submit only through
the documented source file or generator input; skip it when that source cannot carry a target-native Hermes Tweet entry.
Reject generated distribution mirrors, read-only sync repositories, and catalog-only source-list shells when their README says manual edits are overwritten or all entries are sourced from the maintainer's own upstream repo.
Treat filename hits such as `catalog.json`, `registry.yaml`, `marketplaces.yml`, seed JSON, or tools YAML as evidence only; submit only when target docs mark that file as the PR-editable source for external source-linked package entries.
Reject local-snapshot Codex plugin marketplaces and contribution workflows that
require creating a local `<plugin>/.claude-plugin/plugin.json` inside the target repository or a vendored plugin
folder inside the target repository unless they also document an external
source-repository entry for third-party plugins. Do not copy, vendor, or
repackage Hermes Tweet into a local target plugin folder to satisfy a registry generator.
Reject official-directory snapshot lists whose contribution rules only accept
plugins already published in an upstream official catalog. Treat them as status
mirrors until Hermes Tweet is already listed in that upstream catalog, then
record the live surface instead of opening a speculative PR.
Reject topic-search hits that are only source repositories, standalone
skills/plugins, framework examples, or product implementations unless the target
exposes a documented third-party catalog, registry, marketplace, or showcase
file intended for external additions. Topic metadata such as `agent-skills`,
`claude-code-plugin`, `mcp-server`, or `awesome-list` is discovery evidence
only; it is not a native submission route without an editable third-party entry
surface.
Reject curated public skill catalogs that require maintainer proof or promotion evidence before a skill enters the public tree, registry CLIs whose author flow only discovers topic-tagged source repositories instead of accepting PR-editable source entries, and product-specific skill packs that require their platform access. Reject product-owned Hermes skill taps, product-owned Hermes skill tap repos, generated product skill bundles, NSFW X/Twitter single-skill source repos, and registry tap repos when the repository is the install source for one vendor's own skill set and has no PR-editable third-party source-entry lane.
Reject framework-specific plugin marketplaces, IDE agent extension marketplaces,
single-app tool collections, offline marketplace mirrors, one-plugin product Codex marketplaces, or SDK tool packages
such as Dify, LangGraph, LlamaIndex, AutoGen, OpenAI Agents SDK, Cline, Roo
Code, Cursor, Windsurf, Open WebUI, LibreChat, AnythingLLM, BeeAI, Rivet, or
Langroid, AutoGPT Forge, OpenAgents, Agent Zero, SuperAGI, BabyAGI, or
Smolagents, DSPy, Julep, MetaGPT, Qwen-Agent, PraisonAI, Swarms, or
Letta, MemGPT, Griptape, Mirascope, Marvin AI, Agency Swarm, Phidata, Motia,
Pydantic AI, AG2, CAMEL AI, Agno, or Flowise, Haystack, Sema4.ai, MindsDB, or
product-specific tool adapters unless the target accepts external source
repositories in Hermes Tweet's shipped package format. Do not translate Hermes
Tweet into another runtime package, tool subclass, module, framework tool,
block, extension, action, pipeline, or function pack just to satisfy a framework
marketplace.
Reject agent-framework runtime toolkits, A2A or agent-card registry
implementations, and tool galleries such as AutoGen, CrewAI, LangGraph, Mastra,
Letta, Semantic Kernel, Pydantic AI, AG2, CAMEL AI, Agno, allenday/a2a-registry,
ericabouaf/a2a-registry, or Peer-to-Service when they require a runtime-specific tool implementation, adapter class, graph node, agent action, registry server,
sample agent card, local demo agent, discovery API, or plugin function instead
of a source-linked Hermes Tweet package entry.
Reject agent tool registries, ToolCard and ToolSpec registries, onchain agent tool registries, and local tool-resolution catalogs when the route accepts API/MCP/CLI tool metadata, smart-contract tool manifests, hosted execution specs, or runtime adapters instead of Hermes Tweet's shipped source repository package.
Reject hosted agent builder, assistant builder, toolgroup, and action-group
catalogs such as Chainlit, Microsoft PromptFlow, Llama Stack, CopilotKit, Rasa
CALM, or AWS Bedrock Agents when the route only accepts app-native tools,
workflow nodes, declarative action groups, prompt-flow components, or
runtime-specific tool definitions. Treat these as integration targets, not
Hermes Tweet outreach routes, unless the target exposes a PR-editable catalog
entry that links to Hermes Tweet's shipped source repository package.
Reject hosted AI app directories and assistant action galleries such as ChatGPT apps, OpenAI Apps SDK examples, GPT Store listings, custom GPT directories, assistant store catalogs, Gemini Gems galleries,
Poe bot marketplaces, Character.AI bot directories, GPT action directories, MCP UI registries, MCP server discovery catalogs, MCP-server-only submit forms, static MCP seed marketplaces, official MCP registry mirrors, upstream server lists, Vercel AI SDK templates, or LangChain Hub snippets
when they require app manifests, UI widgets, action schemas, custom assistant prompts, bot persona cards, SDK demos, hub snippets, or MCP server packages instead
of a source-linked Hermes Tweet package entry, or when Hermes Tweet is not itself an MCP server and the target has no external non-MCP plugin entry surface.
Reject protocol conformance registries, platform-neutral product distribution hubs, TIP-style manifest schema registries, and single-product marketplace manifests when they publish one product's adapters, validator schemas, capability catalogs, or install metadata instead of third-party source-linked Hermes Tweet package entries.
Reject prompt, evaluation, benchmark leaderboard, eval task gallery, and observability hubs such as LangSmith Hub,
PromptLayer, Langfuse, Braintrust, promptfoo, or OpenPipe when they only accept
prompt templates, eval datasets, benchmark tasks, task suites, trace dashboards, eval configs, SDK snippets,
or experiment recipes instead of a source-linked Hermes Tweet package entry.
Reject LLM security, AI guardrails, prompt-injection scanning, red-team evaluation, and AI safety marketplaces such as Lakera Guard integrations, garak plugin catalogs, Guardrails AI Hub validators, LLM vulnerability scanners, or AI policy enforcement catalogs when they only accept scanner rules, guardrail validators, policy packs, red-team scenarios, jailbreak benchmarks, prompt-defense recipes, or safety dashboards instead of a source-linked Hermes Tweet package entry.
Reject model hubs, model galleries, inference-provider catalogs, dataset marketplaces, annotation-template catalogs, synthetic-data marketplaces, feature-store catalogs, experiment-tracking hubs, and
MLOps registries such as Hugging Face Spaces, Hugging Face model hubs, Replicate collections, Ollama libraries, OpenRouter app catalogs, Kaggle datasets, Papers With Code, Roboflow Universe, Label Studio templates, Scale AI marketplaces, MLflow registries, Weights & Biases artifacts, Kubeflow components, Feast feature stores, or model registry catalogs when they only accept hosted models,
demo spaces, model cards, notebooks, datasets, benchmark links, annotation tasks, labeling templates, synthetic-data packages, feature definitions, experiment runs, model artifacts, or model deployment recipes instead of a source-linked Hermes Tweet package entry.
Reject lab, science, biotech, ELN, LIMS, bioinformatics, genomics, chemistry,
and scientific workflow marketplaces such as Benchling app marketplaces, LabKey
app marketplaces, Galaxy Tool Shed, JupyterHub scientific extensions, KNIME Hub
nodes, Nextflow plugin registries, Snakemake workflow catalogs, ELN app
marketplaces, LIMS app marketplaces, or chemistry plugin marketplaces when they
only accept assay templates, sample-tracking connectors, workflow nodes,
pipeline wrappers, notebook extensions, lab instrument integrations, genomic
analysis packages, chemistry tool plugins, or platform-native lab automation
packages instead of a source-linked Hermes Tweet package entry.
Reject academic publishing, citation-manager, reference-manager, scholarly workflow, and preprint template marketplaces such as Zotero plugin catalogs, Mendeley app marketplaces, Overleaf template galleries, ORCID integrations, arXiv tool lists, Crossref app catalogs, or journal workflow marketplaces when they only accept citation plugins, bibliography styles, LaTeX templates, author identifier connectors, preprint workflows, manuscript submission widgets, peer-review forms, or platform-native scholarly packages instead of a source-linked Hermes Tweet package entry.
Reject RAG, retrieval, and vector-store integration catalogs such as LlamaHub,
Pinecone Assistant, Weaviate, Qdrant, Chroma, or retriever plugin galleries
when they only accept data loaders, vector indexes, retriever classes, ingestion
pipelines, or demo notebooks instead of a source-linked Hermes Tweet package entry.
Reject notebook, data-app, and BI assistant galleries such as Jupyter AI,
NotebookLM, marimo, Hex, Deepnote, Observable Framework, or Databricks Apps when
they only accept notebooks, magic commands, app templates, dashboards,
workspace recipes, or data-app examples instead of a source-linked Hermes Tweet package entry.
Reject data-visualization, dashboarding, charting, and BI visual marketplaces
such as Tableau Exchange, Power BI visuals marketplace, Looker Marketplace,
Metabase plugins, Apache Superset extensions, Observable visualization plugins,
Chart.js plugin registries, D3 plugin catalogs, dashboard widget marketplaces,
or reporting widget marketplaces when they only accept dashboard templates,
visual components, chart plugins, BI connectors, metric widgets, report blocks,
data exploration examples, or platform-native visualization packages instead of a source-linked Hermes Tweet package entry.
Reject browser-automation and computer-use agent toolkits such as Browser Use,
Stagehand, Browserbase, Hyperbrowser, Playwright agent tools, or browser-agent
registries when they require browser task scripts, replay recipes, hosted
browser workflows, DOM automation examples, or computer-use action packs instead
of a source-linked Hermes Tweet package entry.
Reject enterprise hosted-agent surfaces such as Google Vertex AI Agent Builder,
Salesforce Agentforce, ServiceNow AI Agent Studio, Oracle AI Agent Studio,
Slack agent platform tools, and Mistral agent connectors when they only accept
platform-native extensions, connectors, actions, or managed-agent definitions.
Reject productivity and workspace app directories such as Google Workspace
Marketplace, Microsoft Teams apps, Slack App Directory, Notion, Airtable,
monday.com, or Asana when they only accept app add-ons, workspace bots,
slash-command apps, database blocks, workspace automations, or product-specific
integrations instead of a source-linked Hermes Tweet package entry.
Reject project management, task management, agile, product roadmap, issue
tracker, bug tracker, ITSM, and service-desk app marketplaces such as
Atlassian Marketplace, Jira apps, Trello Power-Ups, Linear integrations,
ClickUp App Center, Shortcut integrations, GitHub Issues extensions, GitLab
issue integrations, Azure DevOps Marketplace, or product-roadmap marketplaces
when they only accept board widgets, task automations, issue sync connectors,
sprint dashboards, roadmap cards, service-desk macros, incident workflows, or
platform-native project packages instead of a source-linked Hermes Tweet package entry.
Reject localization, translation-management, i18n, and CAT-tool marketplaces
such as Crowdin Marketplace, Lokalise app marketplace, Phrase integrations,
Transifex integrations, Weblate add-ons, Smartling marketplace, DeepL app
marketplace, or Google Translate integrations when they only accept translation
memory connectors, glossary sync apps, localization workflow automations,
machine-translation plugins, string extraction tools, project webhooks, or
translation-provider extensions instead of a source-linked Hermes Tweet package entry.
Reject CRM, support, and commerce app marketplaces, plus ecommerce seller, marketplace seller tools, and social commerce seller app marketplaces, customer
reviews, reputation management, loyalty marketing, referral marketing, affiliate marketing, customer advocacy, rewards program, and UGC marketplace routes
such as HubSpot Marketplace, Salesforce AppExchange, Zendesk Marketplace, Intercom App Store, Freshworks Marketplace, Pipedrive Marketplace, Zoho
Marketplace, Shopify App Store, Amazon seller app marketplaces, eBay seller tools marketplaces, Etsy seller app marketplaces, Walmart Marketplace seller
apps, marketplace seller tools app catalogs, ecommerce seller operations marketplaces, merchant app marketplaces, social commerce seller app marketplaces, Yotpo integrations,
Trustpilot integrations, Reviews.io integrations, Bazaarvoice integrations, Smile.io integrations, LoyaltyLion integrations, ReferralCandy integrations,
Impact.com integrations, or customer engagement marketplaces when they only accept CRM apps, support widgets, sales automations, helpdesk macros, review
widgets, reputation dashboards, loyalty points, referral widgets, affiliate tracking links, creator campaign briefs, rewards program connectors, commerce
app packages, or storefront integrations, seller dashboards, listing sync, order routing, marketplace ads, inventory feeds, or fulfillment workflows instead
of a source-linked Hermes Tweet package entry.
Reject PIM, DAM, product catalog, fashion, apparel, luxury retail,
merchandising, brand asset, and retail content app marketplaces such as Akeneo
App Store, Salsify integrations, Syndigo integrations, Contentful Marketplace,
Bynder integrations, Brandfolder integrations, Shopify product feeds, fashion
retail app marketplaces, apparel merchandising catalogs, or product catalog
marketplaces when they only accept product information connectors, digital
asset widgets, catalog enrichment workflows, merchandising dashboards, SKU sync
tools, product-feed automations, brand-asset portals, or platform-native retail
content packages instead of a source-linked Hermes Tweet package entry.
Reject printing, print-on-demand, ebook, self-publishing, author platform, book distribution, packaging, signage,
digital signage, kiosk display, DOOH, retail media network, label printing, prepress, wide-format printing,
print shop software, product customization, shipping label, print fulfillment app marketplaces, signage CMS, digital menu board app marketplaces,
Kindle Direct Publishing tools, IngramSpark integrations, Kobo Writing Life tools, Draft2Digital connectors, Reedsy marketplaces,
Wattpad app catalogs, Printful app marketplaces, Printify integrations, Gelato print integrations, Lulu publishing integrations, Moo integrations,
VistaPrint integrations, Shippo label printing integrations, EasyPost label integrations, Packhelp integrations, Zakeke product customizer integrations,
PrintNode integrations, Screenly app marketplaces, Yodeck integrations, BrightSign Network apps, or Xibo CMS modules when they only accept
ebook conversion jobs, author profile widgets, royalty dashboards, print product catalogs, fulfillment connectors, shipping label workflows, package design templates,
prepress automation, proofing widgets, wide-format job tickets, product personalization widgets, digital signage playlists, kiosk screen widgets, screen-network schedulers, retail media placements, or platform-native signage packages instead of a source-linked Hermes Tweet package entry.
Reject restaurant, hospitality, hotel, reservation, food delivery, online
ordering, retail POS, and point-of-sale app marketplaces such as Toast Partner
Connect, Square App Marketplace, Clover App Market, Lightspeed integrations,
OpenTable integrations, DoorDash developer apps, Uber Eats integrations, hotel
PMS app marketplaces, hospitality app marketplaces, or restaurant POS app
marketplaces when they only accept menu sync connectors, payment terminal apps,
reservation widgets, delivery workflows, online ordering automations, loyalty
program integrations, property-management connectors, table-management tools,
or platform-native hospitality packages instead of a source-linked Hermes Tweet package entry.
Reject food safety, food manufacturing, CPG, consumer packaged goods, beverage,
brewery, winery, and packaged-goods app marketplaces such as TraceGains
integrations, SafetyChain marketplaces, FoodLogiQ connectors, brewery software
marketplaces, winery software marketplaces, beverage distribution app catalogs,
or CPG retail execution marketplaces when they only accept HACCP checklists,
batch records, recall workflows, compliance labels, cellar management,
distributor ordering, or platform-native food and beverage packages instead of a source-linked Hermes Tweet package entry.
Reject community chat and bot directories such as Discord App Directory,
Discord bot lists, Telegram bot catalogs, Matrix bot directories, Mastodon app
directories, Reddit app directories, or Twitch Extension Marketplace when they
only accept chat bots, server apps, slash commands, moderation workflows, social
feed relays, or extension packages instead of a source-linked Hermes Tweet package entry.
Reject dating, matchmaking, community platform, forum, classifieds, and
marketplace community app directories such as Discourse plugins, Circle
integrations, Mighty Networks app directories, Hivebrite integrations, Tribe
or Bettermode app marketplaces, Sharetribe integrations, dating app
marketplaces, classifieds app marketplaces, or membership community catalogs
when they only accept profile widgets, member-directory apps, forum plugins,
moderation extensions, matchmaking workflows, listing templates, marketplace
seller tools, or platform-native community packages instead of a source-linked Hermes Tweet package entry.
Reject CMS, content publishing, and creator platform marketplaces such as
WordPress Plugin Directory, Drupal module directory, Ghost integrations,
Webflow App Marketplace, Wix App Market, or Squarespace Extensions when they
only accept CMS plugins, theme extensions, site widgets, publishing
automations, form handlers, or website-builder app packages instead of a
source-linked Hermes Tweet package entry.
Reject social listening, brand monitoring, public relations, media relations, press release, newsroom, journalist database, and marketing analytics app
directories such as Hootsuite App Directory, Buffer integrations, Sprout Social app directory, Semrush App Center, brand-monitoring integration galleries,
Muck Rack integrations, Cision app marketplaces, Prowly integrations, Meltwater integrations, press release distribution catalogs, newsroom app
marketplaces, or martech app marketplaces when they only accept dashboards, analytics connectors, reporting widgets, campaign automations, social inbox
apps, press release templates, media lists, journalist outreach workflows, newsroom widgets, earned-media reports, or platform-specific integrations
instead of a source-linked Hermes Tweet package entry.
Reject product analytics, session replay, heatmap, feature flag,
experimentation, A/B testing, customer journey, and growth analytics app
marketplaces such as Amplitude integrations, Mixpanel integrations, PostHog
apps, LaunchDarkly integrations, Optimizely app marketplaces, VWO
integrations, FullStory integrations, Hotjar integrations, Heap integrations,
or customer journey analytics catalogs when they only accept event tracking
connectors, experiment templates, feature flag SDK packages, session recording
widgets, heatmap snippets, funnel dashboards, cohort reports, or
platform-native growth analytics packages instead of a source-linked Hermes Tweet package entry.
Reject customer success app marketplaces, digital adoption platform marketplaces, product adoption app marketplaces, user onboarding app marketplaces, and
in-app guidance catalogs such as Gainsight marketplaces, Pendo integrations, Appcues integrations, Userpilot integrations, ChurnZero marketplaces,
WalkMe app directories, Userflow integrations, or customer education adoption catalogs when they only accept success-plan templates, health score widgets,
onboarding checklist embeds, walkthrough scripts, in-app guides, usage telemetry dashboards, NPS automations, or platform-native adoption packages instead
of a source-linked Hermes Tweet package entry.
Reject SEO, search-console, web analytics, and advertising partner
marketplaces such as Google Search Console integrations, Bing Webmaster Tools
integrations, Ahrefs app marketplace, Moz app marketplace, Similarweb
integrations, Google Analytics integrations, Adobe Analytics Exchange, Google
Ads marketplace, Meta Business Partner Marketplace, or adtech marketplaces
when they only accept site-verification integrations, keyword rank trackers,
SEO audit dashboards, tag-management connectors, campaign reporting widgets,
conversion tracking packages, ads automation apps, or partner-program listings
instead of a source-linked Hermes Tweet package entry.
Reject LMS, documentation, and knowledge-base marketplaces such as Moodle
Plugin Directory, Canvas LMS integrations, Blackboard app catalog, Confluence
Marketplace, GitBook integrations, or knowledge-base app marketplaces when they
only accept course plugins, learning-tool integrations, documentation widgets,
space macros, help-center automations, or knowledge-base connectors instead of
a source-linked Hermes Tweet package entry.
Reject creator course marketplaces, coaching platform app marketplaces, knowledge commerce app marketplaces, and online course platform integration catalogs
such as Teachable app marketplaces, Thinkific app stores, Kajabi app marketplaces, Podia integrations, Maven course platform catalogs, creator coaching
app directories, or cohort course app marketplaces when they only accept course checkout widgets, coaching intake forms, member-area apps, lesson embeds,
student progress dashboards, community prompts, cohort schedule syncs, affiliate links, or platform-native course packages instead of a source-linked
Hermes Tweet package entry.
Reject education, edtech, classroom, school administration, student information
system, campus, university, and district app marketplaces such as Google
Classroom add-ons, Schoology App Center, PowerSchool App Marketplace, Infinite
Campus integrations, ClassLink App Library, Clever Library, K-12 SIS
integration catalogs, campus app marketplaces, or edtech app marketplaces when
they only accept assignment widgets, gradebook sync connectors, roster sync
tools, SSO launch apps, classroom add-ons, SIS connectors, parent portal
workflows, attendance dashboards, campus services apps, or platform-native
education packages instead of a source-linked Hermes Tweet package entry.
Reject API marketplaces, public API networks, and developer portal catalogs
such as RapidAPI, Postman Public API Network, SwaggerHub, Stoplight, ReadMe,
Kong Plugin Hub, or API gateway marketplaces when they only accept API specs,
hosted API listings, request collections, docs workspaces, gateway plugins, or
API management connectors instead of a source-linked Hermes Tweet package entry.
Reject language package indexes, package-manager plugin catalogs, and dependency-registry MCP servers such as PyPI plugin lists, npm package collections, crates.io crates, Homebrew taps, RubyGems, Go module catalogs, pub.dev MCP servers, Hex.pm MCP servers, or lockfile advisory registries when they only accept package metadata, formulae, crates, dependency lookup servers, advisory feeds, or ecosystem-native package entries instead of a source-linked Hermes Tweet package entry.
Reject data warehouse, ETL, reverse ETL, customer data platform, and data
workflow orchestration marketplaces such as Snowflake Marketplace, dbt Package
Hub, Airbyte connectors, Fivetran connectors, Hightouch destinations, Census integrations, Segment integrations, Airflow Providers, Dagster integrations,
Prefect collections, Mage templates, Kestra plugins, Meltano Hub entries, Singer taps, or data integration catalogs when they only accept data connectors,
warehouse apps, transform packages, destination syncs, ingestion pipelines, DAG providers, pipeline assets, orchestration blocks, customer profile activations, or platform-native data app packages instead of a source-linked Hermes Tweet package entry.
Reject data catalog, metadata governance, data lineage, ontology, and knowledge graph marketplaces such as OpenMetadata, DataHub, Amundsen, Collibra, Alation, Atlan, ontology registries, or lineage catalogs when they only accept metadata connectors, lineage extractors, glossary packages, ontology terms, graph schemas, or platform-native governance apps instead of a source-linked Hermes Tweet package entry.
Reject database extension, cache module, search engine plugin, message queue,
event-streaming connector, and graph database app marketplaces such as
PostgreSQL extension registries, pgxn distributions, MySQL plugin directories,
MongoDB integrations, Redis modules, Elasticsearch plugin catalogs, OpenSearch
plugin catalogs, Kafka connector hubs, RabbitMQ plugin directories, or Neo4j
Graph App Gallery when they only accept SQL extensions, database operators,
cache modules, search analyzers, connector plugins, stream processors, queue
adapters, graph widgets, or platform-native data infrastructure packages
instead of a source-linked Hermes Tweet package entry.
Reject SQL client, database admin, schema management, ERD, migration, and ORM extension marketplaces such as DBeaver plugin catalogs, TablePlus extensions, DataGrip plugins, pgAdmin tools, Supabase integration catalogs, Prisma generator registries, Hasura connector catalogs, or schema-tool galleries when they only accept query editor add-ons, database dashboards, schema diff tools, ERD templates, migration helpers, ORM generators, admin panels, or platform-native SQL tooling packages instead of a source-linked Hermes Tweet package entry.
Reject tax, bookkeeping, invoicing, expense management, receipt scanning, FP&A,
treasury, finance, accounting, payroll, procurement, and ERP app marketplaces
such as QuickBooks App Store, Xero App Store, NetSuite SuiteApps, SAP Store,
Workday Marketplace, ADP Marketplace, Stripe App Marketplace, Avalara Marketplace, Bill.com App Center, Expensify integrations, Brex integrations, Ramp app marketplace, or procurement
app marketplaces when they only accept accounting connectors, billing apps,
tax filing workflows, receipt capture connectors, expense approvals, invoice sync widgets, budget dashboards, cash management workflows,
payroll automations, procurement workflows, ERP extensions, or
platform-native financial integration packages instead of a source-linked Hermes Tweet package entry.
Reject banking, lending, mortgage, credit union, wealth management, financial
advisor, loan origination, core banking, and fintech app marketplaces such as
Plaid integrations, nCino marketplaces, Blend integrations, Encompass partner
integrations, Jack Henry marketplaces, Fiserv app marketplaces, Temenos
Exchange, Q2 partner integrations, banking app marketplaces, or lending
software marketplaces when they only accept account data connectors, loan
origination workflows, credit decisioning templates, mortgage application
widgets, advisor CRM syncs, digital banking widgets, KYC workflow connectors,
payment rail adapters, portfolio reporting dashboards, or platform-native
banking packages instead of a source-linked Hermes Tweet package entry.
Reject insurance, claims, risk, broker, policy administration, actuarial, and
insurtech app marketplaces such as Guidewire Marketplace, Duck Creek Content
Exchange, Applied Epic marketplaces, Vertafore marketplaces, insurance app
marketplaces, claims automation marketplaces, broker management app
marketplaces, policy administration app marketplaces, risk modeling
marketplaces, or actuarial app marketplaces when they only accept carrier
connectors, claims workflows, broker-management integrations, policy lifecycle
tools, underwriting dashboards, actuarial models, risk-scoring templates,
document intake automations, or platform-native insurance packages instead of a source-linked Hermes Tweet package entry.
Reject government, civic tech, municipal, public sector, open data,
permitting, 311 service, and public records app marketplaces such as GovTech
app marketplaces, Socrata app marketplaces, ArcGIS Hub civic integrations,
OpenGov marketplaces, Granicus integrations, CivicPlus app marketplaces,
public records software integrations, permitting software marketplaces, or
municipal app marketplaces when they only accept open-data dashboards,
resident-service forms, permitting workflows, 311 request connectors, council
agenda tools, records-request portals, GIS story maps, procurement notices, or
platform-native civic packages instead of a source-linked Hermes Tweet package entry.
Reject political campaign, election, voter outreach, canvassing, petition,
civic advocacy, constituent outreach, ballot, and campaign management app
marketplaces such as NGP VAN integrations, NationBuilder app marketplaces,
Action Network integrations, Ecanvasser integrations, Mobilize integrations,
EveryAction app marketplaces, campaign management marketplaces, voter outreach
app marketplaces, petition platform marketplaces, or advocacy platform app
stores when they only accept canvassing workflows, voter-file syncs, phone bank
tools, text banking automations, petition forms, donation widgets, volunteer
mobilization tools, ballot lookup widgets, constituent email workflows, or
platform-native campaign packages instead of a source-linked Hermes Tweet package entry.
Reject weather, meteorology, emergency management, disaster response, public
safety, 911 software, mass notification, emergency alerting, incident command,
wildfire response, flood alert, and earthquake alert app marketplaces such as
NOAA weather integrations, Everbridge integrations, OnSolve integrations, Rave
Mobile Safety integrations, AlertMedia integrations, Veoci app marketplaces,
WebEOC integrations, or CivicReady integrations when they only accept weather
widgets, hazard data feeds, emergency alert templates, incident command
dashboards, dispatch connectors, mass-notification workflows, evacuation maps,
preparedness forms, or platform-native emergency operations packages instead of a source-linked Hermes Tweet package entry.
Reject defense, military, law enforcement, first responder, CAD, RMS,
body-camera, evidence management, records management, and public safety
software marketplaces such as Axon integrations, Motorola Solutions
marketplaces, Mark43 integrations, Tyler Technologies public safety
marketplaces, CentralSquare integrations, Versaterm integrations, defense
software marketplaces, law enforcement app marketplaces, dispatch software
marketplaces, or evidence management app catalogs when they only accept
computer-aided dispatch connectors, records management workflows, body-camera
ingest tools, evidence vault connectors, incident reporting templates,
case-management syncs, radio system integrations, responder rostering tools,
or platform-native public safety packages instead of a source-linked Hermes Tweet package entry.
Reject nonprofit, fundraising, donor management, association management, membership management,
church management, ministry, faith community, synagogue, mosque, worship planning, labor union,
collective bargaining, worker organization, and member-advocacy app marketplaces such as Blackbaud Marketplace,
DonorPerfect integrations, Bloomerang integrations, Neon CRM app marketplaces, Planning Center app marketplaces,
Pushpay app marketplaces, nonprofit app marketplaces, fundraising app marketplaces, donor management catalogs,
association management marketplaces, faith community app marketplaces, synagogue management app marketplaces,
mosque community app marketplaces, worship planning software marketplaces, union management integrations,
dues management marketplaces, or grievance workflow catalogs when they only accept donation widgets, donor-sync connectors,
membership workflows, pledge forms, volunteer scheduling tools, church directory integrations, ministry communication apps, worship roster tools, sermon media workflows, congregation messaging connectors, collective bargaining workflows, dues collection portals, grievance case forms, shop-steward rosters, or platform-native nonprofit packages instead of a
source-linked Hermes Tweet package entry.
Reject restaurant, hospitality, hotel PMS, food delivery, reservation platform,
point-of-sale, and POS integration marketplaces such as OpenTable Marketplace,
Toast integrations, Square App Marketplace, Clover App Market, DoorDash
developer marketplaces, Uber Eats integration marketplaces, hotel PMS app
marketplaces, hospitality app marketplaces, or restaurant app marketplaces
when they only accept menu sync connectors, table reservation widgets,
ordering workflows, kitchen display integrations, loyalty apps, payment
terminal add-ons, delivery dispatch connectors, or platform-native hospitality
packages instead of a source-linked Hermes Tweet package entry.
Reject legal tech, law practice management, e-discovery, contract lifecycle
management, compliance, and case management marketplaces such as Clio app
directories, MyCase app marketplaces, PracticePanther integrations,
NetDocuments marketplaces, iManage integrations, DocuSign App Center, Ironclad
integrations, Relativity App Hub, or legal app marketplaces when they only
accept matter-management connectors, document management integrations,
e-discovery workflows, contract review templates, e-signature add-ons,
compliance dashboards, time-billing connectors, or platform-native legal
packages instead of a source-linked Hermes Tweet package entry.
Reject intellectual property, patent, trademark, copyright, legal research,
prior art, docketing, and patent analytics marketplaces such as Anaqua app
marketplaces, PatSnap integrations, Clarivate IP integrations, LexisNexis legal
research integrations, Westlaw integrations, FoundationIP marketplaces,
Alt Legal integrations, trademark docketing catalogs, patent analytics app
stores, or legal research app marketplaces when they only accept patent docket
connectors, prior-art search widgets, trademark filing workflows, IP portfolio
dashboards, legal citation tools, matter sync templates, office action
workflows, or platform-native IP management packages instead of a source-linked Hermes Tweet package entry.
Reject real estate, property management, proptech, mortgage, MLS, leasing, construction management, facilities management, building information modeling marketplaces, interior design app marketplaces, home improvement marketplaces, remodeling software marketplaces, renovation contractor marketplaces, furniture home decor app marketplaces, kitchen bath design software marketplaces, flooring cabinet showroom app marketplaces, and home staging app marketplaces such as Procore App Marketplace, AppFolio Stack, Yardi marketplaces, Buildium marketplaces, Autodesk Construction Cloud app marketplaces, Houzz Pro integrations, DesignFiles marketplaces, Buildertrend integrations, CoConstruct integrations, 2020 Design integrations, or construction app marketplaces when they only accept listing sync connectors, lease workflows, tenant portals, work-order automations, property accounting connectors, mortgage origination integrations, BIM content, facilities maintenance apps, mood boards, room layouts, material catalogs, contractor bid workflows, showroom quotes, staging checklists, or platform-native property packages instead of a source-linked Hermes Tweet package entry.
Reject homeowner association, HOA, condo, condominium, strata, co-op,
community association, resident portal, board portal, and property association
app marketplaces such as Vantaca integrations, CINC Systems marketplaces,
Condo Control integrations, TOPS integrations, Enumerate marketplaces,
TownSq integrations, AppFolio association integrations, HOA software
marketplaces, condo management app marketplaces, or strata management
marketplaces when they only accept dues payment connectors, violation
workflows, architectural review queues, amenity booking widgets, resident
portals, board packet templates, maintenance requests, or platform-native
community management packages instead of a source-linked Hermes Tweet package entry.
Reject laboratory, LIMS, ELN, research software, academic, science, lab
automation, and research data management marketplaces such as Benchling App
Marketplace, LabArchives integrations, LabWare LIMS marketplaces, SciNote
integrations, Open Science Framework add-ons, laboratory app marketplaces,
LIMS app marketplaces, or research software marketplaces when they only accept
instrument data connectors, sample tracking workflows, notebook templates,
protocol registries, assay dashboards, research data repositories, grant
reporting tools, or platform-native laboratory packages instead of a
source-linked Hermes Tweet package entry.
Reject pharmaceutical, life sciences, clinical trial, patient recruitment,
pharmacovigilance, drug safety, regulatory affairs, eTMF, EDC, and trial
operations marketplaces such as Veeva integrations, Medidata app marketplaces,
Oracle Clinical integrations, Florence eBinders integrations, Castor EDC
integrations, Trialbee integrations, Saama marketplaces, ArisGlobal
integrations, clinical trial app marketplaces, pharmacovigilance marketplaces,
or regulatory affairs software marketplaces when they only accept trial data
connectors, study startup workflows, patient recruitment widgets, adverse
event intake forms, safety case dashboards, regulatory submission templates,
site monitoring tools, eTMF binders, EDC form extensions, or platform-native
life sciences packages instead of a source-linked Hermes Tweet package entry.
Reject music, audio, podcast, streaming creator, DAW plugin, video production,
livestreaming, radio broadcast, broadcast, NLE plugin, music marketing, creator monetization marketplaces, AI avatar, digital human,
synthetic media, text-to-speech, and voice clone marketplaces such as Spotify developer app
directories, Apple Podcasts integrations, SoundCloud app galleries, Bandcamp developer integrations, Twitch Extensions,
OBS plugin marketplaces, Stream Deck plugin stores, Elgato Marketplace, Adobe Premiere plugin marketplaces, DaVinci Resolve plugin catalogs,
Final Cut Pro plugin marketplaces, DAW plugin marketplaces, podcast app marketplaces, audio plugin marketplaces, HeyGen integrations,
Synthesia app marketplaces, D-ID app directories, ElevenLabs integrations, or Tavus integrations when they
only accept playback widgets, scene widgets, audio processing plugins, stream overlays, channel extensions,
podcast hosting connectors, encoder plugins, control-surface actions, NLE effects, title templates,
media-export presets, artist storefront tools, royalty reporting dashboards, broadcast automation workflows,
avatar render jobs, talking-head templates, voice clone presets, synthetic media assets,
or platform-native media packages instead of a source-linked Hermes Tweet package entry.
Reject agriculture, farming, agritech, precision agriculture, crop analytics,
livestock, and farm management app marketplaces such as John Deere Operations
Center, Climate FieldView app directories, Trimble Agriculture integrations,
Agworld integration marketplaces, Granular app marketplaces, farm management
app marketplaces, crop analytics marketplaces, livestock management
marketplaces, or precision agriculture catalogs when they only accept
equipment data connectors, field operations workflows, crop scouting tools,
yield maps, agronomy dashboards, livestock record systems, farm ERP
integrations, or platform-native agriculture packages instead of a source-linked Hermes Tweet package entry.
Reject cannabis, dispensary, seed-to-sale, cultivation, cannabis point of
sale, cannabis delivery, hemp, and regulated retail app marketplaces such as
Dutchie integrations, Flowhub marketplaces, Treez integrations, Cova Software
integrations, Jane integrations, BioTrack integrations, METRC connector
marketplaces, cannabis compliance marketplaces, cultivation management app
marketplaces, or dispensary delivery marketplaces when they only accept menu
sync widgets, seed-to-sale records, inventory compliance connectors, delivery
dispatch workflows, age-verification checks, cultivation room dashboards,
label-printing templates, or platform-native cannabis retail packages instead of a source-linked Hermes Tweet package entry.
Reject Web3, crypto wallet, dapp, NFT, and decentralized social marketplaces
such as MetaMask Snaps, WalletConnect AppKit plugins, Alchemy dapp galleries,
thirdweb marketplaces, Chainlink Functions galleries, OpenSea app
marketplaces, Farcaster frame catalogs, Lens Protocol app directories, or
wallet plugin marketplaces when they only accept wallet extensions, dapp
templates, smart-contract functions, NFT storefront apps, blockchain
connectors, decentralized social frames, or token-gated app packages instead of a source-linked Hermes Tweet package entry.
Reject energy, utilities, climate, sustainability, ESG, carbon accounting, EV
charging, solar, and smart-grid app marketplaces such as utility data
integrations, Green Button app directories, OpenADR integration catalogs,
ChargePoint app integrations, solar monitoring app marketplaces, carbon
accounting app marketplaces, ESG reporting app catalogs, climate-tech app
marketplaces, or building energy management app marketplaces when they only
accept meter-data connectors, demand-response workflows, charging station
integrations, solar monitoring connectors, carbon-reporting dashboards, ESG
workflow templates, smart-grid adapters, building energy controls, or
platform-native sustainability packages instead of a source-linked Hermes Tweet package entry.
Reject natural resources, mining, oil and gas, petroleum, water utility, waste
management, geoscience, and pipeline operations app marketplaces, plus aquaculture, fisheries,
seafood traceability, and marine farming marketplaces such as mining software marketplaces,
oilfield app stores, petroleum data marketplaces, water utility integration catalogs,
waste management app marketplaces, geology plugin catalogs, geoscience app marketplaces,
pipeline operations catalogs, environmental operations marketplaces, aquaculture app marketplaces,
fishery management catalogs, or seafood supply-chain app marketplaces when they only accept
mine-planning plugins, well log connectors, reservoir dashboards, field operations forms,
meter data integrations, waste collection routing, geology model plugins, pipeline integrity tools,
environmental reporting workflows, fish farm records, marine harvest dashboards,
seafood traceability forms, fisheries data feeds, or platform-native resource operations packages
instead of a source-linked Hermes Tweet package entry.
Reject forestry, timber, logging, sawmill, lumber yard, wood products, forest
management, and harvest planning app marketplaces such as Trimble Forestry
integrations, Remsoft marketplaces, Forest Metrix integrations, Log Inventory
marketplaces, lumber yard point-of-sale marketplaces, sawmill planning
marketplaces, timber ERP app catalogs, or wood products marketplaces when they
only accept stand inventory forms, harvest scheduling tools, log yard
connectors, timber sale records, scaling tickets, sawmill optimization
dashboards, lumber inventory sync, or platform-native forestry packages
instead of a source-linked Hermes Tweet package entry.
Reject HR, recruiting, talent, benefits, workforce, employee advocacy, and
internal communications app marketplaces such as Greenhouse integrations, Lever
integrations, Ashby marketplace, Workable app marketplace, BambooHR app
marketplace, Gusto integrations, LinkedIn Talent Solutions partner apps,
Simpplr integrations, Staffbase app marketplaces, Haiilo integrations,
EveryoneSocial integrations, or recruiting app marketplaces when they only
accept ATS connectors, candidate-source automations, job board integrations,
interview workflows, employee-directory apps, benefits connectors, onboarding
tasks, employee advocacy workflows, intranet widgets, internal announcement
feeds, or workforce platform packages instead of a source-linked Hermes Tweet package entry.
Reject freelancer, gig economy, contractor, creator marketplace, talent
marketplace, service marketplace, work marketplace, and job board app
directories such as Upwork Marketplace, Fiverr integrations, Toptal partner
integrations, Contra integrations, Freelancer integrations, Guru integrations,
Taskrabbit integrations, Thumbtack integrations, Behance creator tools,
Dribbble hiring integrations, or job board app marketplaces when they only
accept hiring widgets, contractor onboarding workflows, talent profile syncs,
service listing templates, project brief automations, escrow payment
connectors, creator portfolio widgets, job posting feeds, or platform-native
work marketplace packages instead of a source-linked Hermes Tweet package entry.
Reject healthcare, EHR, FHIR, mental health, therapy, behavioral health, EAP, telehealth, wellness, and fitness app
marketplaces such as Epic App Orchard, Oracle Health App Gallery, SMART App Gallery, FHIR app galleries, athenahealth Marketplace,
SimplePractice integrations, TherapyNotes integrations, Headspace for Organizations, Lyra Health integrations, telehealth app
marketplaces, counseling and psychiatry app marketplaces, wellness app marketplaces, or fitness app marketplaces when they only
accept EHR integrations, clinical apps, FHIR launch apps, patient portal widgets, therapist directory widgets, EAP referral workflows,
mood tracking dashboards, care workflows, wellness programs, device integrations, substance use workflow connectors, or
platform-native health app packages or behavioral health packages instead of a source-linked Hermes Tweet package entry.
Reject dental, orthodontic, dental lab, DSO, dental imaging, and dental practice management app marketplaces
such as Dentrix Marketplace, Open Dental integrations, Eaglesoft integrations, CareStack marketplaces,
Curve Dental integrations, dental lab marketplaces, or dental imaging app catalogs when they only accept
patient chart connectors, appointment recall workflows, treatment plan templates, claim attachments,
imaging viewers, lab case tickets, or platform-native dental packages instead of a source-linked Hermes Tweet package entry.
Reject pharmacy, drugstore, PBM, e-prescribing, prescription management, 340B,
and pharmacy point-of-sale app marketplaces such as PioneerRx integrations,
QS/1 integrations, NCPDP app catalogs, CoverMyMeds integrations, Surescripts
integrations, pharmacy benefit management marketplaces, drugstore POS
marketplaces, or prescription workflow marketplaces when they only accept claim
adjudication connectors, refill workflows, formulary lookups, medication
synchronization widgets, prior authorization forms, e-prescribing connectors,
or platform-native pharmacy packages instead of a source-linked Hermes Tweet package entry.
Reject veterinary, pet care, animal health, animal shelter, kennel, boarding,
and grooming app marketplaces such as IDEXX integrations, Covetrus
marketplaces, PetDesk integrations, Shelterluv integrations, Chameleon shelter
software integrations, Gingr app marketplaces, Pawfinity integrations,
veterinary practice management marketplaces, pet grooming app marketplaces, or
kennel software marketplaces when they only accept veterinary practice
connectors, appointment reminders, animal shelter workflows, kennel booking
widgets, grooming schedule tools, prescription refill integrations, pet health
records, or platform-native animal care packages instead of a source-linked Hermes Tweet package entry.
Reject senior care, elder care, home care, assisted living, childcare, daycare, nanny, babysitting, and caregiving app marketplaces
such as Brightwheel integrations, Procare integrations, Kinderlime app marketplaces, ChildcareCRM integrations, Care.com integrations,
WellSky Personal Care integrations, AlayaCare integrations, ClearCare integrations, senior care app marketplaces, or home care agency marketplaces
when they only accept childcare attendance connectors, parent communication widgets, care-plan workflows, caregiver schedule tools,
family portal apps, visit verification connectors, resident engagement widgets, or platform-native care services packages
instead of a source-linked Hermes Tweet package entry.
Reject accessibility, assistive technology, disability services, screen reader,
captioning, and WCAG testing app marketplaces such as Deque integrations, Level
Access integrations, UserWay widgets, accessiBe integrations, audio description
tools, captioning workflows, ARIA audit dashboards, or platform-native
accessibility packages instead of a source-linked Hermes Tweet package entry.
Reject death care, funeral home, cemetery, cremation, mortuary, memorial,
obituary, and end-of-life planning app marketplaces such as Tribute Technology
integrations, Passare app marketplaces, SRS Computing integrations, CIMS
cemetery management integrations, PlotBox marketplaces, Frazer Consultants
integrations, Everdays app marketplaces, Legacy.com integrations, funeral home
software marketplaces, or cemetery management app marketplaces when they only
accept obituary publishing widgets, memorial page templates, service schedule
feeds, case-management workflows, cremation authorization forms, cemetery plot
maps, tribute video tools, family notification workflows, preneed planning
connectors, or platform-native death-care packages instead of a source-linked Hermes Tweet package entry.
Reject beauty, salon, spa, barber, appointment booking, local services, cleaning service app marketplaces, janitorial software marketplaces,
laundry and dry cleaning app marketplaces, pest control software marketplaces, pool service app marketplaces, lawn care landscaping marketplaces, facility services marketplaces, home cleaning marketplaces, and field-service booking marketplaces such as Mindbody integrations, Vagaro app marketplaces, Boulevard app marketplaces, Fresha integrations, Zenoti integrations, GlossGenius integrations, Square Appointments integrations, Acuity Scheduling integrations, Booksy app marketplaces, wellness appointment marketplaces, Janitorial Manager integrations, CleanCloud integrations, PestPac marketplaces, Skimmer integrations, or Aspire landscaping integrations when they only accept booking widgets, staff schedule sync, intake forms, client profile connectors, point-of-sale add-ons, membership automations, service catalog sync, location availability widgets, provider calendar workflows, route sheets, service tickets, chemical logs, garment tracking, or platform-native appointment packages instead of a source-linked Hermes Tweet package entry.
Reject field service management, warranty, appliance repair, home services,
maintenance dispatch, service scheduling, technician routing, and repair
operations app marketplaces such as ServiceTitan integrations, Jobber app
marketplaces, Housecall Pro integrations, FieldPulse integrations, Workiz
integrations, Service Fusion integrations, Dispatch integrations, Zuper
marketplaces, Syncron warranty integrations, or ServiceMax marketplaces when
they only accept technician schedules, dispatch boards, warranty claim
workflows, work-order syncs, route optimization widgets, service estimate
templates, customer appointment portals, parts inventory connectors,
inspection forms, or platform-native field service packages instead of a
source-linked Hermes Tweet package entry.
Reject legal, compliance, e-signature, identity, KYC, contract automation, eDiscovery, GRC, and privacy automation app marketplaces, plus consent management,
cookie compliance, DSAR, CCPA, data subject request, environmental health and safety, OSHA compliance, workplace safety management, and safety training marketplaces such as Clio App
Directory, DocuSign App Center, Adobe Acrobat Sign integrations, Okta Integration Network, Auth0 Marketplace, OneTrust app catalogs, Vanta
integrations, Drata integrations, Relativity app directories, contract lifecycle marketplaces, compliance automation marketplaces, Cookiebot integrations,
Didomi integrations, TrustArc integrations, Osano app catalogs, Usercentrics integrations, Intelex marketplaces, SpheraCloud integrations, Cority app catalogs, Enablon integrations, or SafetyCulture integrations when they only accept legaltech connectors,
e-signature connectors, identity integrations, compliance controls, audit workflows, eDiscovery workflows, contract templates, trust-center automations,
KYC checks, privacy assessments, consent banners, cookie scanners, CMP tags, DSAR intake forms, data subject request workflows, EHS checklists, OSHA logs, near-miss forms, hazard registers, risk assessment templates, safety training records,
incident workflows, or platform-native governance apps instead of a source-linked Hermes Tweet package entry.
Reject password-manager, secrets-management, access-governance, and
trust-center app marketplaces such as 1Password integrations, Bitwarden
integrations, HashiCorp Vault catalogs, Doppler integrations, Okta Integration
Network, Auth0 Marketplace, Vanta integrations, or Drata integrations when they
only accept vault connectors, SSO apps, secret-sync automations, policy evidence
exports, access-review workflows, or platform-native identity packages instead
of a source-linked Hermes Tweet package entry.
Reject quality management, QMS, CAPA, audit management, document control,
nonconformance, inspection, ISO compliance, and quality assurance app
marketplaces such as MasterControl integrations, ETQ Reliance marketplaces,
Greenlight Guru integrations, Qualio integrations, Arena QMS integrations,
Intellect QMS marketplaces, audit management software marketplaces, document
control app marketplaces, CAPA software marketplaces, or quality compliance
catalogs when they only accept audit checklists, document approval workflows,
nonconformance intake forms, corrective action trackers, inspection templates,
supplier quality dashboards, training record connectors, ISO evidence packs, or
platform-native quality management packages instead of a source-linked Hermes Tweet package entry.
Reject security operations, SIEM, SOAR, and observability integration catalogs,
plus security awareness, phishing simulation, cyber range, and attack simulation training marketplaces such as Splunkbase, Elastic integrations, Datadog integrations, Grafana plugin
catalog, New Relic Instant Observability, Sumo Logic app catalog, Cortex XSOAR content packs, KnowBe4 integrations, Proofpoint security awareness catalogs, Cofense integrations, Immersive Labs catalogs, or RangeForce content catalogs when they only accept
dashboards, detection rules, log parsers, alert connectors, runbooks, incident workflows, phishing templates, awareness modules,
cyber-range labs, breach simulation scenarios, human-risk dashboards, or platform-specific integration packages instead of a source-linked
Hermes Tweet package entry.
Reject QA testing, browser testing, synthetic monitoring, and test automation extension marketplaces such as BrowserStack integrations, Sauce Labs integrations, Cypress plugins, Selenium plugin indexes, Playwright plugin catalogs, Checkly integrations, Pingdom extensions, or Datadog Synthetic Monitoring integrations when they only accept test runners, browser automation fixtures, synthetic checks, uptime monitors, assertion dashboards, or platform-native QA packages instead of a source-linked Hermes Tweet package entry.
Reject physical security, CCTV, VMS, access control, visitor management,
alarm, badge, and workplace safety app marketplaces such as Verkada
integrations, Genetec app marketplaces, Milestone Marketplace, Axis
Communications integrations, Avigilon integrations, LenelS2 partner apps,
Brivo integrations, Kisi integrations, or Envoy visitor-management apps when
they only accept camera device connectors, video analytics plugins, door access
workflows, badge provisioning automations, visitor kiosk widgets, incident
response dashboards, alarm panel integrations, or platform-native physical
security packages instead of a source-linked Hermes Tweet package entry.
Reject CI/CD, DevOps automation, DevSecOps, application security scanning, and pipeline extension marketplaces such as
GitHub Marketplace Actions, GitLab CI/CD Catalog, CircleCI orb registry,
Jenkins plugin index, Buildkite plugins, Travis CI add-ons, Snyk integrations, Semgrep registry entries, CodeQL packs,
Veracode integrations, Checkmarx integrations, Mend integrations, Black Duck integrations, or pipeline
automation marketplaces when they only accept workflow actions, CI templates, SAST rules, SCA policies, SBOM reports,
secret scanning detectors, dependency scan jobs, container scan policies, orb packages, build plugins, deployment automations, or source-control workflows instead of a source-linked Hermes Tweet package entry.
Reject container, cloud-native, and infrastructure packaging registries such as Docker Hub extensions, Kubernetes operator catalogs, Helm chart repositories, Artifact Hub, Terraform Registry, Pulumi Registry, Crossplane package registry, or Backstage plugin catalogs when they only accept container images, operators, charts, infrastructure providers, platform plugins, or deployment packages instead of a source-linked Hermes Tweet package entry.
Reject cloud software, SaaS procurement, reseller, and hyperscaler marketplace routes, plus FinOps, cloud-cost optimization, cloud billing, Kubernetes cost, spend management, cost governance, and usage analytics marketplace routes such as AWS Marketplace, Azure Marketplace, Google Cloud Marketplace, Microsoft AppSource, Oracle Cloud Marketplace, Salesforce AppExchange, Atlassian Marketplace, ServiceNow Store, cloud partner catalogs, SaaS marketplace listings, software procurement portals, reseller app marketplaces, CloudHealth integrations, Cloudability integrations, Infracost integrations, OpenCost plugins, or Kubecost integrations when they only accept VM images, managed service listings, private offers, transactable SaaS plans, admin center add-ons, enterprise procurement connectors, cloud billing dashboards, reserved-instance reports, savings-plan recommendations, cost allocation tags, Kubernetes cost dashboards, or platform-native cloud marketplace packages instead of a source-linked Hermes Tweet package entry.
Reject backup, disaster recovery, data protection, business continuity, and
ransomware recovery marketplaces such as Veeam integrations, Acronis
integrations, Druva marketplace, Rubrik integrations, Cohesity Marketplace,
Datto integrations, or storage replication connectors when they only accept
backup policy templates, restore workflow automations, retention dashboards, or
platform-native resilience packages instead of a source-linked Hermes Tweet package entry.
Reject IoT, smart-home, industrial-device, edge-device, and maker hardware marketplaces such as Home Assistant integrations, HACS repositories,
SmartThings Edge drivers, Homey apps, Hubitat apps, openHAB bindings, Matter plugin catalogs, Node-RED flow libraries, IFTTT applets, Arduino Library
Manager, Raspberry Pi project galleries, industrial IoT app marketplaces, or
device plugin catalogs when they only accept home automation integrations,
device drivers, flow recipes, firmware libraries, hardware projects, sensor
connectors, connected-device packages, or platform-native device packages instead of a source-linked Hermes Tweet package entry.
Reject industrial automation, MES, SCADA, CMMS, EAM, plant operations, and
factory automation marketplaces such as Rockwell Automation marketplaces,
Siemens industrial app marketplaces, PTC ThingWorx marketplaces, AVEVA
marketplaces, Ignition Exchange, maintenance management app stores, plant
operations catalogs, or factory automation marketplaces when they only accept
PLC connectors, historian dashboards, HMI modules, production-line workflows,
asset maintenance tools, work-order automations, OEE dashboards, machine data
adapters, or platform-native industrial operations packages instead of a
source-linked Hermes Tweet package entry.
Reject CAD, CAM, PLM, EDA, additive manufacturing, robotics, and
autonomous-systems app marketplaces, including additive manufacturing app
marketplaces such as Autodesk App Store, Fusion 360 add-ins, SolidWorks marketplace, Onshape App Store, Altium extensions, KiCad
plugin repositories, FreeCAD Addon Manager, CAD plugin marketplaces, PLM app
stores, EDA plugin catalogs, ROS package indexes, Gazebo plugins, Open-RMF adapters, PX4 extensions, ArduPilot
companion apps, robot app catalogs, or manufacturing app marketplaces when they only accept engineering add-ins, CAD toolbars, model plugins, circuit-design extensions, CAM post-processors, slicer integrations, simulation templates, ROS nodes, robot fleet adapters, companion-computer packages, manufacturing workflows, or platform-native engineering packages instead of a source-linked Hermes Tweet package entry.
Reject construction, BIM, property, facilities, and real estate app
marketplaces such as Procore Marketplace, Autodesk Construction Cloud apps, BIM
360 app stores, Revit add-in marketplaces, SketchUp Extension Warehouse,
Archicad add-ons, construction app marketplaces, BIM plugin marketplaces,
property management app marketplaces, facilities management app marketplaces,
or real estate app marketplaces when they only accept project-management
connectors, BIM model plugins, drawing workflows, field-report forms, building
operations integrations, lease or listing apps, facility work-order tools, or
platform-native construction packages instead of a source-linked Hermes Tweet package entry.
Reject equipment rental, tool rental, self-storage, parking management, facility booking, venue booking, desk booking, and space reservation app marketplaces,
parks recreation app marketplaces, campground reservation app marketplaces, marina management app marketplaces, golf course management marketplaces, country club management marketplaces, resort activity booking app marketplaces, outdoor recreation software marketplaces, and parks department app marketplaces such as Booqable integrations, EZRentOut marketplaces, Rentman integrations, Point of Rental integrations, Storable integrations, SiteLink app marketplaces, ParkMobile integrations, Flash Parking integrations, Skedda integrations, Robin workplace integrations, RecDesk app marketplaces, CampLife integrations, Dockwa marina integrations, ForeUp integrations, Clubessential marketplaces, and resort activity catalogs when they only accept inventory availability widgets, rental checkout workflows, storage-unit portals, parking permit connectors, access-code automations, booking calendars, occupancy dashboards, desk maps, venue availability feeds, campground availability feeds, slip reservation widgets, tee-time booking tools, member portal apps, activity waivers, parks permit forms, or platform-native rental and space-management packages instead of a source-linked Hermes Tweet package entry.
Reject browser, AI browser extension directory, desktop AI-client plugin directory, launcher, shortcut, read-it-later, and mobile app extension stores, plus link-in-bio, URL shortener,
QR code, microsite builder, digital business card, email signature, vCard, contact-card, and creator landing-page marketplaces such as Chrome Web Store, Firefox Add-ons, Microsoft Edge Add-ons,
Raycast extensions, Alfred workflows, Setapp, iOS Shortcuts galleries, bookmark manager catalogs, web-clipping marketplaces,
Linktree integrations, Carrd plugins, Beacons app marketplaces, Bitly integrations, HiHello integrations, Blinq integrations, Popl integrations, QR code generator marketplaces, or landing-page builder app stores
when they only accept browser extensions, extension manifests, desktop launcher commands, packaged apps, mobile intents, automation shortcuts, clipping workflows,
bio-page widgets, short-link dashboards, signature banners, vCard landing pages, QR landing pages, profile-card templates, or app-store listings instead of a source-linked Hermes Tweet
package entry.
Reject design, creative, whiteboard, knowledge-app, font, icon, stock-media,
template, and digital-asset marketplaces such as Figma Community plugins, Canva
Apps Marketplace, Miro Marketplace, FigJam widgets, Adobe Express add-ons,
Framer Marketplace, Obsidian community plugins, Blender extensions, Google Fonts
directory, Font Awesome icons, Noun Project, Unsplash app integrations, Adobe
Stock, Creative Market, Envato Elements, or template galleries when they only
accept design plugins, canvas widgets, creative app add-ons, personal knowledge
plugins, scene extensions, fonts, icons, stock assets, templates, or
product-native UI integrations instead of a source-linked Hermes Tweet package entry.
Reject game engine, AR/VR, 3D asset, and creator gaming marketplaces such as
Unity Asset Store, Unreal Engine Marketplace, Roblox Creator Store, Godot Asset
Library, Steamworks tools, itch.io tool marketplaces, Meta Quest App Lab, or
VRChat marketplaces when they only accept engine plugins, editor extensions,
game assets, scripts, SDK integrations, creator tools, avatar or world
packages, or app-store listings instead of a source-linked Hermes Tweet package entry.
Reject voice assistant, speech, meeting, and real-time communications app
marketplaces such as Alexa Skills Store, Google Assistant Actions, Bixby
capsules, Zoom App Marketplace, Microsoft Teams meeting apps, Slack huddle app
surfaces, or conferencing integration catalogs when they only accept voice
skills, assistant actions, meeting bots, call workflows, transcript tools, or
communications app packages instead of a source-linked Hermes Tweet package
entry.
Reject messaging, SMS, chat API, and customer communications app marketplaces
such as Twilio Marketplace, Vonage integrations, MessageBird or Bird app
marketplaces, Sinch integrations, WhatsApp Business app integrations, Sendbird
marketplace, or customer communications app marketplaces when they only accept
SMS connectors, chat widgets, messaging templates, contact-center workflows,
conversation routing apps, notification automations, or platform-native
communications packages instead of a source-linked Hermes Tweet package entry.
Reject telecom, ISP, domain registrar, DNS, CDN, edge-network, and network
operations app marketplaces such as Cloudflare Apps, Akamai Marketplace,
Fastly integrations, registrar app directories, cPanel extensions, WHMCS
Marketplace, OSS/BSS integration catalogs, or network-operations marketplaces
when they only accept DNS widgets, registrar extensions, CDN edge apps,
hosting-panel modules, provisioning dashboards, network monitoring connectors,
or platform-native telecom packages instead of a source-linked Hermes Tweet package entry.
Reject email marketing, newsletter, scheduling, event, form, and survey app marketplaces, plus wedding planning app marketplaces,
event planning software marketplaces, webinar app marketplaces, virtual event platform marketplaces, conference platform integration catalogs, catering app
marketplaces, banquet hall venue management marketplaces, RSVP guest list app marketplaces, seating chart software marketplaces, event vendor marketplaces,
and wedding venue app marketplaces such as Mailchimp integrations, SendGrid integrations, Brevo app store, Substack app directories, Calendly integrations,
Eventbrite app marketplace, Cvent app marketplaces, Hopin app marketplaces, Bizzabo integrations, Airmeet integrations, ON24 integrations, Typeform app
marketplace, or SurveyMonkey app directories when they only accept email automations, newsletter connectors, booking workflows, event listings, form widgets,
webinar registration widgets, virtual booth apps, attendee badge sync, agenda embeds, seating plans, vendor directories, survey templates, or
platform-native integration packages instead of a source-linked Hermes Tweet package entry.
Reject static-site, blog, RSS, and newsletter social-publishing plugin routes such as Hugo modules, Jekyll plugins, Astro integrations, RSS-to-X bots,
or blog automation catalogs when they only accept theme add-ons, feed actions, content snippets, or site-generator packages instead of a source-linked Hermes Tweet package entry.
Also reject market research, survey panel, user research, and consumer insights
app marketplaces such as Qualtrics Marketplace, UserTesting integrations,
Dovetail integrations, panel sample connectors, product feedback repositories,
feedback dashboards, and platform-native insights packages when they only accept
survey distribution workflows or native research dashboards instead of a source-linked Hermes Tweet package entry.
Reject sports, league management, fan engagement, sports ticketing, venue
operations, stadium, and esports tournament app marketplaces, plus performing arts, theater,
concert, festival, box office, live entertainment, and event ticketing platform app marketplaces such as TeamSnap
app marketplaces, SportsEngine integrations, LeagueApps marketplaces, Ticketmaster app marketplaces,
SeatGeek integrations, fan engagement app marketplaces, sports league management catalogs, esports tournament marketplaces,
theater ticketing marketplaces, festival management app marketplaces, box office software marketplaces, or arts venue app marketplaces when they only accept
team roster connectors, schedule widgets, ticketing workflows, venue operations tools, stadium experience apps,
fan data dashboards, tournament brackets, concert promotion workflows, seating maps, artist settlement reports, or platform-native sports packages instead of a source-linked Hermes Tweet package entry.
Reject sports betting, casino, lottery, sportsbook, fantasy sports, iGaming,
odds-data, and gaming compliance app marketplaces such as DraftKings developer
integrations, FanDuel integrations, Sportradar marketplaces, Genius Sports data
integrations, OpenBet marketplaces, BetConstruct integrations, casino software
marketplaces, lottery platform marketplaces, sportsbook app marketplaces, or
odds API catalogs when they only accept odds feeds, bet-slip widgets, player
account connectors, affiliate-tracking pixels, responsible-gaming workflows,
fantasy lineup tools, lottery draw widgets, trading dashboards, risk and
compliance connectors, or platform-native wagering packages instead of a
source-linked Hermes Tweet package entry.
Reject library, museum, archive, cultural heritage, digital collections,
exhibit management, museum ticketing, ILS, and library management app
marketplaces such as Koha plugin catalogs, ArchivesSpace integrations, Omeka
plugin marketplaces, MuseumPlus integrations, Tessitura app marketplaces,
Blackbaud Altru integrations, library app marketplaces, museum app
marketplaces, or archive app marketplaces when they only accept catalog
widgets, collections dashboards, exhibit workflows, ticketing connectors,
donor CRM integrations, digitization tools, finding-aid templates, patron
account portals, or platform-native cultural heritage packages instead of a
source-linked Hermes Tweet package entry.
Reject maps, geospatial, travel, mobility, logistics, and fleet app
marketplaces such as Google Maps Platform integrations, Mapbox plugin catalog,
ArcGIS Marketplace, QGIS plugin repository, travel booking marketplaces,
Expedia app marketplace, Uber developer app marketplaces, or logistics and
fleet app marketplaces when they only accept map plugins, GIS extensions,
geospatial data connectors, travel booking widgets, ride-hailing workflows,
fleet automations, or route-optimization packages instead of a source-linked Hermes Tweet package entry.
Reject supply-chain, warehouse management, WMS, TMS, inventory, order
management, fulfillment, shipping carrier, freight forwarding, returns, and
3PL app marketplaces such as ShipStation integrations, ShipBob integrations,
Easyship apps, Flexport integrations, Manhattan Associates marketplaces, Blue
Yonder marketplaces, Oracle SCM integrations, SAP Logistics Business Network,
or supply-chain app marketplaces when they only accept carrier connectors,
warehouse pick-pack workflows, inventory sync widgets, order routing
automations, freight booking tools, returns portals, 3PL dashboards, or
platform-native supply-chain packages instead of a source-linked Hermes Tweet package entry.
Reject aerospace, aviation, airline operations, airport operations, drone,
UAS, maritime, rail, flight operations, space mission, satellite data, Earth observation, remote sensing,
orbital analytics, and transport-operations app marketplaces such as ForeFlight integrations,
AirMap integrations, DroneDeploy app marketplaces, DJI developer marketplaces, SITA aviation marketplaces,
Amadeus travel platform integrations, Sabre marketplaces, maritime logistics integrations, railway operations integrations,
STAC catalogs, satellite imagery marketplaces, or mission control app marketplaces when they only accept flight
planning widgets, airspace data connectors, drone mission packages, aircraft maintenance workflows,
airport operations dashboards, crew scheduling tools, vessel tracking connectors, rail timetable feeds,
remote-sensing data products, satellite imagery orders, orbital ephemeris feeds, mission-planning dashboards,
or platform-native transport operations packages instead of a source-linked Hermes Tweet package entry.
Reject automotive, car dealership, auto repair, vehicle service, auto parts,
connected car, dealer management system, and DMS app marketplaces such as CDK
Global marketplaces, Reynolds and Reynolds integrations, Dealertrack app
marketplaces, Mitchell 1 integrations, ALLDATA integrations, Shopmonkey app
marketplaces, Tekmetric integrations, automotive app marketplaces, car
dealership app marketplaces, or auto repair shop marketplaces when they only
accept inventory sync connectors, service scheduling workflows, repair-order
dashboards, parts catalog integrations, VIN lookup widgets, customer-pay
portals, connected-vehicle telemetry, or platform-native automotive packages
instead of a source-linked Hermes Tweet package entry.
Reject code-assistant extension marketplaces and developer-agent tool catalogs
such as Amazon Q Developer, Continue, Sourcegraph Cody, JetBrains Junie, Devin,
or Tabby when they only accept IDE extensions, editor plugins, workspace
automation packs, or assistant-specific tool definitions instead of a
PR-editable Hermes Tweet source package entry.
Reject local coding-agent command packs, workflow recipes, CLI extension registries, terminal or shell plugin indexes, and rule bundles such as rulepack catalogs, Cursor rule marketplaces, repository instruction catalogs, GitHub Copilot Extensions, OpenCode
commands, Aider workflows, Goose extensions, Kiro hooks, Amp tools, Oh My Zsh plugins, fish shell plugins, or terminal assistant catalogs when they only accept agent-local prompts, commands, recipes, hooks, shell integrations, or editor workflows instead of a source-linked Hermes Tweet package entry.
Reject hosted automation, app-action, chat-platform tool/function, and component galleries such as Zapier,
Pipedream, Activepieces, Composio, Arcade, Toolhouse, Langflow, Open WebUI, LibreChat, Dify, Flowise, or AnythingLLM when the
route only accepts workflow templates, provider connectors, hosted app actions, chat tools,
tool/function manifests, or framework-native components. Treat those as integration surfaces unless they
expose a PR-editable third-party source repository entry for Hermes Tweet's
shipped package.
Reject RPA and no-code automation marketplaces such as UiPath, Robocorp, n8n, Make, or Workato when they only accept bots, community nodes, workflow exports, automation recipes, or task templates instead of a source-linked Hermes Tweet package entry.
Reject web-agent workflow libraries, browser-agent recipe libraries, automation runbook catalogs, and AI agent recipe collections when they only accept prompt-recipe collections, browser task demos, evaluation trace bundles, or platform-native action recipes instead of a PR-editable third-party Hermes Tweet package entry.
Reject operator runbook packs, self-setup Hermes starter packs, domain-only SRE skill libraries, public agent memory vaults, single-product setup-stack runbooks, and project workbench template catalogs unless they expose a PR-editable third-party Hermes Tweet source/catalog entry.
Reject agent app-store manifests, AI assistant app directory manifests, chatbot app-store source catalogs, agent workflow source catalogs, agent workflow template galleries, agent workflow recipe registries, automation workflow marketplaces, workflow example libraries, workflow-template marketplaces, and action recipe catalogs when they only accept app manifests, directory profile metadata, template recipes, workflow examples, generated indexes, or hosted workflow bundles instead of a PR-editable third-party source repository entry for Hermes Tweet.
Reject prompt-only agent repositories, persona catalogs, system-prompt libraries, converted instruction mirrors, AI-native learning plugin marketplaces, and assistant profile collections when they only accept Markdown prompt files, role cards, usage examples, prompt quality checklists, training workflows, or prompt templates instead of a source-linked Hermes Tweet package entry.
Reject embedded `.agents`, `.agent`, `.antigravity`, project-template, single-skill Claude templates, brand-specific agent skill packs, and copied skill directories inside application repositories unless the repository itself documents a third-party skill catalog, registry, or contribution lane. Treat those hits as downstream copies or mirrors, not fresh Hermes Tweet submission routes.
Reject peer Hermes Agent plugin source repositories, plugin examples, showcase repos, and demo plugin repos unless the repository itself documents a PR-editable third-party plugin catalog, registry, or source-list lane. A repo being another Hermes Agent plugin is ecosystem evidence only; do not open Hermes Tweet outreach there unless it can accept a source-linked Hermes Tweet package entry without copying, translating, or repackaging Hermes Tweet.
Reject peer X/Twitter agent skill source repos, social-production plugin source repos, product-specific X/Twitter growth skill repos, and peer X/Twitter CLI or MCP source repos unless they document a PR-editable third-party catalog lane for Hermes Tweet's shipped package.
Reject generic skill-index import registries, source-agnostic skill package managers, skill graph package registries, RagCode skill pack registries, action package marketplaces, agent skill graph catalogs, agent tool hub source registries, assistant extension index manifests, agent capability manifest catalogs, agent protocol plugin marketplaces, agent protocol bridge catalogs, agent operating system plugin marketplaces, multi-agent collaboration plugin hubs, Claude Code plugin marketplace templates, developer productivity agent marketplaces, coding assistant skill registries, agentic IDE plugin catalogs, software engineering agent skill directories, code review agent marketplaces, pull request agent plugin registries, developer workflow agent catalogs, Copilot plugin sync marketplaces, generated VS Code agent plugin marketplaces, upstream-only plugin sync mirrors, personal Codex plugin marketplace catalogs, owner-owned git-subdir plugin catalogs, community skill search indexes, token-efficient skill resolution APIs, external skill import CLIs, AI skills registry CLIs without Hermes lanes, MCP client plugin marketplaces, MCP client extension registries, product-specific MCP client plugins, single-plugin MCP proxy clients, client tooling plugin marketplaces, workflow builder plugin marketplaces, AI automation canvas agent registries, app builder Claude plugin marketplaces, Grounded Intelligence client plugin marketplaces, team agent workflow builder plugins, data-space MCP connector plugins, any-MCP-client product plugin repos, profile-manager curated marketplace apps, AI product-team agent packs, team-owned Claude plugin marketplaces, AI teammate plugin marketplaces, agent workspace app directories, agent team command marketplaces, AI coworker extension catalogs, autonomous agent team plugin hubs, company-specific data workflow skill marketplaces, source-owned Codex skill marketplace mirrors, framework-aware coding skill marketplaces without social or Hermes lanes, GitHub-topic-only discovery CLIs, GitHub repo install CLIs, VS Code Copilot marketplace publisher extensions, external-PR-closing plugin marketplaces, README-only placeholder registries, zip-only skill wrapper repos, source-owned generated catalogs, generated Hermes skill catalogs, source-list catalog JSON files, domain-specific skill bundles, finance-only local skill bundles, product-owned playbook repositories, portfolio playbook repositories, private-beta source-owned skill hubs, skill provenance sidecar utilities, personal workbench template catalogs, agent blueprint catalogs, agent starter-kit catalogs, template-gallery application repos, AI agent template galleries, aggregated Claude marketplace indexes, generated awesome Claude plugin indexes, agent connector registries, AI agent connector catalogs, AI agent data connector marketplaces, data-source MCP connector catalogs, database agent integration registries, BI agent connector galleries, enterprise data-source MCP server indexes, assistant connector registries, LLM agent connector hubs, agent identity credential plugin registries, AI agent auth connector catalogs, LLM agent credential wallet marketplaces, agent passport plugin registries, agent trust identity extension catalogs, AI agent secrets credential tool registries, AI agent deployment runtime registries, agent cloud runtime plugin catalogs, LLM agent deployment marketplaces, agent runtime cloud connector catalogs, AI agent hosting extension marketplaces, serverless agent framework plugin registries, agent platform deployment template catalogs, AI framework connector registry, agent framework adapter catalog, LLM orchestration framework integrations, RAG framework component integrations, workflow AI framework tools registry, AI agent plugin source list manifest, agent marketplace source registry YAML, AI plugin catalog external repositories, MCP tool catalog source list, AI agent marketplace TOML manifests, agent tool gallery YAML files, assistant marketplace registry JSON files, AI plugin index manifests, LLM plugin marketplace manifest repositories, social automation AI tool galleries, MatrixHub MCP server manifest indexes, AI agent framework cookbook integrations, LLM framework example plugin catalogs, agent framework extension galleries, AI framework tools example registries, LLM app integration showcases, single-company social media manager agents, already-listed Hermes Atlas source catalogs, live Hermes Atlas MCP wrappers, AI agent protocol package catalogs, agent interoperability protocol marketplaces, agent-to-agent communication protocol registries, hosted agent service marketplaces, protocol-native MCP auth bridges, AI agent escrow marketplace protocols, AI agent payment protocol registries, agent wallet plugin registries, x402 payment integration demos, MCP payment server repos, agent commerce protocol SDKs, agent runtime extension marketplaces, tool protocol package registries, model context protocol package catalogs, unrelated runtime package repos, AI agent provider adapter registries, LLM agent adapter marketplaces, agent framework provider catalogs, AI agent template hubs, X Twitter agent template registries, social listening agent adapters, AI agent observability plugin registries, LLM agent telemetry connector catalogs, agent tracing plugin marketplaces, AI agent monitoring extension registries, agent evaluation telemetry catalogs, LLM ops agent plugin directories, agent analytics connector marketplaces, single-app swappable marketplace adapter demos, framework-agnostic agent adapter marketplaces, AI framework bridge package catalogs, microagent framework discovery registries, owner-bundled Claude marketplace plugin trees, framework-owned `.claude-plugin` marketplace manifests, MCP app builder skill bundles, agent sandbox execution runtimes, code-execution sandbox frameworks, MCP filesystem sandbox servers, agent red-team audit tools, agent benchmark tool directories, owner-specific MCP wrapper suites, always-on companion harness plugins, ADK-specific agent framework plugin suites, single-plugin harness scaffolders, agent-hiring relay skills, OpenClaw-only telemetry plugins, product-owned optimization skill catalogs, auto-synced aggregation catalogs, source-repo-only skill aggregation catalogs, research-only multi-CLI skill catalogs, SimpleContext memory plugin registries, first-party safety observability plugin catalogs, Hermes workflow orchestration marketplaces, generated developer-tool MCP hubs, source-owned translation plugin catalogs, installer-only Claude marketplace bridges, official first-party social plugin suites, accessibility-only developer toolkit marketplaces, database-backed MVP marketplace apps without source catalog seeds, agent integration marketplaces, connector-registry product repos, methodology-owned skill marketplaces, owner-specific plugin bundles, owner-specific global agent hubs, personal Claude Code/Codex plugin marketplaces, owner-branded memory plugin marketplaces, context-memory Claude plugin marketplaces, topic-auto-indexed Hermes plugin hubs, empty Hermes vault catalogs, personal Hermes skill backup repositories, coming-soon source-owned plugin marketplaces, personal AI CLI configuration marketplaces, owner-specific AI CLI configuration marketplaces, source-owned first-party plugin bundles, already-merged catalog listings, marketplace-keyword application repos, tenant or fleet skill registries, generic skill-registry submission guides, onboarding docs, direct-PR-prohibited Hermes awesome lists, and wishlist issues when they describe review policy, local plugin setup, learning paths, import APIs, publication tooling, external submission forms, member-only contribution lanes, app implementations, embedded framework examples, owned tool registries, sandbox runtimes, local execution engines, red-team scanners, benchmark harnesses, or topic-based skill discovery but do not expose a PR-editable registry source file, catalog seed, or source-list lane for third-party Hermes Tweet package entries.
Reject Git-backed AI asset registry CLIs with bundled sample assets, Discord Watchtower agent economy frameworks, personal chatops Claude plugin bundles, and malformed terms-of-service dump repositories when they only expose user-maintained registry examples, autonomous work protocols, owner-specific plugin bundles, or unrelated scraped legal text instead of a PR-editable third-party Hermes Tweet package entry.
Reject framework-aware Agent Skills marketplaces without social or Hermes package lanes, documentation-only Claude Code skill marketplaces, code-review Agent Skills marketplaces, native `SKILL.md`-only contribution lanes, Aeon-only skill pack registries, website-specific browser automation skill libraries, desktop assistant app marketplaces, browser MCP automation thread catalogs, GitHub Copilot asset catalogs, Shopware-specific Claude marketplaces, CRM app agent-tool projects, and self-hosted AI agent listing apps when they require adding target-native skill markdown, platform-native app listings, or workspace-local Copilot files instead of accepting a source-linked Hermes Tweet package listing.
Reject agent protocol bridge catalogs, owner-specific global agent hubs, source-owned workflow recipe hubs, and Telegram bridge plugin marketplaces when they only publish runtime bridges, personal project registries, generated recipe hubs, or channel integrations instead of a PR-editable Hermes Tweet source entry.
Reject self-hostable agent harnesses, Hermes/OpenClaw replacement runtimes, and bundled runtime skill trees when they only ship local runtime code, built-in skill folders, or compatibility examples instead of a PR-editable third-party Hermes Tweet package entry.
Reject cybersecurity-only skill libraries, Obsidian-only skill marketplaces, brand-owned social media pipelines, first-party-only registry placeholders, and hosted marketplace SEO stubs when they only accept in-domain skills, first-party package sources, or off-repo hosted products.
Reject personal agent memory repositories, agent memory pack registries, cross-agent memory plugin marketplaces, OpenHands microagent folders, hosted MCP directory profile pages, live catalog MCP wrappers whose native source repo already closed a Hermes Tweet PR, Hermes-specific operator guides, profile playbooks, swarm specs, companion architecture repos, and owner-operated MCP plugin repositories such as `.openhands`, Smithery, Glama, PulseMCP, FrankX/Starlight, or Gumloop-hosted MCP plugin repos when they only publish owner-specific Claude/Codex plugin metadata, skills, or MCP endpoint config without a third-party catalog lane for a Hermes Tweet package listing; require a PR-editable third-party source/catalog entry that can reference Hermes Tweet's shipped package without copying, translating, or repackaging it.
Reject owner-specific Codex plugin marketplaces, single-product Codex plugin marketplaces, hosted skill-protocol entrypoints, OpenClaw landing-page apps, Paperclip-only npm plugin hubs, and paid-skill storefront shells when they only list owner plugins, first-party plugin bundles, protocol onboarding files, runtime-specific package manifests, hosted submission flows, or unfinished marketplace application code instead of a PR-editable third-party plugin source entry.
Reject tool-surface dump catalogs, agent tool indexes, generated ranked tool datasets, issue-only tool directories, agent capability registries, tool-vault directories, tools YAML registries, catalog drift analyzers, agent infrastructure awesome lists, AI gateway registry proxies, pre-deployment agent registries, content-addressed skill registry loadout systems, database-backed MCP skill registry servers, database-backed crowdsourced skill registry servers, community-support skill registries, moderation agent skill registries, forum-support agent catalogs, customer-support agent skill marketplaces, authenticated web/API skill submission queues, CLI-publish registry apps with only test fixtures, and internal tool-registry backends such as agent app tool dumps, toolmirror-style diff tools, or organizational LLM tool registry apps when they document runtime-owned tool schemas, agent protocol manifests with endpoint URIs, runtime/API code without a PR-editable source catalog lane, generated JSON/CSV exports, or capability schemas for live agent/tool endpoints instead of accepting source-linked third-party Hermes Tweet package entries.
Reject agent governance registries, AI talent governance registries, on-chain AI agent registries, agent reliability signal exchanges, agent trust signal registries, agent provenance registries, AI agent verification registries, agent trust badge registries, agent package provenance catalogs, AI agent scorecard registries, agent supply chain scorecard registries, agent certification marketplaces, AI agent attestation directories, AI agent tool rating registries, agent tool usage signal APIs, agent leaderboard registries, well-known agent tools registries, open-source AI agent trust leaderboards, public agent trust score registries, URL-source personal Claude Code marketplaces, maintainer-only agent-evaluation platform plugin marketplaces, first-party agent commerce MCP servers, single-plugin validation marketplaces, AI policy playbooks, policy-pack guardrail marketplaces, moderation or safety control catalogs, moderation workflow agent catalogs, MCP registry governance servers, organization-scoped MCP catalog servers, enterprise AI agent catalog product repos, AI agent incident corpora, compliance evidence agent directories, cloud marketplace-style agent tool catalogs, catalog-less protocol integration registries, and hosted first-party MCP plugin repos such as A2A governance marketplaces, context-governance playbooks, Gumloop-style hosted plugins, agent permission guardrail registries, approval-gate plugin templates, and agent approval workflow demos when they only accept live agent/tool endpoint registrations, policy templates, moderation workflow YAML, reputation ledgers, risk-control evidence, permission ceilings, policy-plugin manifests, compliance evidence dossiers, owner-specific plugin metadata, runtime-owned tool catalog metadata, incident evidence, or evaluation guardrails instead of a PR-editable third-party Hermes Tweet package entry.
Reject supply-chain attack demo marketplaces, signed-skill registry prototypes and offline-key signed manifest workflows, signed AgentPlane recipe catalogs, commercial Recipes meta-skill storefronts, agent commerce API marketplaces, ClawRecipes marketplace applications, Claude Code skills marketplaces with unrelated business integration recipes, marketplace security-awareness landing pages, and toy marketplace-provenance workspaces when they only provide red-team samples, signed workflow bundles, hosted publish flows, generated registry code, marketplace application code, business integration recipes, awareness-site copy, quarantined marketplace inboxes, or org-specific toy skills instead of a PR-editable third-party Hermes Tweet package entry.
Reject catalogs whose contribution rules require measurable community usage, maturity, a minimum star count, prohibit automated submissions, reject paid SaaS-dependent entries, or impose a maintainer-curated quality bar until Hermes Tweet visibly satisfies that target's stated threshold or a maintainer explicitly asks for another submission. Treat a closed prior Hermes Tweet PR for maturity, usage, or quality-bar reasons as a target-specific blocker, not as an invitation to resubmit with the same evidence.
Reject source-packet, evidence-packet, handoff-guide, Xquik toolkit,
xquik-twitter-data, or Xquik API integration submissions when they do not add a
target-native Hermes Tweet entry.

## Duplicate Gate

Before opening or refreshing a submission:

- Search the target README, docs, manifests, examples, skills, and indexes for
  `Hermes Tweet`, `hermes-tweet`, `Xquik`, and the repository URL.
- Run a public GitHub code search for live `Hermes Tweet`, `hermes-tweet`, and
  repository URL mentions before treating a target as fresh. If the hit is an
  accepted default-branch listing or generated named-skill listing, record it in `docs/ECOSYSTEM.md` instead of
  opening a duplicate submission.
- Check open and closed PRs and issues for prior Hermes Tweet proposals.
- Treat head-branch PR collision, PR-create duplicate branch errors, and "already exists for the same head branch" responses as overlap: treat a PR creation duplicate error as canonical overlap evidence, then inspect that existing PR instead of retrying.
- For Hermes-native awesome/plugin catalogs, repository-config catalogs with prior closed Hermes Tweet or Xquik route, cross-CLI skill libraries, SkillX-style seed JSON with an existing open Hermes Tweet seed PR, personal Claude Code plugin marketplace with an open Hermes Tweet plugin PR, and OpenClaw, Antigravity, Codex, Cursor, Claude, or Gemini marketplace mirrors, treat any open or merged Hermes Tweet listing, or any existing Hermes Tweet listing or merged PR, as duplicate saturation. Repair that existing route before opening a new listing.
- Reject targets that require an unsigned CLA or legal agreement before mergeability; close any discovered attempt and defer the route until the account owner signs.
- Treat a closed prior Hermes Tweet issue as a completed or rejected submission
  route. Do not reopen the same target with a PR unless a maintainer asks for a
  new PR, conversion, or updated evidence.
- Search open and closed PRs and issues for adjacent `TweetClaw`, `OpenClaw`,
  `SocialClaw`, `x-twitter-scraper`, and Xquik-only proposals before treating a
  target as fresh.
- Treat adjacent-only PR history as a conflict signal unless the target docs
  show a separate native Hermes Tweet route.
- Treat accepted adjacent entries as saturation too. If the target already has
  a live Xquik, TweetClaw, OpenClaw, SocialClaw, or x-twitter-scraper entry in
  the same catalog, tool list, or awesome-list section, reject another Hermes
  Tweet submission unless the target has a distinct Hermes Agent plugin lane.
- For awesome lists, plugin lists, and topic-search hits, including universal skill hubs, treat an open
  adjacent X/social submission or adjacent skill PR in the same target as saturation when the target
  has no explicit Hermes Tweet or Hermes Agent plugin lane. A generic Claude
  plugin or agent-skill heading is not enough by itself when the adjacent entry
  would occupy the same list slot.
- If any open authored PR in the target is Xquik-only, TweetClaw-only,
  OpenClaw-only, source-packet-only, evidence-packet-only, MCP-data-only, or
  otherwise adjacent-only, treat the target as saturated. Do not open another
  submission there unless a maintainer explicitly asks for a target-specific
  Hermes Tweet conversion or separate native Hermes Tweet entry.
- Require the PR or issue title and summary to name `Hermes Tweet` or
  `hermes-tweet`. Do not submit or refresh routes titled only for `Xquik`,
  `TweetClaw`, `OpenClaw`, or other adjacent projects.
- Before waiting on checks, reread the outbound title, summary, and added
  lines. If the branch or PR is Xquik-only, TweetClaw-only, OpenClaw-only, or
  otherwise adjacent-only, close it immediately with a short scope comment
  instead of leaving off-scope outreach open.
- Reject slugs, package names, plugin names, or catalog keys centered on
  `xquik-*`, `tweetclaw-*`, `openclaw-*`, `source-packets`, or
  `evidence-packets` unless the same submission clearly installs or indexes
  Hermes Tweet as the native entry.
- Check accepted examples so the wording, file layout, and validation match the
  target's own format.
- For translated or mirrored awesome lists, check the upstream source list and
  translation issue tracker. If either already has a live Hermes Tweet entry,
  open Hermes Tweet PR, or open Hermes Tweet issue, treat the mirror as
  duplicate unless the maintainer asks for an independent localized submission.
- Trace fork parents before using a personal fork, and use a renamed fork only
  when the normal fork name is already occupied by another parent.
- Respect target contribution docs. If a target requires issue-first
  submissions or maintainer-curated additions, update the existing issue or
  open a new issue instead of opening a direct PR.

If a target already has a live Hermes Tweet entry or the same target already has an open Hermes Tweet PR, do not open another one.
Refresh only when it fixes a concrete merge blocker, stale target-native wording, stale source pin, or broken validation evidence.

## Native Wording

Prefer concise wording that explains where Hermes Tweet fits:

- native Hermes Agent X/Twitter plugin
- optional Hermes Agent backend for X/Twitter reads
- read-only by default, with explicit action gating
- compatible with Hermes Desktop, remote gateway, TUI, CLI, dashboard, cron, and
  CI smoke-test surfaces
- source-native `.claude-plugin/plugin.json` metadata for catalogs that install
  plugins directly from a repository
- source-native `.codex-plugin/plugin.json` metadata with HOL Plugin Scanner
  evidence for Codex plugin catalogs
- complementary to local browser-cookie or direct OAuth examples
- copied endpoint URLs resolve only to catalog-listed `/api/v1/...` paths

Avoid wording that implies Hermes Tweet replaces the target project, fixes a
target bug, bypasses platform rules, removes user approval, or requires secrets
inside docs, prompts, issues, or PR comments.

## Validation

Every submission should include target-native validation when feasible:

- target tests, linters, manifest checks, catalog generators, or README
  generators
- `git diff --check`
- exact conflict-marker scan
- added-line public-safety scan for secrets and private implementation details
- live link checks for Hermes Tweet, Xquik, and target-owned links touched by
  the change

If the target has no CI and the submission repairs a conflict or review
request, leave at most one concise validation comment. Do not repeat comments
when the PR already has current validation evidence.

When creating PRs or issues from a shell, write Markdown bodies through a
reviewed file or another non-interpolating path. Verify the rendered body keeps
repository names, backticked literals, and validation commands intact before
waiting on checks or asking maintainers to review.

## Public-Safety Gate

Public submissions must not include:

- API keys, cookies, tokens, screenshots, logs, or private runtime artifacts
- nonpublic service names, restricted provider names, nonpublic pricing units,
  or private implementation details
- commands that require production SSH, browser login, manual legal acceptance,
  payment, or secret retrieval

Keep public examples to placeholder environment variable names and documented Hermes Tweet settings: `XQUIK_API_KEY`, `XQUIK_BASE_URL`, and `HERMES_TWEET_ENABLE_ACTIONS`.
