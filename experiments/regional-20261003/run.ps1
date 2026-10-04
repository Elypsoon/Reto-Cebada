param(
    [ValidateSet('freeze','robust','verify','app')][string]$Command = 'verify',
    [string]$ArtifactDirectory = 'artifacts',
    [switch]$OfficialOnly
)
$experimentRoot = $PSScriptRoot
$workspaceInfo = Get-Content -LiteralPath (Join-Path $experimentRoot 'workspace.json') -Raw | ConvertFrom-Json
$runtimePath = Join-Path $workspaceInfo.active_root '.venv/Scripts/python.exe'
$previousPythonPath = $env:PYTHONPATH
$previousArtifactPath = $env:AGROCEBADA_ARTIFACTS
try {
    $env:PYTHONPATH = Join-Path $experimentRoot 'src'
    $destination = [IO.Path]::GetFullPath((Join-Path $experimentRoot $ArtifactDirectory))
    if (-not $destination.StartsWith($experimentRoot + [IO.Path]::DirectorySeparatorChar)) { throw 'Destino fuera de la versión experimental' }
    $env:AGROCEBADA_ARTIFACTS = $destination
    if ($Command -eq 'app') { & $runtimePath -m streamlit run (Join-Path $experimentRoot 'app.py') }
    else {
        $arguments = @('-m','agrocebada.cli',$Command,'--artifact-dir',$destination)
        if ($OfficialOnly) { $arguments += '--official-only' }
        & $runtimePath @arguments
    }
    if ($LASTEXITCODE -ne 0) { throw "La ejecución terminó con código $LASTEXITCODE" }
} finally {
    $env:PYTHONPATH = $previousPythonPath
    $env:AGROCEBADA_ARTIFACTS = $previousArtifactPath
}
