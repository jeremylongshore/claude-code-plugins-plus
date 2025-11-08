# Skill Best Practices

Guidelines for optimal skill usage and development.

## For Users

### Activation Best Practices

1. **Use Clear Trigger Phrases**
   - Match phrases from skill description
   - Be specific about intent
   - Provide necessary context

2. **Provide Sufficient Context**
   - Include relevant file paths
   - Specify scope of analysis
   - Mention any constraints

3. **Understand Tool Permissions**
   - Check allowed-tools in frontmatter
   - Know what the skill can/cannot do
   - Request appropriate actions

### Workflow Optimization

- Start with simple requests
- Build up to complex workflows
- Verify each step before proceeding
- Use skill consistently for related tasks

## For Developers

### Skill Development Guidelines

1. **Clear Descriptions**
   - Include explicit trigger phrases
   - Document all capabilities
   - Specify limitations

2. **Proper Tool Permissions**
   - Use minimal necessary tools
   - Document security implications
   - Test with restricted tools

3. **Comprehensive Documentation**
   - Provide usage examples
   - Document common pitfalls
   - Include troubleshooting guide

### Maintenance

- Keep version updated
- Test after tool updates
- Monitor user feedback
- Iterate on descriptions

## Performance Tips

- Scope skills to specific domains
- Avoid overlapping trigger phrases
- Keep descriptions under 1024 chars
- Test activation reliability

## Security Considerations

- Never include secrets in skill files
- Validate all inputs
- Use read-only tools when possible
- Document security requirements
