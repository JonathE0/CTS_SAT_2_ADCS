"""Parametric stationary bench housing, mm. Four production parts and shared-CAD
fit coupons. Electronics/fastener dimensions are provisional, not physical fits.
Only this external_electronics tree is written by this generator.
"""
import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import struct
import manifold3d as m3
import numpy as np

HERE=Path(__file__).resolve().parent


@dataclass(frozen=True)
class Parameters:
    length: float=125.0
    width: float=90.0
    height: float=35.0
    floor: float=3.0
    wall: float=2.5
    esp_centre_x: float=44.0
    driver_centre_x: float=102.5
    module_centre_y: float=47.0
    esp_mount_length: float=72.0
    driver_mount_length: float=35.0
    mount_width: float=60.0
    mount_bottom: float=5.0
    mount_thickness: float=2.0
    interface_half_x: float=12.0
    interface_half_y: float=26.0
    interface_boss_radius: float=4.0
    bearing_half_x: float=12.0
    bearing_half_y: float=18.0
    bearing_radius: float=3.0
    locator_pin_diameter: float=2.6
    locator_hole_diameter: float=3.6
    locator_slot_extra: float=0.6
    m25_clearance: float=3.1
    module_screw_length: float=10.0
    module_tool_access_diameter: float=7.0
    frame_screw_length: float=10.0
    m25_diameter: float=2.5
    m25_pitch: float=0.45
    m25_head_diameter: float=5.5  # envelope only; kit label says socket-head
    m25_head_height: float=3.0
    m25_nut_flats: float=5.0
    m25_nut_height: float=2.0
    frame_mount_half_y: float=26.0
    frame_boss_radius: float=4.0
    nut_pocket_flats: float=5.4
    nut_pocket_bottom: float=8.0
    nut_pocket_axial_clearance: float=0.3
    nut_entry_width: float=6.4
    carrier_length: float=60.0
    carrier_width: float=40.0
    carrier_thickness: float=1.6
    carrier_bottom: float=12.5
    carrier_tail_allowance: float=3.0
    carrier_post_inset_x: float=2.5
    carrier_post_inset_y: float=4.0
    carrier_post_radius: float=2.4
    carrier_edge_overlap: float=3.0
    carrier_locator_gap: float=0.5
    carrier_capture_gap: float=0.4  # deliberate capture play, not PCB preload
    carrier_thickness_error: float=0.1
    print_z_error: float=0.1
    print_xy_error: float=0.2
    solder_extra_allowance: float=0.3
    retainer_thickness: float=3.0
    retainer_rail_thickness: float=1.6
    socket_height: float=6.0
    socket_row_spacing: float=25.4
    socket_row_length: float=46.0
    socket_body_width: float=2.6
    socket_origin_x_offset: float=0.0
    socket_origin_y_offset: float=0.0
    esp_length: float=55.0
    esp_width: float=28.0
    pcb_thickness: float=1.6
    driver_length: float=26.0
    driver_width: float=21.5
    driver_standoff: float=6.0
    driver_post_radius: float=2.5
    driver_hole_pitch_x: float=22.0
    driver_hole_pitch_y: float=17.5
    driver_hole_diameter: float=2.0
    driver_bore: float=2.6
    driver_screw_length: float=12.0
    driver_head_diameter: float=4.0
    driver_head_height: float=2.5
    m2_nut_flats: float=4.0
    m2_nut_height: float=1.6
    foot_height_allowance: float=6.0
    foot_radius: float=4.0
    foot_inset_x: float=8.0
    foot_inset_y: float=6.0
    service_window_half_x: float=15.0
    service_window_half_y: float=15.0
    exit_sill: float=10.0
    usb_y0: float=32.0
    usb_y1: float=64.0
    power_motor_x0: float=92.0
    power_motor_x1: float=116.0
    sensor_x0: float=32.0
    sensor_x1: float=58.0
    usb_body_width: float=14.0
    usb_body_height: float=9.0
    usb_below_pcb: float=3.0
    driver_control_plug_height: float=22.0
    driver_phase_plug_height: float=22.0
    driver_power_plug_height: float=13.0


def box(x0,x1,y0,y1,z0,z1):
    return m3.Manifold.cube((x1-x0,y1-y0,z1-z0)).translate((x0,y0,z0))


def cylinder(x,y,radius,z0,z1):
    return m3.Manifold.cylinder(z1-z0,radius,circular_segments=48).translate((x,y,z0))


def hex_prism(x,y,flats,z0,z1):
    return m3.Manifold.cylinder(z1-z0,flats/math.sqrt(3),circular_segments=6).translate((x,y,z0))


