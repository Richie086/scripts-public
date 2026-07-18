<#
.SYNOPSIS
    Example template PowerShell script demonstrating robust automation standards.
.DESCRIPTION
    A boilerplate script showing parameter definitions, standard logging, and error handling.
.PARAMETER Hostname
    Specify the target host address (default: 127.0.0.1).
.EXAMPLE
    .\example.ps1 -Hostname "192.168.1.1"
#>
[CmdletBinding()]
param (
    [string]$Hostname = "127.0.0.1"
)

# Strict option error action
$ErrorActionPreference = "Stop"

function Log-Message {
    param (
        [string]$Level = "INFO",
        [string]$Message
    )
    $timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    Write-Host "[$timestamp] [$Level] $Message"
}

Log-Message -Level "INFO" -Message "Starting PowerShell script execution..."
Log-Message -Level "INFO" -Message "Target hostname: $Hostname"
Log-Message -Level "INFO" -Message "Execution completed successfully!"
