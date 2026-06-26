<#
.SYNOPSIS
    OpenSSL certificate utility for Windows PowerShell.

.DESCRIPTION
    Extract certificates, CA chains, private keys, PEM bundles, and CSRs from .pfx, .p12, or .p7b files.
    .p7b files are treated as certificate bundles and do not contain private keys.

.PARAMETER CertIn
    Path to the input certificate file. Supported formats: .pfx, .p12, .p7b.

.PARAMETER CertOut
    Base output path and file name prefix for extracted files.

.PARAMETER Help
    Display this help message and exit.

.EXAMPLE
    .\openssl-certtool.ps1 -CertIn .\cert.pfx

.EXAMPLE
    .\openssl-certtool.ps1 -CertIn .\cert.p7b -CertOut .\wildcard_extremasarcasm_org

.NOTES
    Requires OpenSSL in PATH.
#>
param(
    [Parameter(Mandatory=$false, Position=0)]
    [ValidateNotNullOrEmpty()]
    [Alias('InputFile')]
    [string]$CertIn,

    [Parameter(Mandatory=$false, Position=1)]
    [ValidateNotNullOrEmpty()]
    [Alias('Output')]
    [string]$CertOut,

    [Alias('h')]
    [switch]$Help
)

if ($args -contains '--help' -or $args -contains '-help' -or $args -contains '-h' -or $args -contains '/help') {
    $Help = $true
}

function Show-Help {
    Write-Host "Usage: .\openssl-certtool.ps1 [-CertIn <path>] [-CertOut <prefix>] [-Help]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -CertIn <path>   Specify the input .pfx, .p12, or .p7b certificate file"
    Write-Host "  -CertOut <name>  Specify the base output file path/name (for example: C:\temp\mycert)"
    Write-Host "  -Help            Show this help message and exit"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\openssl-certtool.ps1 -CertIn .\cert.pfx"
    Write-Host "  .\openssl-certtool.ps1 -CertIn .\cert.p7b -CertOut .\wildcard_domain"
    exit 0
}

if ($Help) {
    Show-Help
}

function Throw-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
    Throw-Error "OpenSSL is not installed or not available in PATH."
}

if (-not $CertIn) {
    $CertIn = Read-Host 'Enter the full path to the certificate file [Default: .\cert.pfx]'
    if (-not $CertIn) {
        $CertIn = '.\cert.pfx'
    }
}

if (-not (Test-Path -Path $CertIn -PathType Leaf)) {
    Throw-Error "Certificate file not found at '$CertIn'."
}

$extension = [System.IO.Path]::GetExtension($CertIn).TrimStart('.').ToLower()
switch ($extension) {
    'p7b' { $script:InputType = 'p7b' }
    'pfx' { $script:InputType = 'pfx' }
    'p12' { $script:InputType = 'pfx' }
    default { Throw-Error 'Unsupported certificate type. Use .pfx, .p12, or .p7b.' }
}

if (-not $CertOut) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($CertIn)
    $outputDir = [System.IO.Path]::GetDirectoryName($CertIn)
    if ([string]::IsNullOrEmpty($outputDir)) { $outputDir = '.' }
    $CertOut = Join-Path $outputDir $baseName
}

function Test-PfxNoPassword {
    & openssl pkcs12 -in $CertIn -nokeys -passin pass: -info > $null 2>&1
    return $LASTEXITCODE -eq 0
}

function Detect-P7bFormat {
    & openssl pkcs7 -inform DER -in $CertIn -print_certs -out NUL > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        return 'DER'
    }

    & openssl pkcs7 -inform PEM -in $CertIn -print_certs -out NUL > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        return 'PEM'
    }

    Throw-Error 'Unable to parse .p7b file format.'
}

function Prepare-CertificateInput {
    if ($script:InputType -eq 'p7b') {
        $env:CERT_PASS = ''
        $script:PKCS7Format = Detect-P7bFormat
        return
    }

    if (Test-PfxNoPassword) {
        $env:CERT_PASS = ''
        return
    }

    $securePass = Read-Host 'Enter the .pfx password (leave blank if none)' -AsSecureString
    $plainPass = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass))
    $env:CERT_PASS = $plainPass
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePass)) | Out-Null
}

