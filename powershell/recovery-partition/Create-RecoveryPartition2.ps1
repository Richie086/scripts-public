# 1. Automatically detect the volume labeled "Recovery" on your main system disk
$cPartition = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
$diskNum = $cPartition.DiskNumber

$recoveryPart = Get-Partition -DiskNumber $diskNum | Where-Object { 
    $_.Type -like "*Recovery*" -or 
    (Get-Volume -Partition $_).FileSystemLabel -eq "Recovery" 
}

# 2. Check if a matching partition was found
if ($recoveryPart) {
    $partNum = $recoveryPart.PartitionNumber
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
    reagentc /enable
    reagentc /info
} else {
    Write-Host "Error: Could not automatically detect a partition named 'Recovery'." -ForegroundColor Red
}
