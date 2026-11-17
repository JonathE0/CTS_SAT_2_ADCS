# Slice Flywheel_D100.stl with PrusaSlicer's stock CORE One HF0.4 presets (same as rev 2's slice_plates.ps1).
#   .\slice_flywheel.ps1
# Writes ../../printing/print_ready/gcode/Flywheel_D100.gcode (plain text) and 3mf/Flywheel_D100.3mf. No supports, no brim:
# the wheel prints z = 0 face down.
param([string]$Slicer = 'C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe')

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $here '..\..\printing\print_ready'
New-Item -ItemType Directory -Force (Join-Path $out 'gcode'), (Join-Path $out '3mf') | Out-Null
$out = (Resolve-Path $out).Path
$stl = Join-Path $here 'Flywheel_D100.stl'

$base = @('--printer-profile', 'Prusa CORE One HF0.4 nozzle',
          '--print-profile', '0.20mm BALANCED @COREONE HF0.4',
          '--material-profile', 'Prusament PLA @COREONE HF0.4',
          '--center', '125,110')

& $Slicer @base --export-gcode --no-binary-gcode --output (Join-Path $out 'gcode\Flywheel_D100.gcode') $stl | Out-Null
& $Slicer @base --export-3mf --output (Join-Path $out '3mf\Flywheel_D100.3mf') $stl | Out-Null

$g = Get-Content (Join-Path $out 'gcode\Flywheel_D100.gcode') -Tail 400
$time = ($g | Select-String 'estimated printing time \(normal mode\) = (.+)').Matches.Groups[1].Value
$grams = ($g | Select-String '^; total filament used \[g\] = (.+)').Matches.Groups[1].Value
'Flywheel_D100   {0}   {1} g' -f $time, $grams
