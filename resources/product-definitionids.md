# Product Definition IDs

> **Referenced by:** [`generate-release-notes`](../.github/skills/generate-release-notes/SKILL.md)

A mapping of product names to their build definition IDs in your CI/CD system (e.g., Azure DevOps).

## Format

```
<Product Name>: <Build Definition URL or ID>
```

## Example

| Product | Definition ID | URL |
|---------|--------------|-----|
| Product A | 15168 | `https://dev.azure.com/<org>/<project>/_build?definitionId=15168` |
| Product B | 9507 | `https://dev.azure.com/<org>/<project>/_build?definitionId=9507` |

## Usage

These IDs are used by the `generate-release-notes` skill to fetch build details and associated work items. See `private/product-definitionids.md` for your company-specific mappings.
