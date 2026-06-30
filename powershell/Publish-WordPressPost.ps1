param(
    [Parameter(Mandatory=$true)]
    [string]$Title,
    
    [Parameter(Mandatory=$true)]
    [string]$Content
)

$wpUrl = $env:WP_URL
$wpUser = $env:WP_USERNAME
$wpPass = $env:WP_APP_PASSWORD

if (-not $wpUrl -or -not $wpUser -or -not $wpPass) {
    Write-Error "Missing required environment variables: WP_URL, WP_USERNAME, WP_APP_PASSWORD."
    exit 1
}

# Ensure URL doesn't have trailing slash for consistency
$wpUrl = $wpUrl.TrimEnd('/')

$apiUrl = "$wpUrl/wp-json/wp/v2/posts"
$authString = "$($wpUser):$($wpPass)"
$authBytes = [System.Text.Encoding]::UTF8.GetBytes($authString)
$authBase64 = [System.Convert]::ToBase64String($authBytes)

$headers = @{
    "Authorization" = "Basic $authBase64"
    "Content-Type"  = "application/json"
}

$body = @{
    title   = $Title
    content = $Content
    status  = "draft"
} | ConvertTo-Json -Depth 5

try {
    Write-Host "Creating WordPress post '$Title'..."
    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers $headers -Body $body
    Write-Host "Post created successfully!"
    Write-Host "ID: $($response.id)"
    Write-Host "Link: $($response.link)"
} catch {
    Write-Error "Failed to create post. Error: $_"
}
