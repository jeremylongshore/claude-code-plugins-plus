# Apollo Core Workflow A: Lead Search & Enrichment - Implementation Guide

> Full implementation details and code examples for the `apollo-core-workflow-a` skill.

# Apollo Core Workflow A: Lead Search & Enrichment

## Overview
Implement the primary Apollo.io workflow for searching leads and enriching contact/company data. This is the core use case for B2B sales intelligence.

## Prerequisites
- Completed `apollo-sdk-patterns` setup
- Valid Apollo API credentials
- Understanding of your target market criteria

## Workflow Components

### 1. People Search
Search for contacts based on various criteria like company, title, location, and industry.

```typescript
// src/services/apollo/people-search.ts
import { apollo } from '../../lib/apollo/client';

interface PeopleSearchCriteria {
  domains?: string[];
  titles?: string[];
  locations?: string[];
  industries?: string[];
  employeeRanges?: string[];
  page?: number;
  perPage?: number;
}

export async function searchPeople(criteria: PeopleSearchCriteria) {
  const response = await apollo.searchPeople({
    q_organization_domains: criteria.domains,
    person_titles: criteria.titles,
    person_locations: criteria.locations,
    q_organization_industry_tag_ids: criteria.industries,
    organization_num_employees_ranges: criteria.employeeRanges,
    page: criteria.page || 1,
    per_page: criteria.perPage || 25,
  });

  return {
    contacts: response.people.map(transformPerson),
    pagination: response.pagination,
  };
}

function transformPerson(person: any) {
  return {
    id: person.id,
    name: person.name,
    firstName: person.first_name,
    lastName: person.last_name,
    title: person.title,
    email: person.email,
    phone: person.phone_numbers?.[0]?.sanitized_number,
    linkedin: person.linkedin_url,
    company: {
      id: person.organization?.id,
      name: person.organization?.name,
      domain: person.organization?.primary_domain,
    },
  };
}
```

### 2. Company Enrichment
Enrich company data to get comprehensive firmographic information.

```typescript
// src/services/apollo/company-enrichment.ts
import { apollo } from '../../lib/apollo/client';

export async function enrichCompany(domain: string) {
  const response = await apollo.enrichOrganization(domain);
  const org = response.organization;

  return {
    id: org.id,
    name: org.name,
    domain: org.primary_domain,
    website: org.website_url,
    industry: org.industry,
    subIndustry: org.sub_industry,
    employeeCount: org.estimated_num_employees,
    annualRevenue: org.annual_revenue,
    founded: org.founded_year,
    description: org.short_description,
    technologies: org.technologies || [],
    locations: {
      headquarters: {
        city: org.city,
        state: org.state,
        country: org.country,
      },
    },
    social: {
      linkedin: org.linkedin_url,
      twitter: org.twitter_url,
      facebook: org.facebook_url,
    },
  };
}
```

### 3. Contact Enrichment
Enrich individual contacts with email and additional data.

```typescript
// src/services/apollo/contact-enrichment.ts
export async function enrichContact(params: {
  email?: string;
  firstName?: string;
  lastName?: string;
  domain?: string;
  linkedinUrl?: string;
}) {
  const response = await apollo.enrichPerson({
    email: params.email,
    first_name: params.firstName,
    last_name: params.lastName,
    organization_domain: params.domain,
    linkedin_url: params.linkedinUrl,
  });

  return {
    ...transformPerson(response.person),
    enrichmentScore: calculateEnrichmentScore(response.person),
  };
}

function calculateEnrichmentScore(person: any): number {
  let score = 0;
  if (person.email) score += 30;
  if (person.phone_numbers?.length) score += 20;
  if (person.linkedin_url) score += 15;
  if (person.title) score += 10;
  if (person.organization) score += 15;
  if (person.city) score += 10;
  return score;
}
```

### 4. Complete Lead Generation Pipeline

```typescript
// src/services/apollo/lead-pipeline.ts
import { searchPeople } from './people-search';
import { enrichCompany } from './company-enrichment';
import { enrichContact } from './contact-enrichment';

interface LeadCriteria {
  targetDomains?: string[];
  targetTitles: string[];
  targetLocations?: string[];
  targetIndustries?: string[];
  minEmployees?: number;
  maxEmployees?: number;
}

export async function generateLeads(criteria: LeadCriteria) {
  // Step 1: Search for matching contacts
  const searchResults = await searchPeople({
    domains: criteria.targetDomains,
    titles: criteria.targetTitles,
    locations: criteria.targetLocations,
    industries: criteria.targetIndustries,
  });

  // Step 2: Enrich companies for each unique domain
  const uniqueDomains = [...new Set(
    searchResults.contacts
      .map(c => c.company.domain)
      .filter(Boolean)
  )];

  const enrichedCompanies = await Promise.all(
    uniqueDomains.slice(0, 10).map(async (domain) => {
      try {
        return await enrichCompany(domain);
      } catch {
        return null;
      }
    })
  );

  const companyMap = new Map(
    enrichedCompanies
      .filter(Boolean)
      .map(c => [c!.domain, c])
  );

  // Step 3: Combine and filter results
  return searchResults.contacts.map(contact => ({
    ...contact,
    company: companyMap.get(contact.company.domain) || contact.company,
  }));
}
```

## Usage Example

```typescript
// Example: Find engineering leads at fintech companies
const leads = await generateLeads({
  targetTitles: ['VP Engineering', 'CTO', 'Engineering Manager'],
  targetIndustries: ['financial services', 'fintech'],
  minEmployees: 50,
  maxEmployees: 500,
});

console.log(`Found ${leads.length} leads`);
leads.forEach(lead => {
  console.log(`${lead.name} - ${lead.title} at ${lead.company.name}`);
});
```

## Output
- Paginated people search results
- Enriched company firmographic data
- Enriched contact data with emails
- Combined lead pipeline with scoring

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty Results | Too narrow criteria | Broaden search parameters |
| Missing Emails | Contact not in database | Try LinkedIn enrichment |
| Rate Limited | Too many enrichment calls | Implement batching |
| Invalid Domain | Domain doesn't exist | Validate domains first |

## Resources
- [Apollo People Search Docs](https://apolloio.github.io/apollo-api-docs/#search-for-people)
- [Apollo Organization Enrichment](https://apolloio.github.io/apollo-api-docs/#enrich-organization)
- [Apollo Person Enrichment](https://apolloio.github.io/apollo-api-docs/#enrich-person)

## Next Steps
Proceed to `apollo-core-workflow-b` for email sequences and outreach.
