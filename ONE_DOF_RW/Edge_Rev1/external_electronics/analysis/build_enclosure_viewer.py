"""Build only the existing external enclosure viewer. Never writes testbench,
wiring or original Edge assets. Reuses Jonathan's layout CSS and CAD mesh format.
"""
import base64
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[2]
VIEW=REPO/'CTS_Simple_Visulizers'/'External Electronics Enclosure'
sys.path.insert(0,str(ROOT/'mechanical'))
import make_housing as h
import assembly_parts
import fasteners


def steps(p):
    return [
      dict(title='Modular kit',short='Kit / exploded',text='Four printed parts: common tray, ESP32 mount, driver mount and carrier retaining frame. Both electronics mounts are assembled off the case.',fact='Candidate CAD only. Print the retention coupon, carrier coupon and driver coupon before a full enclosure.'),
      dict(title='Prepare the common base',short='Base, feet and cable ties',text='Deburr the tray and fit insulating feet. Fit cable ties before the modules; keep the underside nuts and service openings accessible.',fact=f'Case {p.length:g} × {p.width:g} × {p.height:g} mm. Feet Ø{2*p.foot_radius:g} × {p.foot_height_allowance:g} are unmeasured allowances, positioned clear of tie slots and nuts.'),
      dict(title='Prepare the ESP32 module',short='Side-load nuts and place carrier',text='Support the ESP mount outside the case. Slide one M2.5 nut into each outward-facing side port, beneath the solid roofs. Lower the prepared socket carrier onto its four landing posts.',fact=f'Nut wells AF{p.nut_pocket_flats:g}, entry width{p.nut_entry_width:g}; each roof is {h.frame_bottom(p)-h.nut_roof(p):g} mm thick. Short bridge print quality must be checked on the coupon.'),
      dict(title='Close the carrier retaining frame',short='Frame and independent screws',text='Lower the frame and fit its two M2.5 screws. The frame seats on printed hard-stop columns. It captures the carrier edge strips with deliberate play; it does not intentionally compress the PCB.',fact=f'Frame screws M2.5 × {p.frame_screw_length:g}; carrier capture gap {p.carrier_capture_gap:g} mm nominal. Side-loaded nuts bear against the solid roof, giving a positive load path into the mount.'),
      dict(title='Seat the ESP32',short='ESP32 into sockets',text='Seat the ESP32 evenly into the measured socket arrangement, USB facing left. Keep BOOT/EN, GPIO and antenna areas clear. Check actual plug insertion and socket retention.',fact=f'Overall board envelope {p.esp_length:g} × {p.esp_width:g}, socket spacing {p.socket_row_spacing:g} and socket origin remain provisional. No ESP32 holes are assumed.'),
      dict(title='Prepare the driver module',short='Driver and four insulating M2 bolts',text='Support the driver mount off the case. Place the PCB on four posts, insert four insulating M2 screws and fit four insulating nuts from below while access is unrestricted.',fact=f'M2 × {p.driver_screw_length:g}, additional stock. Reference Ø{p.driver_hole_diameter:g} holes on {p.driver_hole_pitch_x:g} × {p.driver_hole_pitch_y:g}; delivered board unconfirmed. Never use M2.5 through the PCB.'),
      dict(title='Install complete modules',short='Lift, align and lower modules',text='Lift each completed module above the rim, translate over its bay, then lower onto the common locating pins and bearing pads. Electronics remain secured to their modules throughout this move.',fact=f'Both bays use a {2*p.interface_half_x:g} × {2*p.interface_half_y:g} diagonal two-hole interface and z{p.mount_bottom:g} seating plane. Outlines differ; replacement mounts must stay within bay and service-window limits.'),
      dict(title='Fasten modules to the base',short='Two screws per removable module',text='Insert two M2.5 screws per mount and hold their ordinary underside nuts with a wrench. ESP frame access notches admit the module screw heads and tools without dismantling its electronics.',fact=f'Four M2.5 × {p.module_screw_length:g} base screws. Remove only those two screws to lift either complete module. Frame screws remain installed in its captive nuts.'),
      dict(title='Complete stationary enclosure',short='Complete assembly',text='Inspect insulation, cable restraint, carrier play, feet and socket seating before powered tests. Check temperatures under the intended bench load. This enclosure stays separate from the balancing cube.',fact='Four production prints; six M2.5 screws/nuts and four insulating M2 screws/nuts. No washers or bought spacers in the nominal stack. Physical fit, strength and thermal behavior remain unverified.'),
    ]


