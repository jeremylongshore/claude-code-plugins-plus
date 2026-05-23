# Release Workflow

## Release Workflow

Complete release process:

1. **Determine Bump Type**
   - Review changes since last version
   - Decide: patch/minor/major

2. **Update Version**
   - Bump plugin.json
   - Update marketplace catalog
   - Sync marketplace.json

3. **Update Changelog**
   - Add release notes
   - List changes
   - Include date

4. **Commit Changes**

   ```bash
   git add .
   git commit -m "chore: Release v1.2.4"
   ```

5. **Create Tag**

   ```bash
   git tag -a "v1.2.4" -m "Release v1.2.4"
   ```

6. **Push**

   ```bash
   git push origin main
   git push origin v1.2.4
   ```

7. **Validate**
   - Check GitHub release created
   - Verify marketplace updated
   - Test plugin installation
