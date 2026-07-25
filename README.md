# Product Hub Skills

Shared [Copilot agent skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills) for the product team. These skills help automate common product workflows inside VS Code and reduce time PM has to spend on those daily tasks.

## How to Use

### Project-level (recommended for teams)

Clone or copy the `.github/skills/` folder into your own repository:

```
your-repo/
├── .github/
│   └── skills/
│       └── answer-data-curiosity/
│           └── SKILL.md
```

### Personal-level

Copy individual skill folders to your personal skills directory:

- Windows: `%USERPROFILE%\.agents\skills\`
- macOS/Linux: `~/.agents/skills/`

Skills placed here are available in all your workspaces.

## Available Skills

| Skill | Description |
|-------|-------------|
| `answer-data-curiosity` | Answer data questions by querying your data warehouse (Snowflake, Databricks) |
| `batch-send-emails` | Batch send a reusable email to many users by loading the content from a separate file |
| `generate-release-notes` | Generate user-facing release notes from GitHub commits or Azure DevOps builds/definitions |

## Contributing

1. Create a new folder under `.github/skills/<skill-name>/`
2. Add a `SKILL.md` with proper frontmatter (`name`, `description`) and step-by-step procedures
3. Keep `SKILL.md` under 500 lines — split heavy content into `./references/`
4. Open a PR for review
