/* Housing-only Chrome checks. Never loads or writes ADCS Testbench data. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
const {pathToFileURL}=require('node:url');

(async()=>{
  // Default to the Chromium installed by this Playwright version on any OS.
  // An explicitly selected browser is optional, never a machine prerequisite.
  const executable=process.env.CTS_CHROME_EXECUTABLE;
  const browser=await chromium.launch({executablePath:executable,headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[],bad=[];
    page.on('pageerror',e=>errors.push(String(e)));page.on('response',r=>{if(r.status()>=400)bad.push(r.url());});
    const base=process.env.CTS_VIEWER_BASE_URL||'http://127.0.0.1:8765';
    await page.route('**/*',route=>route.request().url().startsWith('http')&&!route.request().url().startsWith(base)?route.abort():route.continue());
    assert.equal((await page.goto(base+'/CTS_Simple_Visulizers/External%20Electronics%20Enclosure/index.html')).status(),200);
    await page.waitForFunction(()=>window.CTS_ASSEMBLY);
    const N=await page.evaluate(()=>CTS_ASSEMBLY.data.steps.length-1);
    assert.ok(page.url().endsWith('/External%20Electronics%20Enclosure/index.html'));
    assert.equal(await page.title(),'External Electronics Enclosure Assembly');
    assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.data.parts.filter(p=>p.kind==='Printed CAD').length),4);
    assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.state.progress),0);
    assert.equal(await page.locator('#steps li').count(),9);
    await page.locator('#bNext').click();await page.waitForFunction(()=>CTS_ASSEMBLY.state.progress===1);
    await page.locator('#bPrev').click();await page.waitForFunction(()=>CTS_ASSEMBLY.state.progress===0);
    await page.locator('#bPlay').click();await page.waitForTimeout(1100);
    assert.ok(await page.evaluate(()=>CTS_ASSEMBLY.state.progress)>.1);
    await page.locator('#bPlay').click();const paused=await page.evaluate(()=>CTS_ASSEMBLY.state.progress);
    await page.waitForTimeout(250);assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.state.progress),paused);
    assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.state.playing),false);
    await page.locator('#scrub').evaluate((el,n)=>{el.value=n-.2;el.dispatchEvent(new Event('input'));},N);
    await page.locator('#bPlay').click();await page.waitForFunction(n=>CTS_ASSEMBLY.state.progress===n&&!CTS_ASSEMBLY.state.playing,N);
    assert.equal(await page.locator('#bPlay').textContent(),'Replay');
    await page.locator('#bPlay').click();await page.waitForFunction(()=>CTS_ASSEMBLY.state.progress<1);
    await page.locator('#bPlay').click();
    for(const time of [0,1,1.6,2,2.6,3,4,4.5,4.8,5,5.25,5.65,6,6.3,6.6,7,8]){
      await page.locator('#scrub').evaluate((el,t)=>{el.value=t;el.dispatchEvent(new Event('input'));},String(time));
      assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.state.progress),time);
      await page.waitForFunction(t=>CTS_ASSEMBLY.data.parts.every(p=>CTS_ASSEMBLY.meshes.get(p.id).position.toArray().every((v,k)=>Math.abs(v-CTS_ASSEMBLY.offsetAt(p,t)[k])<1e-4)),time,{timeout:5000});
    }
    await page.locator('#bKit').click();assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.state.target),0);
    await page.locator('#bDone').click();assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.state.target),N);
    for(const id of ['vIso','vTop','vSide','vEnd','vReset']){
      await page.locator('#'+id).click();assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.camera.position.toArray().every(Number.isFinite)),true);
    }
    await page.getByRole('checkbox',{name:'Show External Tray',exact:true}).uncheck();
    assert.equal(await page.evaluate(()=>CTS_ASSEMBLY.meshes.get('tray').visible),false);
    await page.getByRole('checkbox',{name:'Show External Tray',exact:true}).check();
    await page.locator('#oCut').check();assert.equal(await page.evaluate(()=>[...CTS_ASSEMBLY.meshes.values()].every(m=>m.material.clippingPlanes.length===1)),true);
    await page.locator('#oCut').uncheck();await page.locator('#oEdge').uncheck();
    assert.equal(await page.evaluate(()=>[...CTS_ASSEMBLY.meshes.values()].every(m=>!m.children[0].visible)),true);
    await page.locator('#oEdge').check();await page.locator('#oLabels').check();await page.waitForTimeout(150);
    assert.ok(await page.locator('.part-label:visible').count()>0);
    await page.getByRole('button',{name:'Frame M2.5 × 10 screws',exact:false}).click();
    assert.ok((await page.locator('#partInfo').textContent()).includes('unmeasured'));
    await page.locator('#scrub').evaluate((el,n)=>{el.value=n;el.dispatchEvent(new Event('input'));},N);await page.waitForTimeout(600);
    await page.locator('canvas').scrollIntoViewIfNeeded();
    const bounds=await page.locator('canvas').boundingBox(),before=await page.evaluate(()=>CTS_ASSEMBLY.state.camera);
    await page.mouse.move(bounds.x+bounds.width/2,bounds.y+bounds.height/2);await page.mouse.down();await page.mouse.move(bounds.x+bounds.width*.6,bounds.y+bounds.height*.55,{steps:8});await page.mouse.up();
    assert.notDeepEqual(await page.evaluate(()=>CTS_ASSEMBLY.state.camera),before);
    const zoom=await page.evaluate(()=>CTS_ASSEMBLY.state.camera[2]);await page.mouse.wheel(0,150);await page.waitForTimeout(150);
    assert.notEqual(await page.evaluate(()=>CTS_ASSEMBLY.state.camera[2]),zoom);
    for(const url of await page.locator('a').evaluateAll(nodes=>nodes.map(a=>a.href).filter(url=>url.startsWith(location.origin))))assert.equal((await page.request.get(url)).status(),200,'Broken link '+url);
    await page.setViewportSize({width:390,height:844});await page.waitForTimeout(200);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Mobile overflow');
    assert.deepEqual(errors,[]);assert.deepEqual(bad,[]);
    const reduced=await browser.newPage({reducedMotion:'reduce'});await reduced.goto(base+'/CTS_Simple_Visulizers/External%20Electronics%20Enclosure/index.html');await reduced.waitForFunction(()=>window.CTS_ASSEMBLY);
    await reduced.locator('#bNext').click();assert.equal(await reduced.evaluate(()=>CTS_ASSEMBLY.state.progress),1);
    const sceneText=await page.evaluate(()=>JSON.stringify(CTS_ASSEMBLY.data));
    const quantities=await page.evaluate(()=>({screws:CTS_ASSEMBLY.data.parts.filter(p=>/screws/.test(p.name)).reduce((a,p)=>a+p.quantity,0),nuts:CTS_ASSEMBLY.data.parts.filter(p=>/nut/.test(p.name)).reduce((a,p)=>a+p.quantity,0)}));
    assert.deepEqual(quantities,{screws:10,nuts:10});
    if(process.env.CTS_SCREENSHOT_DIR){
      fs.mkdirSync(process.env.CTS_SCREENSHOT_DIR,{recursive:true});await reduced.setViewportSize({width:1440,height:1150});
      await reduced.locator('#bDone').click();await reduced.waitForTimeout(2200);
      await reduced.screenshot({path:path.join(process.env.CTS_SCREENSHOT_DIR,'assembled.png'),fullPage:true});
      await reduced.locator('#bKit').click();await reduced.waitForTimeout(2200);
      await reduced.screenshot({path:path.join(process.env.CTS_SCREENSHOT_DIR,'exploded.png'),fullPage:true});
    }
    let standalone=false;
    if(process.env.CTS_STANDALONE_PATH){
      const offline=await browser.newPage({reducedMotion:'reduce'}),network=[];
      offline.on('pageerror',e=>errors.push(String(e)));
      await offline.route('**/*',route=>{if(route.request().url().startsWith('http')){network.push(route.request().url());return route.abort();}return route.continue();});
      await offline.goto(pathToFileURL(path.resolve(process.env.CTS_STANDALONE_PATH)).href);await offline.waitForFunction(()=>window.CTS_ASSEMBLY);
      assert.equal(await offline.evaluate(()=>JSON.stringify(CTS_ASSEMBLY.data)),sceneText,'Standalone contains stale scene');
      await offline.locator('#bNext').click();assert.equal(await offline.evaluate(()=>CTS_ASSEMBLY.state.progress),1);
      await offline.locator('#bDone').click();assert.equal(await offline.evaluate(()=>CTS_ASSEMBLY.state.progress),N);
      assert.deepEqual(network,[],'Standalone requested external resources');standalone=true;await offline.close();
    }
    assert.deepEqual(errors,[]);
    const report={scope:'External housing viewer only',stages:9,standaloneOffline:standalone,quantities,finalUrl:page.url(),playPause:true,nextPrevious:true,progressKeyframes:true,kitComplete:true,
                  cameraPresets:true,orbitZoom:true,sectionCut:true,outlines:true,visibility:true,labels:true,partsAndQuantities:true,
                  mobileLayout:true,reducedMotion:true,pageErrors:errors,failedResources:bad};
    fs.writeFileSync(path.resolve(__dirname,'../mechanical/housing_browser_validation.json'),JSON.stringify(report,null,2)+'\n');
    console.log('PASS housing-only browser assembly interactions');
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
