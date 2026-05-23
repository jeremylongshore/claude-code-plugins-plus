# Installing Extensions

## Installing Extensions

### From Marketplace

```
1. Open Extensions panel: Cmd+Shift+X
2. Search for extension
3. Click Install
4. Reload if prompted
```

### From Command Line

```bash
# Install extension
cursor --install-extension <extension-id>

# Example
cursor --install-extension esbenp.prettier-vscode
cursor --install-extension dbaeumer.vscode-eslint

# List installed extensions
cursor --list-extensions

# Uninstall extension
cursor --uninstall-extension <extension-id>
```

### From VSIX File

```bash
# Install from local file
cursor --install-extension path/to/extension.vsix

# Useful for:
- Private extensions
- Specific versions
- Offline installation
```
