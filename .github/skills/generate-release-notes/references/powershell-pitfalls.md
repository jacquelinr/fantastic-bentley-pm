# PowerShell Implementation Notes

> **Critical:** Read these before writing any terminal commands. These are tested constraints.

1. **Reserved variables:** `$PID` is read-only in PowerShell. Never use `$pId` — use `$parentNum` or `$parentWiId` instead.
2. **`az pipelines build list`** does NOT support `--min-time` or `--query-order`. Use `--top 200 --status completed` then filter in PowerShell:
   ```powershell
   $all = az pipelines build list --definition-ids <id> --status completed --top 200 --output json | ConvertFrom-Json
   $sel = $all | Where-Object { $_.finishTime -and ([datetime]$_.finishTime -ge $from) -and ([datetime]$_.finishTime -le $to) }
   ```
3. **`az rest` fails** with Azure DevOps URLs (encoding, resource issues). Use **`az devops invoke`** instead:
   ```powershell
   # Build work items
   az devops invoke --area build --resource workitems --route-parameters project=beconnect buildId=$bid --api-version 7.0 --output json
   # Individual work item with relations
   az boards work-item show --id $id --expand Relations --output json
   ```
4. **UTF-8 BOM:** `Out-File -Encoding utf8` adds BOM on Windows PowerShell 5.1, which breaks `az devops invoke --in-file`. Use:
   ```powershell
   [System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($false)))
   ```
5. **No heredoc:** `<<<` does not exist in PowerShell. Write JSON to a temp file, then pass via `--in-file`.
6. **Hashtable serialization:** `ConvertTo-Json` fails on Hashtable with non-string keys. Use `[ordered]@{}` or convert keys to strings.
7. **Hashtable key type mismatch:** When building `$map` with integer keys, lookups like `$map[[string]$wid]` may fail. Keep keys as strings consistently, or use `$map[$wid]` with the same type used at insertion.
8. **Build version filtering:** Build numbers like `23.00.00.111`, `24.00.02.03`, `01.00.41.00` use different version schemes. String comparison (`-gt '01.00.28'`) will match old-format builds (`23.x`, `24.x`, `25.x`) since `2 > 0` lexicographically. Always filter with a regex like `$_.buildNumber -match '^01\.00\.'` first, then compare the numeric segment.
9. **Parent link relation type:** `System.LinkTypes.Hierarchy-Reverse` in the `relations` array points to the parent work item. Extract the parent ID from the URL with `-match '/workItems/(\d+)$'`.
10. **`az boards work-item show` does NOT accept `--project`:** Only pass `--organization`. Including `--project` silently fails (error goes to stderr, `ConvertFrom-Json` gets `$null` for every field). This is the #1 cause of "all nulls" enrichment runs.
11. **Batch API for work items:** Instead of calling `az boards work-item show` once per work item (N+1 problem), use the **Work Items Batch** endpoint via `az devops invoke`. This fetches up to 200 items per call with `$expand=Relations`:
   ```powershell
   # CRITICAL: Do NOT use ConvertTo-Json for the batch body — PowerShell backtick-escapes
   # the $ in $expand, producing `$expand in the JSON which the API silently ignores.
   # Instead, build the JSON string manually:
   $idsJson = ($ids | ForEach-Object { $_ }) -join ','
   $bodyJson = '{"ids":[' + $idsJson + '],"$expand":"Relations"}'
   [System.IO.File]::WriteAllText($bodyPath, $bodyJson, (New-Object System.Text.UTF8Encoding($false)))
   # Single API call replaces N individual calls
   $result = az devops invoke --area wit --resource workitemsbatch `
       --http-method POST --in-file $bodyPath `
       --organization https://dev.azure.com/<org> `
       --api-version 7.0 --output json | ConvertFrom-Json
   # $result.value contains all work items with relations
   ```
   For >200 items, split into batches of 200.

## Hard Rules

> **Do NOT use `az rest`** for Azure DevOps APIs — it fails with encoding and resource-param issues on Windows.
> **Do NOT use `az pipelines build list --min-time`** — that parameter does not exist; filter in PowerShell instead.
> **Do NOT pass `--project` to `az boards work-item show`** — it silently fails. Only use `--organization`.
> **Do NOT use `az boards work-item show` in a loop** — use the batch endpoint above instead.