def slot(x,y0,y1,width,z0,z1):
    return m3.Manifold.batch_hull([cylinder(x,y,width/2,z0,z1) for y in (y0,y1)])


def union(solids):
    return m3.Manifold.batch_boolean(list(solids),m3.OpType.Add)


def centre(p,side):return (p.esp_centre_x if side=='esp' else p.driver_centre_x,p.module_centre_y)
def mount_top(p):return p.mount_bottom+p.mount_thickness
def carrier_top(p):return p.carrier_bottom+p.carrier_thickness
def frame_bottom(p):return carrier_top(p)+p.carrier_capture_gap
def nut_roof(p):return p.nut_pocket_bottom+p.m25_nut_height+p.nut_pocket_axial_clearance


def board_bottom(p,name):
    return carrier_top(p)+p.socket_height if name.startswith('ESP') else mount_top(p)+p.driver_standoff


def interface_mounts(p,side):
    x,y=centre(p,side)
    return [(x-p.interface_half_x,y-p.interface_half_y),(x+p.interface_half_x,y+p.interface_half_y)]


def bearing_points(p,side):
    x,y=centre(p,side)
    return [(x+sx*p.bearing_half_x,y+sy*p.bearing_half_y) for sx in (-1,1) for sy in (-1,1)]


def locating_pins(p,side):
    q=bearing_points(p,side)
    return [q[0],q[-1]]


def frame_mounts(p):
    return [(p.esp_centre_x,p.module_centre_y+sy*p.frame_mount_half_y) for sy in (-1,1)]


def carrier_mounts(p):
    # Our carrier landing pads, not ESP32 or perfboard mounting holes.
    return [(p.esp_centre_x+sx*(p.carrier_length/2-p.carrier_post_inset_x),
             p.module_centre_y+sy*(p.carrier_width/2-p.carrier_post_inset_y)) for sx in (-1,1) for sy in (-1,1)]


def driver_mounts(p):
    x,y=centre(p,'driver')
    return [(x+sx*p.driver_hole_pitch_x/2,y+sy*p.driver_hole_pitch_y/2) for sx in (-1,1) for sy in (-1,1)]


def carrier_locators(p):
    cx,cy=centre(p,'esp');x0,x1=cx-p.carrier_length/2,cx+p.carrier_length/2
    y0,y1=cy-p.carrier_width/2,cy+p.carrier_width/2;g=p.carrier_locator_gap
    stops=[box(a,b,c,d,mount_top(p)-.01,carrier_top(p))
        for a,b in ((x0-g-3,x0-g),(x1+g,x1+g+3)) for c,d in ((y0+1,y0+6),(y1-6,y1-1))]
    stops += [box(a,b,c,d,mount_top(p)-.01,carrier_top(p)) for a,b,c,d in
        ((cx-15,cx-7,y0-g-2,y0-g),(cx+7,cx+15,y1+g,y1+g+2))]
    return union(stops)


def nut_pocket(p,x,y):
    # Side entry under a REAL solid roof. Front/rear ports face outward.
    a=p.nut_pocket_bottom;b=nut_roof(p);direction=-1 if y<p.module_centre_y else 1
    entry=box(x-p.nut_entry_width/2,x+p.nut_entry_width/2,
        min(y,y+direction*(p.frame_boss_radius+1)),max(y,y+direction*(p.frame_boss_radius+1)),a,b)
    return hex_prism(x,y,p.nut_pocket_flats,a,b)+entry


def mount_blank(p,side):
    cx,cy=centre(p,side);length=p.esp_mount_length if side=='esp' else p.driver_mount_length
    plate=box(cx-length/2,cx+length/2,cy-p.mount_width/2,cy+p.mount_width/2,p.mount_bottom,mount_top(p))
    for x,y in interface_mounts(p,side):plate-=cylinder(x,y,p.m25_clearance/2,p.mount_bottom-1,mount_top(p)+1)
    pins=locating_pins(p,side)
    plate-=cylinder(*pins[0],p.locator_hole_diameter/2,p.mount_bottom-1,mount_top(p)+1)
    x,y=pins[1]
    plate-=slot(x,y-p.locator_slot_extra/2,y+p.locator_slot_extra/2,p.locator_hole_diameter,p.mount_bottom-1,mount_top(p)+1)
    return plate


def exits(p):
    return {'USB':box(-1,p.wall+1,p.usb_y0,p.usb_y1,p.exit_sill,p.height+1),
        'power':box(p.power_motor_x0,p.power_motor_x1,-1,p.wall+1,p.exit_sill,p.height+1),
        'motor_phases':box(p.power_motor_x0,p.power_motor_x1,p.width-p.wall-1,p.width+1,p.exit_sill,p.height+1),
        'sensors':box(p.sensor_x0,p.sensor_x1,p.width-p.wall-1,p.width+1,p.exit_sill,p.height+1)}


