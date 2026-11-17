# Slice every plate in plates/ with PrusaSlicer's stock CORE One HF0.4 presets (not the user copies).
#   .\slice_plates.ps1
# Writes gcode/<plate>.gcode (plain text, runs on the CORE One) and gcode/<plate>.3mf (open it in PrusaSlicer to look first).
# Extras: supports on the lid only (the X arms float 15 mm over the bed), a 4 mm brim on the plates with rods and cotters.
param([string]$Slicer = 'C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe')

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $here 'gcode'
New-Item -ItemType Directory -Force $out | Out-Null

$base = @('--printer-profile', 'Prusa CORE One HF0.4 nozzle',
          '--print-profile', '0.20mm BALANCED @COREONE HF0.4',
          '--material-profile', 'Prusament PLA @COREONE HF0.4',
          '--center', '125,110')
$extra = @{
    plate1_frame = @('--brim-width', '4')
    plate3_walls = @('--brim-width', '4')
    plate4_lid   = @('--support-material', '--support-material-auto', '--support-material-buildplate-only', '--support-material-style', 'organic')
}

foreach ($stl in Get-ChildItem (Join-Path $here 'plates') -Filter *.stl) {
    $name = $stl.BaseName
    $opts = if ($extra.ContainsKey($name)) { $extra[$name] } else { @() }
    & $Slicer @base @opts --export-gcode --no-binary-gcode --output (Join-Path $out "$name.gcode") $stl.FullName | Out-Null
    & $Slicer @base @opts --export-3mf --output (Join-Path $out "$name.3mf") $stl.FullName | Out-Null
    $g = Get-Content (Join-Path $out "$name.gcode") -Tail 400
    $time = ($g | Select-String 'estimated printing time \(normal mode\) = (.+)').Matches.Groups[1].Value
    $grams = ($g | Select-String '^; total filament used \[g\] = (.+)').Matches.Groups[1].Value
    '{0,-22} {1,-14} {2} g' -f $name, $time, $grams
}
