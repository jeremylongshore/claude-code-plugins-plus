Full company CRUD operations for Shopify B2B using the GraphQL Admin API.

## Create a Company with Multiple Contacts

```typescript
const COMPANY_CREATE = `
  mutation companyCreate($input: CompanyCreateInput!) {
    companyCreate(input: $input) {
      company {
        id
        name
        note
        externalId
        mainContact {
          id
          customer { id email firstName lastName }
        }
        locations(first: 10) {
          edges {
            node {
              id
              name
              shippingAddress { address1 city provinceCode countryCode zip }
            }
          }
        }
      }
      userErrors { field message code }
    }
  }
`;

await client.request(COMPANY_CREATE, {
  variables: {
    input: {
      company: {
        name: "Acme Distribution LLC",
        note: "Gold tier partner since 2024",
        externalId: "CRM-ACME-001", // Your internal ID for syncing
      },
      companyContact: {
        email: "purchasing@acme-dist.com",
        firstName: "Sarah",
        lastName: "Chen",
        title: "Head of Procurement",
      },
      companyLocation: {
        name: "Main Warehouse",
        billingAddress: {
          address1: "500 Industrial Blvd",
          address2: "Suite 100",
          city: "Dallas",
          provinceCode: "TX",
          countryCode: "US",
          zip: "75201",
          phone: "+12145551234",
        },
        shippingAddress: {
          address1: "500 Industrial Blvd",
          address2: "Dock 3",
          city: "Dallas",
          provinceCode: "TX",
          countryCode: "US",
          zip: "75201",
        },
      },
    },
  },
});
```

## Add Additional Contacts

```typescript
const CONTACT_CREATE = `
  mutation companyContactCreate(
    $companyId: ID!,
    $input: CompanyContactInput!
  ) {
    companyContactCreate(companyId: $companyId, input: $input) {
      companyContact {
        id
        customer { id email }
        title
        isMainContact
      }
      userErrors { field message code }
    }
  }
`;

await client.request(CONTACT_CREATE, {
  variables: {
    companyId: "gid://shopify/Company/123",
    input: {
      email: "accounts@acme-dist.com",
      firstName: "Mike",
      lastName: "Johnson",
      title: "Accounts Payable",
    },
  },
});
```

## Add Additional Locations

```typescript
const LOCATION_CREATE = `
  mutation companyLocationCreate(
    $companyId: ID!,
    $input: CompanyLocationInput!
  ) {
    companyLocationCreate(companyId: $companyId, input: $input) {
      companyLocation {
        id
        name
        shippingAddress { address1 city provinceCode }
      }
      userErrors { field message code }
    }
  }
`;

await client.request(LOCATION_CREATE, {
  variables: {
    companyId: "gid://shopify/Company/123",
    input: {
      name: "West Coast Warehouse",
      billingAddress: {
        address1: "200 Pacific Ave",
        city: "Los Angeles",
        provinceCode: "CA",
        countryCode: "US",
        zip: "90001",
      },
      shippingAddress: {
        address1: "200 Pacific Ave",
        city: "Los Angeles",
        provinceCode: "CA",
        countryCode: "US",
        zip: "90001",
      },
    },
  },
});
```

## Update a Company

```typescript
const COMPANY_UPDATE = `
  mutation companyUpdate($companyId: ID!, $input: CompanyInput!) {
    companyUpdate(companyId: $companyId, input: $input) {
      company {
        id
        name
        note
      }
      userErrors { field message code }
    }
  }
`;

await client.request(COMPANY_UPDATE, {
  variables: {
    companyId: "gid://shopify/Company/123",
    input: {
      name: "Acme Distribution International",
      note: "Upgraded to Platinum tier Q1 2026",
    },
  },
});
```

## Query Companies

```typescript
const COMPANIES_QUERY = `
  query companies($first: Int!, $query: String, $after: String) {
    companies(first: $first, query: $query, after: $after) {
      edges {
        node {
          id
          name
          note
          externalId
          contactCount
          locationCount
          ordersCount
          mainContact {
            customer { email }
          }
          locations(first: 5) {
            edges {
              node {
                id
                name
                catalogs(first: 5) {
                  edges { node { id title } }
                }
              }
            }
          }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
`;

// Search by name
await client.request(COMPANIES_QUERY, {
  variables: { first: 25, query: "name:Acme*" },
});
```

## Delete a Company

```typescript
const COMPANY_DELETE = `
  mutation companyDelete($id: ID!) {
    companyDelete(id: $id) {
      deletedCompanyId
      userErrors { field message code }
    }
  }
`;

// WARNING: This also removes all associated contacts, locations, and catalog assignments
await client.request(COMPANY_DELETE, {
  variables: { id: "gid://shopify/Company/123" },
});
```

## Assign Contact Roles

```typescript
const ASSIGN_ROLE = `
  mutation companyContactAssignRole(
    $companyContactId: ID!,
    $companyContactRoleAssignment: CompanyContactRoleAssignmentInput!
  ) {
    companyContactAssignRole(
      companyContactId: $companyContactId,
      companyContactRoleAssignment: $companyContactRoleAssignment
    ) {
      companyContactRoleAssignment {
        id
        role { id name }
      }
      userErrors { field message }
    }
  }
`;

// Roles: "Order only", "Location admin", "Location manager"
await client.request(ASSIGN_ROLE, {
  variables: {
    companyContactId: "gid://shopify/CompanyContact/456",
    companyContactRoleAssignment: {
      companyLocationId: "gid://shopify/CompanyLocation/789",
      roleId: "gid://shopify/CompanyContactRole/1", // Look up via companyContactRoles query
    },
  },
});
```
