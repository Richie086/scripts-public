# 1. Automatically find the C: Drive disk and partition details
$cPartition = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
$diskNum = $cPartition.DiskNumber
$cPartitionNum = $cPartition.PartitionNumber

# 2. Dynamically find the Recovery partition on that same disk
$recoveryPartition = Get-Partition -DiskNumber $diskNum | Where-Object { $_.GptType -eq "{de94bba4-06d1-4d40-a16a-bfd50179d6ac}" -or $_.Type -like "*Recovery*" }

# 3. Safely delete the recovery partition if it exists
if ($recoveryPartition) {
    Write-Host "Found Recovery Partition #$($recoveryPartition.PartitionNumber). Deleting..." -ForegroundColor Yellow
    Remove-Partition -DiskNumber $diskNum -PartitionNumber $recoveryPartition.PartitionNumber -Confirm:$false
} else {
    Write-Host "No blocking Recovery Partition found. Moving to resize step." -ForegroundColor Green
}

# 4. Fetch the maximum available expanded size and extend the C: drive
Write-Host "Calculating maximum available disk space..." -ForegroundColor Cyan
$maxSize = (Get-PartitionSupportedSize -DiskNumber $diskNum -PartitionNumber $cPartitionNum).SizeMax

Write-Host "Extending C: Drive partition..." -ForegroundColor Cyan
Resize-Partition -DiskNumber $diskNum -PartitionNumber $cPartitionNum -Size $maxSize

Write-Host "Success! Your C: Drive has been fully expanded." -ForegroundColor Green
