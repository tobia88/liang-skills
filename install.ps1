# Links every SKILL.md-bearing directory in this repo into ~/.claude/skills so
# Claude Code loads each skill natively. Junctions require no admin rights.
# Re-runnable: links new skills, skips existing entries, prunes links that point
# into this repo but whose source skill no longer exists.
$ErrorActionPreference = 'Stop'

$repo = $PSScriptRoot
$dest = Join-Path $env:USERPROFILE '.claude\skills'
if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Force $dest | Out-Null }

Get-ChildItem $dest -Directory | Where-Object { $_.LinkType } | ForEach-Object {
    $target = @($_.Target)[0]
    if ($target -and
        $target.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase) -and
        -not (Test-Path (Join-Path $target 'SKILL.md'))) {
        Write-Host "prune  $($_.Name)  (dead link)"
        $_.Delete()  # removes the reparse point only, never the target
    }
}

Get-ChildItem $repo -Directory | Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | ForEach-Object {
    $link = Join-Path $dest $_.Name
    if (Test-Path $link) {
        Write-Host "skip   $($_.Name)  (already present)"
    } else {
        New-Item -ItemType Junction -Path $link -Target $_.FullName | Out-Null
        Write-Host "link   $($_.Name)"
    }
}
