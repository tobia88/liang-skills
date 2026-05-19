#
# batch-executor.ps1
# Deterministic batch executor for general quest campaigns.
# Zero LLM calls — delegates all intelligence to Pi CLI children.
#

#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$CampaignPath,
    [int]$MaxRetries = 3,
    [switch]$Resume
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------
$EXIT_SUCCESS      = 0
$EXIT_PREFLIGHT_FAIL = 1
$EXIT_EXECUTION_FAIL = 2
$EXIT_CRASH_ABORT  = 3

# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

function Get-Timestamp {
    <#
    .SYNOPSIS
    Return current UTC time as ISO 8601 string (yyyy-MM-ddTHH:mm:ssZ).
    #>
    return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
}

function Write-Log {
    <#
    .SYNOPSIS
    Timestamped console output: "[YYYY-MM-DD HH:MM:SS] [LEVEL] Message"
    Levels: INFO, WARN, ERROR, STEP, QUEST.
    #>
    param(
        [string]$Message,
        [string]$Level = 'INFO'
    )
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Write-Host "[$ts] [$Level] $Message"
}

function Read-ManifestYaml {
    <#
    .SYNOPSIS
    Lightweight regex-based YAML reader for manifest.yaml.
    Parses campaign_id, slug, title, and quests array with nested fields.
    No external YAML modules — pure regex/string parsing.
    #>
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "manifest.yaml not found at: $Path"
    }

    $lines = Get-Content $Path -Encoding UTF8
    $manifest = @{
        campaign_id = ''
        slug        = ''
        title       = ''
        quests      = [System.Collections.ArrayList]@()
    }

    $currentQuest    = $null
    $inQuests        = $false
    $inQuestItem     = $false
    $inDependsOn     = $false
    $lastQuestIndent = -1

    foreach ($rawLine in $lines) {
        # Preserve original for indent detection; work with trimmed for matching
        $indent = 0
        $trimmed = $rawLine.TrimStart()
        if ($trimmed.Length -gt 0) {
            $indent = $rawLine.Length - $trimmed.Length
        }

        # Skip comment-only lines
        if ($trimmed -match '^#') { continue }

        # Top-level scalar fields
        if ($indent -eq 0) {
            $inDependsOn = $false

            if ($trimmed -match '^campaign_id:\s*[''"]?([^''"#\r\n]+)[''"]?\s*$') {
                $manifest.campaign_id = $Matches[1].Trim()
            }
            elseif ($trimmed -match '^slug:\s*[''"]?([^''"#\r\n]+)[''"]?\s*$') {
                $manifest.slug = $Matches[1].Trim()
            }
            elseif ($trimmed -match '^title:\s*[''"]?([^''"#\r\n]+)[''"]?\s*$') {
                $manifest.title = $Matches[1].Trim()
            }
            elseif ($trimmed -match '^quests:\s*$') {
                $inQuests = $true
                continue
            }
            else {
                # Leaving quests block if we hit another top-level key
                if ($inQuests) {
                    if ($currentQuest -ne $null) {
                        [void]$manifest.quests.Add($currentQuest)
                        $currentQuest = $null
                    }
                    $inQuests = $false
                    $inQuestItem = $false
                }
            }
        }

        if (-not $inQuests) { continue }

        # Detect new quest list item (starts with "  - " at indent 2)
        if ($trimmed -match '^-\s') {
            $inDependsOn = $false
            if ($currentQuest -ne $null) {
                [void]$manifest.quests.Add($currentQuest)
            }
            $currentQuest = @{
                id                      = ''
                title                   = ''
                path                    = ''
                priority                = ''
                readiness               = ''
                status                  = ''
                workflow                = ''
                depends_on              = [System.Collections.ArrayList]@()
                current_cycle           = 0
                total_cycles            = 0
                current_step_started_at = ''
                started_at              = ''
                completed_at            = ''
                skip_reason             = ''
            }
            $inQuestItem = $true
            $lastQuestIndent = $indent

            # The line may carry an inline field after "- "
            $rest = $trimmed -replace '^-\s+', ''
            if ($rest -match '^(\w+):\s*[''"]?([^''"#\r\n]*)[''"]?\s*$') {
                $k = $Matches[1]; $v = $Matches[2].Trim()
                if ($currentQuest.ContainsKey($k)) { $currentQuest[$k] = $v }
            }
            continue
        }

        if (-not $inQuestItem -or $currentQuest -eq $null) { continue }

        # Inside a quest item — parse fields
        if ($trimmed -match '^depends_on:\s*$') {
            $inDependsOn = $true
            continue
        }

        if ($inDependsOn) {
            if ($trimmed -match '^-\s+[''"]?([^''"#\r\n]+)[''"]?') {
                [void]$currentQuest.depends_on.Add($Matches[1].Trim())
                continue
            }
            else {
                # End of depends_on list
                $inDependsOn = $false
            }
        }

        # Inline depends_on (single line): depends_on: ["q001","q002"]
        if ($trimmed -match '^depends_on:\s*\[([^\]]*)\]') {
            $raw = $Matches[1]
            $parts = $raw -split ',' | ForEach-Object { $_.Trim().Trim('"').Trim("'") } | Where-Object { $_ -ne '' }
            foreach ($p in $parts) { [void]$currentQuest.depends_on.Add($p) }
            continue
        }

        # Scalar quest fields
        if ($trimmed -match '^(id|title|path|priority|readiness|status|workflow|skip_reason|started_at|completed_at|current_step_started_at):\s*[''"]?([^''"#\r\n]*)[''"]?\s*$') {
            $k = $Matches[1]; $v = $Matches[2].Trim()
            if ($currentQuest.ContainsKey($k)) { $currentQuest[$k] = $v }
        }
        elseif ($trimmed -match '^(current_cycle|total_cycles):\s*(\d+)') {
            $k = $Matches[1]; $v = [int]$Matches[2]
            $currentQuest[$k] = $v
        }
    }

    # Flush last quest
    if ($currentQuest -ne $null) {
        [void]$manifest.quests.Add($currentQuest)
    }

    return $manifest
}

