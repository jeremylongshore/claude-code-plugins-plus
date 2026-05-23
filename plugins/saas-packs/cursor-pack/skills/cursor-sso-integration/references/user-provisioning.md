# User Provisioning

## User Provisioning

### Just-In-Time (JIT) Provisioning

```
How it works:
1. User attempts Cursor login
2. Redirects to IdP
3. User authenticates
4. IdP sends SAML assertion
5. Cursor creates account automatically
6. User has immediate access

Benefits:
- No manual user creation
- Always synchronized
- Reduced admin overhead
```

### SCIM Provisioning

```
For Enterprise plans:

SCIM Endpoint: https://cursor.com/scim/v2
Supported operations:
- Create users
- Update users
- Deactivate users
- Group management

Configure in IdP:
1. Add SCIM provisioning
2. Enter Cursor SCIM endpoint
3. Configure Bearer token
4. Map attributes
5. Enable sync
```
