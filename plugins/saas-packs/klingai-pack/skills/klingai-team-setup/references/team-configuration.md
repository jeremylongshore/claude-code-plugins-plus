# Team Configuration

## Team Configuration

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import os
import json

class TeamRole(Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"

@dataclass
class TeamMember:
    id: str
    email: str
    name: str
    role: TeamRole
    projects: List[str] = field(default_factory=list)
    monthly_limit: Optional[int] = None  # Credits limit

@dataclass
class Project:
    id: str
    name: str
    description: str
    api_key: str  # Project-specific API key
    members: List[str] = field(default_factory=list)
    monthly_budget: int = 1000  # Credits

@dataclass
class TeamConfig:
    organization_id: str
    organization_name: str
    admin_email: str
    members: List[TeamMember] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    global_monthly_limit: int = 10000  # Total org credits

class TeamManager:
    """Manage Kling AI team configuration."""

    def __init__(self, config_path: str = "team_config.json"):
        self.config_path = config_path
        self.config: Optional[TeamConfig] = None

    def load_config(self) -> TeamConfig:
        """Load team configuration from file."""
        if os.path.exists(self.config_path):
            with open(self.config_path) as f:
                data = json.load(f)
                self.config = self._parse_config(data)
        else:
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        return self.config

    def save_config(self):
        """Save team configuration to file."""
        if self.config:
            with open(self.config_path, "w") as f:
                json.dump(self._serialize_config(), f, indent=2)

    def add_member(self, member: TeamMember):
        """Add a new team member."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        # Check for duplicates
        if any(m.email == member.email for m in self.config.members):
            raise ValueError(f"Member already exists: {member.email}")

        self.config.members.append(member)
        self.save_config()
        print(f"Added member: {member.name} ({member.role.value})")

    def remove_member(self, email: str):
        """Remove a team member."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        self.config.members = [m for m in self.config.members if m.email != email]
        self.save_config()
        print(f"Removed member: {email}")

    def create_project(self, project: Project):
        """Create a new project."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        if any(p.id == project.id for p in self.config.projects):
            raise ValueError(f"Project already exists: {project.id}")

        self.config.projects.append(project)
        self.save_config()
        print(f"Created project: {project.name}")

    def assign_to_project(self, member_email: str, project_id: str):
        """Assign a member to a project."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        member = next((m for m in self.config.members if m.email == member_email), None)
        project = next((p for p in self.config.projects if p.id == project_id), None)

        if not member:
            raise ValueError(f"Member not found: {member_email}")
        if not project:
            raise ValueError(f"Project not found: {project_id}")

        if project_id not in member.projects:
            member.projects.append(project_id)
        if member.id not in project.members:
            project.members.append(member.id)

        self.save_config()
        print(f"Assigned {member.name} to {project.name}")

    def get_member_projects(self, email: str) -> List[Project]:
        """Get all projects for a member."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        member = next((m for m in self.config.members if m.email == email), None)
        if not member:
            return []

        return [p for p in self.config.projects if p.id in member.projects]

    def check_permission(self, email: str, project_id: str, action: str) -> bool:
        """Check if member has permission for action on project."""
        if not self.config:
            raise RuntimeError("Config not loaded")

        member = next((m for m in self.config.members if m.email == email), None)
        if not member:
            return False

        # Admin can do anything
        if member.role == TeamRole.ADMIN:
            return True

        # Check project assignment
        if project_id not in member.projects:
            return False

        # Role-based permissions
        permissions = {
            TeamRole.MANAGER: ["view", "generate", "manage_members"],
            TeamRole.DEVELOPER: ["view", "generate"],
            TeamRole.VIEWER: ["view"]
        }

        return action in permissions.get(member.role, [])

    def _parse_config(self, data: dict) -> TeamConfig:
        """Parse config from dict."""
        members = [
            TeamMember(
                id=m["id"],
                email=m["email"],
                name=m["name"],
                role=TeamRole(m["role"]),
                projects=m.get("projects", []),
                monthly_limit=m.get("monthly_limit")
            )
            for m in data.get("members", [])
        ]

        projects = [
            Project(
                id=p["id"],
                name=p["name"],
                description=p.get("description", ""),
                api_key=p["api_key"],
                members=p.get("members", []),
                monthly_budget=p.get("monthly_budget", 1000)
            )
            for p in data.get("projects", [])
        ]

        return TeamConfig(
            organization_id=data["organization_id"],
            organization_name=data["organization_name"],
            admin_email=data["admin_email"],
            members=members,
            projects=projects,
            global_monthly_limit=data.get("global_monthly_limit", 10000)
        )

    def _serialize_config(self) -> dict:
        """Serialize config to dict."""
        return {
            "organization_id": self.config.organization_id,
            "organization_name": self.config.organization_name,
            "admin_email": self.config.admin_email,
            "global_monthly_limit": self.config.global_monthly_limit,
            "members": [
                {
                    "id": m.id,
                    "email": m.email,
                    "name": m.name,
                    "role": m.role.value,
                    "projects": m.projects,
                    "monthly_limit": m.monthly_limit
                }
                for m in self.config.members
            ],
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "api_key": p.api_key,
                    "members": p.members,
                    "monthly_budget": p.monthly_budget
                }
                for p in self.config.projects
            ]
        }
```
