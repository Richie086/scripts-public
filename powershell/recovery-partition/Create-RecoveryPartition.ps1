# =========================================================
# PHASE 1: SHRINK C: AND CREATE THE PARTITION
# =========================================================

# Disable the current Recovery Environment to avoid conflicts
Write-Host "Disabling Windows Recovery Environment..." -ForegroundColor Cyan
reagentc /disable

# Grab your C: drive details
$cPartition = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
$diskNum = $cPartition.DiskNumber
$cPartitionNum = $cPartition.PartitionNumber

# Shrink the C: drive by exactly 1024MB (1 GB)
Write-Host "Shrinking C: drive by 1GB..." -ForegroundColor Cyan
$currentSize = $cPartition.Size
$newSize = $currentSize - 1024MB
Resize-Partition -DiskNumber $diskNum -PartitionNumber $cPartitionNum -Size $newSize

# Create the new partition using the standard Recovery GUID
Write-Host "Creating and formatting new partition..." -ForegroundColor Cyan
$recoveryTypeGuid = "{de94bba4-06d1-4d40-a16a-bfd50179d6ac}"
$newPartition = New-Partition -DiskNumber $diskNum -UseMaximumSize -GptType $recoveryTypeGuid

# Format as NTFS and label it "Recovery"
Format-Volume -Partition $newPartition -FileSystem NTFS -NewFileSystemLabel "Recovery" -Confirm:$false

# Give Windows a moment to register the new volume label before searching for it
Start-Sleep -Seconds 3

# =========================================================
# PHASE 2: DETECTION, ATTRIBUTES, AND ENABLEMENT
# =========================================================

# 1. Automatically detect the volume labeled "Recovery" on your main system disk
$cPartition = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
$diskNum = $cPartition.DiskNumber

$recoveryPart = Get-Partition -DiskNumber $diskNum | Where-Object { 
    $_.Type -like "*Recovery*" -or 
    (Get-Volume -Partition $_ -ErrorAction SilentlyContinue).FileSystemLabel -eq "Recovery" 
}

# 2. Check if a matching partition was found
if ($recoveryPart) {
    # If multiple recovery partitions exist, grab the one we just created (the last one)
    $partNum = $recoveryPart[-1].PartitionNumber
    Write-Host "Detected Recovery Partition on Disk $diskNum, Partition #$partNum" -ForegroundColor Green
    
    # 3. Build and pipe the script into diskpart to apply the correct GPT attributes
    $diskpartScript = @"
select disk $diskNum
select partition $partNum
set id=de94bba4-06d1-4d40-a16a-bfd50179d6ac
gpt attributes=0x8000000000000001
exit
"@
    Write-Host "Applying hidden system attributes..." -ForegroundColor Cyan
    $diskpartScript | diskpart
    
    # 4. Turn on the Windows Recovery Environment
    Write-Host "Enabling Windows Recovery Environment..." -ForegroundColor Cyan
    reagentc /enable
    reagentc /info
} else {
    Write-Host "Error: Could not automatically detect a partition named 'Recovery'." -ForegroundColor Red
}