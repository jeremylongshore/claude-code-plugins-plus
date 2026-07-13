# Step 3: Team and Project Management

Deep-dive reference for the `figma-enterprise-rbac` skill — extracted from the 'Step 3: Team and Project Management' step of the workflow.

```typescript
// GET /v1/teams/:team_id/projects -- list team projects
async function getTeamProjects(teamId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/teams/${teamId}/projects`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.json(); // { projects: [{ id, name }] }
}

// GET /v1/projects/:project_id/files -- list project files
async function getProjectFiles(projectId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/projects/${projectId}/files`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.json(); // { files: [{ key, name, thumbnail_url, last_modified }] }
}

// GET /v1/teams/:team_id/components -- published components (Tier 3)
async function getTeamComponents(teamId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/teams/${teamId}/components`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.json();
  // { meta: { components: [{ key, file_key, node_id, name, description }] } }
}

// GET /v1/teams/:team_id/styles -- published styles (Tier 3)
async function getTeamStyles(teamId: string, token: string) {
  const res = await fetch(
    `https://api.figma.com/v1/teams/${teamId}/styles`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.json();
  // { meta: { styles: [{ key, file_key, node_id, name, style_type }] } }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
