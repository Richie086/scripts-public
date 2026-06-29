param (
    [Parameter(Mandatory=$false)]
    [string]$TargetFolder = ".",

    [Parameter(Mandatory=$false)]
    [string]$Recursive = "Off"
)

# Ensure the target folder exists
if (-not (Test-Path -Path $TargetFolder -PathType Container)) {
    Write-Error "The specified directory does not exist: $TargetFolder"
    exit
}

# Helper function for human-readable sizes
function Format-Bytes {
    param([long]$bytes)
    $units = "B", "KB", "MB", "GB", "TB"
    $unit = 0
    $val = $bytes
    while ($val -ge 1024 -and $unit -lt ($units.Count - 1)) {
        $val /= 1024
        $unit++
    }
    return "{0:N2} {1}" -f $val, $units[$unit]
}

# Process a single directory
function Process-Directory {
    param([string]$Path)

    # Get files and folders (no recursion)
    $files = Get-ChildItem -Path $Path -File
    $folders = Get-ChildItem -Path $Path -Directory

    $totalFiles = @($files).Count
    $totalFolders = @($folders).Count

    # Process sizes and build output
    $totalSize = 0
    $outputLines = @()
    $outputLines += "Folder Statistics for: $Path"
    $outputLines += "========================================"
    $outputLines += "Total Folders: $totalFolders"
    $outputLines += "Total Files: $totalFiles"
    $outputLines += ""
    $outputLines += "File Breakdown:"
    $outputLines += "----------------------------------------"

    foreach ($file in $files) {
        $totalSize += $file.Length
        $sizeStr = Format-Bytes -bytes $file.Length
        $outputLines += "$($file.Name) - $sizeStr"
    }

    $totalSizeStr = Format-Bytes -bytes $totalSize
    $outputLines += "----------------------------------------"
    $outputLines += "Total Folder Size: $totalSizeStr"

    # 1. Output to standard out
    $outputLines | Write-Host

    # 2. Output to text file in the target directory
    $outFilePath = Join-Path -Path $Path -ChildPath "folder_stats.txt"
    $outputLines | Out-File -FilePath $outFilePath -Encoding utf8

    Write-Host "`nReport successfully saved to: $outFilePath"
    Write-Host ""
}

# 1. Always process the root directory
Process-Directory -Path $TargetFolder

# 2. Process subdirectories if Recursive is On
if ($Recursive -eq "On") {
    # Get all subdirectories recursively from the root folder
    $allSubDirs = Get-ChildItem -Path $TargetFolder -Directory -Recurse
    foreach ($subDir in $allSubDirs) {
        Process-Directory -Path $subDir.FullName
    }
}
