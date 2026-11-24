param([string]$Compiler = 'C:/msys64/ucrt64/bin/g++.exe')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputDirectory = Join-Path $projectRoot '.pio/host-tests'
if (-not (Get-Command $Compiler -ErrorAction SilentlyContinue)) {
    throw 'Host tests require g++. Pass its path with -Compiler.'
}
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
$compilerPath = (Get-Command $Compiler).Source
$env:PATH = "$(Split-Path -Parent $compilerPath);$env:PATH"
foreach ($source in Get-ChildItem -LiteralPath (Join-Path $projectRoot 'test/host') -Filter '*.cpp') {
    $executable = Join-Path $outputDirectory ($source.BaseName + '.exe')
    & $Compiler -std=c++17 -Wall -Wextra -Werror -static "-I$projectRoot/include" `
        $source.FullName -o $executable
    if ($LASTEXITCODE -ne 0) { throw "Test compilation failed for $($source.Name) ($LASTEXITCODE)." }
    & $executable
    if ($LASTEXITCODE -ne 0) { throw "Host tests failed for $($source.Name) ($LASTEXITCODE)." }
}
