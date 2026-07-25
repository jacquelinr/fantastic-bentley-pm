# collect-builds.ps1 — Multi-build data collection for generate-release-notes skill
# Usage: Substitute placeholders and run in async terminal mode.
#
# Parameters (set before running):
#   $org       - Azure DevOps organization URL (e.g., 'https://dev.azure.com/myorg')
#   $project   - Azure DevOps project name
#   $defId     - Build definition ID
#   $from      - Start date as [datetime] (UTC)
#   $to        - End date as [datetime] (UTC), default: now
#   $tmpDir    - Directory for checkpoint/output files

param(
    [string]$org,
    [string]$project,
    [int]$defId,
    [datetime]$from,
    [datetime]$to = (Get-Date).ToUniversalTime(),
    [string]$tmpDir = '.\tmp'
)

if (-not (Test-Path $tmpDir)) { New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null }

# ── Step A: Fetch and filter builds ──
Write-Host '=== Step A: Fetching builds...'
$all = az pipelines build list --definition-ids $defId --status completed --top 200 `
    --organization $org --project $project --output json | ConvertFrom-Json
$sel = $all | Where-Object {
    $_.finishTime -and
    ([datetime]$_.finishTime -ge $from) -and
    ([datetime]$_.finishTime -le $to) -and
    $_.result -ne 'failed' -and $_.result -ne 'canceled'
} | Sort-Object { [datetime]$_.finishTime }
Write-Host "  Found $($sel.Count) builds"
$sel | ConvertTo-Json -Depth 5 | Set-Content "$tmpDir\sel-builds-$defId.json"

# ── Step B: Collect work items per build (union + dedupe) ──
Write-Host '=== Step B: Collecting work items per build...'
$map = @{}  # key=workItemId, value=@{ id; builds=@() }
foreach ($b in $sel) {
    $wi = az devops invoke --area build --resource workitems `
        --route-parameters project=$project buildId=$($b.id) `
        --organization $org --api-version 7.0 --output json | ConvertFrom-Json
    foreach ($r in $wi.value) {
        $id = [int]$r.id
        if (-not $map.ContainsKey($id)) { $map[$id] = @{ id=$id; builds=@() } }
        if ($map[$id].builds -notcontains $b.id) { $map[$id].builds += $b.id }
    }
}
Write-Host "  Found $($map.Count) unique work items"
$mapOut = [ordered]@{}
$map.Keys | ForEach-Object { $mapOut[[string]$_] = $map[$_] }
$mapOut | ConvertTo-Json -Depth 5 | Set-Content "$tmpDir\wi-map-$defId.json"

# ── Step C: Batch-enrich work items + resolve parents ──
Write-Host '=== Step C: Enriching work items via batch API...'
$allIds = @($map.Keys | ForEach-Object { [int]$_ })
$bodyPath = "$tmpDir\wi-batch-body.json"
$enriched = @()

for ($i = 0; $i -lt $allIds.Count; $i += 200) {
    $batch = $allIds[$i..([Math]::Min($i + 199, $allIds.Count - 1))]
    Write-Host "  Batch $([Math]::Floor($i/200)+1): fetching $($batch.Count) work items..."
    $idsJson = ($batch | ForEach-Object { $_ }) -join ','
    $bodyJson = '{"ids":[' + $idsJson + '],"$expand":"Relations"}'
    [System.IO.File]::WriteAllText($bodyPath, $bodyJson, (New-Object System.Text.UTF8Encoding($false)))
    $resp = az devops invoke --area wit --resource workitemsbatch `
        --http-method POST --in-file $bodyPath `
        --organization $org --api-version 7.0 --output json | ConvertFrom-Json
    $enriched += $resp.value
}
Write-Host "  Enriched $($enriched.Count) work items"

# Extract parent IDs from enriched items
$parentIds = @()
foreach ($wi in $enriched) {
    $parentRel = $wi.relations | Where-Object { $_.rel -eq 'System.LinkTypes.Hierarchy-Reverse' } | Select-Object -First 1
    if ($parentRel -and $parentRel.url -match '/workItems/(\d+)$') {
        $parentNum = [int]$Matches[1]
        if ($parentIds -notcontains $parentNum -and $allIds -notcontains $parentNum) {
            $parentIds += $parentNum
        }
    }
}
Write-Host "  Found $($parentIds.Count) unique parent IDs to fetch"

# Batch-fetch parents
$parentMap = @{}
if ($parentIds.Count -gt 0) {
    for ($i = 0; $i -lt $parentIds.Count; $i += 200) {
        $batch = $parentIds[$i..([Math]::Min($i + 199, $parentIds.Count - 1))]
        Write-Host "  Parent batch: fetching $($batch.Count) parents..."
        $bodyObj = [ordered]@{ ids = $batch }
        $bodyJson = $bodyObj | ConvertTo-Json -Depth 3
        [System.IO.File]::WriteAllText($bodyPath, $bodyJson, (New-Object System.Text.UTF8Encoding($false)))
        $resp = az devops invoke --area wit --resource workitemsbatch `
            --http-method POST --in-file $bodyPath `
            --organization $org --api-version 7.0 --output json | ConvertFrom-Json
        foreach ($p in $resp.value) { $parentMap[$p.id] = $p }
    }
}

# Assemble final enriched output
$results = @()
foreach ($wi in $enriched) {
    $wid = $wi.id
    $parentNum = $null; $parentTitle = $null; $parentType = $null
    $parentRel = $wi.relations | Where-Object { $_.rel -eq 'System.LinkTypes.Hierarchy-Reverse' } | Select-Object -First 1
    if ($parentRel -and $parentRel.url -match '/workItems/(\d+)$') {
        $parentNum = [int]$Matches[1]
        $p = $parentMap[$parentNum]
        if ($p) { $parentTitle = $p.fields.'System.Title'; $parentType = $p.fields.'System.WorkItemType' }
    }
    $results += [ordered]@{
        id = $wid
        title = $wi.fields.'System.Title'
        type = $wi.fields.'System.WorkItemType'
        parentId = $parentNum
        parentTitle = $parentTitle
        parentType = $parentType
        builds = $map[[string]$wid].builds
    }
}
$results | ConvertTo-Json -Depth 5 | Set-Content "$tmpDir\wi-enriched-$defId.json"
Write-Host "`n=== DONE: $($results.Count) work items enriched, $($parentMap.Count) parents resolved ==="
Write-Host 'DONE-MARKER'
