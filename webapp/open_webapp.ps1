$uri = "http://127.0.0.1:8123/"
$pythonExe = (Get-Command python -ErrorAction Stop).Source

function Test-WebAppServer {
    param([string]$TargetUri)

    try {
        Invoke-WebRequest -UseBasicParsing $TargetUri -TimeoutSec 2 | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

if (-not (Test-WebAppServer -TargetUri $uri)) {
    Start-Process -WindowStyle Hidden -FilePath $pythonExe -ArgumentList ".\\server.py" -WorkingDirectory $PSScriptRoot | Out-Null
    Start-Sleep -Seconds 2
}

Start-Process $uri
