# =========================================================
# Requires Administrator Privileges
# =========================================================
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: You must run this script as an Administrator." -ForegroundColor Red
    Exit
}

# =========================================================
# The "Some Guy's Website" Disclaimer
# =========================================================
Clear-Host
Write-Host "===============================================================================" -ForegroundColor Red
Write-Host "                               !!! WARNING !!!                                 " -ForegroundColor Red
Write-Host "===============================================================================" -ForegroundColor Red
Write-Host "I am not responsible for any lost data as a result of running this script." -ForegroundColor Yellow
Write-Host "You should probably not be running PowerShell scripts that you find on some" -ForegroundColor Yellow
Write-Host "guy's website in the first place." -ForegroundColor Yellow
Write-Host ""
Write-Host "Please make sure your data is backed up to a location that is NOT on this" -ForegroundColor Yellow
Write-Host "computer on the off chance something goes horribly wrong and your C: drive" -ForegroundColor Yellow
Write-Host "is suddenly gone." -ForegroundColor Yellow
Write-Host "===============================================================================" -ForegroundColor Red

while ($true) {
    $agree = Read-Host "`nDo you accept these risks and wish to continue? (Y/N)"
    if ($agree -eq 'Y' -or $agree -eq 'y') {
        break
    } elseif ($agree -eq 'N' -or $agree -eq 'n') {
        Write-Host "Smart choice. Exiting script." -ForegroundColor Cyan
        exit
    } else {
        Write-Host "Please enter 'Y' to continue or 'N' to exit." -ForegroundColor Gray
    }
}

# =========================================================
# Main Script Logic
# =========================================================

# Automatically find the OS Disk
$cPartition = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
$osDiskNum = $cPartition.DiskNumber