def keys_for(group,p):
    if group=='fixed':return [(0,[0,0,0]),(8,[0,0,0])]
    if group=='feet':return [(0,[0,0,-9]),(1,[0,0,0]),(8,[0,0,0])]
    if group=='module_nuts':return [(0,[0,-30,-10]),(6,[0,-30,-10]),(6.3,[0,0,-10]),(6.6,[0,0,0]),(8,[0,0,0])]
    if group=='module_bolts':return [(0,[0,0,110]),(6.6,[0,0,110]),(7,[0,0,0]),(8,[0,0,0])]
    side='driver' if group.startswith('driver') else 'esp';work=np.array([70.,0,0]) if side=='driver' else np.array([-110.,0,0])
    local={
      'esp_mount':[(0,[0,0,0]),(5,[0,0,0])],
      'driver_mount':[(0,[0,0,0]),(5,[0,0,0])],
      'carrier':[(0,[0,0,55]),(1,[0,0,55]),(2,[0,0,0]),(5,[0,0,0])],
      'retainer':[(0,[0,0,85]),(2,[0,0,85]),(2.6,[0,0,0]),(5,[0,0,0])],
      'frame_bolts':[(0,[0,0,110]),(2.6,[0,0,110]),(3,[0,0,0]),(5,[0,0,0])],
      'frame_nut_front':[(0,[0,-12,-.3]),(1,[0,-12,-.3]),(1.6,[0,0,-.3]),(2.6,[0,0,-.3]),(3,[0,0,0]),(5,[0,0,0])],
      'frame_nut_rear':[(0,[0,12,-.3]),(1,[0,12,-.3]),(1.6,[0,0,-.3]),(2.6,[0,0,-.3]),(3,[0,0,0]),(5,[0,0,0])],
      'esp':[(0,[0,0,130]),(3,[0,0,130]),(4,[0,0,0]),(5,[0,0,0])],
      'driver':[(0,[0,0,65]),(4,[0,0,65]),(4.5,[0,0,0]),(5,[0,0,0])],
      'driver_bolts':[(0,[0,0,110]),(4.5,[0,0,110]),(4.8,[0,0,0]),(5,[0,0,0])],
      'driver_nuts':[(0,[0,0,-15]),(4.8,[0,0,-15]),(5,[0,0,0])],
    }[group]
    if group.startswith('frame_nut'):
        local=[(t,[v[0],v[1],-p.nut_pocket_axial_clearance if v[2]<0 else v[2]]) for t,v in local]
    result=[(t,(work+np.asarray(offset)).tolist()) for t,offset in local]
    result += [(5.25,(work+[0,0,45]).tolist()),(5.65,[0,0,45]),(6,[0,0,0]),(8,[0,0,0])]
    return result


def build_scene(p=h.Parameters()):
    models=assembly_parts.components(p);hardware=fasteners.groups(p);parts=[]
    def add(key,model,quantity,group):
        tri=h.triangles(model['solid'])+np.array([0,0,p.foot_height_allowance]);xyz=tri.reshape(-1,3)
        size=xyz.max(0)-xyz.min(0);motion=keys_for(group,p)
        parts.append(dict(id=key,name=model['name'],kind=model['kind'],note=model['note'],quantity=quantity,
          color=model.get('color','#9aa7ab'),positions_b64=base64.b64encode(tri.astype('<f4').tobytes()).decode(),
          bounds=[*xyz.min(0).tolist(),*xyz.max(0).tolist()],dimensions=(f'Ø{2*p.foot_radius:g} × {p.foot_height_allowance:g} mm each (allowance)' if key=='feet' else
            f'Each row {p.socket_row_length:g} × {p.socket_body_width:g}; height{p.socket_height:g}; spacing{p.socket_row_spacing:g}' if key=='sockets' else
            ' × '.join(f'{v:g}' for v in size)+' mm group bounds'),
          group='electronics',visible=True,stage_group=group,keyframes=[dict(time=t,offset=v) for t,v in motion],explode=motion[0][1],stage=0))
    for key,qty,group in [('tray',1,'fixed'),('feet',4,'feet'),('esp_mount',1,'esp_mount'),('driver_mount',1,'driver_mount'),
       ('retainer',1,'retainer'),('carrier',1,'carrier'),('sockets',2,'carrier'),('carrier_tails',0,'carrier'),
       ('esp',1,'esp'),('esp_details',0,'esp'),('driver',1,'driver'),('driver_details',0,'driver')]:add(key,models[key],qty,group)
    for key,model in hardware.items():add(key,model,model['quantity'],model['stage_group'])
    return dict(title='External Electronics Enclosure Assembly',mode='enclosure',units='mm',parts=parts,wires=[],steps=steps(p),
       fastener_stacks=fasteners.stacks(p),parameters=h.asdict(p),
       notice='Modular preliminary CAD: four production prints, ten screws. Print fit coupons first. Boards, sockets, hardware, print tolerances and strength remain physically unverified.',
       original_viewer_reference='CTS_Simple_Visulizers/Edge Cube Assembly/',
       assembly_note='Preassemble electronics off case. Complete modules move rigidly above the rim before lowering; separate base screws release either complete mount.')