Prepare-CertificateInput

function Extract-Cer {
    Write-Host "`n[+] Extracting Public Certificate..." -ForegroundColor Yellow
    if ($script:InputType -eq 'p7b') {
        & openssl pkcs7 -in $CertIn -inform $script:PKCS7Format -print_certs -out "${CertOut}.cer"
    }
    else {
        & openssl pkcs12 -in $CertIn -clcerts -nokeys -legacy -out "${CertOut}.cer" -passin env:CERT_PASS
    }
    if ($LASTEXITCODE -eq 0) { Write-Host " -> Created: ${CertOut}.cer" -ForegroundColor Green }
}

function Extract-CaChain {
    Write-Host "`n[+] Extracting CA Chain (Root/Intermediate)..." -ForegroundColor Yellow
    if ($script:InputType -eq 'p7b') {
        & openssl pkcs7 -in $CertIn -inform $script:PKCS7Format -print_certs -out "${CertOut}_ca_chain.cer"
    }
    else {
        & openssl pkcs12 -in $CertIn -nokeys -cacerts -legacy -out "${CertOut}_ca_chain.cer" -passin env:CERT_PASS
    }
    if ($LASTEXITCODE -eq 0) { Write-Host " -> Created: ${CertOut}_ca_chain.cer" -ForegroundColor Green }
}

function Extract-Pem {
    if ($script:InputType -eq 'p7b') {
        Write-Host "`n[!] Error: .p7b files do not contain private keys, so PEM extraction is not supported." -ForegroundColor Red
        return
    }

    Write-Host "`n[+] Extracting Cert + Unencrypted Key (.pem)..." -ForegroundColor Yellow
    & openssl pkcs12 -in $CertIn -out "${CertOut}.pem" -nodes -legacy -passin env:CERT_PASS
    if ($LASTEXITCODE -eq 0) {
        icacls "${CertOut}.pem" /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
        Write-Host " -> Created and secured: ${CertOut}.pem" -ForegroundColor Green
    }
}

function Extract-Key {
    if ($script:InputType -eq 'p7b') {
        Write-Host "`n[!] Error: .p7b files do not contain private keys, so key extraction is not supported." -ForegroundColor Red
        return
    }

    Write-Host "`n[+] Extracting Unencrypted Private Key (.key)..." -ForegroundColor Yellow
    & openssl pkcs12 -in $CertIn -nocerts -out "${CertOut}.key" -nodes -legacy -passin env:CERT_PASS
    if ($LASTEXITCODE -eq 0) {
        icacls "${CertOut}.key" /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null
        Write-Host " -> Created and secured: ${CertOut}.key" -ForegroundColor Green
    }
}

function Copy-P12 {
    if ($script:InputType -eq 'p7b') {
        Write-Host "`n[!] Error: .p7b files cannot be converted to .p12 because they do not contain private keys." -ForegroundColor Red
        return
    }

    Copy-Item -Path $CertIn -Destination "${CertOut}.p12" -Force
    Write-Host "`n -> Created: ${CertOut}.p12" -ForegroundColor Green
}

function View-CertInfo {
    if (-not (Test-Path "${CertOut}.cer")) {
        Write-Host "`n[!] Error: ${CertOut}.cer not found. Please extract the .cer file first." -ForegroundColor Red
        return
    }

    Write-Host "`n=== Certificate Details ===" -ForegroundColor Yellow
    & openssl x509 -in "${CertOut}.cer" -noout -subject -issuer -dates
    Write-Host "--- Subject Alternative Names (SANs) ---" -ForegroundColor Cyan
    & openssl x509 -in "${CertOut}.cer" -noout -text | Select-String -Pattern 'Subject Alternative Name' -Context 0,1
}

