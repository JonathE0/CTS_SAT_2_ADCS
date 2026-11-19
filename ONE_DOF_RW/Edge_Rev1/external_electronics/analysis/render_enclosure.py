"""Independent housing previews from its one generated scene; no legacy imports.
Canonical PNG outputs live beside the existing housing viewer.
"""
import base64
import json
import os
from pathlib import Path
import tempfile
import numpy as np
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'cts-housing-matplotlib'))
os.environ.setdefault('XDG_CACHE_HOME',str(Path(tempfile.gettempdir())/'cts-housing-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
ROOT=Path(__file__).resolve().parents[1]
VIEW=ROOT.parents[2]/'CTS_Simple_Visulizers'/'External Electronics Enclosure'
PAPER='#f6f5f1'
INK='#213744'


def triangles(part):
    return np.frombuffer(base64.b64decode(part['positions_b64']), '<f4').reshape(-1, 3, 3).astype(float)


def part_geometry(part, exploded=False):
    tri = triangles(part)
    if exploded:
        tri += np.asarray(part['explode'])
    normals = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
    light = np.array([-.35, -.45, 1.0]); light /= np.linalg.norm(light)
    shade = .53+.47*np.clip(np.abs(normals @ light), 0, 1)
    colours = np.asarray(to_rgb(part['color']))[None, :]*shade[:, None]
    return tri, colours


def rasterize(triangles_, colours, top=False, exploded=False):
    """Orthographic depth-buffer renderer for truthful inter-part occlusion.

    Matplotlib's painter ordering cannot resolve the case's large floor triangles
    against the boards above them. A small NumPy z buffer resolves visibility per
    pixel; matplotlib handles labels, captions and PNG publication below.
    """
    width, height = 2400, 1523
    if top:
        right, up, direction = np.eye(3)
    else:
        elevation = np.radians(24 if exploded else 36)
        azimuth = np.radians(-62)
        direction=np.array([np.cos(elevation)*np.cos(azimuth),np.cos(elevation)*np.sin(azimuth),np.sin(elevation)])
        right=np.array([-np.sin(azimuth),np.cos(azimuth),0])
        up=np.cross(direction,right)
    basis=np.stack([right,up,direction],axis=1)
    projected=triangles_@basis
    vertices=projected.reshape(-1,3)
    centre=(vertices.min(0)+vertices.max(0))/2
    span=np.maximum(vertices.max(0)-vertices.min(0),1)
    scale=min((width-90)/span[0],(height-70)/span[1])
    def project(points):
        q=np.asarray(points)@basis
        return np.stack([(q[...,0]-centre[0])*scale+width/2,
                         height/2-(q[...,1]-centre[1])*scale,q[...,2]],axis=-1)
    q=project(triangles_)
    pixels=np.tile(np.asarray(to_rgb(PAPER))*255,(height,width,1)).astype(np.uint8)
    depth=np.full((height,width),-np.inf,dtype=np.float32)
    for face,colour in zip(q,colours):
        xmin,ymin=np.maximum(np.floor(face[:,:2].min(0)).astype(int),[0,0])
        xmax,ymax=np.minimum(np.ceil(face[:,:2].max(0)).astype(int),[width-1,height-1])
        if xmin>xmax or ymin>ymax:continue
        (x0,y0,z0),(x1,y1,z1),(x2,y2,z2)=face
        den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(den)<.02:continue
        yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1]
        a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
        b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den
        c=1-a-b
        z=a*z0+b*z1+c*z2
        old=depth[ymin:ymax+1,xmin:xmax+1]
        mask=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)&(z>old)
        old[mask]=z[mask]
        pixels[ymin:ymax+1,xmin:xmax+1][mask]=np.clip(colour*255,0,255).astype(np.uint8)
    return pixels,project


def main():
    data=json.loads((VIEW/'scene.json').read_text())
    for filename,exploded in [('assembled.png',False),('exploded.png',True)]:
        triangles_=[];colours=[]
        for part in data['parts']:
            tri,color=part_geometry(part,exploded);triangles_.append(tri);colours.append(color)
        pixels,_=rasterize(np.concatenate(triangles_),np.concatenate(colours),exploded=exploded)
        fig=plt.figure(figsize=(13.5,9),dpi=160,facecolor=PAPER)
        ax=fig.add_axes((.025,.13,.95,.76));ax.imshow(pixels);ax.set_axis_off()
        fig.text(.045,.955,data['title'],fontsize=23,weight='bold',color=INK)
        fig.text(.045,.914,('EXPLODED' if exploded else 'ASSEMBLED')+' · generated modular CAD · mm',fontsize=11,color=INK)
        fig.text(.045,.085,'125 × 90 × 35 mm · independent electronics mounts · four production prints · ten screws',fontsize=11,color=INK)
        fig.text(.045,.053,'Fit coupons first. Electronics, hardware, print tolerances, roof strength and physical fit remain unverified.',fontsize=10,color=INK)
        target=VIEW/'preview'/filename;target.parent.mkdir(parents=True,exist_ok=True)
        fig.savefig(target,facecolor=PAPER);plt.close(fig);print('Wrote',target)


if __name__=='__main__':main()
