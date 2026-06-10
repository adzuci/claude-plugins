Write-Output "== Apollo CLI bootstrap =="

$apolloCommand = Get-Command apollo -ErrorAction SilentlyContinue

if (-not $apolloCommand) {
  Write-Output "STATUS: MISSING"
  $userBin = "$env:USERPROFILE\bin"
  New-Item -ItemType Directory -Force $userBin | Out-Null

  Write-Output "STATUS: INSTALLING_BINARY"
  Invoke-WebRequest `
    -Uri "https://github.com/apolloio/apollo-io-cli/releases/latest/download/apollo-windows-x64.exe" `
    -OutFile "$userBin\apollo.exe"

  if (($env:Path -split ';') -notcontains $userBin) {
    [Environment]::SetEnvironmentVariable(
      "Path",
      "$userBin;" + [Environment]::GetEnvironmentVariable("Path", "User"),
      "User"
    )
    $env:Path = "$userBin;$env:Path"
  }
}
else {
  Write-Output "STATUS: FOUND"
}

$version = apollo --version 2>$null
if (-not $version) {
  $version = "UNKNOWN"
}
Write-Output "VERSION: $version"

Write-Output ""
Write-Output "== Auth =="
$authOutput = apollo auth whoami 2>&1
if ($LASTEXITCODE -eq 0) {
  Write-Output "PASS: auth whoami"
}
else {
  Write-Output "STATUS: AUTH_REQUIRED"
  apollo auth login
  apollo auth whoami
  if ($LASTEXITCODE -ne 0) {
    Write-Output "STATUS: AUTH_FAILED"
    exit 2
  }
  Write-Output "PASS: auth whoami"
}

Write-Output ""
Write-Output "RESULT: READY_FOR_READ_ONLY_TEST"
