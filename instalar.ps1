# Instala a skill editar-reel no Claude Code (Windows).
$ErrorActionPreference = 'Stop'

$Origem = Join-Path $PSScriptRoot 'editar-reel'
$Destino = Join-Path $HOME '.claude\skills\editar-reel'

Write-Host "Instalando editar-reel em $Destino"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host 'Falta o ffmpeg. Instale com: winget install Gyan.FFmpeg (depois feche e abra o terminal)'
    exit 1
}

$Py = $null
foreach ($c in @('py', 'python')) {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        & $c -c 'import sys; assert sys.version_info >= (3,9)' 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $c; break }
    }
}
if (-not $Py) {
    Write-Host 'Falta Python 3.9 ou mais novo. Instale com: winget install Python.Python.3.12'
    exit 1
}

New-Item -ItemType Directory -Force -Path $Destino | Out-Null
# Atualiza os arquivos e mantém a .venv que já existir.
Get-ChildItem -Force $Destino | Where-Object { $_.Name -ne '.venv' } | Remove-Item -Recurse -Force
Copy-Item -Recurse -Force (Join-Path $Origem '*') $Destino

$VenvPy = Join-Path $Destino '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) { & $Py -m venv (Join-Path $Destino '.venv') }
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet -r (Join-Path $Destino 'requirements.txt')

& $VenvPy (Join-Path $Destino 'motor\cli.py') checar
Write-Host ''
Write-Host 'Pronto. No Claude Code, chame /editar-reel'
