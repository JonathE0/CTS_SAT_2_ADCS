"""Builds the Edge Cube Assembly page: embeds the CAD in ../mechanical/viewer_data.json into assembly_template.html.

    python build_assembly_page.py [artifact_out]

Run ../mechanical/make_cube_parts.py first so viewer_data.json matches the current design. Writes
  ../../../CTS_Simple_Visulizers/Edge Cube Assembly/index.html   a complete HTML document for opening locally (three.js comes from jsDelivr)
  artifact_out (optional)                                     the same page without the document wrapper, for publishing as an Artifact (the publisher adds its own)
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / 'mechanical' / 'viewer_data.json'
OUT = HERE.parent.parent.parent / 'CTS_Simple_Visulizers' / 'Edge Cube Assembly' / 'index.html'

cad = json.loads(DATA.read_text(encoding='utf-8'))
need = {'base', 'cap', 'wheel', 'bolts', 'motor', 'board', 'hw', 'screws', 'imu', 'wires'}
missing = need - set(cad['parts'])
assert not missing, f'viewer_data.json lacks {sorted(missing)}; re-run make_cube_parts.py'
tpl = (HERE / 'assembly_template.html').read_text(encoding='utf-8')
assert tpl.count('/*CAD_JSON*/') == 1 and tpl.count('<main class="page">') == 1
payload = json.dumps(cad, separators=(',', ':')).replace('</', '<\\/')          # nothing in base64 can close the script tag, but be safe
page = tpl.replace('/*CAD_JSON*/', payload)

head, body = page.split('<main class="page">', 1)
wrapped = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n' + head +
           '</head>\n<body>\n<main class="page">' + body.rstrip() + '\n</body>\n</html>\n')
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(wrapped, encoding='utf-8', newline='\n')
print('wrote', OUT, f'{OUT.stat().st_size / 1024:.0f} KB')
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(page, encoding='utf-8', newline='\n')
    print('wrote', sys.argv[1])
