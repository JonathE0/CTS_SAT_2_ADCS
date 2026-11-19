"""Exact printed solids plus explicitly unmeasured electronics/connector proxies."""
import make_housing as h
union=h.union


def components(p=h.Parameters()):
    out={}
    def add(key,name,solid,color,kind,note):out[key]=dict(name=name,solid=solid,color=color,kind=kind,note=note)
    printed=h.build(p)
    for key,name,color,note in [
      ('tray','External_Tray','#c9bda8','125 × 90 × 35 stationary base; common locating/through-bolt interfaces, service windows and cable exits; USB support belongs to replaceable ESP mount.'),
      ('esp_mount','ESP32_Mount','#9eb7bf','Replaceable ESP mount; four landing posts, locating stops and genuinely roofed side-entry nut pockets.'),
      ('driver_mount','Driver_Mount','#829faa','Replaceable driver mount; four plain M2 bored posts. Board-specific pattern is confined to this part.'),
      ('retainer','Carrier_Retainer','#7493a0','Bears on printed hard-stop columns, with deliberate capture play over the prepared carrier; independent of module-to-base screws.')]:
        add(key,name.replace('_',' '),printed[name],color,'Printed CAD',note)
    ex,ey=h.centre(p,'esp');dx,dy=h.centre(p,'driver');esp_z=h.board_bottom(p,'ESP32');driver_z=h.board_bottom(p,'Driver')
    carrier=h.box(ex-p.carrier_length/2,ex+p.carrier_length/2,ey-p.carrier_width/2,ey+p.carrier_width/2,p.carrier_bottom,h.carrier_top(p))
    add('carrier','Prepared insulating socket carrier',carrier,'#bd9856','Unmeasured prepared carrier',
        '60 × 40 × 1.6 allowance. Reserve bare edge strips and landing areas; no carrier or ESP32 holes assumed. Measure actual flatness and thickness.')
    sx,sy=ex+p.socket_origin_x_offset,ey+p.socket_origin_y_offset
    def rows(z0,z1):
        return union(h.box(sx-p.socket_row_length/2,sx+p.socket_row_length/2,
            sy+sign*p.socket_row_spacing/2-p.socket_body_width/2,sy+sign*p.socket_row_spacing/2+p.socket_body_width/2,z0,z1) for sign in (-1,1))
    add('sockets','ESP32 female socket rows',rows(h.carrier_top(p),esp_z),'#263238','Unmeasured socket allowance',
        'Row length, width, spacing, height and origin are configurable. Overall board outline is not a confirmed header datum.')
    add('carrier_tails','Carrier solder and pin allowance',rows(p.carrier_bottom-p.carrier_tail_allowance,p.carrier_bottom),'#83948d','Unmeasured underside envelope',
        'Measured solder peaks must fit the clearance budget including carrier play, print error and extra solder allowance. Print the carrier coupon first.')
    add('esp','ESP32 development-board envelope',h.box(ex-p.esp_length/2,ex+p.esp_length/2,ey-p.esp_width/2,ey+p.esp_width/2,esp_z,esp_z+p.pcb_thickness),
        '#245b45','Unmeasured 55 × 28 envelope','USB left; BOOT/EN and headers accessible from open top. No confirmed board revision or hole pattern. Socket friction/USB retention requires physical testing.')
    add('esp_details','ESP32 module, USB and buttons',union([
        h.box(ex+3,ex+21,ey-8,ey+8,esp_z+p.pcb_thickness,esp_z+5.5),
        h.box(ex-p.esp_length/2,ex-p.esp_length/2+6.5,ey-4,ey+4,esp_z+p.pcb_thickness,esp_z+4.5),
        *[h.box(ex-24,ex-20,ey+sign*9-1.5,ey+sign*9+1.5,esp_z+p.pcb_thickness,esp_z+3.5) for sign in (-1,1)]]),
        '#b7c2c7','Illustrative details','Simplified shapes only. Verify antenna copper/wiring keepout and actual controls before preparing the carrier.')
    board=h.box(dx-p.driver_length/2,dx+p.driver_length/2,dy-p.driver_width/2,dy+p.driver_width/2,driver_z,driver_z+p.pcb_thickness)
    for x,y in h.driver_mounts(p):board-=h.cylinder(x,y,p.driver_hole_diameter/2,driver_z-1,driver_z+p.pcb_thickness+1)
    add('driver','SimpleFOC Mini v1.0 reference PCB',board,'#b84337','Reference PCB — delivered kit unconfirmed',
        '26 × 21.5; four Ø2 holes on22 × 17.5 reference centers. Outline is simplified, not the actual scalloped board. Never force M2.5 through PCB holes.')
    add('driver_details','Driver IC and connector allowances',union([
        h.box(dx-5,dx+5,dy-3,dy+4,driver_z+1.6,driver_z+4.1),
        h.box(dx-8.5,dx+8.5,dy-10.75,dy-7,driver_z+1.6,driver_z+9),
        h.box(dx-4.5,dx+5.5,dy+8,dy+11,driver_z+1.6,driver_z+10),
        h.cylinder(dx-11,dy+1,2.8,driver_z+1.6,driver_z+8)]),
        '#303a42','Illustrative details','Required control row front, motor header rear, supply left. Verify populated rows, pin order, component heights and safe head bearing areas on delivered board.')
    add('feet','Insulating adhesive feet',union(h.cylinder(x,y,p.foot_radius,-p.foot_height_allowance,0) for x in (p.foot_inset_x,p.length-p.foot_inset_x) for y in (p.foot_inset_y,p.width-p.foot_inset_y)),
        '#303b42','Bought envelope','Four Ø8 × 6 allowances, moved clear of tie anchors and underside nuts. Verify compressed height, ties and screw-tip clearance to bench.')
    return out
