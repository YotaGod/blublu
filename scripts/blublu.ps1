<#
.SYNOPSIS
    blublu CLI entrypoint wrapper for Windows PowerShell
#>
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonBin = (Get-Command python, python3 -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $PythonBin) {
    $PythonBin = "python"
}
& $PythonBin "$ScriptDir\blublu.py" @args
exit $LASTEXITCODE
