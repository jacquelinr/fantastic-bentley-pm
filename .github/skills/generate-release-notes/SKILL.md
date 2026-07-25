---
name: generate-release-notes
description: 'Generate a user-facing release note from a GitHub commit, Azure DevOps build URL, Azure DevOps commit URL, or Azure DevOps build definition URL/ID (multi-build). Fetches commit and work item details via git CLI or Azure DevOps APIs and writes a polished release note to projects/release-notes/.'
argument-hint: '<commit-sha|github-url|ado-build-url|ado-commit-url|ado-definition-url|definition-id> [from-date] [to-date]'
disable-model-invocation: true
context: fork
user-invocable: true
---

# Generate Release Notes

Generate a user-facing release note from a GitHub commit, Azure DevOps build/commit URL, or an Azure DevOps build definition (multi-build), written from the perspective of the end user.

**Author:** Jacqueline Chen 

**Usage:**
- GitHub: `/generate-release-notes <commit-sha>` or `/generate-release-notes <github-commit-url>`
- Azure DevOps: `/generate-release-notes <ado-build-url>` or `/generate-release-notes <ado-commit-url>`
- Azure DevOps (multi-build): `/generate-release-notes <ado-definition-url>` or `/generate-release-notes <definition-id>`
- Azure DevOps (multi-build + date range): `/generate-release-notes <definition-id> from <YYYY-MM-DD> to <YYYY-MM-DD|now>`

The argument can be:
- A commit SHA (e.g. `abc123def45`)
- A GitHub commit URL (e.g. `https://github.com/org/repo/commit/abc123`)
- An Azure DevOps build URL (e.g. `https://dev.azure.com/org/project/_build/results?buildId=12345`)
- An Azure DevOps commit URL (e.g. `https://dev.azure.com/org/project/_git/repo/commit/abc123`)
- An Azure DevOps build definition URL (e.g. `https://dev.azure.com/org/project/_build?definitionId=9507`)
- An Azure DevOps definition ID (e.g. `9507`) when organization/project context is available
- Optional date range for multi-build mode (e.g. `from 2026-04-01 to now`)

## Prerequisites

- **Azure CLI:** Run `az login` to authenticate with your Azure account
- **Personal Access Token:** If using the API directly, ensure you have an Azure DevOps PAT with appropriate permissions
- **Git:** For local Git operations, ensure you have the repository cloned locally

## Implementation References

Before writing any PowerShell commands, read: [PowerShell pitfalls](./references/powershell-pitfalls.md)

For multi-build data collection, use: [collect-builds.ps1](./scripts/collect-builds.ps1)

## Steps

### 1. Parse the URL or SHA

#### For GitHub:
Extract the commit SHA from the URL format: `https://github.com/<owner>/<repo>/commit/<sha>`

#### For Azure DevOps:
Extract relevant information from the URL:

- **Build URL:** `https://dev.azure.com/<organization>/<project>/_build/results?buildId=<buildId>` → extract org, project, buildId
- **Commit URL:** `https://dev.azure.com/<organization>/<project>/_git/<repo>/commit/<commitId>` → extract org, project, repo, commitId
- **Definition URL (multi-build):** `https://dev.azure.com/<organization>/<project>/_build?definitionId=<definitionId>` → extract org, project, definitionId
- **Plain definition ID:** Use current/default organization and project context

**Date range parsing for definition mode:**
- Accept explicit `from` and `to` dates (ISO format: `YYYY-MM-DD`)
- Interpret `to now` as current UTC timestamp
- If no date range is provided, default to latest 10 completed builds

#### Validation:
If no valid input is provided, report an error and stop.

### 2. Fetch Source Details

#### For GitHub or Direct Commit SHA:
```bash
git show <sha>
git show --stat <sha>
git show --patch <sha>
```

#### For Azure DevOps Build URL:
1. Get build details: `az pipelines build show --id <buildId> --organization https://dev.azure.com/<organization> --project <project> --output json`
2. Extract `sourceVersion` (commit SHA), `sourceBranch`, repository context
3. Fetch related work items using the Build Work Items endpoint (primary source):
   ```
   GET https://dev.azure.com/<organization>/<project>/_apis/build/builds/<buildId>/workitems?api-version=7.0
   ```
   Important: Do not rely only on `relatedWorkItems` inside `az pipelines build show` — it can be empty.
