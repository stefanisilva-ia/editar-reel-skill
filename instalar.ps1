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
# Atualiza os arquivos e mantém a .venv, o seu estilo-padrao.json e as receitas que você criou.
$EstiloArq = Join-Path $Destino 'estilo-padrao.json'
$Guardado = $null
if (Test-Path $EstiloArq) { $Guardado = Get-Content -Raw $EstiloArq }
$PastaReceitas = Join-Path $Destino 'estilos'
$Receitas = $null
if (Test-Path $PastaReceitas) {
    $Receitas = Join-Path ([System.IO.Path]::GetTempPath()) ('receitas-' + [guid]::NewGuid())
    Copy-Item -Recurse -Force $PastaReceitas $Receitas
}
Get-ChildItem -Force $Destino | Where-Object { $_.Name -ne '.venv' } | Remove-Item -Recurse -Force
Copy-Item -Recurse -Force (Join-Path $Origem '*') $Destino
if ($Guardado) { Set-Content -NoNewline -Encoding UTF8 -Path $EstiloArq -Value $Guardado; Write-Host 'Mantive o seu estilo-padrao.json.' }
if ($Receitas) {
    Get-ChildItem $Receitas | ForEach-Object {
        $Alvo = Join-Path $PastaReceitas $_.Name
        if (-not (Test-Path $Alvo)) { Copy-Item $_.FullName $Alvo; Write-Host "Mantive a sua receita $($_.Name)." }
    }
    Remove-Item -Recurse -Force $Receitas
}

$VenvPy = Join-Path $Destino '.venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) { & $Py -m venv (Join-Path $Destino '.venv') }
& $VenvPy -m pip install --quiet --upgrade pip
& $VenvPy -m pip install --quiet -r (Join-Path $Destino 'requirements.txt')

& $VenvPy (Join-Path $Destino 'motor\cli.py') checar
Write-Host ''
Write-Host 'Pronto. No Claude Code, chame /editar-reel'