def tie_openings(p):
    cy=p.module_centre_y;rects=[(4,7,cy-9,cy-7.2),(4,7,cy+7.2,cy+9)]
    for x,y in (((p.power_motor_x0+p.power_motor_x1)/2,10),((p.power_motor_x0+p.power_motor_x1)/2,p.width-10),((p.sensor_x0+p.sensor_x1)/2,p.width-10)):
        rects += [(x+dx-.9,x+dx+.9,y-2,y+2) for dx in (-7,7)]
    return [box(*r,-1,p.floor+1) for r in rects]


def service_windows(p):
    return [box(cx-p.service_window_half_x,cx+p.service_window_half_x,cy-p.service_window_half_y,cy+p.service_window_half_y,-1,p.floor+1)
        for cx,cy in (centre(p,'esp'),centre(p,'driver'))]


def connector_envelopes(p):
    ex,ey=centre(p,'esp');dx,dy=centre(p,'driver');dz=board_bottom(p,'Driver')+p.pcb_thickness
    return {'USB plug and boot':box(-2,ex-p.esp_length/2,ey-p.usb_body_width/2,ey+p.usb_body_width/2,
        board_bottom(p,'ESP32')-p.usb_below_pcb,board_bottom(p,'ESP32')-p.usb_below_pcb+p.usb_body_height),
        'Driver control mating envelope':box(dx-8.5,dx+8.5,dy-21,dy-8.75,dz,dz+p.driver_control_plug_height),
        'Driver phase mating envelope':box(dx-6.5,dx+8.5,dy+9,dy+22,dz,dz+p.driver_phase_plug_height),
        'Driver power service envelope':box(dx-22.5,dx-12,dy-6,dy+6,board_bottom(p,'Driver'),board_bottom(p,'Driver')+p.driver_power_plug_height)}


def build(p=Parameters()):
    values=asdict(p)
    if not all(np.isfinite(v) for v in values.values()):raise ValueError('Non-finite parameter')
    if any(v<=0 for k,v in values.items() if not k.startswith('socket_origin_')):raise ValueError('Dimensions must be positive')
    if p.mount_bottom<=p.floor or nut_roof(p)>=frame_bottom(p)-2:raise ValueError('Mount seating/retention roof thickness invalid')
    if p.carrier_capture_gap<=p.carrier_thickness_error+2*p.print_z_error:raise ValueError('Capture gap does not cover assumed thickness/Z error')
    if p.nut_entry_width<p.m25_nut_flats*2/math.sqrt(3)+2*p.print_xy_error:raise ValueError('Nut entry too narrow for vertices and allowance')
    if p.carrier_tail_allowance>=p.carrier_bottom-mount_top(p):raise ValueError('Solder tails exceed nominal mount clearance')
    tray=box(0,p.length,0,p.width,0,p.height)-box(p.wall,p.length-p.wall,p.wall,p.width-p.wall,p.floor,p.height+1)
    for window in service_windows(p):tray-=window
    for side in ('esp','driver'):
        for x,y in interface_mounts(p,side):
            tray+=cylinder(x,y,p.interface_boss_radius,p.floor-.01,p.mount_bottom)
            tray-=cylinder(x,y,p.m25_clearance/2,-1,p.mount_bottom+1)
        for x,y in bearing_points(p,side):tray+=cylinder(x,y,p.bearing_radius,p.floor-.01,p.mount_bottom)
        for x,y in locating_pins(p,side):tray+=cylinder(x,y,p.locator_pin_diameter/2,p.mount_bottom-.01,mount_top(p))
    for cutter in [*exits(p).values(),*tie_openings(p)]:tray-=cutter
    esp=mount_blank(p,'esp');cx,cy=centre(p,'esp')
    # USB support belongs to replaceable electronics geometry, not the base.
    esp+=box(3.8,9,cy-7,cy+7,p.mount_bottom,mount_top(p))
    esp+=box(3.8,7.5,cy-7,cy+7,mount_top(p)-.01,board_bottom(p,'ESP32')-p.usb_below_pcb)
    esp-=box(cx-p.socket_row_length/2-1,cx+p.socket_row_length/2+1,cy-15,cy+15,p.mount_bottom-1,mount_top(p)+1)
    for x,y in carrier_mounts(p):esp+=cylinder(x,y,p.carrier_post_radius,mount_top(p)-.01,p.carrier_bottom)
    esp+=carrier_locators(p)
    for x,y in frame_mounts(p):
        esp+=cylinder(x,y,p.frame_boss_radius,mount_top(p)-.01,frame_bottom(p))
        esp-=nut_pocket(p,x,y)
        esp-=cylinder(x,y,p.m25_clearance/2,p.mount_bottom-1,frame_bottom(p)+1)
    x0,x1=cx-p.carrier_length/2,cx+p.carrier_length/2;y0,y1=cy-p.carrier_width/2,cy+p.carrier_width/2
    bottom=frame_bottom(p)
    frame=box(x0-5,x1+4,y0-10,y0+p.carrier_edge_overlap,bottom,bottom+p.retainer_thickness)
    frame+=box(x0-5,x1+4,y1-p.carrier_edge_overlap,y1+10,bottom,bottom+p.retainer_thickness)
    for a,b in ((x0-5,x0-2),(x1+1,x1+4)):
        frame+=box(a,b,y0-10,y1+10,bottom,bottom+p.retainer_rail_thickness)
    for x,y in frame_mounts(p):frame-=cylinder(x,y,p.m25_clearance/2,bottom-1,bottom+p.retainer_thickness+1)
    # Open U-notches admit the module bolt heads and tools while the complete
    # ESP carrier/frame remains assembled. No fragile thin ligament at the rim.
    r=p.module_tool_access_diameter/2
    for i,(x,y) in enumerate(interface_mounts(p,'esp')):
        frame-=cylinder(x,y,r,bottom-1,bottom+p.retainer_thickness+1)
        lo,hi=(y0-11,y) if i==0 else (y,y1+11)
        frame-=box(x-r,x+r,lo,hi,bottom-1,bottom+p.retainer_thickness+1)
    driver=mount_blank(p,'driver');dx,dy=centre(p,'driver')
    for x in (dx-5.5,dx+2.5):driver-=box(x-1.5,x+1.5,dy-7,dy+7,p.mount_bottom-1,mount_top(p)+1)
    for x,y in driver_mounts(p):
        driver+=cylinder(x,y,p.driver_post_radius,mount_top(p)-.01,board_bottom(p,'Driver'))
        driver-=cylinder(x,y,p.driver_bore/2,p.mount_bottom-1,board_bottom(p,'Driver')+1)
    return {'External_Tray':tray,'ESP32_Mount':esp,'Driver_Mount':driver,'Carrier_Retainer':frame}


