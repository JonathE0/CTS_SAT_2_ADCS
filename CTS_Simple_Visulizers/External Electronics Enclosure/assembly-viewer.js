/* Housing-only assembly transport. Adapted from Edge Rev 1's progress/waypoint,
 * smoothstep, play/pause, visibility and manual-orbit approach. Its original
 * viewer and the older runtime shared by the testbench are left untouched. */
(async function(){
  'use strict';
  const $=id=>document.getElementById(id);
  let cad;
  try{
    const embedded=document.getElementById('cad-scene');
    if(embedded)cad=JSON.parse(embedded.textContent);
    else{const response=await fetch('scene.json',{cache:'no-store'});
      if(!response.ok)throw new Error('scene.json HTTP '+response.status);cad=await response.json();}
    window.CTS_SCENE=cad;
  }catch(error){$('notice').textContent='Unable to load enclosure scene. Use the HTTP launch command in README.md. '+error.message;return;}
  const N=cad.steps.length-1;$('scrub').max=N;
  const reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  $('notice').textContent=cad.notice;
  let T=0,target=0,playing=false,pauseUntil=0,dirty=true,labelsDirty=true;
  let az=-.96,el=.58,zoom=1,distance=600;
  const steps=[],checks=new Map(),labels=new Map(),meshes=new Map();
  const state={get progress(){return T},get target(){return target},get playing(){return playing},get camera(){return [az,el,zoom]}};
  function smooth(f){return f*f*(3-2*f);}
  function offsetAt(part,t){
    const keys=part.keyframes;
    if(t<=keys[0].time)return keys[0].offset;
    for(let k=1;k<keys.length;k++)if(t<=keys[k].time){
      const a=keys[k-1],b=keys[k],f=smooth((t-a.time)/(b.time-a.time));
      return a.offset.map((v,j)=>v+(b.offset[j]-v)*f);
    }
    return keys[keys.length-1].offset;
  }
  function shownStep(){return Math.min(N,Math.ceil(T-1e-6));}
  function updateUI(){
    const n=shownStep(),step=cad.steps[n];
    $('chipStep').textContent='Step '+n+' of '+N;$('chipName').textContent=step.short;
    $('stepNo').textContent='STEP '+n+' OF '+N;$('stepTitle').textContent=step.title;
    $('stepText').textContent=step.text;$('stepFact').textContent=step.fact;
    $('scrub').value=T;$('bPlay').textContent=playing?'Pause':(T>=N-1e-6?'Replay':'Play');
    $('bPrev').disabled=T<=1e-6;$('bNext').disabled=T>=N-1e-6;
    steps.forEach((button,k)=>{if(k===n)button.setAttribute('aria-current','step');else button.removeAttribute('aria-current');button.classList.toggle('done',k<n);});
  }
  function go(value,immediate=false){target=Math.max(0,Math.min(N,value));if(immediate||reduce)T=target;dirty=true;labelsDirty=true;updateUI();}
  cad.steps.forEach((step,k)=>{
    const li=document.createElement('li'),button=document.createElement('button');button.type='button';
    const number=document.createElement('span');number.className='n';number.textContent=k;
    const text=document.createElement('span');text.textContent=step.short;button.append(number,text);
    button.onclick=()=>{playing=false;go(k);};li.append(button);$('steps').append(li);steps.push(button);
  });
  cad.parts.forEach(part=>{
    const li=document.createElement('li'),check=document.createElement('input');check.type='checkbox';check.checked=true;check.setAttribute('aria-label','Show '+part.name);
    const swatch=document.createElement('span');swatch.className='sw';swatch.style.background=part.color;
    const name=document.createElement('button');name.className='pname';name.textContent=part.name;
    const note=document.createElement('small');note.textContent=part.dimensions;name.append(note);
    name.onclick=()=>inspect(part.id);
    const quantity=document.createElement('span');quantity.className='pmass';quantity.textContent=part.quantity?'×'+part.quantity:'incl.';
    li.append(check,swatch,name,quantity);$('parts').append(li);checks.set(part.id,check);
    check.onchange=()=>{if(meshes.has(part.id))meshes.get(part.id).visible=check.checked;dirty=true;labelsDirty=true;};
  });
  $('bPrev').onclick=()=>{playing=false;go(Math.max(0,Math.ceil(T-1e-6)-1));};
  $('bNext').onclick=()=>{playing=false;go(Math.min(N,Math.floor(T+1e-6)+1));};
  $('bPlay').onclick=()=>{if(playing){playing=false;target=T;}else{if(T>=N-1e-6)go(0,true);playing=true;pauseUntil=0;}dirty=true;updateUI();};
  $('bKit').onclick=()=>{playing=false;go(0);};$('bDone').onclick=()=>{playing=false;go(N);};
  $('scrub').oninput=event=>{playing=false;go(Number(event.target.value),true);};
  let renderer;
  try{renderer=new THREE.WebGLRenderer({canvas:$('view'),antialias:true,preserveDrawingBuffer:true});}
  catch(error){$('nogl').hidden=false;updateUI();return;}
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.localClippingEnabled=true;renderer.outputEncoding=THREE.sRGBEncoding;
  const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(34,1,.5,4000);camera.up.set(0,0,1);
  scene.add(new THREE.HemisphereLight(0xffffff,0x8a98a4,.8));
  for(const [x,y,z,intensity]of [[100,-180,300,.85],[-180,140,230,.4]]){const light=new THREE.DirectionalLight(0xffffff,intensity);light.position.set(x,y,z);scene.add(light);}
  const clip=new THREE.Plane(new THREE.Vector3(0,1,0),-45);
  let selected=null,grid=null;const centre=new THREE.Vector3(62,45,40),centreGoal=centre.clone();
  function decode(raw){const bytes=Uint8Array.from(atob(raw),c=>c.charCodeAt(0));return new Float32Array(bytes.buffer);}
  cad.parts.forEach(part=>{
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(decode(part.positions_b64),3));geometry.computeVertexNormals();
    const material=new THREE.MeshStandardMaterial({color:new THREE.Color(part.color).convertSRGBToLinear(),roughness:.7,metalness:.07,side:THREE.DoubleSide});
    const mesh=new THREE.Mesh(geometry,material);mesh.userData.part=part;
    mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry,38),new THREE.LineBasicMaterial({color:0x1b2a31,transparent:true,opacity:.25})));
    scene.add(mesh);meshes.set(part.id,mesh);
    const label=document.createElement('span');label.className='part-label';label.textContent=part.name;$('labels').append(label);labels.set(part.id,label);
  });
  function applyTheme(){
    const css=getComputedStyle(document.documentElement);scene.background=new THREE.Color(css.getPropertyValue('--view').trim());
    if(grid){scene.remove(grid);grid.geometry.dispose();grid.material.dispose();}
    grid=new THREE.GridHelper(800,40,new THREE.Color(css.getPropertyValue('--grid-a').trim()),new THREE.Color(css.getPropertyValue('--grid-b').trim()));grid.rotation.x=Math.PI/2;grid.position.z=-.2;scene.add(grid);
    for(const mesh of meshes.values())mesh.children[0].material.color.set(css.getPropertyValue('--edge').trim());
    dirty=true;
  }
  applyTheme();window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change',applyTheme);
  function pose(){
    for(const part of cad.parts){const mesh=meshes.get(part.id),offset=offsetAt(part,T);mesh.position.set(...offset);
      const moving=Math.abs(T-target)>1e-6&&offsetAt(part,Math.max(0,T-.02)).some((v,j)=>Math.abs(v-offset[j])>.001);
      mesh.material.emissive.set(part.id===selected?'#0e7c86':(moving?'#0a454a':'#000000'));mesh.material.emissiveIntensity=.2;
    }
  }
  function bounds(){
    const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];
    for(const part of cad.parts){const mesh=meshes.get(part.id);if(!mesh.visible)continue;
      for(let k=0;k<3;k++){low[k]=Math.min(low[k],part.bounds[k]+mesh.position.getComponent(k));high[k]=Math.max(high[k],part.bounds[k+3]+mesh.position.getComponent(k));}
    }
    if(!Number.isFinite(low[0]))return [new THREE.Vector3(0,0,0),new THREE.Vector3(125,90,60)];
    return [new THREE.Vector3(...low),new THREE.Vector3(...high)];
  }
  function frameGoal(){
    const [lo,hi]=bounds();centreGoal.copy(lo).add(hi).multiplyScalar(.5);
    const back=new THREE.Vector3(Math.cos(el)*Math.cos(az),Math.cos(el)*Math.sin(az),Math.sin(el));
    const right=new THREE.Vector3().crossVectors(camera.up,back).normalize(),up=new THREE.Vector3().crossVectors(back,right).normalize();
    const tangent=Math.tan(camera.fov*Math.PI/360);let fit=70;
    for(const x of [lo.x,hi.x])for(const y of [lo.y,hi.y])for(const z of [lo.z,hi.z]){
      const point=new THREE.Vector3(x,y,z).sub(centreGoal),depth=point.dot(back);
      fit=Math.max(fit,Math.abs(point.dot(right))/(tangent*camera.aspect)+depth,Math.abs(point.dot(up))/tangent+depth);
    }
    return fit*1.12*zoom;
  }
  function preset(name){
    const values={iso:[-.96,.58],top:[-Math.PI/2,Math.PI/2-.001],side:[-Math.PI/2,.001],end:[0,.001]};
    [az,el]=values[name];zoom=1;dirty=true;labelsDirty=true;
    for(const [id,key]of [['vIso','iso'],['vTop','top'],['vSide','side'],['vEnd','end']])$(id).setAttribute('aria-pressed',String(key===name));
  }
  $('vIso').onclick=()=>preset('iso');$('vTop').onclick=()=>preset('top');$('vSide').onclick=()=>preset('side');$('vEnd').onclick=()=>preset('end');$('vReset').onclick=()=>preset('iso');
  $('oEdge').onchange=()=>{for(const mesh of meshes.values())mesh.children[0].visible=$('oEdge').checked;dirty=true;};
  $('oCut').onchange=()=>{for(const mesh of meshes.values())for(const object of [mesh,mesh.children[0]])object.material.clippingPlanes=$('oCut').checked?[clip]:[];dirty=true;};
  $('oLabels').onchange=()=>{dirty=true;labelsDirty=true;};
  function inspect(id){const part=cad.parts.find(p=>p.id===id);if(!part)return;selected=id;$('partInfo').textContent=part.name+' — '+part.kind+'. '+part.note;dirty=true;}
  const pointers=new Map();let pinch=0,start=null;
  $('view').addEventListener('pointerdown',event=>{start=[event.clientX,event.clientY];$('view').setPointerCapture(event.pointerId);pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});});
  $('view').addEventListener('pointermove',event=>{
    const p=pointers.get(event.pointerId);if(!p)return;
    if(pointers.size===1){az-=(event.clientX-p.x)*.008;el=Math.max(-1.3,Math.min(1.56,el+(event.clientY-p.y)*.008));}
    else if(pointers.size===2){const other=[...pointers.entries()].find(([id])=>id!==event.pointerId)[1];const d=Math.hypot(event.clientX-other.x,event.clientY-other.y);if(pinch>0)zoom=Math.max(.35,Math.min(2.5,zoom*pinch/d));pinch=d;}
    p.x=event.clientX;p.y=event.clientY;dirty=true;labelsDirty=true;
  });
  $('view').addEventListener('pointerup',event=>{
    pointers.delete(event.pointerId);pinch=0;
    if(start&&Math.hypot(event.clientX-start[0],event.clientY-start[1])<5){
      const rect=$('view').getBoundingClientRect(),ray=new THREE.Raycaster();ray.setFromCamera(new THREE.Vector2((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1),camera);
      const hit=ray.intersectObjects([...meshes.values()].filter(m=>m.visible),false)[0];if(hit)inspect(hit.object.userData.part.id);
    }
  });
  $('view').addEventListener('pointercancel',event=>{pointers.delete(event.pointerId);pinch=0;});
  $('view').addEventListener('wheel',event=>{event.preventDefault();zoom=Math.max(.35,Math.min(2.5,zoom*Math.exp(event.deltaY*.0012)));dirty=true;},{passive:false});
  function resize(){const w=$('view').clientWidth,h=$('view').clientHeight;if(w<2||h<2)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();dirty=true;}
  new ResizeObserver(resize).observe($('view'));resize();preset('iso');
  function updateLabels(){
    for(const part of cad.parts){const mesh=meshes.get(part.id),label=labels.get(part.id);label.hidden=!$('oLabels').checked||!mesh.visible;if(label.hidden)continue;
      const b=part.bounds,point=new THREE.Vector3((b[0]+b[3])/2,(b[1]+b[4])/2,b[5]+2).add(mesh.position).project(camera);
      label.hidden=point.z>1||point.z< -1||Math.abs(point.x)>1||Math.abs(point.y)>1;
      label.style.left=(point.x+1)/2*$('view').clientWidth+'px';label.style.top=(1-point.y)/2*$('view').clientHeight+'px';
    }
  }
  let last=performance.now();
  function tick(now){
    requestAnimationFrame(tick);const dt=Math.min(.05,(now-last)/1000);last=now;
    if(Math.abs(target-T)>1e-6){
      T=reduce?target:T+Math.sign(target-T)*Math.min(Math.abs(target-T),dt*.8);
      if(Math.abs(target-T)<1e-6){T=target;pauseUntil=now+800;}
      dirty=true;updateUI();
    }else if(playing&&now>=pauseUntil){
      if(T>=N-1e-6){playing=false;updateUI();}
      else{target=Math.floor(T+1e-6)+1;if(reduce){T=target;pauseUntil=now+1100;dirty=true;updateUI();}}
    }
    pose();const goal=frameGoal();let moved=false;
    if(Math.abs(goal-distance)>.03){distance+=(goal-distance)*.18;moved=true;}
    if(centre.distanceTo(centreGoal)>.01){centre.lerp(centreGoal,.18);moved=true;}
    if(!dirty&&!moved)return;
    camera.position.set(centre.x+distance*Math.cos(el)*Math.cos(az),centre.y+distance*Math.cos(el)*Math.sin(az),centre.z+distance*Math.sin(el));camera.lookAt(centre);
    renderer.render(scene,camera);updateLabels();dirty=false;labelsDirty=false;
  }
  window.CTS_ASSEMBLY={data:cad,state,meshes,scene,camera,renderer,offsetAt,inspect,go,preset};
  updateUI();requestAnimationFrame(tick);
})();