function Verify-Match {
    if ((-not (Test-Path "${CertOut}.cer")) -or (-not (Test-Path "${CertOut}.key"))) {
        Write-Host "`n[!] Error: Both .cer and .key files must exist to verify." -ForegroundColor Red
        return
    }

    Write-Host "`n[+] Calculating and comparing Modulus..." -ForegroundColor Yellow
    $certMod = (& openssl x509 -noout -modulus -in "${CertOut}.cer")
    $keyMod = (& openssl rsa -noout -modulus -in "${CertOut}.key")

    if ([string]::IsNullOrWhiteSpace($certMod) -or [string]::IsNullOrWhiteSpace($keyMod)) {
        Write-Host "[!] Could not generate modulus. Verify both files are valid." -ForegroundColor Red
        return
    }

    if ($certMod -eq $keyMod) {
        Write-Host "[SUCCESS] The Certificate and Private Key match perfectly!" -ForegroundColor Green
    }
    else {
        Write-Host "[FAILED] Mismatch detected! The key does not belong to this certificate." -ForegroundColor Red
    }
}

function Display-Base64 {
    if (-not (Test-Path "${CertOut}.cer")) {
        Write-Host "`n[!] Error: Please extract the .cer file first." -ForegroundColor Red
        return
    }

    Write-Host "`n[+] Base64 String for Cloud/K8s Secrets:" -ForegroundColor Yellow
    $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path "${CertOut}.cer").Path)
    [Convert]::ToBase64String($bytes)
}

function Generate-Csr {
    if (-not (Test-Path "${CertOut}.key")) {
        Write-Host "`n[!] Error: Please extract the private key first." -ForegroundColor Red
        return
    }

    Write-Host "`n[+] Generating new CSR..." -ForegroundColor Yellow
    & openssl req -new -key "${CertOut}.key" -out "${CertOut}.csr"
    if ($LASTEXITCODE -eq 0) { Write-Host "[SUCCESS] CSR generated at: ${CertOut}.csr" -ForegroundColor Green }
}

try {
    while ($true) {
        Write-Host "`nTarget Context: $CertOut" -ForegroundColor Cyan
        Write-Host "------------------------------------------------------"
        Write-Host "Extraction Options:" -ForegroundColor Yellow
        Write-Host "  1) Extract .cer (Public Certificate)"
        Write-Host "  2) Extract .key (Unencrypted Private Key - SECURED)"
        Write-Host "  3) Extract .pem (Cert + Private Key - SECURED)"
        Write-Host "  4) Extract CA Chain (Root/Intermediate certificates)"
        Write-Host "  5) Copy to .p12 format"
        Write-Host "  6) Extract All of the above"
        Write-Host ""
        Write-Host "Advanced Tools:" -ForegroundColor Yellow
        Write-Host "  7) View Expiration Date & SANs (Requires .cer)"
        Write-Host "  8) Verify Cert & Key Match     (Requires .cer & .key)"
        Write-Host "  9) Print Cert as Base64        (Requires .cer)"
        Write-Host " 10) Generate a new CSR          (Requires .key)"
        Write-Host ""
        Write-Host " 11) Exit & Wipe Memory" -ForegroundColor Red

        $choice = Read-Host 'Select an option [1-11]'
        switch ($choice) {
            '1' { Extract-Cer }
            '2' { Extract-Key }
            '3' { Extract-Pem }
            '4' { Extract-CaChain }
            '5' { Copy-P12 }
            '6' { Extract-Cer; Extract-Key; Extract-Pem; Extract-CaChain }
            '7' { View-CertInfo }
            '8' { Verify-Match }
            '9' { Display-Base64 }
            '10' { Generate-Csr }
            '11' {
                Write-Host "`nExiting. Have a great day!" -ForegroundColor Green
                exit 0
            }
            default { Write-Host "`n[!] Invalid choice. Please try again." -ForegroundColor Red }
        }
    }
}
finally {
    # Ensure memory is wiped even if the user forces exit (Ctrl+C)
    Remove-Item env:CERT_PASS -ErrorAction SilentlyContinue
}