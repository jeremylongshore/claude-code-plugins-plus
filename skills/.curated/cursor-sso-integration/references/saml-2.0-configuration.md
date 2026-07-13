# Saml 2.0 Configuration

## SAML 2.0 Configuration

### Cursor SAML Details

```
For your IdP configuration:

ACS URL (Assertion Consumer Service):
https://cursor.com/api/auth/saml/callback

Entity ID (SP Entity ID):
https://cursor.com/saml/sp

Name ID Format:
urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress

Required Attributes:
- email (required)
- firstName (optional)
- lastName (optional)
```

### IdP Configuration

#### Okta

```
1. Admin Console > Applications > Create App Integration
2. Select SAML 2.0
3. Configure:
   - App name: Cursor
   - Single sign on URL: https://cursor.com/api/auth/saml/callback
   - Audience URI: https://cursor.com/saml/sp
   - Name ID format: Email
4. Attribute Statements:
   - email: user.email
   - firstName: user.firstName
   - lastName: user.lastName
5. Download IdP metadata XML
6. Upload to Cursor Admin
```

#### Azure AD (Entra ID)

```
1. Azure Portal > Enterprise Applications > New
2. Create your own application
3. Set up SSO > SAML
4. Configure:
   - Identifier: https://cursor.com/saml/sp
   - Reply URL: https://cursor.com/api/auth/saml/callback
   - Sign on URL: https://cursor.com
5. Attributes & Claims:
   - email: user.mail
   - firstName: user.givenname
   - lastName: user.surname
6. Download Federation Metadata XML
7. Upload to Cursor Admin
```

#### Google Workspace

```
1. Admin Console > Apps > Web and mobile apps
2. Add App > Search for or Add Custom SAML App
3. Configure:
   - ACS URL: https://cursor.com/api/auth/saml/callback
   - Entity ID: https://cursor.com/saml/sp
   - Name ID format: EMAIL
4. Attribute Mapping:
   - email: Primary Email
   - firstName: First Name
   - lastName: Last Name
5. Download IdP metadata
6. Upload to Cursor Admin
```

### Completing Setup in Cursor

```
1. Cursor Admin > Settings > SSO
2. Upload IdP metadata XML
   - Or enter details manually:
     - SSO URL
     - Certificate
     - Entity ID
3. Save configuration
4. Test SSO login
5. Enable for organization
```
