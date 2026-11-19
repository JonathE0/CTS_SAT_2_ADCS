"""Commercial fastener envelopes and nominal stacks, not thread/strength models.
All six M2.5 screws use listed kit length10; driver needs four insulating M2x12.
"""
import make_housing as h
union=h.union


def nut(x,y,flats,bore,z0,z1):
    return h.hex_prism(x,y,flats,z0,z1)-h.cylinder(x,y,bore/2,z0-1,z1+1)


def screw(x,y,diameter,length,head_d,head_h,seat):
    return h.cylinder(x,y,diameter/2,seat-length,seat)+h.cylinder(x,y,head_d/2,seat,seat+head_h)


def stacks(p=h.Parameters()):
    module_seat=h.mount_top(p);frame_seat=h.frame_bottom(p)+p.retainer_thickness
    pcb_seat=h.board_bottom(p,'Driver')+p.pcb_thickness
    return {
      'modules':dict(size='M2.5',quantity=4,length=p.module_screw_length,head_seat=module_seat,
        grip=module_seat,nut_height=p.m25_nut_height,nut_bottom=-p.m25_nut_height,nut_top=0,
        projection=p.module_screw_length-module_seat-p.m25_nut_height,tip_z=module_seat-p.module_screw_length,
        bench_clearance=p.foot_height_allowance+module_seat-p.module_screw_length,
        load_path='head → removable plate → base support/floor → underside nut; two independent through-bolts per module'),
      'frame':dict(size='M2.5',quantity=2,length=p.frame_screw_length,head_seat=frame_seat,
        nut_bottom=h.nut_roof(p)-p.m25_nut_height,nut_top=h.nut_roof(p),nut_height=p.m25_nut_height,
        grip=frame_seat-h.nut_roof(p),projection=h.nut_roof(p)-p.m25_nut_height-(frame_seat-p.frame_screw_length),
        projection_nut_on_pocket_floor=p.nut_pocket_bottom-(frame_seat-p.frame_screw_length),
        tip_z=frame_seat-p.frame_screw_length,roof_thickness=h.frame_bottom(p)-h.nut_roof(p),
        load_path='head → frame/hard-stop column → solid pocket roof → nut → screw; independent of enclosure fastening'),
      'driver':dict(size='M2 insulating',quantity=4,length=p.driver_screw_length,head_seat=pcb_seat,
        grip=pcb_seat-p.mount_bottom,nut_height=p.m2_nut_height,nut_bottom=p.mount_bottom-p.m2_nut_height,nut_top=p.mount_bottom,
        projection=p.driver_screw_length-(pcb_seat-p.mount_bottom)-p.m2_nut_height,
        tip_z=pcb_seat-p.driver_screw_length,bench_clearance=pcb_seat-p.driver_screw_length+p.foot_height_allowance,
        load_path='insulating head → PCB at four reference holes → printed posts/plate → insulating underside nuts; preassemble off case')
    }


def groups(p=h.Parameters()):
    out={};s=stacks(p)
    def add(key,name,items,quantity,note,group,color='#8d9a9e'):
        out[key]=dict(name=name,solid=union(items),quantity=quantity,note=note,stage_group=group,color=color,
            kind='Commercial hardware allowance — actual stock unmeasured')
    for side in ('esp','driver'):
        pts=h.interface_mounts(p,side)
        add(side+'_module_bolts',side.upper()+' mount M2.5 × 10 screws',
            [screw(x,y,p.m25_diameter,p.module_screw_length,p.m25_head_diameter,p.m25_head_height,s['modules']['head_seat']) for x,y in pts],2,
            'Two through-bolts release this complete mount. Kit head unconfirmed; Ø5.5 × 3 envelope. Hold ordinary underside nuts with a wrench.', 'module_bolts')
        add(side+'_module_nuts',side.upper()+' mount M2.5 underside nuts',
            [nut(x,y,p.m25_nut_flats,p.m25_diameter,-p.m25_nut_height,0) for x,y in pts],2,
            'AF5 × 2 allowance. Ordinary accessible underside nuts, not printed threads or claimed captive pockets.', 'module_nuts')
    pts=h.frame_mounts(p)
    add('frame_bolts','Frame M2.5 × 10 screws',
        [screw(x,y,p.m25_diameter,p.frame_screw_length,p.m25_head_diameter,p.m25_head_height,s['frame']['head_seat']) for x,y in pts],2,
        'Fastens frame independently to ESP mount. Preload closes on printed hard stops; nominal carrier capture play0.4, no intentional PCB compression.', 'frame_bolts')
    for i,(x,y) in enumerate(pts):
        name='front' if i==0 else 'rear'
        add('frame_nut_'+name,'Frame captive M2.5 nut — '+name,
            [nut(x,y,p.m25_nut_flats,p.m25_diameter,s['frame']['nut_bottom'],s['frame']['nut_top'])],1,
            'Slide into side port before frame. Solid roof above nut prevents upward withdrawal; installed screw prevents escape through side entry.', 'frame_nut_'+name)
    pts=h.driver_mounts(p)
    add('driver_bolts','Insulating M2 × 12 driver screws',
        [screw(x,y,2,p.driver_screw_length,p.driver_head_diameter,p.driver_head_height,s['driver']['head_seat']) for x,y in pts],4,
        'Additional stock: commercial insulating screws. Ø4 × 2.5 head allowance; verify actual shaft fit and component-free bearing areas.', 'driver_bolts','#d7d0bd')
    add('driver_nuts','Insulating M2 driver nuts',
        [nut(x,y,p.m2_nut_flats,2,s['driver']['nut_bottom'],s['driver']['nut_top']) for x,y in pts],4,
        'Additional stock, AF4 × 1.6 allowance. Fit off case; generic base service window leaves clearance after module installation.', 'driver_nuts','#d7d0bd')
    return out
