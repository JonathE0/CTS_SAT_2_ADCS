"""Current scene/CAD agreement and sampled modular assembly paths.
No machine-local preservation files; optional outputs stay in housing tree.
"""
import base64
import itertools
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_enclosure_viewer as builder


def require(ok,message):
    if not ok:raise ValueError(message)


def offset_at(part,time):
    keys=part['keyframes']
    if time<=keys[0]['time']:return np.array(keys[0]['offset'])
    for a,b in zip(keys[:-1],keys[1:]):
        if time<=b['time']:
            f=(time-a['time'])/(b['time']-a['time']);f=f*f*(3-2*f)
            return np.array(a['offset'])*(1-f)+np.array(b['offset'])*f
    return np.array(keys[-1]['offset'])


def canonical(points):
    points=np.round(points,4)
    return points[np.lexsort((points[:,2],points[:,1],points[:,0]))]


def main():
    data=json.loads((builder.VIEW/'scene.json').read_text());p=builder.h.Parameters(**data['parameters']);N=len(data['steps'])-1
    require(N==8,'Expected nine modular assembly stages')
    models=builder.assembly_parts.components(p);models.update(builder.fasteners.groups(p))
    require(set(models)=={q['id'] for q in data['parts']},'Stale or omitted assembly part')
    solids={k:v['solid'] for k,v in models.items()}
    for part in data['parts']:
        shown=np.frombuffer(base64.b64decode(part['positions_b64']),'<f4').reshape(-1,3)
        expected=builder.h.triangles(solids[part['id']]).reshape(-1,3)+[0,0,p.foot_height_allowance]
        require(shown.shape==expected.shape and np.allclose(canonical(shown),canonical(expected),atol=.0002),'Viewer mesh differs from CAD: '+part['id'])
        require(np.allclose(offset_at(part,N),[0,0,0]),'Part not assembled at final stage')
    indexed={q['id']:q for q in data['parts']}
    groups=[('esp',{'esp_mount','carrier','retainer','frame_bolts','frame_nut_front','frame_nut_rear','esp'}),
            ('driver',{'driver_mount','driver','driver_bolts','driver_nuts'})]
    for name,members in groups:
        assembly=[q for q in data['parts'] if q['stage_group'] in members]
        for t in np.linspace(5,6,41):
            offsets=[offset_at(q,t) for q in assembly]
            require(all(np.allclose(offsets[0],o) for o in offsets),name+': electronics move relative to module during insertion')
    require(np.allclose(offset_at(indexed['frame_bolts'],3),[-110,0,0]),'Frame not secured off case before ESP seating')
    for key in ('driver','driver_details','driver_bolts','driver_nuts'):
        require(np.allclose(offset_at(indexed[key],5),[70,0,0]),'Driver not secured before moving its mount')
    for key in ('esp_module_bolts','driver_module_bolts','esp_module_nuts','driver_module_nuts'):
        require(np.allclose(offset_at(indexed[key],7),[0,0,0]),'Module attachment incomplete at its named stage')
    times=np.unique(np.r_[np.linspace(0,N,241),[k['time'] for part in data['parts'] for k in part['keyframes']]])
    collisions=[];probes=0
    for t in times:
        posed={q['id']:solids[q['id']].translate(offset_at(q,t)) for q in data['parts']}
        boxes={key:np.asarray(solid.bounding_box()) for key,solid in posed.items()}
        for a,b in itertools.combinations(posed,2):
            aa,bb=boxes[a],boxes[b]
            if np.any(aa[:3]>=bb[3:]-1e-6) or np.any(bb[:3]>=aa[3:]-1e-6):continue
            overlap=(posed[a]^posed[b]).volume();probes+=1
            if overlap>1e-5:collisions.append((a,b,float(t),overlap))
    require(not collisions,'Assembly path interference: '+str(collisions[:15]))
    report=dict(stages=len(data['steps']),part_groups=len(data['parts']),printed_meshes_match_CAD=4,
        all_serialized_meshes_match_CAD=len(data['parts']),sample_times=len(times),pairwise_path_probes=probes,
        nominal_interference_mm3=0,rigid_loaded_module_insertion=True,
        scope='Sampled rigid geometry only. Mechanical retention is tested separately by check_housing.py; physical hardware/strength/threads unverified')
    (builder.ROOT/'mechanical/housing_assembly_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',report)


if __name__=='__main__':main()