def html(style,p):
    page='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>External Electronics Enclosure Assembly</title><style>'''+style+'''
body{margin:0}.page{max-width:1350px}.grid{grid-template-columns:minmax(0,1.9fr) minmax(320px,1fr)}
.right .parts{max-height:410px;overflow:auto}.viewbox #labels{position:absolute;inset:0;pointer-events:none;overflow:hidden}.part-label{position:absolute;font-size:10px;background:var(--panel);border:1px solid var(--line);padding:2px 5px;border-radius:3px;transform:translate(-50%,-110%);white-space:nowrap}.notice{border-left:3px solid var(--warn);padding:9px 12px;background:var(--soft);font-size:13px}.part-info{font-size:13px;margin-top:8px;color:var(--muted)}.dimensions{width:100%;border-collapse:collapse;font-size:13px}.dimensions td{padding:5px 0;border-bottom:1px solid var(--line)}.dimensions td:last-child{text-align:right}.parts .pname{padding:0;border:0;background:transparent;text-align:left}.part-list-heading{display:flex;justify-content:space-between}.foot a{color:var(--accent)}#view{height:590px}.scrub input{height:24px}@media(max-width:880px){.grid{grid-template-columns:1fr}#view{height:420px}.right .parts{max-height:none}}@media(max-width:520px){.opts button{padding:5px 9px}.buttons button{padding:6px 10px}}
</style></head><body><main class="page"><header><h1>External Electronics Enclosure Assembly</h1><p class="lede">The stationary housing, built from the CAD that generates its STL files. Follow the replaceable mounts, socket carrier, retaining frame, boards and fasteners from the kit to the finished assembly.</p></header><p class="notice" id="notice"></p>
<section class="grid"><div class="left"><div class="card viewbox"><canvas id="view" aria-label="Interactive exploded housing assembly; drag to orbit, scroll to zoom"></canvas><div id="labels"></div><div class="chips"><span class="chip" id="chipStep"></span><span class="chip" id="chipName"></span></div><p class="hint">drag to orbit · scroll to zoom · click a part</p><div class="nogl" id="nogl" hidden>WebGL is unavailable. Open the static previews linked below.</div></div>
<div class="card transport"><div class="buttons"><button id="bPrev">Previous</button><button id="bPlay" class="primary">Play</button><button id="bNext">Next</button><span class="spacer"></span><button id="bKit">Kit / exploded</button><button id="bDone">Complete assembly</button></div><div class="scrub"><input id="scrub" type="range" min="0" max="8" step="0.01" value="0" aria-label="Assembly progress"><div class="ticks"><span>the kit</span><span>complete assembly</span></div></div><div class="opts"><div class="group"><span>View</span><button id="vIso">Three-quarter</button><button id="vTop">Top</button><button id="vSide">Side</button><button id="vEnd">End</button><button id="vReset">Reset</button></div><label><input id="oCut" type="checkbox">Section cut</label><label><input id="oEdge" type="checkbox" checked>Outlines</label><label><input id="oLabels" type="checkbox">Labels</label></div></div>
<section class="card"><h2>Dimensions and mounting</h2><table class="dimensions"><tbody><tr><td>Open-top enclosure</td><td>125 × 90 × 35 mm</td></tr><tr><td>Printed production parts</td><td>4; two replaceable mounts</td></tr><tr><td>M2.5 fasteners</td><td>6 × M2.5 × 10 mm</td></tr><tr><td>Driver fasteners</td><td>4 × insulating M2 × 12 mm</td></tr><tr><td>Nuts / washers / bought spacers</td><td>10 / 0 / 0</td></tr><tr><td>Carrier capture</td><td>0.4 mm nominal play; hard stops</td></tr></tbody></table><p class="part-info">M2.5 heads modeled within Ø5.5 × 3 mm; kit head shape and actual bearing areas unconfirmed. Never pass M2.5 through the driver's reference Ø2 holes.</p></section></div>
<div class="right"><section class="card step" aria-live="polite"><div class="no" id="stepNo"></div><h3 id="stepTitle"></h3><p class="text" id="stepText"></p><p class="fact" id="stepFact"></p></section><section class="card"><h2>Steps</h2><ol class="steplist" id="steps"></ol></section><section class="card"><div class="part-list-heading"><h2>Parts</h2><span class="foot">quantity</span></div><ul class="parts" id="parts"></ul><p class="foot">Untick to inspect behind a part. Select its name for mounting details.</p><p id="partInfo" class="part-info">Tray, ESP mount, driver mount and retaining frame are printed. Fit coupons are separate test pieces. Boards, carrier, sockets and fasteners are bought/prepared items.</p></section></div></section>
<p class="foot">The base stays stationary. Steps show off-case board assembly and independent removal of complete modules. Geometric retention is checked; material strength and print quality are not. Physical fit, thread quality, USB retention and actual electronics dimensions require measurement. No other project viewer or firmware is changed.</p><p class="foot"><a href="README.md">Viewer instructions</a> · <a href="../../ONE_DOF_RW/Edge_Rev1/external_electronics/PARTS.md">Complete parts and screw stacks</a> · <a href="preview/exploded.png">Exploded preview</a> · <a href="preview/assembled.png">Assembled preview</a></p></main><script src="vendor/three.min.js"></script><script src="assembly-viewer.js"></script></body></html>'''

    return (page.replace('125 × 90 × 35 mm',f'{p.length:g} × {p.width:g} × {p.height:g} mm')
        .replace('6 × M2.5 × 10 mm',f'4 × M2.5 × {p.module_screw_length:g}; 2 × {p.frame_screw_length:g} mm')
        .replace('4 × insulating M2 × 12 mm',f'4 × insulating M2 × {p.driver_screw_length:g} mm')
        .replace('0.4 mm nominal play',f'{p.carrier_capture_gap:g} mm nominal play')
        .replace('Ø5.5 × 3 mm',f'Ø{p.m25_head_diameter:g} × {p.m25_head_height:g} mm'))


