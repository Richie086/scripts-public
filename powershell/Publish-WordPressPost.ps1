param(
    [Parameter(Mandatory=$true)]
    [string]$Title,
    
    [Parameter(Mandatory=$true)]
    [string]$Content,
    
    [Parameter(Mandatory=$false)]
    [string]$Status = "private",
    
    [Parameter(Mandatory=$false)]
    [string]$PostId = ""
)

$webhookUrl = $env:WP_WEBHOOK_URL
if ($PostId -ne "") {
    $webhookUrl = $env:WP_UPDATE_WEBHOOK_URL
}

if (-not $webhookUrl -or $webhookUrl -eq "paste_your_uncanny_webhook_url_here") {
    Write-Error "Missing or invalid required environment variable for webhook URL."
    exit 1
}

# Format content as a Gutenberg shortcode block if it is a raw shortcode
if ($Content.Trim().StartsWith("[") -and $Content.Trim().EndsWith("]")) {
    $Content = "<!-- wp:shortcode -->`n$Content`n<!-- /wp:shortcode -->"
}

$headers = @{
    "Content-Type"  = "application/json"
    "User-Agent"    = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

$separator = if ($webhookUrl -match '\?') { '&' } else { '?' }
$fullUrl = "$webhookUrl${separator}title=$([uri]::EscapeDataString($Title))&content=$([uri]::EscapeDataString($Content))&status=$([uri]::EscapeDataString($Status))"

if ($PostId -ne "") {
    $fullUrl += "&post_id=$([uri]::EscapeDataString($PostId))"
}

try {
    Write-Host "Triggering WordPress Webhook for post '$Title'..."
    $response = Invoke-RestMethod -Uri $fullUrl -Method Get -Headers $headers
    Write-Host "Webhook triggered successfully!"
    Write-Host "Response: $($response | ConvertTo-Json -Compress)"
} catch {
    Write-Error "Failed to trigger webhook. Error: $_"
}
