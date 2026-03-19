import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// process.cwd() is `site/` during build; README is one level up at project root
const README_PATH = resolve(process.cwd(), '..', 'README.md');

function readReadme(): string {
  return readFileSync(README_PATH, 'utf-8');
}

/** Extract content between two headings of the same level */
function extractSection(content: string, heading: string, level = 2): string {
  const prefix = '#'.repeat(level);
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const lines = content.split('\n');
  let start = -1;
  let end = lines.length;

  for (let i = 0; i < lines.length; i++) {
    if (start === -1) {
      if (lines[i].match(new RegExp(`^${prefix}\\s+${escaped}\\s*$`))) {
        start = i + 1;
      }
    } else if (lines[i].match(new RegExp(`^#{1,${level}}\\s`))) {
      end = i;
      break;
    }
  }

  if (start === -1) return '';
  return lines.slice(start, end).join('\n').trim();
}

export interface ReadmeData {
  tagline: string;
  description: string;
  whatItDoes: string;
  quickStart: {
    local: string;
    intent: string;
    githubPR: string;
  };
  mcpTools: { tool: string; description: string }[];
  pluginInstall: string;
  agentProtocol: string;
  exitCodes: { code: string; meaning: string }[];
  driftSignals: { signal: string; trigger: string }[];
  cliReference: string;
  riskClassification: { category: string; severity: string; triggers: string }[];
  architecture: string;
  designPrinciples: string[];
  envVars: { variable: string; required: string; description: string }[];
  githubAction: string;
}

function parseTable(section: string): Record<string, string>[] {
  const lines = section.split('\n').filter(l => l.trim().startsWith('|'));
  if (lines.length < 3) return [];
  const headers = lines[0].split('|').map(h => h.trim()).filter(Boolean);
  return lines.slice(2).map(line => {
    const cells = line.split('|').map(c => c.trim()).filter(Boolean);
    const row: Record<string, string> = {};
    headers.forEach((h, i) => { row[h.toLowerCase()] = cells[i] || ''; });
    return row;
  });
}

function extractCodeBlock(content: string, lang?: string): string {
  const pattern = lang
    ? new RegExp(`\`\`\`${lang}\\n([\\s\\S]*?)\`\`\``, 'm')
    : /```[\w]*\n([\s\S]*?)```/m;
  const match = content.match(pattern);
  return match ? match[1].trim() : '';
}

export function parseReadme(): ReadmeData {
  const content = readReadme();

  // Tagline and description from first lines
  const lines = content.split('\n');
  const tagline = lines.find(l => l.startsWith('**'))?.replace(/\*\*/g, '') || '';
  const descLine = lines.find(l => l.startsWith('Turn any code change'));
  const description = descLine || '';

  // What It Does
  const whatItDoes = extractSection(content, 'What It Does');

  // Quick Start sections
  const quickStartFull = extractSection(content, 'Quick Start');
  const localSection = extractSection(quickStartFull, 'Local Diff \\(no GitHub needed\\)', 3);
  const intentSection = extractSection(quickStartFull, 'Intent \\+ Drift Detection', 3);
  const prSection = extractSection(quickStartFull, 'GitHub PR Analysis', 3);

  // MCP Server
  const mcpSection = extractSection(content, 'MCP Server');
  const toolsTable = parseTable(mcpSection);
  const mcpTools = toolsTable.map(r => ({
    tool: r['tool']?.replace(/`/g, '') || '',
    description: r['description'] || '',
  }));

  // Plugin install code
  const pluginInstall = extractSection(mcpSection, 'Plugin Installation', 3);

  // Agent Protocol
  const agentSection = extractSection(content, 'Agent Protocol');
  const agentProtocol = extractCodeBlock(agentSection, 'json');

  // Exit Codes
  const exitTable = parseTable(extractSection(agentSection, 'Exit Codes', 3));
  const exitCodes = exitTable.map(r => ({
    code: r['code']?.replace(/`/g, '') || '',
    meaning: r['meaning'] || '',
  }));

  // Drift Signals
  const driftTable = parseTable(extractSection(agentSection, 'Drift Signals', 3));
  const driftSignals = driftTable.map(r => ({
    signal: r['signal']?.replace(/`/g, '') || '',
    trigger: r['trigger'] || '',
  }));

  // CLI Reference
  const cliReference = extractSection(content, 'CLI Reference');

  // Risk Classification
  const riskSection = extractSection(content, 'Risk Classification');
  const riskTable = parseTable(riskSection);
  const riskClassification = riskTable.map(r => ({
    category: r['category']?.replace(/`/g, '') || '',
    severity: r['severity']?.replace(/\*\*/g, '') || '',
    triggers: r['triggers'] || '',
  }));

  // Architecture
  const archSection = extractSection(content, 'Architecture');
  const architecture = extractCodeBlock(archSection);

  // Design Principles
  const dpSection = extractSection(archSection, 'Design Principles', 3);
  const designPrinciples = dpSection
    .split('\n')
    .filter(l => l.startsWith('- '))
    .map(l => l.replace(/^- /, ''));

  // Environment Variables
  const envSection = extractSection(content, 'Environment Variables');
  const envTable = parseTable(envSection);
  const envVars = envTable.map(r => ({
    variable: r['variable']?.replace(/`/g, '') || '',
    required: r['required'] || '',
    description: r['description'] || '',
  }));

  // GitHub Action
  const gaSection = extractSection(content, 'GitHub Action');
  const githubAction = extractCodeBlock(gaSection, 'yaml');

  return {
    tagline,
    description,
    whatItDoes,
    quickStart: {
      local: extractCodeBlock(localSection, 'bash'),
      intent: extractCodeBlock(intentSection, 'bash'),
      githubPR: extractCodeBlock(prSection, 'bash'),
    },
    mcpTools,
    pluginInstall,
    agentProtocol,
    exitCodes,
    driftSignals,
    cliReference,
    riskClassification,
    architecture,
    designPrinciples,
    envVars,
    githubAction,
  };
}