def standalone(page,scene,target):
    # Generated distribution only: no new runtime dependency or second source.
    escaped_close='<'+chr(92)+'/'
    payload=json.dumps(scene,separators=(',',':')).replace('</',escaped_close)
    license_text=(VIEW/'vendor/THREE-LICENSE.txt').read_text()
    three=(VIEW/'vendor/three.min.js').read_text().replace('</script',escaped_close+'script')
    runtime=(VIEW/'assembly-viewer.js').read_text().replace('</script',escaped_close+'script')
    scripts='<!-- Three.js license: '+license_text.replace('--','—')+' -->'+ '<script>'+three+'</script>'
    scripts+='<script id="cad-scene" type="application/json">'+payload+'</script><script>'+runtime+'</script>'
    page=page.replace('<script src="vendor/three.min.js"></script><script src="assembly-viewer.js"></script>',scripts)
    # Repository-relative document/PNG links are not part of a standalone file.
    a=page.index('<p class="foot"><a href="README.md">');b=page.index('</p>',a)+4
    page=page[:a]+'<p class="foot">Standalone CAD review. Full manufacturing checklist is maintained in the repository PARTS.md. Physical fit and strength are unverified.</p>'+page[b:]
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(page)
    print('Standalone offline review export:',target)


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parameters',type=Path)
    parser.add_argument('--standalone',type=Path,help='Optional generated all-in-one HTML distribution outside source files')
    args=parser.parse_args();p=h.Parameters(**json.loads(args.parameters.read_text())) if args.parameters else h.Parameters()
    h.generate(ROOT,p);scene=build_scene(p)
    template=REPO/'ONE_DOF_RW/Edge_Rev1/analysis/assembly_template.html';source=template.read_text()
    style=source.split('<style>',1)[1].split('</style>',1)[0]
    scene['style_source_sha256']=hashlib.sha256(template.read_bytes()).hexdigest();raw=json.dumps(scene,separators=(',',':'))
    page=html(style,p)
    (VIEW/'scene.json').write_text(raw+'\n');(VIEW/'index.html').write_text(page)
    if args.standalone:standalone(page,scene,args.standalone)
    print('Built housing only:',len(scene['parts']),'part groups,',len(scene['steps']),'stages')


if __name__=='__main__':main()
