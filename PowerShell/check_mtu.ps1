param(
    [Parameter(Mandatory=$false, Position=0)]
    [string[]]$Targets,

    [string]$Interface,

    [switch]$Help
)

# -----------------------------
# HELP / USAGE
# -----------------------------
if ($Help -or -not $Targets) {
    Write-Output @"
Usage:
    .\check_mtu.ps1 -Targets <hosts or IPs> [-Interface <name>]

Description:
    Performs MTU validation testing using ICMP.

Targets Formats:
    - Space-separated: 10.1.1.1 8.8.8.8
    - Comma-separated: "10.1.1.1,8.8.8.8"
    - Mixed supported

Examples:
    .\check_mtu.ps1 -Targets 10.93.254.1
    .\check_mtu.ps1 -Targets 10.93.254.1 8.8.8.8
    .\check_mtu.ps1 -Targets "10.93.254.1,8.8.8.8"
    .\check_mtu.ps1 -Targets "server1,server2" -Interface "Ethernet 3"
"@
    exit 0
}

# -----------------------------
# VALIDATION
# -----------------------------
if (-not $Targets -or $Targets.Count -eq 0) {
    Write-Error "At least one target must be specified."
    exit 1
}

# -----------------------------
# CONFIG
# -----------------------------
$MTUSizes = @(1400,1408,1450,1472,1500,9000,9216)

$script:FailedCommands = @()
$script:PassedCommands = @()

# -----------------------------
# NORMALIZE TARGETS
# -----------------------------
$TargetHosts = @()
foreach ($t in $Targets) {
    $TargetHosts += ($t -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

# -----------------------------
# INTERFACE DETECTION
# -----------------------------
if (-not $Interface) {
    $Interface = (Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
        Sort-Object RouteMetric |
        Select-Object -First 1).InterfaceAlias
}

if (-not $Interface) {
    Write-Error "Could not determine interface"
    exit 1
}

# -----------------------------
# HEADER
# -----------------------------
Write-Output "========================================="
Write-Output " Network Validation Report"
Write-Output " Host: $env:COMPUTERNAME"
Write-Output " Interface: $Interface"
Write-Output " Date: $(Get-Date)"
Write-Output "========================================="

# -----------------------------
# INTERFACE SUMMARY
# -----------------------------
Write-Output "`nINTERFACE SUMMARY"

Get-NetAdapter -Name $Interface | ForEach-Object {
    $stats = Get-NetAdapterStatistics -Name $_.Name
    $mtu = (Get-NetIPInterface -InterfaceAlias $_.Name -AddressFamily IPv4).NlMtu

    [PSCustomObject]@{
        Interface   = $_.Name
        MTU         = $mtu
        RX_Dropped  = $stats.ReceivedDiscardedPackets
        TX_Dropped  = $stats.OutboundDiscardedPackets
        RX_Errors   = $stats.ReceivedPacketErrors
        TX_Errors   = $stats.OutboundPacketErrors
    }
} | Format-Table -AutoSize

# -----------------------------
# RESOLVE TARGET
# -----------------------------
function Resolve-Target {
    param($Target)
    try {
        $resolved = Resolve-DnsName $Target -ErrorAction Stop |
            Where-Object {$_.Type -eq "A"} |
            Select-Object -First 1 -ExpandProperty IPAddress
        if ($resolved) { return $resolved }
    } catch {}
    return $Target
}

# -----------------------------
# MTU TEST FUNCTION
# -----------------------------
function Run-MtuTest {
    param(
        [string]$Target,
        [bool]$DontFragment
    )

    $resolved = Resolve-Target $Target

    Write-Output "`n-----------------------------------------"
    Write-Output " L3 MTU TEST: $Target ($resolved) | DF=$DontFragment"
    Write-Output "-----------------------------------------"

    $passed = @()
    $failed = @()

    foreach ($mtu in $MTUSizes) {

        $payload = $mtu - 28
        if ($payload -le 0) {
            $failed += $mtu
            continue
        }

        $args = @("-n","2","-w","2000","-l",$payload,$resolved)
        if ($DontFragment) {
            $args = @("-f") + $args
        }

        $result = & ping.exe $args 2>&1
        $exitCode = $LASTEXITCODE
        $cmdString = "ping " + ($args -join " ")

        if ($exitCode -ne 0 -or
            $result -match "fragment" -or
            $result -match "timed out" -or
            $result -match "could not find host") {

            $failed += $mtu
            $script:FailedCommands += $cmdString
        }
        else {
            $passed += $mtu
            $script:PassedCommands += $cmdString
        }
    }

    Write-Output "MTU PASSED : $($passed -join ' ')"
    Write-Output "MTU FAILED : $($failed -join ' ')"
}

# -----------------------------
# RUN TESTS
# -----------------------------
Write-Output "`n========================================="
Write-Output " TARGET HOST TESTS"
Write-Output "========================================="

foreach ($target in $TargetHosts) {
    Run-MtuTest -Target $target -DontFragment $true
    Run-MtuTest -Target $target -DontFragment $false
}

# -----------------------------
# OUTPUT RESULTS
# -----------------------------
Write-Output "`n========================================="
Write-Output " FAILED COMMANDS"
Write-Output "========================================="

if ($script:FailedCommands.Count -eq 0) {
    Write-Output "None"
} else {
    $script:FailedCommands | Sort-Object -Unique
}

Write-Output "`n========================================="
Write-Output " PASSED COMMANDS"
Write-Output "========================================="

if ($script:PassedCommands.Count -eq 0) {
    Write-Output "None"
} else {
    $script:PassedCommands | Sort-Object -Unique
}

Write-Output "`n========================================="
Write-Output " End of Report"
Write-Output "========================================="