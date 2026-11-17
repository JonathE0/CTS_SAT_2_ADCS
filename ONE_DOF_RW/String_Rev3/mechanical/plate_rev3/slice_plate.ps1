# Slice every new or changed rev 3 part on one CORE One build plate (stock PrusaSlicer presets, same as slice_flywheel.ps1).
#   python make_plate.py ; .\slice_plate.ps1
# make_plate.py has already laid the parts out on the 250 x 220 bed in Rev3_plate.stl (PrusaSlicer's --merge arranger crashes on this set). Auto supports only where an overhang is shallower than 35 degrees from
# horizontal, so the 45 degree thread flanks and fillets stay clean while the basket's lips and the slider's gap get supported.
param([string]$Slicer = 'C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe')

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$out = Join-Path $here '..\..\printing\print_ready'
New-Item -ItemType Directory -Force (Join-Path $out 'gcode'), (Join-Path $out '3mf') | Out-Null
$out = (Resolve-Path $out).Path
$stl = Join-Path $out 'stl\Rev3_plate.stl'

$base = @('--printer-profile', 'Prusa CORE One HF0.4 nozzle',
          '--print-profile', '0.20mm BALANCED @COREONE HF0.4',
          '--material-profile', 'Prusament PLA @COREONE HF0.4',
          '--support-material', '--support-material-auto', '--support-material-threshold', '35', '--center', '125,110')

& $Slicer @base --export-gcode --no-binary-gcode --output (Join-Path $out 'gcode\Rev3_all_parts.gcode') $stl | Out-Null
& $Slicer @base --export-3mf --output (Join-Path $out '3mf\Rev3_all_parts.3mf') $stl | Out-Null

$g = Get-Content (Join-Path $out 'gcode\Rev3_all_parts.gcode') -Tail 400
$time = ($g | Select-String 'estimated printing time \(normal mode\) = (.+)').Matches.Groups[1].Value
$grams = ($g | Select-String '^; total filament used \[g\] = (.+)').Matches.Groups[1].Value
'Rev3_all_parts   {0}   {1} g' -f $time, $grams
