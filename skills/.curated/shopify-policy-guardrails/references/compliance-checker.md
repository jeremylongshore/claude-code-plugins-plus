# App Store Compliance Checker

Pre-submission script that validates GDPR webhooks, token hygiene, CSP headers, and API version stability.

```typescript
// scripts/check-app-compliance.ts
// Run before submitting to Shopify App Store

interface ComplianceCheck {
  name: string;
  required: boolean;
  check: () => Promise<boolean>;
}

const checks: ComplianceCheck[] = [
  {
    name: "GDPR webhook: customers/data_request",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return toml.includes("customers/data_request");
    },
  },
  {
    name: "GDPR webhook: customers/redact",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return toml.includes("customers/redact");
    },
  },
  {
    name: "GDPR webhook: shop/redact",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return toml.includes("shop/redact");
    },
  },
  {
    name: "No hardcoded tokens in source",
    required: true,
    check: async () => {
      const { execSync } = require("child_process");
      const result = execSync(
        'grep -rE "shpat_[a-f0-9]{32}" app/ --include="*.ts" --include="*.tsx" || true'
      ).toString();
      return result.trim() === "";
    },
  },
  {
    name: "CSP frame-ancestors header set",
    required: true,
    check: async () => {
      const files = await glob("app/**/*.ts");
      const hasCSP = files.some((f) => {
        const content = readFileSync(f, "utf-8");
        return content.includes("frame-ancestors");
      });
      return hasCSP;
    },
  },
  {
    name: "API version is not unstable",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return !toml.includes('api_version = "unstable"');
    },
  },
];

async function runComplianceChecks(): Promise<void> {
  console.log("=== Shopify App Store Compliance Check ===\n");
  let passed = 0;
  let failed = 0;

  for (const check of checks) {
    const result = await check.check();
    const status = result ? "PASS" : check.required ? "FAIL" : "WARN";
    console.log(`${status}: ${check.name}`);
    result ? passed++ : failed++;
  }

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}
```