4. Merge fallback sources if needed (build changes, commit message refs, PR-linked items), dedupe by ID
5. Fetch commit details via `git show <sourceVersion>` or the REST API

#### For Azure DevOps Definition URL/ID (multi-build):

> **Performance:** Run data collection as a **single combined PowerShell script** in **async terminal mode**. Use [collect-builds.ps1](./scripts/collect-builds.ps1) as the template.

**Execution:**
1. Copy the script, substitute actual org/project/defId/dates
2. Save to `tmp/collect-<definitionId>.ps1`
3. Run async: `powershell -File "tmp/collect-<definitionId>.ps1"`
4. Wait for `DONE-MARKER` output
5. Read `tmp/wi-enriched-<definitionId>.json` for enriched data

**Checkpoint files** (in `tmp/`) enable resume if something fails:
- `sel-builds-<id>.json` — filtered builds
- `wi-map-<id>.json` — deduped work items per build
- `wi-enriched-<id>.json` — fully enriched output

| Approach | API calls (90 WIs + 64 parents) | Time |
|---|---|---|
| Old (individual calls) | ~154 sequential | 5–8 min |
| New (batch endpoint) | ~4 calls | 30–60 sec |

#### For Azure DevOps Commit URL:
Use `git show <commitId>` or the REST API:
```
GET https://dev.azure.com/<organization>/<project>/_apis/git/repositories/<repoId>/commits/<commitId>?api-version=7.0
```

### 3. Analyze the Changes

Focus on **user impact**, not technical implementation:
- What can users do now that they couldn't before?
- What works better now?
- What pain point is resolved?

### 3a. Extract Related Work Items and Parent Context

When a build URL or definition URL/ID is provided:

1. Start with work items from the Build Work Items endpoint(s)
2. For each work item, extract: ID, title, type, `relations` array
3. Construct work item URLs: `https://dev.azure.com/<organization>/<project>/_workitems/edit/<workItemId>`
4. Fetch parent work items (via `System.LinkTypes.Hierarchy-Reverse` relation)
5. Extract parent details: ID, title, type, description (user-need/problem statements)
6. Validate coverage: ensure all work item IDs from the build are in the final table
7. In multi-build mode: track which build ID(s) contributed each work item
8. Synthesize themes from parent descriptions:
   - Group child work items under each parent theme
   - Extract user-facing intent from parent descriptions
   - Cover all major parent themes in the narrative

**Note:** Parent work items provide strategic/feature context. Always use parent descriptions to shape the body narrative.

### 4. Load Context

Read optional product context files:
- `resources/features.md` — existing features and terminology (skip if not relevant)
- `resources/value-proposition.md` — product language alignment (skip if not relevant)

### 5. Write the Release Note

- **Title**: Clear, user-facing, Title Case (`# H1`). Reads like a feature announcement.
- **Summary**: Bulleted `## Summary` section — one bullet per major theme, quick at-a-glance overview.
- **Body**: 1-6 paragraphs covering what changed, the value to users, and each major parent theme.
- **Related Work Items** (footer): Table with full traceability:

  ```markdown
  ---

  ## Related Work Items

  | ID | Title | Type | Build IDs |
  |---|---|---|---|
  | [#2030732](https://dev.azure.com/<org>/<project>/_workitems/edit/2030732) | Track app crashes | User Story | 5050746, 5050712 |
  ```

**Writing guidelines:**
- Write for end users, not developers
- Lead with the benefit or capability, not the technical change
- Don't mention commits, PRs, code, or technical internals
- Follow benefit-first, grouped-sections style (similar to ServiceNow release notes)
- Prioritize parent items (Epics, Features) over child items (Tasks, Bugs) for user clarity
- One sentence per work item: what changed + why it matters

### 6. Save the Release Note

Ask the user which directory to save the release note to. Suggest `projects/release-notes/` as the default.

Filename format: `YYYY-MM-DD-<slug>.md` (kebab-case title)
Save to: `<user-specified-directory>/<filename>`

### 7. Report Result

Output the release note content and confirm the file path.
