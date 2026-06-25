# 1. Turn off the current Recovery Environment mapping to avoid conflicts
Write-Host "Disabling Windows Recovery Environment..." -ForegroundColor Cyan
reagentc /disable

# 2. Grab your C: drive details
Write-Host "Gathering C: drive details..." -ForegroundColor Cyan
$cPartition = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
$diskNum = $cPartition.DiskNumber
$cPartitionNum = $cPartition.PartitionNumber

# 3. Shrink the C: drive by exactly 1024MB (1 GB) to make space at the end
Write-Host "Shrinking C: drive by 1GB. This may take a moment..." -ForegroundColor Cyan
$currentSize = $cPartition.Size
$newSize = $currentSize - 1024MB
Resize-Partition -DiskNumber $diskNum -PartitionNumber $cPartitionNum -Size $newSize

# 4. Create the new Recovery partition in the freshly unallocated space
Write-Host "Creating new Recovery partition..." -ForegroundColor Cyan
$recoveryTypeGuid = "{de94bba4-06d1-4d40-a16a-bfd50179d6ac}"
$newPartition = New-Partition -DiskNumber $diskNum -UseMaximumSize -GptType $recoveryTypeGuid

# 5. Format the partition as NTFS and label it "Recovery"
Write-Host "Formatting partition as NTFS..." -ForegroundColor Cyan
Format-Volume -Partition $newPartition -FileSystem NTFS -NewFileSystemLabel "Recovery" -Confirm:$false

# 6. Build and pipe the script into diskpart to apply the correct GPT attributes
# This ensures it gets the official hidden/system flags (0x8000000000000001)
$partNum = $newPartition.PartitionNumber
Write-Host "Applying required system attributes via diskpart..." -ForegroundColor Cyan
$diskpartScript = @"
select disk $diskNum
select partition $partNum
set id=de94bba4-06d1-4d40-a16a-bfd50179d6ac
gpt attributes=0x8000000000000001
exit
"@
$diskpartScript | diskpart

# 7. Turn the Windows Recovery Environment back on 
Write-Host "Enabling Windows Recovery Environment..." -ForegroundColor Cyan
reagentc /enable

# 8. Output configuration details to verify it works
Write-Host "Task complete. Verifying Configuration:" -ForegroundColor Green
reagentc /info