while ($true) {
    Clear-Host
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host "       Windows Recovery Partition Manager          " -ForegroundColor White
    Write-Host "             Targeting OS Disk: $osDiskNum                 " -ForegroundColor White
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host " 1. View all Disks"
    Write-Host " 2. View existing Partitions (OS Disk)"
    Write-Host " 3. Delete an existing Partition (OS Disk)"
    Write-Host " 4. Create a new Recovery Partition (Shrink C:)"
    Write-Host " 5. Exit"
    Write-Host "===================================================" -ForegroundColor Cyan
    
    $choice = Read-Host "Select an option (1-5)"

    switch ($choice) {
        '1' {
            # Option 1: View All Disks
            Write-Host "`n--- All Disks on System ---" -ForegroundColor Yellow
            Get-Disk | Sort-Object Number | Format-Table Number, FriendlyName, HealthStatus, OperationalStatus, PartitionStyle -AutoSize
            
            Read-Host "`nPress Enter to return to the menu..."
        }

        '2' {
            # Option 2: View Partitions
            Write-Host "`n--- Current Partitions on Disk $osDiskNum ---" -ForegroundColor Yellow
            Get-Partition -DiskNumber $osDiskNum | Select-Object PartitionNumber, DriveLetter, Type, Size, GptType | Format-Table -AutoSize
            
            Write-Host "Note: Standard Recovery GUID is {de94bba4-06d1-4d40-a16a-bfd50179d6ac}" -ForegroundColor DarkGray
            Read-Host "`nPress Enter to return to the menu..."
        }

        '3' {
            # Option 3: Delete a Partition
            Write-Host "`n--- Delete a Partition on Disk $osDiskNum ---" -ForegroundColor Yellow
            Get-Partition -DiskNumber $osDiskNum | Select-Object PartitionNumber, DriveLetter, Type, Size | Format-Table -AutoSize
            
            $partToDelete = Read-Host "Enter the Partition Number you want to DELETE (or type 'c' to cancel)"
            
            if ($partToDelete -eq 'c') { continue }

            try {
                $targetPart = Get-Partition -DiskNumber $osDiskNum -PartitionNumber $partToDelete -ErrorAction Stop
                
                Write-Host "WARNING: You are about to delete Partition $partToDelete ($($targetPart.Type))." -ForegroundColor Red
                $confirm = Read-Host "Are you absolutely sure? (Y/N)"
                
                if ($confirm -eq 'Y' -or $confirm -eq 'y') {
                    Remove-Partition -DiskNumber $osDiskNum -PartitionNumber $partToDelete -Confirm:$false
                    Write-Host "Partition $partToDelete successfully deleted." -ForegroundColor Green
                } else {
                    Write-Host "Deletion cancelled." -ForegroundColor Yellow
                }
            } catch {
                Write-Host "Error: Invalid partition number or partition does not exist." -ForegroundColor Red
            }
            Read-Host "`nPress Enter to return to the menu..."
        }

        '4' {
            # Option 4: Create New Recovery Partition
            Write-Host "`n--- Creating New Recovery Partition ---" -ForegroundColor Yellow
            
            # Prompt for size with a 1GB default
            $sizeInput = Read-Host "Enter size for the new Recovery Partition in GB [Default: 1]"
            
            if ([string]::IsNullOrWhiteSpace($sizeInput)) {
                $recSizeMB = 1024
            } else {
                # Validate input is a number
                if ($sizeInput -match '^\d+(\.\d+)?$') {
                    $recSizeMB = [math]::Round([double]$sizeInput * 1024)
                } else {
                    Write-Host "Invalid input. Defaulting to 1GB." -ForegroundColor Yellow
                    $recSizeMB = 1024
                }
            }

            Write-Host "Disabling Windows Recovery Environment..." -ForegroundColor Cyan
            reagentc /disable

            # Refresh C: drive details in case of changes
            $currentC = Get-Partition | Where-Object { $_.DriveLetter -eq 'C' }
            $cDiskNum = $currentC.DiskNumber
            $cPartNum = $currentC.PartitionNumber

            Write-Host "Shrinking C: drive by $($recSizeMB / 1024) GB..." -ForegroundColor Cyan
            
            try {
                $newSize = $currentC.Size - ($recSizeMB * 1MB)
                Resize-Partition -DiskNumber $cDiskNum -PartitionNumber $cPartNum -Size $newSize -ErrorAction Stop
            } catch {
                Write-Host "Error: Failed to shrink the C: drive. Make sure you have enough free space." -ForegroundColor Red
                Read-Host "`nPress Enter to return to the menu..."
                continue
            }

            Write-Host "Creating and formatting new partition..." -ForegroundColor Cyan
            $recoveryTypeGuid = "{de94bba4-06d1-4d40-a16a-bfd50179d6ac}"
            $newPartition = New-Partition -DiskNumber $cDiskNum -UseMaximumSize -GptType $recoveryTypeGuid
            Format-Volume -Partition $newPartition -FileSystem NTFS -NewFileSystemLabel "Recovery" -Confirm:$false

            Write-Host "Allowing Windows to register the new volume..." -ForegroundColor DarkGray
            Start-Sleep -Seconds 3

            # Detect the newly created partition
            $recoveryPartList = Get-Partition -DiskNumber $cDiskNum | Where-Object { 
                $_.Type -like "*Recovery*" -or 
                (Get-Volume -Partition $_ -ErrorAction SilentlyContinue).FileSystemLabel -eq "Recovery" 
            }

            if ($recoveryPartList) {
                # Grab the last one in the array (the one we just appended to the disk)
                $newRecPartNum = $recoveryPartList[-1].PartitionNumber
                Write-Host "Detected new Recovery Partition: Disk $cDiskNum, Partition #$newRecPartNum" -ForegroundColor Green
                
                Write-Host "Applying hidden system attributes via diskpart..." -ForegroundColor Cyan
                $diskpartScript = @"
select disk $cDiskNum
select partition $newRecPartNum
set id=de94bba4-06d1-4d40-a16a-bfd50179d6ac
gpt attributes=0x8000000000000001
exit
"@
                $diskpartScript | diskpart | Out-Null
                
                Write-Host "Enabling Windows Recovery Environment..." -ForegroundColor Cyan
                reagentc /enable
                reagentc /info
            } else {
                Write-Host "Error: Could not automatically detect the newly created 'Recovery' partition." -ForegroundColor Red
            }
            
            Read-Host "`nPress Enter to return to the menu..."
        }

        '5' {
            # Option 5: Exit
            Write-Host "Exiting Script." -ForegroundColor Cyan
            exit
        }

        default {
            Write-Host "Invalid selection. Please enter a number between 1 and 5." -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}