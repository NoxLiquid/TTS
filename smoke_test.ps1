param(
    [string]$BaseUrl = "http://127.0.0.1:5000",
    [string]$Speaker = "ru_eduard",
    [string]$Text = "Привет, это проверка синтеза речи Respiral.",
    [string]$ApiToken = ""
)

$ErrorActionPreference = "Stop"

Write-Host "== GET $BaseUrl/health =="
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
$health | ConvertTo-Json -Compress | Write-Host

Write-Host "== POST $BaseUrl/tts =="
$payload = @{
    api_token   = $ApiToken
    text        = $Text
    speaker     = $Speaker
    ssml        = $false
    put_accent  = $true
    put_yo      = $false
    sample_rate = 24000
    format      = "ogg"
}
$json = $payload | ConvertTo-Json -Compress
$bytesBody = [System.Text.Encoding]::UTF8.GetBytes($json)

$resp = Invoke-RestMethod -Uri "$BaseUrl/tts" -Method Post -Body $bytesBody -ContentType "application/json; charset=utf-8"
if (-not $resp.results -or $resp.results.Count -eq 0) { throw "empty results" }

$audio = [Convert]::FromBase64String($resp.results[0].audio)
$magic = [System.Text.Encoding]::ASCII.GetString($audio[0..3])
Write-Host ("audio bytes: {0}, magic: '{1}', sha1: {2}" -f $audio.Length, $magic, $resp.original_sha1)

$outFile = Join-Path $PSScriptRoot "sample.ogg"
[IO.File]::WriteAllBytes($outFile, $audio)
Write-Host "saved: $outFile"

if ($magic -ne "OggS") { throw "not a valid OGG stream (magic='$magic')" }
Write-Host "OK: valid OGG produced."