def fit_tests(p=Parameters(),parts=None):
    # Crops of final geometry: never a separately redrawn PCB pattern or pocket.
    parts=parts or build(p);cx,cy=centre(p,'esp');x,y=frame_mounts(p)[0]
    region=box(x-6,x+6,y-p.frame_boss_radius,y+10,p.mount_bottom-1,frame_bottom(p)+p.retainer_thickness+1)
    coupon_top=max(frame_bottom(p),board_bottom(p,'ESP32')-p.usb_below_pcb)+1
    esp_region=box(cx-p.carrier_length/2-4,cx+p.carrier_length/2+4,cy-p.carrier_width/2-4,cy+p.carrier_width/2+4,p.mount_bottom-1,coupon_top)
    esp_region+=box(cx-5,cx+5,cy-p.mount_width/2,cy+p.mount_width/2,p.mount_bottom-1,coupon_top)
    esp_region+=box(3,14,cy-7,cy+7,p.mount_bottom-1,coupon_top)
    dx,dy=centre(p,'driver')
    driver_region=box(dx-p.driver_hole_pitch_x/2-5,dx+p.driver_hole_pitch_x/2+5,dy-p.driver_hole_pitch_y/2-5,dy+p.driver_hole_pitch_y/2+5,p.mount_bottom-1,board_bottom(p,'Driver')+1)
    return {'Fit_Retention_Base':parts['ESP32_Mount']^region,
        'Fit_Retention_Cap':parts['Carrier_Retainer']^region,
        'Fit_ESP_Carrier':parts['ESP32_Mount']^esp_region,
        'Fit_Driver_Mount':parts['Driver_Mount']^driver_region}


def triangles(solid):
    mesh=solid.to_mesh()
    return np.asarray(mesh.vert_properties)[:,:3][np.asarray(mesh.tri_verts)]


def write_stl(path,solid):
    tri=triangles(solid).astype('<f4')
    records=np.zeros(len(tri),dtype=[('normal','<f4',3),('vertices','<f4',(3,3)),('attribute','<u2')])
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    records['normal']=normals/np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-20);records['vertices']=tri
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b'CTS preliminary fit prototype; mm'.ljust(80,b'\0')+struct.pack('<I',len(tri))+records.tobytes())


