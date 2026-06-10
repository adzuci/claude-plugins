Write-Output "== Apollo CLI smoke check =="

$apolloCommand = Get-Command apollo -ErrorAction SilentlyContinue

if (-not $apolloCommand) {
  Write-Output "STATUS: MISSING"
  Write-Output "apollo command not found. Install the native Apollo CLI from the official Apollo-provided source before continuing."
  exit 1
}

Write-Output "STATUS: FOUND"

try {
  $version = apollo --version 2>$null
  if (-not $version) {
    $version = "UNKNOWN"
  }
  Write-Output "VERSION: $version"
}
catch {
  Write-Output "VERSION: UNKNOWN"
}

Write-Output ""
Write-Output "== Root help =="
apollo --help | Out-Null
Write-Output "PASS: apollo --help"

Write-Output ""
Write-Output "== Auth =="
$authOutput = apollo auth whoami 2>&1
if ($LASTEXITCODE -eq 0) {
  Write-Output "PASS: auth whoami"
}
else {
  $authOutput
  Write-Output "STATUS: AUTH_REQUIRED"
  Write-Output "Run apollo auth login in the approved assistant environment."
  exit 2
}

Write-Output ""
Write-Output "== Safe command help checks =="
$commands = @(
  "users profile",
  "usage credits",
  "email-accounts list",
  "people search",
  "companies search",
  "contacts search",
  "sequences search",
  "tasks search",
  "analytics report"
)

foreach ($cmd in $commands) {
  $parts = $cmd.Split(" ")
  & apollo @parts --help | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Output "FAIL: apollo $cmd --help"
    exit 3
  }
  Write-Output "PASS: apollo $cmd --help"
}

Write-Output ""
Write-Output "RESULT: READY_FOR_READ_ONLY_TEST"
