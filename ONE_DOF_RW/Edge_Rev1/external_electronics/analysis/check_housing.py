"""Verify modular candidate meshes, shared coupons, rigid retention and clearances.
Geometric retention does not establish strength, friction, real preload or print fit.
"""
import argparse
from dataclasses import replace
import importlib.util
import itertools
import json
import math
from pathlib import Path
import sys
import manifold3d as m3
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'mechanical'))
import make_housing as h
import assembly_parts
import fasteners
spec=importlib.util.spec_from_file_location('edge_export',ROOT.parent/'mechanical/export_print_ready.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


def require(ok,message):
    if not ok:raise ValueError(message)


def layer_report(name,solid,p):
    oriented=h.print_orientation(solid);worst,bad,z=e.layer_check(oriented)
    if worst<.01 and bad==0:return dict(max_unsupported_layer_mm2=float(worst),short_bridge_layers=0,supports='none indicated by layer probe')
    # The ONLY deliberate bridge is the flat roof of each side-entry nut pocket.
    # Fill those pockets in a control model: every other layer must be supported.
    filled=solid
    for x,y in h.frame_mounts(p):
        plug=h.nut_pocket(p,x,y)^h.cylinder(x,y,p.frame_boss_radius,p.nut_pocket_bottom,h.nut_roof(p))
        # Crop plugs to this piece's XY footprint (coupon pieces are subsets).
        x0,y0,z0,x1,y1,z1=solid.bounding_box()
        plug=plug^h.box(x0,x1,y0,y1,z0,z1)
        plug-=h.cylinder(x,y,p.m25_clearance/2,z0-1,z1+1)
        filled+=plug
    control,control_bad,_=e.layer_check(h.print_orientation(filled))
    require(control<.01 and control_bad==0,name+': unsupported geometry beyond the nut-pocket roof')
    require(bad==1 and abs(z-(h.nut_roof(p)-solid.bounding_box()[2]))<.21,name+': unexpected bridge height/count')
    require(p.nut_entry_width<=6.5,name+': bridge span exceeds this prototype coupon allowance')
    return dict(max_unsupported_layer_mm2=float(worst),short_bridge_layers=int(bad),bridge_span_allowance_mm=p.nut_entry_width,
        bridge_height_from_bed_mm=float(z),filled_pocket_control_mm2=float(control),
        supports='Two short nut-roof bridges (one on retention coupon); print coupon first. Strength/bridge quality unverified.')


def retention_checks(p,parts,models,hardware):
    esp=parts['ESP32_Mount'];frame_group=h.union([parts['Carrier_Retainer'],hardware['frame_bolts']['solid'],
        hardware['frame_nut_front']['solid'],hardware['frame_nut_rear']['solid']])
    probes=[]
    for dz in (.01,.05,.1,.25,.5,1,2,4):
        overlap=(frame_group.translate((0,0,dz))^esp).volume()
        require(overlap>.01,'Assembled frame can withdraw upward with fasteners installed')
        probes.append(dict(withdrawal_mm=dz,interference_mm3=overlap))
    # Repeat inside the shaft-clearance circle: lateral bore play cannot bypass
    # the roof. Sampled intended withdrawal only, not arbitrary contact physics.
    radius=min((p.m25_clearance-p.m25_diameter)/2,(p.nut_pocket_flats-p.m25_nut_flats)/2)*.9
    for angle in np.linspace(0,2*np.pi,16,endpoint=False):
        offset=(radius*np.cos(angle),radius*np.sin(angle),.05)
        require((frame_group.translate((offset[0],offset[1],0))^esp).volume()<1e-5,'Lateral retention probe starts from an invalid pose')
        require((frame_group.translate(offset)^esp).volume()>.01,'Lateral fastener play defeats roof')
    # Regression control: recreate open-top wells. The same loaded fastening
    # group MUST then lift out freely, reproducing the audited defect.
    bad=esp
    for x,y in h.frame_mounts(p):bad-=h.hex_prism(x,y,p.nut_pocket_flats,h.nut_roof(p)-.01,h.frame_bottom(p)+1)
    require(all((frame_group.translate((0,0,float(z)))^bad).volume()<1e-5 for z in np.linspace(.01,20,41)),
        'Open-top pocket defect control did not reproduce withdrawal')
    require((parts['Carrier_Retainer'].translate((0,0,1))^esp).volume()<1e-6,'Frame cannot be removed after fasteners removed')
    for key,(x,y) in zip(('frame_nut_front','frame_nut_rear'),h.frame_mounts(p)):
        nut=hardware[key]['solid'];direction=-1 if y<p.module_centre_y else 1
        for distance in np.linspace(0,12,25):
            require((nut.translate((0,direction*float(distance),0))^esp).volume()<1e-5,'Nut side insertion/removal blocked')
        turned=nut.translate((-x,-y,0)).rotate((0,0,30)).translate((x,y,0))
        require((turned^esp).volume()>.01,'Nut is not prevented from freely rotating')
    # Base retention is a separate fastening loop: ordinary underside nuts
    # bear on the floor, rather than on an open pocket in a removable plate.
    for side,mount_key in [('esp','ESP32_Mount'),('driver','Driver_Mount')]:
        group=h.union([parts[mount_key],hardware[side+'_module_bolts']['solid'],hardware[side+'_module_nuts']['solid']])
        require((group.translate((0,0,.05))^parts['External_Tray']).volume()>.01,side+': installed mount can lift out')
        require((parts[mount_key].translate((0,0,30))^parts['External_Tray']).volume()<1e-5,side+': mount removal blocked after bolts removed')
    # Driver retention has two distinct barriers: heads stop the PCB lifting
    # along the shafts, and underside nuts stop the loaded hardware lifting
    # through the mount. Removing nuts must restore the intended removal path.
    pcb=models['driver']['solid'];bolts=hardware['driver_bolts']['solid']
    nuts=hardware['driver_nuts']['solid'];driver_group=h.union([pcb,bolts,nuts])
    require((driver_group^parts['Driver_Mount']).volume()<1e-5,'Driver retention probe starts from an invalid pose')
    driver_probes=[]
    for dz in (.01,.05,.1,.25,.5):
        head_overlap=(pcb.translate((0,0,dz))^bolts).volume()
        nut_overlap=(driver_group.translate((0,0,dz))^parts['Driver_Mount']).volume()
        require(head_overlap>.01,'Driver PCB can lift past installed screw heads')
        require(nut_overlap>.01,'Driver and installed fasteners can lift out of mount')
        driver_probes.append(dict(withdrawal_mm=dz,head_interference_mm3=head_overlap,nut_interference_mm3=nut_overlap))
    without_nuts=h.union([pcb,bolts])
    require(all((without_nuts.translate((0,0,float(z)))^parts['Driver_Mount']).volume()<1e-5 for z in np.linspace(.01,30,61)),
        'Driver cannot be removed after underside nuts are removed')
    carrier=models['carrier']['solid'];gap=p.carrier_capture_gap
    require((carrier.translate((0,0,gap*.5))^parts['Carrier_Retainer']).volume()<1e-5,'Carrier has unintended preload')
    require((carrier.translate((0,0,gap+.05))^parts['Carrier_Retainer']).volume()>.01,'Carrier can lift past retaining edges')
    minimum_gap=gap-p.carrier_thickness_error-2*p.print_z_error
    require(minimum_gap>0,'Assumed thickness/print error can force carrier preload')
    return dict(frame_withdrawal_probes=probes,lateral_roof_probes=16,open_top_defect_control_detected=True,
        driver_withdrawal_probes=driver_probes,driver_without_nuts_control_detected=True,
        captive_nut_antirotation=True,carrier_capture_gap_mm=gap,minimum_gap_in_assumed_Z_budget_mm=minimum_gap,
        tightening_stop='Frame underside on two printed columns; no intentional carrier/PCB compression',
        limitation='Rigid intended-direction separation tests only; no thread failure, roof strength, plastic creep or real preload validation')


def tail_clearance(p,models):
    cx,cy=h.centre(p,'esp');stops=h.carrier_locators(p);carrier=models['carrier']['solid']
    accepted=0;smallest=float('inf');centered=float('inf');worst_pose=None;smallest_support=float('inf')
    post_sections=[h.cylinder(x,y,p.carrier_post_radius,p.carrier_bottom-.1,p.carrier_bottom+.1).slice(p.carrier_bottom) for x,y in h.carrier_mounts(p)]
    # Search translation and rotation permitted by the ACTUAL locating solids.
    for angle in np.linspace(-1.2,1.2,13):
        radians=math.radians(angle);c,s=math.cos(radians),math.sin(radians)
        for dx in np.linspace(-.6,.6,13):
            for dy in np.linspace(-.6,.6,13):
                moved=carrier.translate((-cx,-cy,0)).rotate((0,0,float(angle))).translate((cx+dx,cy+dy,0))
                if (moved^stops).volume()>1e-6:continue
                accepted+=1
                section=moved.slice(p.carrier_bottom+.01)
                smallest_support=min(smallest_support,*[(section^post).area() for post in post_sections])
                for x,y in h.carrier_mounts(p):
                    # Invert the carrier transform for exact point/rectangle XY
                    # distance; using a circle for the polygon post is conservative.
                    vx,vy=x-cx-dx,y-cy-dy
                    px=c*vx+s*vy-p.socket_origin_x_offset;py=-s*vx+c*vy-p.socket_origin_y_offset
                    for sign in (-1,1):
                        lo=sign*p.socket_row_spacing/2-p.socket_body_width/2;hi=lo+p.socket_body_width
                        distance=math.hypot(max(-p.socket_row_length/2-px,0,px-p.socket_row_length/2),max(lo-py,0,py-hi))-p.carrier_post_radius
                        if abs(angle)+abs(dx)+abs(dy)<1e-7:centered=min(centered,distance)
                        if distance<smallest:smallest=distance;worst_pose=[float(dx),float(dy),float(angle)]
    require(accepted>0,'No carrier poses fit locators')
    require(smallest_support>=math.pi*p.carrier_post_radius**2*.8,'Carrier loses more than20% of a landing area within locator play')
    residual=smallest-2*p.print_xy_error-p.solder_extra_allowance
    require(residual>=1.0,'Tail/post residual below 1 mm in assumed XY/solder budget: '+str(residual))
    # Window under sockets preserves floor clearance, even though the plate sits
    # higher. Tail envelope also stays above the remaining plate material.
    require(p.carrier_bottom-p.carrier_tail_allowance-h.mount_top(p)>=2,'Insufficient tail/plate vertical allowance')
    vertical_residual=p.carrier_bottom-p.carrier_tail_allowance-h.mount_top(p)-p.solder_extra_allowance-2*p.print_z_error
    require(vertical_residual>=1.5,'Tail/plate vertical residual below assumed budget')
    return dict(allowed_sampled_poses=accepted,centered_tail_post_gap_mm=centered,minimum_landing_contact_area_mm2=smallest_support,minimum_sampled_tail_post_gap_mm=smallest,worst_sampled_pose_dx_dy_angle=worst_pose,
        assumed_pair_print_error_mm=2*p.print_xy_error,extra_solder_mm=p.solder_extra_allowance,residual_gap_mm=residual,
        tail_floor_gap_mm=p.carrier_bottom-p.carrier_tail_allowance-p.floor,
        tail_plate_top_gap_mm=p.carrier_bottom-p.carrier_tail_allowance-h.mount_top(p),tail_plate_vertical_budget_residual_mm=vertical_residual,
        limitation='Finite pose sampling and provisional rectangular solder strips, not a universal minimum or actual pin fit')


def main(p=h.Parameters(),output_root=ROOT):
    output_root=Path(output_root);h.generate(output_root,p);parts=h.build(p);coupons=h.fit_tests(p,parts)
    report=dict(units='mm',scope='Preliminary computational CAD; physical fit, thread quality, print quality, strength and temperature unverified',parts={})
    expected={'External_Tray':[p.length,p.width,p.height],
        'ESP32_Mount':[p.esp_centre_x+p.esp_mount_length/2-3.8,p.mount_width,max(h.frame_bottom(p),h.board_bottom(p,'ESP32')-p.usb_below_pcb)-p.mount_bottom],
        'Driver_Mount':[p.driver_mount_length,p.mount_width,h.board_bottom(p,'Driver')-p.mount_bottom],
        'Carrier_Retainer':[p.carrier_length+9,p.carrier_width+20,p.retainer_thickness]}
    for name,solid in {**parts,**coupons}.items():
        require(solid.status()==m3.Error.NoError and len(solid.decompose())==1,name+': invalid/disconnected print')
        directory='stl' if name in parts else 'fit_tests';path=output_root/'print_ready'/directory/(name+'.stl')
        mesh=e.analyse(path,solid.volume());size=mesh['hi']-mesh['lo']
        if name in expected:require(np.allclose(size,expected[name],atol=.0001),name+': wrong bounds')
        require(mesh['open_edges']==0 and abs(mesh['dvol'])<.01 and mesh['vol']>0,name+': invalid exported mesh')
        require(abs(mesh['lo'][2])<1e-5 and mesh['bed']>0,name+': not bed oriented')
        actual=e.read_stl(path);predicted=h.triangles(h.print_orientation(solid))
        require(actual.shape==predicted.shape and np.allclose(actual,predicted,atol=1e-5),name+': export differs from oriented CAD')
        layers=layer_report(name,solid,p)
        report['parts'][name]=dict(size_mm=size.tolist(),open_edges=0,connected_solids=1,volume_mm3=float(mesh['vol']),**layers)
        print('PASS',name,size.tolist(),'mm;',layers)
    models=assembly_parts.components(p);hardware=fasteners.groups(p);solids={k:v['solid'] for k,v in {**models,**hardware}.items()}
    for (a,sa),(b,sb) in itertools.combinations(solids.items(),2):
        require((sa^sb).volume()<1e-5,f'Assembled interference: {a}/{b}: {(sa^sb).volume()}')
    for name,space in h.connector_envelopes(p).items():
        for key,solid in parts.items():require((space^solid).volume()<1e-6,f'{name} blocked by {key}')
    for opening in [*h.exits(p).values(),*h.tie_openings(p),*h.service_windows(p)]:
        require((opening^parts['External_Tray']).volume()<1e-6,'Cable/vent/service opening obstructed')
        require(((parts['External_Tray']+opening)^opening).volume()>1,'Blocked-opening control failed')
    for opening in h.tie_openings(p):
        # Include actual underside loops' vertical access beside adhesive feet.
        b=opening.bounding_box();probe=h.box(b[0],b[3],b[1],b[4],-p.foot_height_allowance,p.floor+1)
        require((probe^solids['feet']).volume()<1e-6,'Adhesive foot blocks a tie anchor')
        for key in ('ESP32_Mount','Driver_Mount'):require((probe^parts[key]).volume()<1e-6,'Module blocks floor tie slot')
    for side in ('esp','driver'):
        for x,y in h.interface_mounts(p,side):
            tool=h.cylinder(x,y,p.m25_head_diameter/2,h.mount_top(p),60)
            for key in ('retainer','carrier','sockets','esp','esp_details','driver','driver_details'):
                require((tool^solids[key]).volume()<1e-6,'Module screwdriver blocked by '+key)
            below=h.cylinder(x,y,3,-10,-p.m25_nut_height)
            require((below^solids['feet']).volume()<1e-6,'Underside M2.5 nut tool blocked by feet')
    for x,y in h.frame_mounts(p):
        tool=h.cylinder(x,y,p.m25_head_diameter/2,h.frame_bottom(p)+p.retainer_thickness,60)
        for key in ('carrier','sockets','esp','esp_details'):require((tool^solids[key]).volume()<1e-6,'Frame tool blocked by '+key)
    for x,y in h.driver_mounts(p):
        upper=h.cylinder(x,y,p.driver_head_diameter/2,h.board_bottom(p,'Driver')+p.pcb_thickness,50)
        require((upper^solids['driver_details']).volume()<1e-6,'Driver tool blocked by header proxy')
        lower=h.cylinder(x,y,3,-5,p.mount_bottom-p.m2_nut_height)
        require((lower^parts['Driver_Mount']).volume()<1e-6 and (lower^parts['External_Tray']).volume()<1e-6,'Driver nut tool/service window blocked')
    stacks=fasteners.stacks(p)
    for key in ('modules','frame'):require(stacks[key]['projection']>=p.m25_pitch,'M2.5 nut traversal inadequate: '+key)
    require(stacks['frame']['projection_nut_on_pocket_floor']>=p.m25_pitch,'Frame screw does not start through full nut before seating')
    require(stacks['modules']['bench_clearance']>=2,'Module screw tip too near bench')
    require(stacks['driver']['projection']>=.4,'M2 nut traversal inadequate')
    # Intentional M2.5 prohibition, independently from the printed M2 bores.
    x,y=h.driver_mounts(p)[0];z=h.board_bottom(p,'Driver')
    require((h.cylinder(x,y,p.m25_diameter/2,z,z+p.pcb_thickness)^solids['driver']).volume()>.1,'M2.5-in-PCB-hole control failed')
    # Board-specific revisions must not change the common enclosure geometry.
    alternate=h.build(replace(p,driver_hole_pitch_x=p.driver_hole_pitch_x-1,driver_length=p.driver_length+1,
        carrier_post_inset_x=p.carrier_post_inset_x+.1,socket_origin_x_offset=.1,carrier_thickness=p.carrier_thickness+.05,socket_height=p.socket_height+.2))
    require(np.array_equal(h.triangles(alternate['External_Tray']),h.triangles(parts['External_Tray'])),'Board-specific change modifies base')
    report.update(fastener_stacks=stacks,retention=retention_checks(p,parts,models,hardware),
        solder_clearance=tail_clearance(p,models),board_specific_base_invariance=True,
        carrier_preload='None intended: frame closes on printed hard stops and retains carrier with defined play',
        assumptions_unverified=['Actual boards and header origin','Carrier thickness, bare edge/support areas, solder peaks and socket retention',
            'Stock head/nut/usable-thread dimensions, insulating M2 bearing areas, foot compression and tie sizes',
            'Print XY/Z errors and short-bridge capability; roof/thread strength and creep',
            'Physical tool dexterity, USB insertion loads, insulation, thermal and RF behavior'])
    (output_root/'mechanical/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS rigid retention, open-pocket regression control, support/contact budgets, tools, modularity and provisional connectors')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--parameters',type=Path)
    parser.add_argument('--output-dir',type=Path,default=ROOT);args=parser.parse_args()
    main(h.Parameters(**json.loads(args.parameters.read_text())) if args.parameters else h.Parameters(),args.output_dir)
