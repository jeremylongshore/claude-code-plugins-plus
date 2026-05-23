# Testing Sso

## Testing SSO

### Pre-Launch Testing

```
1. Test with admin account first
2. Verify attribute mapping
3. Check role assignment
4. Test provisioning/deprovisioning
5. Verify logout behavior

Test checklist:
[ ] Login works
[ ] User attributes correct
[ ] Roles assigned properly
[ ] Logout clears session
[ ] Re-login works
```

### Troubleshooting

#### "SAML Response Invalid"

```
Check:
- Certificate hasn't expired
- Clock sync between IdP and SP
- Correct ACS URL
- Valid signature
```

#### "User Not Authorized"

```
Check:
- User assigned to app in IdP
- Email domain verified
- Proper group membership
- Attribute mapping correct
```

#### "Session Timeout Issues"

```
Check:
- IdP session length
- Cursor session settings
- Token refresh configuration
```