def print_orientation(solid):
    x0,y0,z0,x1,y1,_=solid.bounding_box()
    return solid.translate((-(x0+x1)/2,-(y0+y1)/2,-z0))


def draw_layout(root,parts,p):
    lines=['<svg xmlns="http://www.w3.org/2000/svg" width="850" height="660" viewBox="0 0 850 660">',
        '<rect width="100%" height="100%" fill="#fafafa"/><g font-family="sans-serif" fill="#172e3e">',
        '<text x="30" y="35" font-size="22">Modular electronics housing — preliminary fit design</text>',
        '<text x="30" y="62" font-size="16">125 × 90 × 35 mm · four printed parts · actual hardware unmeasured</text>']
    def section(solid,z,fill):
        d=' '.join('M '+' L '.join(f'{90+float(x)*5:.3f},{550-float(y)*5:.3f}' for x,y in loop)+' Z' for loop in solid.slice(z).to_polygons())
        lines.append(f'<path d="{d}" fill="{fill}" stroke="#536a76" stroke-width="0.7" fill-rule="evenodd"/>')
    section(parts['External_Tray'],1.5,'#e5e9ec');section(parts['External_Tray'],8,'#829ca9')
    for key in ('ESP32_Mount','Driver_Mount'):section(parts[key],p.mount_bottom+1,'#a9c3d0')
    section(parts['Carrier_Retainer'],frame_bottom(p)+1,'#769baa')
    for side,l,w,label in [('esp',p.esp_length,p.esp_width,'ESP32'),('driver',p.driver_length,p.driver_width,'SimpleFOC Mini')]:
        cx,cy=centre(p,side)
        lines.append(f'<rect x="{90+(cx-l/2)*5}" y="{550-(cy+w/2)*5}" width="{l*5}" height="{w*5}" fill="#a1cfa6" fill-opacity=".6" stroke="#237246" stroke-dasharray="6 3"/>')
        lines.append(f'<text x="{90+cx*5}" y="{550-cy*5}" text-anchor="middle" font-size="14">{label}</text>')
    lines+=['<text x="30" y="600" font-size="15">USB left · power front · phases rear right · sensors rear left</text>',
        '<text x="30" y="628" font-size="15">Two screws release each complete module; frame has separate positively captured nuts.</text></g></svg>']
    (root/'preview').mkdir(parents=True,exist_ok=True);(root/'preview/layout.svg').write_text('\n'.join(lines)+'\n')


def generate(root=HERE.parent,p=Parameters()):
    root=Path(root);parts=build(p);coupons=fit_tests(p,parts)
    for name,solid in {**parts,**coupons}.items():
        if solid.status()!=m3.Error.NoError or solid.is_empty():raise ValueError('Invalid '+name)
        if name in parts:write_stl(root/'mechanical'/f'{name}.stl',solid)
        directory='stl' if name in parts else 'fit_tests'
        write_stl(root/'print_ready'/directory/f'{name}.stl',print_orientation(solid))
    draw_layout(root,parts,p)
    metadata=dict(units='mm',status='PRELIMINARY CAD — fit coupons first; physical hardware unverified',parameters=asdict(p),
        production_parts=list(parts),fit_test_parts=list(coupons),
        common_interface=dict(seating_z=p.mount_bottom,holes_per_mount=2,diagonal_pitch_mm=[2*p.interface_half_x,2*p.interface_half_y],
            esp_centres=interface_mounts(p,'esp'),driver_centres=interface_mounts(p,'driver'),
            note='Same two-hole datum and seating plane, distinct bay outline capacities; one round and one slotted locating hole.'),
        driver_reference=dict(outline_mm=[26,21.5],hole_diameter_mm=2,hole_spacing_mm=[22,17.5],delivered_board_measured=False,
            drawing='https://dfimg.dfrobot.com/wiki/19354/DRI0058_simplefocmini-driver-board_dimension_V1.0.jpg'),
        driver_mount_centres_mm=driver_mounts(p),carrier_landing_centres_mm=carrier_mounts(p),
        connector_envelopes={k:list(v.bounding_box()) for k,v in connector_envelopes(p).items()},
        physical_validation=False)
    (root/'mechanical/housing_parameters.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print('Generated 4 production parts and 4 coupon pieces; mm; physical fit unverified')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',type=Path,default=HERE.parent)
    parser.add_argument('--parameters',type=Path,help='JSON object of Parameters overrides')
    args=parser.parse_args();p=Parameters(**json.loads(args.parameters.read_text())) if args.parameters else Parameters()
    generate(args.output_dir,p)