function Write-ManifestAtomic {
    <#
    .SYNOPSIS
    Write manifest hashtable back to YAML format atomically.
    Writes to a temp file then Move-Item -Force to replace original.
    #>
    param(
        [string]$Path,
        [hashtable]$Manifest
    )

    $lines = [System.Collections.ArrayList]@()

    $ci = $Manifest.campaign_id
    $sl = $Manifest.slug
    $ti = $Manifest.title

    [void]$lines.Add("campaign_id: `"$ci`"")
    [void]$lines.Add("slug: `"$sl`"")
    [void]$lines.Add("title: `"$ti`"")
    [void]$lines.Add("")
    [void]$lines.Add("quests:")

    foreach ($q in $Manifest.quests) {
        [void]$lines.Add("  - id: `"$($q.id)`"")
        [void]$lines.Add("    title: `"$($q.title)`"")
        [void]$lines.Add("    path: `"$($q.path)`"")
        [void]$lines.Add("    priority: `"$($q.priority)`"")
        [void]$lines.Add("    readiness: `"$($q.readiness)`"")
        [void]$lines.Add("    status: `"$($q.status)`"")

        if ($q.workflow -ne '') {
            [void]$lines.Add("    workflow: `"$($q.workflow)`"")
        }

        # depends_on array
        $deps = @($q.depends_on)
        if ($deps.Count -eq 0) {
            [void]$lines.Add("    depends_on: []")
        }
        else {
            [void]$lines.Add("    depends_on:")
            foreach ($d in $deps) {
                [void]$lines.Add("      - `"$d`"")
            }
        }

        # Executor-managed integer fields (only write if non-zero)
        if ($q.current_cycle -ne 0) {
            [void]$lines.Add("    current_cycle: $($q.current_cycle)")
        }
        if ($q.total_cycles -ne 0) {
            [void]$lines.Add("    total_cycles: $($q.total_cycles)")
        }

        # Executor-managed string timestamps (only write if non-empty)
        foreach ($field in @('started_at','current_step_started_at','completed_at')) {
            $val = $q[$field]
            if ($val -ne $null -and $val -ne '') {
                [void]$lines.Add("    ${field}: `"$val`"")
            }
        }

        if ($q.skip_reason -ne '') {
            [void]$lines.Add("    skip_reason: `"$($q.skip_reason)`"")
        }

        [void]$lines.Add("")
    }

    $yaml = $lines -join "`n"
    $tmpPath = $Path + '.tmp'

    [System.IO.File]::WriteAllText($tmpPath, $yaml, [System.Text.Encoding]::UTF8)
    Move-Item -Path $tmpPath -Destination $Path -Force
}

function Get-DependencyOrder {
    <#
    .SYNOPSIS
    Topological sort of quests using Kahn's algorithm.
    Returns quest IDs in safe execution order.
    Throws on circular dependency.
    #>
    param([hashtable[]]$Quests)

    # Build adjacency and in-degree maps
    $inDegree   = @{}
    $adjacency  = @{}
    $allIds     = @()

    foreach ($q in $Quests) {
        $id = $q.id
        $allIds += $id
        if (-not $inDegree.ContainsKey($id))  { $inDegree[$id]  = 0 }
        if (-not $adjacency.ContainsKey($id)) { $adjacency[$id] = [System.Collections.ArrayList]@() }
    }

    foreach ($q in $Quests) {
        $id   = $q.id
        $deps = @($q.depends_on) | Where-Object { $_ -ne '' -and $allIds -contains $_ }
        foreach ($dep in $deps) {
            # dep must complete before id — dep -> id edge
            if (-not $adjacency.ContainsKey($dep)) { $adjacency[$dep] = [System.Collections.ArrayList]@() }
            [void]$adjacency[$dep].Add($id)
            $inDegree[$id]++
        }
    }

    # Kahn's BFS
    $queue = [System.Collections.Queue]::new()
    foreach ($id in $allIds) {
        if ($inDegree[$id] -eq 0) { $queue.Enqueue($id) }
    }

    $sorted = [System.Collections.ArrayList]@()
    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        [void]$sorted.Add($current)
        foreach ($neighbor in $adjacency[$current]) {
            $inDegree[$neighbor]--
            if ($inDegree[$neighbor] -eq 0) {
                $queue.Enqueue($neighbor)
            }
        }
    }

    if ($sorted.Count -ne $allIds.Count) {
        throw "Circular dependency detected in quest depends_on graph. Cannot determine execution order."
    }

    return [string[]]$sorted
}

function Write-StepResult {
    <#
    .SYNOPSIS
    Write step-<StepId>-result.yaml to .run/<QuestId>/.
    Creates directory if needed.
    #>
    param(
        [string]$RunDir,
        [string]$QuestId,
        [string]$StepId,
        [hashtable]$Result
    )

    $questRunDir = Join-Path $RunDir $QuestId
    if (-not (Test-Path $questRunDir)) {
        New-Item -ItemType Directory -Path $questRunDir -Force | Out-Null
    }

    $filePath = Join-Path $questRunDir "step-$StepId-result.yaml"

    $lines = [System.Collections.ArrayList]@()
    [void]$lines.Add("quest_id: `"$QuestId`"")
    [void]$lines.Add("step_id: `"$StepId`"")

    $status = if ($Result.ContainsKey('status')) { $Result['status'] } else { 'unknown' }
    [void]$lines.Add("status: `"$status`"")

    if ($Result.ContainsKey('started_at') -and $Result['started_at'] -ne '') {
        [void]$lines.Add("started_at: `"$($Result['started_at'])`"")
    }
    if ($Result.ContainsKey('completed_at') -and $Result['completed_at'] -ne '') {
        [void]$lines.Add("completed_at: `"$($Result['completed_at'])`"")
    }

    $attempt = if ($Result.ContainsKey('attempt')) { $Result['attempt'] } else { 1 }
    [void]$lines.Add("attempt: $attempt")

    $tier = if ($Result.ContainsKey('retry_tier')) { $Result['retry_tier'] } else { 'none' }
    [void]$lines.Add("retry_tier: `"$tier`"")

    if ($Result.ContainsKey('failure_reason') -and $Result['failure_reason'] -ne '') {
        $fr = $Result['failure_reason'] -replace '"', "'"
        [void]$lines.Add("failure_reason: `"$fr`"")
    }

    if ($Result.ContainsKey('lessons') -and $Result['lessons'] -ne $null) {
        $ls = $Result['lessons']
        if ($ls -is [System.Collections.IEnumerable] -and $ls -isnot [string]) {
            $lessonArr = @($ls)
            if ($lessonArr.Count -gt 0) {
                [void]$lines.Add("lessons:")
                foreach ($l in $lessonArr) {
                    $escaped = ($l -replace '"', "'")
                    [void]$lines.Add("  - `"$escaped`"")
                }
            }
        }
    }

    $yaml = $lines -join "`n"
    [System.IO.File]::WriteAllText($filePath, $yaml, [System.Text.Encoding]::UTF8)
}

function Read-ProjectYaml {
    <#
    .SYNOPSIS
    Read .liang/project.yaml from workspace root.
    Extract models.planning, models.verify, models.execution_by_difficulty (easy/medium/hard).
    Returns hashtable.
    #>
    param([string]$WorkspaceRoot)

    $yamlPath = Join-Path $WorkspaceRoot '.liang' 'project.yaml'
    if (-not (Test-Path $yamlPath)) {
        throw "project.yaml not found at: $yamlPath"
    }

    $lines = Get-Content $yamlPath -Encoding UTF8

    $config = @{
        schema_version = 1
        vcs            = ''
        models         = @{
            planning              = ''
            verify                = ''
            execution_by_difficulty = @{
                easy   = ''
                medium = ''
                hard   = ''
            }
        }
        executor = @{
            max_cycle_retries     = 3
            child_timeout_seconds = 300
            max_step_retries      = 3
        }
    }

    $inModels         = $false
    $inExecByDiff     = $false
    $inExecutor       = $false

    foreach ($rawLine in $lines) {
        $trimmed = $rawLine.TrimStart()
        if ($trimmed -match '^#') { continue }

        $indent = $rawLine.Length - $trimmed.Length

        if ($indent -eq 0) {
            $inModels      = $false
            $inExecByDiff  = $false
            $inExecutor    = $false

            if ($trimmed -match '^models:\s*$') {
                $inModels = $true
                continue
            }
            elseif ($trimmed -match '^executor:\s*$') {
                $inExecutor = $true
                continue
            }
            elseif ($trimmed -match '^vcs:\s*[''"]?([^''"#\r\n]+)[''"]?') {
                $config.vcs = $Matches[1].Trim()
            }
            elseif ($trimmed -match '^schema_version:\s*(\d+)') {
                $config.schema_version = [int]$Matches[1]
            }
        }

        if ($inModels -and $indent -gt 0) {
            if ($trimmed -match '^execution_by_difficulty:\s*$') {
                $inExecByDiff = $true
                continue
            }
            if ($inExecByDiff -and $indent -gt 2) {
                if ($trimmed -match '^(easy|medium|hard):\s*[''"]?([^''"#\r\n]+)[''"]?') {
                    $config.models.execution_by_difficulty[$Matches[1]] = $Matches[2].Trim()
                }
                continue
            }
            if ($trimmed -match '^planning:\s*[''"]?([^''"#\r\n]+)[''"]?') {
                $config.models.planning = $Matches[1].Trim()
            }
            elseif ($trimmed -match '^verify:\s*[''"]?([^''"#\r\n]+)[''"]?') {
                $config.models.verify = $Matches[1].Trim()
            }
        }

        if ($inExecutor -and $indent -gt 0) {
            if ($trimmed -match '^max_cycle_retries:\s*(\d+)') {
                $config.executor.max_cycle_retries = [int]$Matches[1]
                $config.executor.max_step_retries  = [int]$Matches[1]
            }
            elseif ($trimmed -match '^max_step_retries:\s*(\d+)') {
                $config.executor.max_step_retries = [int]$Matches[1]
            }
            elseif ($trimmed -match '^child_timeout_seconds:\s*(\d+)') {
                $config.executor.child_timeout_seconds = [int]$Matches[1]
            }
        }
    }

    return $config
}

function Read-PlanSteps {
    <#
    .SYNOPSIS
    Extract YAML from opening HTML comment (between <!-- --- and --- -->).
    Parse the steps array with nested fields.
    Return array of step hashtables and set script-scoped $script:PlanDifficulty.
    #>
    param([string]$PlanHtmlPath)

    if (-not (Test-Path $PlanHtmlPath)) {
        throw "plan.html not found at: $PlanHtmlPath"
    }

    $content = [System.IO.File]::ReadAllText($PlanHtmlPath, [System.Text.Encoding]::UTF8)

    # Extract content between <!-- --- and --- -->
    if ($content -notmatch '(?s)<!--\s*---\s*\r?\n(.*?)\r?\n\s*---\s*-->') {
        throw "No YAML frontmatter found in: $PlanHtmlPath"
    }
    $yaml = $Matches[1]

    $lines = $yaml -split "`r?\n"

    # Extract top-level difficulty
    $difficulty = 'medium'
    foreach ($line in $lines) {
        if ($line -match '^difficulty:\s*[''"]?(easy|medium|hard)[''"]?') {
            $difficulty = $Matches[1]
            break
        }
    }
    $script:PlanDifficulty = $difficulty

    # Parse steps array
    $steps         = [System.Collections.ArrayList]@()
    $currentStep   = $null
    $inSteps       = $false
    $inStepItem    = $false
    $inInstructions = $false
    $inFiles       = $false
    $inPrecond     = $false
    $inPostcond    = $false
    $inAcceptance  = $false
    $instructionLines = [System.Collections.ArrayList]@()
    $blockIndent   = -1

    foreach ($rawLine in $lines) {
        $trimmed = $rawLine.TrimStart()
        $indent  = $rawLine.Length - $trimmed.Length

        if ($trimmed -match '^#') { continue }

        # Detect "steps:" top-level key
        if ($indent -eq 0 -and $trimmed -match '^steps:\s*$') {
            $inSteps = $true
            continue
        }

        # Leaving steps block
        if ($indent -eq 0 -and $trimmed -ne '' -and $trimmed -notmatch '^steps:\s*$') {
            if ($inSteps) {
                if ($inInstructions -and $currentStep -ne $null) {
                    $currentStep['instructions'] = ($instructionLines -join "`n").TrimEnd()
                    $instructionLines = [System.Collections.ArrayList]@()
                }
                if ($currentStep -ne $null) { [void]$steps.Add($currentStep) }
                $currentStep = $null
            }
            $inSteps = $false
            $inStepItem = $false
            $inInstructions = $false
            $inFiles = $false
            $inPrecond = $false
            $inPostcond = $false
            $inAcceptance = $false
            continue
        }

        if (-not $inSteps) { continue }

        # New step item: "  - id:" at indent 2
        if ($indent -le 3 -and $trimmed -match '^-\s') {
            # Flush previous step
            if ($inInstructions -and $currentStep -ne $null) {
                $currentStep['instructions'] = ($instructionLines -join "`n").TrimEnd()
                $instructionLines = [System.Collections.ArrayList]@()
                $inInstructions = $false
            }
            if ($currentStep -ne $null) { [void]$steps.Add($currentStep) }

            $currentStep = @{
                id                   = ''
                name                 = ''
                description          = ''
                instructions         = ''
                files                = [System.Collections.ArrayList]@()
                preconditions        = [System.Collections.ArrayList]@()
                postconditions       = [System.Collections.ArrayList]@()
                verification_tier    = 1
                verification_command = ''
                acceptance_criteria  = [System.Collections.ArrayList]@()
            }
            $inStepItem    = $true
            $inInstructions = $false
            $inFiles       = $false
            $inPrecond     = $false
            $inPostcond    = $false
            $inAcceptance  = $false
            $instructionLines = [System.Collections.ArrayList]@()

            $rest = $trimmed -replace '^-\s+', ''
            if ($rest -match '^(id|name|description|verification_command):\s*[''"]?([^''"#\r\n]*)[''"]?') {
                $k = $Matches[1]; $v = $Matches[2].Trim()
                $currentStep[$k] = $v
            }
            elseif ($rest -match '^verification_tier:\s*(\d+)') {
                $currentStep['verification_tier'] = [int]$Matches[1]
            }
            continue
        }

        if (-not $inStepItem -or $currentStep -eq $null) { continue }

        # Detect block scalars (instructions uses |)
        if ($trimmed -match '^instructions:\s*\|\s*$') {
            $inInstructions = $true
            $inFiles = $false; $inPrecond = $false; $inPostcond = $false; $inAcceptance = $false
            $blockIndent = $indent + 2
            continue
        }

        if ($inInstructions) {
            # End of block when indent drops back
            if ($trimmed -ne '' -and $indent -lt $blockIndent) {
                $currentStep['instructions'] = ($instructionLines -join "`n").TrimEnd()
                $instructionLines = [System.Collections.ArrayList]@()
                $inInstructions = $false
                # Fall through to process this line normally
            }
            else {
                # Add line (strip the block indent prefix)
                $stripped = if ($rawLine.Length -ge $blockIndent) { $rawLine.Substring($blockIndent) } else { $trimmed }
                [void]$instructionLines.Add($stripped)
                continue
            }
        }

        # Array fields
        if ($trimmed -match '^files:\s*$') {
            $inFiles = $true; $inPrecond = $false; $inPostcond = $false; $inAcceptance = $false
            continue
        }
        if ($trimmed -match '^preconditions:\s*$') {
            $inPrecond = $true; $inFiles = $false; $inPostcond = $false; $inAcceptance = $false
            continue
        }
        if ($trimmed -match '^postconditions:\s*$') {
            $inPostcond = $true; $inFiles = $false; $inPrecond = $false; $inAcceptance = $false
            continue
        }
        if ($trimmed -match '^acceptance_criteria:\s*$') {
            $inAcceptance = $true; $inFiles = $false; $inPrecond = $false; $inPostcond = $false
            continue
        }

        if ($inFiles -and $trimmed -match '^-\s+[''"]?([^''"#\r\n]+)[''"]?') {
            [void]$currentStep.files.Add($Matches[1].Trim())
            continue
        }
        if ($inPrecond -and $trimmed -match '^-\s+[''"]?([^''"#\r\n]+)[''"]?') {
            [void]$currentStep.preconditions.Add($Matches[1].Trim())
            continue
        }
        if ($inPostcond -and $trimmed -match '^-\s+[''"]?([^''"#\r\n]+)[''"]?') {
            [void]$currentStep.postconditions.Add($Matches[1].Trim())
            continue
        }
        if ($inAcceptance -and $trimmed -match '^-\s+[''"]?([^''"#\r\n]+)[''"]?') {
            [void]$currentStep.acceptance_criteria.Add($Matches[1].Trim())
            continue
        }

        # Reset list-mode flags if we hit a non-list line that is a known field
        if ($trimmed -match '^(id|name|description|verification_command):\s*[''"]?([^''"#\r\n]*)[''"]?') {
            $inFiles = $false; $inPrecond = $false; $inPostcond = $false; $inAcceptance = $false
            $k = $Matches[1]; $v = $Matches[2].Trim()
            $currentStep[$k] = $v
        }
        elseif ($trimmed -match '^verification_tier:\s*(\d+)') {
            $inFiles = $false; $inPrecond = $false; $inPostcond = $false; $inAcceptance = $false
            $currentStep['verification_tier'] = [int]$Matches[1]
        }
    }

    # Flush last step
    if ($inInstructions -and $currentStep -ne $null) {
        $currentStep['instructions'] = ($instructionLines -join "`n").TrimEnd()
    }
    if ($currentStep -ne $null) { [void]$steps.Add($currentStep) }

    return [hashtable[]]$steps
}

# ---------------------------------------------------------------------------
# CRASH RECOVERY
# ---------------------------------------------------------------------------

function Invoke-CrashRecovery {
    param(
        [hashtable]$Manifest,
        [string]$CampaignPath,
        [switch]$AutoResume
    )

    $inProgressQuests = @($Manifest.quests | Where-Object { $_.status -eq 'in_progress' })
    if ($inProgressQuests.Count -eq 0) {
        return $null
    }

    $ids = ($inProgressQuests | ForEach-Object { $_.id }) -join ', '
    Write-Log "Crash recovery: found in_progress quest(s): $ids" -Level WARN

    $doResume = $false
    if ($AutoResume) {
        $doResume = $true
    }
    else {
        Write-Host ''
        Write-Host "Detected interrupted run for quest(s): $ids"
        Write-Host '[R]esume from last checkpoint or [A]bort? (R/A): ' -NoNewline
        $answer = Read-Host
        if ($answer -match '^[Rr]') {
            $doResume = $true
        }
        else {
            Write-Log "User chose to abort crash recovery." -Level WARN
            exit $script:EXIT_CRASH_ABORT
        }
    }

    if ($doResume) {
        # Pick first in-progress quest for recovery
        $q = $inProgressQuests[0]
        $questId = $q.id
        $runDir = Join-Path $CampaignPath '.run' $questId

        $resumeFrom = 0
        if (Test-Path $runDir) {
            $resultFiles = @(Get-ChildItem $runDir -Filter 'step-*-result.yaml' -ErrorAction SilentlyContinue | Sort-Object Name)
            if ($resultFiles.Count -gt 0) {
                # Last result file name pattern: step-s01-result.yaml
                $lastName = $resultFiles[-1].Name
                if ($lastName -match 'step-([^-]+(?:-[^-]+)*)-result\.yaml') {
                    $lastStepId = $Matches[1]
                    # resumeFrom is index after last completed step — caller resolves by step ID
                    $resumeFrom = $lastStepId
                }
            }
        }

        Write-Log "Resuming quest $questId from after step '$resumeFrom'" -Level INFO
        return @{
            QuestId            = $questId
            ResumeFromStep     = $resumeFrom
            AccumulatedLessons = [System.Collections.ArrayList]@()
        }
    }

    return $null
}

# ---------------------------------------------------------------------------
# PRE-FLIGHT GATE
# ---------------------------------------------------------------------------

function Test-PreFlight {
    param(
        [hashtable]$Manifest,
        [string]$CampaignPath,
        [string]$WorkspaceRoot
    )

    $failures = [System.Collections.ArrayList]@()

    # a) project.yaml exists
    $projectYamlPath = Join-Path $WorkspaceRoot '.liang' 'project.yaml'
    if (-not (Test-Path $projectYamlPath)) {
        [void]$failures.Add("project.yaml not found at: $projectYamlPath")
    }
    else {
        # b) project.yaml has required model fields
        $pc = $null
        try { $pc = Read-ProjectYaml $WorkspaceRoot } catch { [void]$failures.Add("Cannot read project.yaml: $_") }

        if ($pc -ne $null) {
            if ($pc.models.verify -eq '') {
                [void]$failures.Add("project.yaml missing models.verify")
            }
            if ($pc.models.execution_by_difficulty.easy -eq '') {
                [void]$failures.Add("project.yaml missing models.execution_by_difficulty.easy")
            }
            if ($pc.models.execution_by_difficulty.medium -eq '') {
                [void]$failures.Add("project.yaml missing models.execution_by_difficulty.medium")
            }
            if ($pc.models.execution_by_difficulty.hard -eq '') {
                [void]$failures.Add("project.yaml missing models.execution_by_difficulty.hard")
            }
        }
    }

    # c) For each general quest: status not ready_for_planning, plan.html exists and parseable
    foreach ($q in $Manifest.quests) {
        if ($q.workflow -ne 'general') { continue }

        if ($q.status -eq 'ready_for_planning') {
            [void]$failures.Add("Quest $($q.id) has status 'ready_for_planning' — Tactician must plan it first")
        }

        if ($q.status -in @('planned', 'in_progress')) {
            $questDir  = Split-Path (Join-Path $CampaignPath $q.path) -Parent
            $planHtml  = Join-Path $questDir 'plan.html'
            if (-not (Test-Path $planHtml)) {
                [void]$failures.Add("Quest $($q.id): plan.html not found at $planHtml")
            }
            else {
                try {
                    $steps = Read-PlanSteps $planHtml
                    if ($steps.Count -eq 0) {
                        [void]$failures.Add("Quest $($q.id): plan.html has no steps")
                    }
                }
                catch {
                    [void]$failures.Add("Quest $($q.id): Cannot parse plan.html — $_")
                }
            }
        }
    }

    # d) No circular dependencies
    try {
        $generalQuests = @($Manifest.quests | Where-Object { $_.workflow -eq 'general' })
        if ($generalQuests.Count -gt 0) {
            Get-DependencyOrder $generalQuests | Out-Null
        }
    }
    catch {
        [void]$failures.Add("Dependency graph error: $_")
    }

    if ($failures.Count -gt 0) {
        foreach ($f in $failures) {
            Write-Log "Pre-flight FAIL: $f" -Level ERROR
        }
        return $false
    }

    $readyCount = ($Manifest.quests | Where-Object { $_.workflow -eq 'general' -and $_.status -in @('planned','in_progress') }).Count
    Write-Log "Pre-flight passed: $readyCount general quest(s) ready" -Level INFO
    return $true
}

# ---------------------------------------------------------------------------
# CASCADE SKIP
# ---------------------------------------------------------------------------

function Invoke-CascadeSkip {
    param(
        [hashtable]$Manifest,
        [string]$FailedQuestId,
        [string]$CampaignPath
    )

    $toSkip = [System.Collections.ArrayList]@()
    $queue  = [System.Collections.Queue]::new()
    $queue.Enqueue($FailedQuestId)

    while ($queue.Count -gt 0) {
        $current = $queue.Dequeue()
        foreach ($q in $Manifest.quests) {
            $deps = @($q.depends_on)
            if ($deps -contains $current -and $q.status -notin @('passed', 'failed', 'skipped')) {
                $q.status       = 'skipped'
                $q.skip_reason  = "dependency $FailedQuestId failed"
                $q.completed_at = Get-Timestamp
                [void]$toSkip.Add($q.id)
                $queue.Enqueue($q.id)
            }
        }
    }

    if ($toSkip.Count -gt 0) {
        Write-ManifestAtomic (Join-Path $CampaignPath 'manifest.yaml') $Manifest
        Write-Log "Cascade skip: $($toSkip -join ', ')" -Level WARN
    }
}

# ---------------------------------------------------------------------------
# TIERED RETRY ENGINE
# ---------------------------------------------------------------------------

function Invoke-PiChild {
    <#
    .SYNOPSIS
    Invoke Pi CLI for a child contract (execute-child, verify-child, re-plan-child).
    Passes context as a temp YAML input file. Returns parsed output hashtable.
    #>
    param(
        [string]$ChildType,
        [string]$Model,
        [hashtable]$InputContext,
        [string]$RunDir,
        [string]$QuestId,
        [string]$StepId,
        [int]$Attempt = 1
    )

    $inputFileName  = "step-${StepId}-${ChildType}-input-attempt${Attempt}.yaml"
    $outputFileName = "step-${StepId}-${ChildType}-output-attempt${Attempt}.yaml"
    $questRunDir    = Join-Path $RunDir $QuestId
    if (-not (Test-Path $questRunDir)) {
        New-Item -ItemType Directory -Path $questRunDir -Force | Out-Null
    }

    $inputPath  = Join-Path $questRunDir $inputFileName
    $outputPath = Join-Path $questRunDir $outputFileName

    # Serialize input context to YAML
    $inputLines = [System.Collections.ArrayList]@()
    foreach ($key in $InputContext.Keys) {
        $val = $InputContext[$key]
        if ($val -is [bool]) {
            $boolVal = if ($val) { 'true' } else { 'false' }
            [void]$inputLines.Add("${key}: $boolVal")
        }
        elseif ($val -is [int]) {
            [void]$inputLines.Add("${key}: $val")
        }
        elseif ($val -is [System.Collections.IEnumerable] -and $val -isnot [string]) {
            $arr = @($val)
            if ($arr.Count -eq 0) {
                [void]$inputLines.Add("${key}: []")
            }
            else {
                [void]$inputLines.Add("${key}:")
                foreach ($item in $arr) {
                    $escaped = ($item.ToString() -replace '"', "'")
                    [void]$inputLines.Add("  - `"$escaped`"")
                }
            }
        }
        else {
            $escaped = ($val.ToString() -replace '"', "'")
            [void]$inputLines.Add("${key}: `"$escaped`"")
        }
    }
    $inputYaml = $inputLines -join "`n"
    [System.IO.File]::WriteAllText($inputPath, $inputYaml, [System.Text.Encoding]::UTF8)

    # Pi CLI invocation
    # Pattern: pi run --model <model> --skill liang-quest-general-executor/<child-type> --input <input-yaml-path> --output <output-yaml-path>
    Write-Log "    Spawning $ChildType (model: $Model, attempt: $Attempt)" -Level INFO
    $piArgs = @(
        'run',
        '--model', $Model,
        '--skill', "liang-quest-general-executor/$ChildType",
        '--input',  $inputPath,
        '--output', $outputPath
    )

    try {
        $proc = Start-Process -FilePath 'pi' -ArgumentList $piArgs -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -ne 0) {
            Write-Log "    $ChildType exited with code $($proc.ExitCode)" -Level WARN
            return @{ passed = $false; failure_reason = "$ChildType exited with code $($proc.ExitCode)" }
        }
    }
    catch {
        Write-Log "    Failed to spawn $ChildType: $_" -Level ERROR
        return @{ passed = $false; failure_reason = "spawn error: $_" }
    }

    # Parse output YAML
    if (-not (Test-Path $outputPath)) {
        return @{ passed = $false; failure_reason = "no output file produced by $ChildType" }
    }

    $outLines = Get-Content $outputPath -Encoding UTF8
    $result   = @{ passed = $false; failure_reason = '' }
    foreach ($l in $outLines) {
        $lt = $l.Trim()
        if ($lt -match '^passed:\s*(true|false)') {
            $result.passed = ($Matches[1] -eq 'true')
        }
        elseif ($lt -match '^status:\s*[''"]?([^''"#\r\n]+)[''"]?') {
            $result['status'] = $Matches[1].Trim()
        }
        elseif ($lt -match '^failure_reason:\s*[''"]?([^''"#\r\n]*)[''"]?') {
            $result.failure_reason = $Matches[1].Trim()
        }
        elseif ($lt -match '^revised_instructions:\s*[''"]?([^''"#\r\n]*)[''"]?') {
            $result['revised_instructions'] = $Matches[1].Trim()
        }
        elseif ($lt -match '^files_changed:\s*[''"]?([^''"#\r\n]*)[''"]?') {
            $result['files_changed'] = $Matches[1].Trim()
        }
        elseif ($lt -match '^implementation_summary:\s*[''"]?([^''"#\r\n]*)[''"]?') {
            $result['implementation_summary'] = $Matches[1].Trim()
        }
    }

    return $result
}

function Invoke-TieredRetry {
    param(
        [hashtable]$Step,
        [int]$Attempt,
        [System.Collections.ArrayList]$AccumulatedLessons,
        [string]$PreviousFailure,
        [hashtable]$ProjectConfig,
        [string]$Difficulty,
        [string]$CampaignPath,
        [string]$QuestId
    )

    Write-Log "  Retry attempt $Attempt for step $($Step.id)" -Level WARN

    $runDir = Join-Path $CampaignPath '.run'

    $execModel = switch ($Difficulty) {
        'easy'   { $ProjectConfig.models.execution_by_difficulty.easy }
        'hard'   { $ProjectConfig.models.execution_by_difficulty.hard }
        default  { $ProjectConfig.models.execution_by_difficulty.medium }
    }
    if ($execModel -eq '') { $execModel = $ProjectConfig.models.execution_by_difficulty.medium }

    if ($Attempt -eq 1) {
        # LESSON-ONLY RETRY — do NOT invoke re-plan-child
        Write-Log "  Tier 1: Lesson-only retry (no re-plan)" -Level INFO

        $inputCtx = @{
            step_id              = $Step.id
            step_name            = $Step.name
            instructions         = $Step.instructions
            is_retry             = $true
            retry_attempt        = $Attempt
            previous_failure     = $PreviousFailure
            accumulated_lessons  = $AccumulatedLessons
            revised_instructions = ''
        }

        $result = Invoke-PiChild -ChildType 'execute-child' -Model $execModel `
            -InputContext $inputCtx -RunDir $runDir -QuestId $QuestId `
            -StepId $Step.id -Attempt ($Attempt + 1)

        return @{ result = $result; retry_tier = 'lesson_only' }
    }
    else {
        # RE-PLAN ESCALATION (Attempt 2+)
        Write-Log "  Tier 2: Re-plan escalation (attempt $Attempt)" -Level INFO

        $planModel = $ProjectConfig.models.planning
        if ($planModel -eq '') { $planModel = $execModel }

        $replanCtx = @{
            step_id             = $Step.id
            step_name           = $Step.name
            original_instructions = $Step.instructions
            accumulated_lessons = $AccumulatedLessons
            previous_failure    = $PreviousFailure
            attempt             = $Attempt
        }

        $replanResult = Invoke-PiChild -ChildType 're-plan-child' -Model $planModel `
            -InputContext $replanCtx -RunDir $runDir -QuestId $QuestId `
            -StepId $Step.id -Attempt $Attempt

        $revisedInstructions = ''
        if ($replanResult.ContainsKey('revised_instructions')) {
            $revisedInstructions = $replanResult['revised_instructions']
        }
        if ($revisedInstructions -eq '') {
            $revisedInstructions = $Step.instructions
        }

        $inputCtx = @{
            step_id              = $Step.id
            step_name            = $Step.name
            instructions         = $revisedInstructions
            is_retry             = $true
            retry_attempt        = $Attempt
            previous_failure     = $PreviousFailure
            accumulated_lessons  = $AccumulatedLessons
            revised_instructions = $revisedInstructions
        }

        $result = Invoke-PiChild -ChildType 'execute-child' -Model $execModel `
            -InputContext $inputCtx -RunDir $runDir -QuestId $QuestId `
            -StepId $Step.id -Attempt ($Attempt + 1)

        return @{ result = $result; retry_tier = 'replan'; revised_instructions = $revisedInstructions }
    }
}

# ---------------------------------------------------------------------------
# RUN REPORT
# Generates run-report.html with timestamp suffix (e.g. run-report-20260101T000000Z.html)
# ---------------------------------------------------------------------------

function New-RunReport {
    param(
        [hashtable]$Manifest,
        [string]$CampaignPath,
        [hashtable]$QuestResults,
        [string]$StartedAt
    )

    $completedAt = Get-Timestamp
    $runDir      = Join-Path $CampaignPath '.run'
    if (-not (Test-Path $runDir)) { New-Item -ItemType Directory -Path $runDir -Force | Out-Null }

    $ts          = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $reportPath  = Join-Path $CampaignPath "run-report-$ts.html"

    $passed  = 0; $failed  = 0; $skipped = 0
    $questRowsHtml = [System.Text.StringBuilder]::new()

    foreach ($q in $Manifest.quests) {
        if ($q.workflow -ne 'general') { continue }

        $st = $q.status
        switch ($st) {
            'passed'  { $passed++ }
            'failed'  { $failed++ }
            'skipped' { $skipped++ }
        }

        $statusClass = switch ($st) {
            'passed'  { 'status-passed' }
            'failed'  { 'status-failed' }
            'skipped' { 'status-skipped' }
            default   { 'status-other' }
        }

        $questRunDir = Join-Path $runDir $q.id
        $stepCount   = 0
        if (Test-Path $questRunDir) {
            $stepCount = @(Get-ChildItem $questRunDir -Filter 'step-*-result.yaml' -ErrorAction SilentlyContinue).Count
        }

        $skipNote = ''
        if ($q.skip_reason -ne '') { $skipNote = " <span class=`"skip-note`">($($q.skip_reason))</span>" }

        [void]$questRowsHtml.AppendLine("<tr>")
        [void]$questRowsHtml.AppendLine("  <td>$($q.id)</td>")
        [void]$questRowsHtml.AppendLine("  <td>$($q.title)</td>")
        [void]$questRowsHtml.AppendLine("  <td class=`"$statusClass`">$st$skipNote</td>")
        [void]$questRowsHtml.AppendLine("  <td>$stepCount</td>")
        [void]$questRowsHtml.AppendLine("  <td>$($q.started_at)</td>")
        [void]$questRowsHtml.AppendLine("  <td>$($q.completed_at)</td>")
        [void]$questRowsHtml.AppendLine("</tr>")
    }

    $total = $passed + $failed + $skipped

    $html = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Run Report — $($Manifest.campaign_id)</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #1a1829; color: #e8e4d9; }
    header { background: #252338; padding: 2rem; border-bottom: 2px solid #3d3a5c; }
    header h1 { margin: 0 0 0.5rem; font-size: 1.6rem; color: #c8c2f0; }
    header p  { margin: 0; font-size: 0.9rem; color: #9b96b8; }
    main { padding: 2rem; max-width: 1100px; margin: 0 auto; }
    .summary { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
    .stat { padding: 1rem 1.5rem; border-radius: 10px; background: #252338; border: 1px solid #3d3a5c; min-width: 120px; }
    .stat .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: #9b96b8; margin-bottom: 0.25rem; }
    .stat .value { font-size: 2rem; font-weight: 700; }
    .stat.passed .value { color: #5dc994; }
    .stat.failed .value { color: #e07070; }
    .stat.skipped .value { color: #d4a14a; }
    .stat.total .value { color: #c8c2f0; }
    h2 { color: #c8c2f0; border-bottom: 1px solid #3d3a5c; padding-bottom: 0.5rem; margin-top: 2rem; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.9rem; }
    th { background: #2e2b48; color: #9b96b8; text-align: left; padding: 0.6rem 1rem; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
    td { padding: 0.7rem 1rem; border-bottom: 1px solid #2e2b48; }
    tr:hover td { background: #252338; }
    .status-passed  { color: #5dc994; font-weight: 600; }
    .status-failed  { color: #e07070; font-weight: 600; }
    .status-skipped { color: #d4a14a; font-weight: 600; }
    .status-other   { color: #9b96b8; }
    .skip-note      { font-size: 0.8rem; color: #9b96b8; font-weight: 400; }
    footer { margin: 3rem 2rem 1rem; font-size: 0.8rem; color: #6b6880; }
  </style>
</head>
<body>
  <header>
    <h1>Run Report — $($Manifest.title)</h1>
    <p>Campaign: <code>$($Manifest.campaign_id)</code> &nbsp;|&nbsp; Started: $StartedAt &nbsp;|&nbsp; Completed: $completedAt</p>
  </header>
  <main>
    <div class="summary">
      <div class="stat total"><div class="label">Total</div><div class="value">$total</div></div>
      <div class="stat passed"><div class="label">Passed</div><div class="value">$passed</div></div>
      <div class="stat failed"><div class="label">Failed</div><div class="value">$failed</div></div>
      <div class="stat skipped"><div class="label">Skipped</div><div class="value">$skipped</div></div>
    </div>
    <h2>Quest Results</h2>
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Title</th>
          <th>Status</th>
          <th>Steps</th>
          <th>Started</th>
          <th>Completed</th>
        </tr>
      </thead>
      <tbody>
$($questRowsHtml.ToString())      </tbody>
    </table>
  </main>
  <footer>Generated by liang-quest-general-executor batch-executor.ps1</footer>
</body>
</html>
"@

    [System.IO.File]::WriteAllText($reportPath, $html, [System.Text.Encoding]::UTF8)
    Write-Log "Run report written: $reportPath" -Level INFO
    return $reportPath
}

# ---------------------------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------------------------

function Invoke-Cleanup([string]$CampaignPath) {
    $tmpFiles = Get-ChildItem $CampaignPath -Filter "*.tmp" -Recurse -ErrorAction SilentlyContinue
    foreach ($tmp in $tmpFiles) {
        Remove-Item $tmp.FullName -Force
        Write-Log "Cleaned up temp file: $($tmp.Name)" -Level INFO
    }
}

# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

Write-Log "Batch executor starting for campaign: $CampaignPath" -Level INFO

if (-not (Test-Path $CampaignPath)) {
    Write-Log "Campaign path not found: $CampaignPath" -Level ERROR
    exit $EXIT_PREFLIGHT_FAIL
}

$manifestPath = Join-Path $CampaignPath 'manifest.yaml'
$manifest     = Read-ManifestYaml $manifestPath

# Resolve workspace root: campaigns/<campaign>/ sits two levels below workspace root
$workspaceRoot = (Resolve-Path (Join-Path $CampaignPath '../..')).Path

# --- Crash recovery check ---
$recovery = Invoke-CrashRecovery -Manifest $manifest -CampaignPath $CampaignPath -AutoResume:$Resume
if ($recovery) {
    Write-Log "Resuming quest $($recovery.QuestId) from after step '$($recovery.ResumeFromStep)'" -Level INFO
}

# --- Pre-flight gate ---
if (-not (Test-PreFlight -Manifest $manifest -CampaignPath $CampaignPath -WorkspaceRoot $workspaceRoot)) {
    Write-Log "Pre-flight failed. Aborting." -Level ERROR
    exit $EXIT_PREFLIGHT_FAIL
}

$projectConfig = Read-ProjectYaml $workspaceRoot
Write-Log "Pre-flight passed. Models loaded from project.yaml." -Level INFO

# --- Build execution queue ---
$generalPlannedQuests = @($manifest.quests | Where-Object {
    $_.workflow -eq 'general' -and $_.status -in @('planned', 'in_progress')
})
$executionOrder = Get-DependencyOrder $generalPlannedQuests

# If recovering, ensure the recovered quest is still in queue
if ($recovery -ne $null) {
    if ($executionOrder -notcontains $recovery.QuestId) {
        Write-Log "Recovered quest $($recovery.QuestId) is not in the execution queue. It may have already completed." -Level WARN
        $recovery = $null
    }
}

Write-Log "Execution queue ($($executionOrder.Count) quests): $($executionOrder -join ' -> ')" -Level INFO

$overallStartedAt = Get-Timestamp
$questResults     = @{}
$runDir           = Join-Path $CampaignPath '.run'

if (-not (Test-Path $runDir)) {
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
}

# --- Quest iteration loop ---
foreach ($questId in $executionOrder) {
    $quest = $manifest.quests | Where-Object { $_.id -eq $questId }
    if ($quest -eq $null) { continue }

    # Check dependencies are satisfied
    $unmetDeps = @($quest.depends_on) | Where-Object {
        $_ -ne '' -and $questResults.ContainsKey($_) -and $questResults[$_] -ne 'passed'
    }
    $missingDeps = @($quest.depends_on) | Where-Object {
        $_ -ne '' -and -not $questResults.ContainsKey($_)
    }

    if ($unmetDeps.Count -gt 0) {
        Write-Log "Quest $questId skipped — dependency failed: $($unmetDeps -join ', ')" -Level WARN
        continue
    }

    Write-Log "Starting quest: $questId — $($quest.title)" -Level QUEST

    # Transition to in_progress
    $quest.status        = 'in_progress'
    $quest.started_at    = Get-Timestamp
    $quest.current_cycle = 0
    Write-ManifestAtomic $manifestPath $manifest

    # Resolve plan.html path
    # quest.path is relative to campaign root e.g. "quest-001-foo/index.html"
    $questDir = Join-Path $CampaignPath (Split-Path $quest.path -Parent)
    $planPath = Join-Path $questDir 'plan.html'

    $script:PlanDifficulty = 'medium'
    $steps = Read-PlanSteps $planPath
    $difficulty = $script:PlanDifficulty

    $quest.total_cycles = $steps.Count
    Write-ManifestAtomic $manifestPath $manifest

    Write-Log "  Plan loaded: $($steps.Count) steps, difficulty: $difficulty" -Level INFO

    # Determine start step for crash recovery
    $startStepIndex = 0
    if ($recovery -ne $null -and $recovery.QuestId -eq $questId -and $recovery.ResumeFromStep -ne '') {
        $resumeId = $recovery.ResumeFromStep
        for ($idx = 0; $idx -lt $steps.Count; $idx++) {
            if ($steps[$idx].id -eq $resumeId) {
                $startStepIndex = $idx + 1
                Write-Log "  Resuming from step index $startStepIndex (after '$resumeId')" -Level INFO
                break
            }
        }
    }

    $questPassed = $true

    # --- Step execution loop ---
    for ($i = $startStepIndex; $i -lt $steps.Count; $i++) {
        $step = $steps[$i]
        Write-Log "  Step $($step.id): $($step.name)" -Level STEP

        # Update manifest progress
        $quest.current_cycle           = $i + 1
        $quest.current_step_started_at = Get-Timestamp
        Write-ManifestAtomic $manifestPath $manifest

        $stepStartedAt = $quest.current_step_started_at

        # Select model by difficulty
        $execModel = switch ($difficulty) {
            'easy'  { $projectConfig.models.execution_by_difficulty.easy }
            'hard'  { $projectConfig.models.execution_by_difficulty.hard }
            default { $projectConfig.models.execution_by_difficulty.medium }
        }
        if ($execModel -eq '') { $execModel = $projectConfig.models.execution_by_difficulty.medium }
        $verifyModel = $projectConfig.models.verify

        # Invoke execute-child (attempt 1)
        $execInputCtx = @{
            step_id      = $step.id
            step_name    = $step.name
            instructions = $step.instructions
            is_retry     = $false
            retry_attempt = 0
            accumulated_lessons  = [System.Collections.ArrayList]@()
            previous_failure     = ''
            revised_instructions = ''
        }

        $execResult = Invoke-PiChild -ChildType 'execute-child' -Model $execModel `
            -InputContext $execInputCtx -RunDir $runDir -QuestId $questId `
            -StepId $step.id -Attempt 1

        # result-file-first: write step result before manifest update
        $stepResult = @{
            status       = 'executed'
            started_at   = $stepStartedAt
            completed_at = Get-Timestamp
            attempt      = 1
            retry_tier   = 'none'
        }
        Write-StepResult -RunDir $runDir -QuestId $questId -StepId $step.id -Result $stepResult

        # Invoke verify-child (attempt 1)
        $verifyCtx = @{
            step_id              = $step.id
            step_name            = $step.name
            verification_tier    = $step.verification_tier
            verification_command = $step.verification_command
            acceptance_criteria  = $step.acceptance_criteria
            files_changed        = if ($execResult.ContainsKey('files_changed')) { $execResult['files_changed'] } else { '' }
            implementation_summary = if ($execResult.ContainsKey('implementation_summary')) { $execResult['implementation_summary'] } else { '' }
        }

        $verifyResult = Invoke-PiChild -ChildType 'verify-child' -Model $verifyModel `
            -InputContext $verifyCtx -RunDir $runDir -QuestId $questId `
            -StepId $step.id -Attempt 1

        $stepPassed     = $verifyResult.passed
        $lastFailure    = $verifyResult.failure_reason
        $accumulatedLessons = [System.Collections.ArrayList]@()

        # --- Tiered retry loop ---
        if (-not $stepPassed) {
            for ($retry = 1; $retry -le $MaxRetries; $retry++) {
                [void]$accumulatedLessons.Add($lastFailure)

                $retryOut = Invoke-TieredRetry `
                    -Step $step `
                    -Attempt $retry `
                    -AccumulatedLessons $accumulatedLessons `
                    -PreviousFailure $lastFailure `
                    -ProjectConfig $projectConfig `
                    -Difficulty $difficulty `
                    -CampaignPath $CampaignPath `
                    -QuestId $questId

                # result-file-first: write retry result before verify
                $retryStepResult = @{
                    status         = 'retry'
                    started_at     = Get-Timestamp
                    completed_at   = Get-Timestamp
                    attempt        = $retry + 1
                    retry_tier     = $retryOut.retry_tier
                    failure_reason = $lastFailure
                    lessons        = $accumulatedLessons
                }
                Write-StepResult -RunDir $runDir -QuestId $questId -StepId "$($step.id)-retry$retry" -Result $retryStepResult

                # Re-verify after retry
                $retryVerifyCtx = @{
                    step_id              = $step.id
                    step_name            = $step.name
                    verification_tier    = $step.verification_tier
                    verification_command = $step.verification_command
                    acceptance_criteria  = $step.acceptance_criteria
                    files_changed        = if ($retryOut.result.ContainsKey('files_changed')) { $retryOut.result['files_changed'] } else { '' }
                    implementation_summary = if ($retryOut.result.ContainsKey('implementation_summary')) { $retryOut.result['implementation_summary'] } else { '' }
                    is_retry             = $true
                    retry_attempt        = $retry
                }

                $retryVerify = Invoke-PiChild -ChildType 'verify-child' -Model $verifyModel `
                    -InputContext $retryVerifyCtx -RunDir $runDir -QuestId $questId `
                    -StepId $step.id -Attempt ($retry + 1)

                if ($retryVerify.passed) {
                    $stepPassed = $true
                    break
                }
                $lastFailure = $retryVerify.failure_reason
            }
        }

        if ($stepPassed) {
            # Update step result to passed
            $finalStepResult = @{
                status       = 'passed'
                started_at   = $stepStartedAt
                completed_at = Get-Timestamp
                attempt      = 1
                retry_tier   = 'none'
            }
            Write-StepResult -RunDir $runDir -QuestId $questId -StepId $step.id -Result $finalStepResult
            Write-Log "  Step $($step.id) PASSED" -Level STEP
        }
        else {
            # Step exhausted retries
            $finalStepResult = @{
                status         = 'failed'
                started_at     = $stepStartedAt
                completed_at   = Get-Timestamp
                attempt        = $MaxRetries + 1
                retry_tier     = 'exhausted'
                failure_reason = $lastFailure
                lessons        = $accumulatedLessons
            }
            Write-StepResult -RunDir $runDir -QuestId $questId -StepId $step.id -Result $finalStepResult
            Write-Log "  Step $($step.id) FAILED after $MaxRetries retries. Reason: $lastFailure" -Level ERROR

            $quest.status       = 'failed'
            $quest.completed_at = Get-Timestamp
            Write-ManifestAtomic $manifestPath $manifest
            $questResults[$questId] = 'failed'
            Write-Log "Quest $questId FAILED on step $($step.id)" -Level ERROR

            Invoke-CascadeSkip -Manifest $manifest -FailedQuestId $questId -CampaignPath $CampaignPath

            $questPassed = $false
            break
        }
    }

    if ($questPassed) {
        $quest.status       = 'passed'
        $quest.completed_at = Get-Timestamp
        Write-ManifestAtomic $manifestPath $manifest
        $questResults[$questId] = 'passed'

        # Write completion marker
        $completionMarker = Join-Path $runDir $questId 'complete.yaml'
        $markerYaml = "quest_id: `"$questId`"`nstatus: `"passed`"`ncompleted_at: `"$(Get-Timestamp)`"`n"
        [System.IO.File]::WriteAllText($completionMarker, $markerYaml, [System.Text.Encoding]::UTF8)

        Write-Log "Quest $questId PASSED ($($steps.Count) steps)" -Level QUEST
    }
}

# --- Run report ---
$reportPath = New-RunReport -Manifest $manifest -CampaignPath $CampaignPath `
    -QuestResults $questResults -StartedAt $overallStartedAt

# --- Cleanup temp files from atomic writes ---
Invoke-Cleanup -CampaignPath $CampaignPath

# --- Summary ---
$passedCount  = @($questResults.GetEnumerator() | Where-Object { $_.Value -eq 'passed' }).Count
$failedCount  = @($questResults.GetEnumerator() | Where-Object { $_.Value -eq 'failed' }).Count
$skippedCount = @($manifest.quests | Where-Object { $_.workflow -eq 'general' -and $_.status -eq 'skipped' }).Count

Write-Log "Campaign complete. Passed: $passedCount  Failed: $failedCount  Skipped: $skippedCount" -Level INFO
Write-Log "Run report: $reportPath" -Level INFO

if ($failedCount -gt 0) {
    exit $EXIT_EXECUTION_FAIL
}
else {
    exit $EXIT_SUCCESS
}
