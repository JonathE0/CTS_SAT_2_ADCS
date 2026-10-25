// Execute the actual embedded routing helpers without a browser.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('cubesat_control_lab.py','utf8');
const start=source.indexOf('function portY('),end=source.indexOf('function drawWires()',start);
assert(start>=0,'Routing helpers missing');
const context={graph:{nodes:[],edges:[]},DATA:{ports:{Gain:1,Sum:2}},Math};
vm.createContext(context);vm.runInContext(source.slice(start,end),context);
const n=(id,x,y,type='Gain')=>({id,x,y,type});
function route(nodes,a,b,port=0){context.graph.nodes=nodes;const result=context.routeWire(a,b,port);assert(result,'No route found');for(let i=1;i<result.length;i++){const p=result[i-1],q=result[i];assert(p[0]===q[0]||p[1]===q[1],'Diagonal wire');}return result;}
const a=n('a',50,100),b=n('b',600,100);
assert.equal(route([a,b],a,b).length,2,'Aligned ports should have one straight segment');
const obstacle=n('obstacle',240,80),detour=route([a,b,obstacle],a,b);
assert(detour.length>2,'Wire must avoid intervening block');
for(let i=1;i<detour.length;i++)assert(context.clearSegment(detour[i-1],detour[i],[context.blockRect(obstacle)]),'Wire intersects obstacle');
const feedback=route([a,b],b,a);assert(feedback.length>=4,'Feedback must go around blocks');
const lower=n('lower',420,270);assert(route([a,lower],a,lower).length<=4,'Simple forward wire needs at most two bends');
context.graph={nodes:[a,b],edges:[{source:'a',target:'b',port:0}]};
assert.equal(context.snapBlock(b,400,107,1,false).y,100,'Nearby ports should snap');
assert.equal(context.snapBlock(b,400,115,1,false).y,115,'Distant ports should not snap');
assert.equal(context.snapBlock(b,400,107,1,true).y,107,'Alt bypasses snapping');
const sum=n('sum',400,100,'Sum');context.graph={nodes:[a,sum],edges:[{source:'a',target:'sum',port:1}]};
assert.equal(context.snapBlock(sum,400,89,1,false).y,84,'Snap must align actual second input port');
assert.equal(context.snapBlock(sum,400,96,.5,false).y,84,'Snap distance scales with zoom');
// A staggered corridor requires more than a single detour.
const finish=n('finish',1000,100),barriers=[n('c',280,60),n('d',490,180),n('e',700,50)];
const complex=route([a,finish,...barriers],a,finish);
for(let i=1;i<complex.length;i++)assert(context.clearSegment(complex[i-1],complex[i],barriers.map(context.blockRect)));
console.log('Routing and snap tests passed');
const lessons=JSON.parse(require('node:child_process').execFileSync('python',['-c','import json,cubesat_control_lab as c; print(json.dumps([c.lesson_graph(i) for i in range(5)]))'],{encoding:'utf8'}));
context.DATA.ports={Constant:0,Gain:1,Sum:2,Integrator:1,Saturation:1,'Cross Product':2,Normalize:1,Scope:1,'Rotate to Body':2,'Quaternion Rate':2};
for(const [index,g] of lessons.entries()){
  context.graph=g;
  for(const e of g.edges){const a=g.nodes.find(n=>n.id===e.source),b=g.nodes.find(n=>n.id===e.target);const points=context.routeWire(a,b,e.port);assert(points,`Lesson ${index+1}: blocked route ${e.source} -> ${e.target}`);for(let i=1;i<points.length;i++)assert(context.clearSegment(points[i-1],points[i],g.nodes.filter(n=>n.id!==a.id&&n.id!==b.id).map(context.blockRect)),`Lesson ${index+1}: route crosses another block`);}
}
console.log('All five lesson diagrams route around blocks');
