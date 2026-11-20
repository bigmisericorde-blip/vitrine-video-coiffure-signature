import '../../commun/metiers.js';
import '../../commun/exemples.js';
import {inspect,demoBlob,inputs} from './media.mjs';
import {loadCore,resourceURL} from './engine/resources.mjs';
import {restoreFiche,href,sceneText,contactAction} from './engine/fiche.mjs';
import {createJob,newId,validateResult,validError,RenderFault} from './engine/contract.mjs';
import {rotate,releaseReservation} from './engine/rotation.mjs';
const $=id=>document.getElementById(id);
const params=new URLSearchParams(location.search), ticket=params.get('fiche');
const q=Number(params.get('ecran'));
const preview=Number.isInteger(q)&&q>=1&&q<=12?q:0;
const {VVBeaute:ui,VVExemples:catalogue}=globalThis, baseURL=new URL('../../',import.meta.url);
let CORE,DATA,saved=null,job=null,demo=false,scenes=[],metier='autre',sample=null;
const takes=new Map(),accepted=new Set(),samples=new Map();
const cam=$('cam'),replay=$('replay'),ad=$('ad');
let idx=0,state='A',epoch=0,eventScope=new AbortController(),animation=0,recSession=null,activeRun=null,renderId=null,detailEditor=null,result=null;
const current=()=>scenes[idx];
const fmt=s=>`0:${String(Math.max(0,Math.floor(s))).padStart(2,'0')}`;
const reference=s=>catalogue.asset(metier,'t2',s.id+'.mp4',baseURL)?.href||null;
const sizeAt=()=>current().secondes;
const canReuse=()=>!preview&&!demo&&current().id==='S3'&&accepted.has('S2')&&takes.has('S2');
const freezeAt=()=>[.88,1.2,3.8,4.72][idx];

function releaseVideo(v){
  v.pause();v.srcObject=null;v.removeAttribute('src');v.load();
}
function showError(text,retry=null){
  $('mediaMessage').textContent=text;
  $('mediaRetry').hidden=!retry;$('mediaRetry').onclick=retry;
  $('mediaBack').hidden=!!preview;$('mediaFeedback').hidden=false;
}
function clearError(){$('mediaFeedback').hidden=true;}
function stopRecord(session){
  if(!session)return;
  session.live=false;
  if(session.mr.state!=='inactive')session.mr.stop();
  session.stream.getTracks().forEach(t=>t.stop());
  if(recSession===session)recSession=null;
}
function transition(next){
  $('sansExtrait').hidden=true;delete $('app').dataset.detailPreview;
  epoch++;eventScope.abort();eventScope=new AbortController();cancelAnimationFrame(animation);
  stopRecord(recSession);cancelDetail();clearError();releaseVideo(cam);releaseVideo(replay);replay.style.display='none';
  for(const name of ['rec','review','panelMontage'])$(name).classList.remove('on');
  $('sheet').classList.toggle('hidden',next!=='A');
  $('scrim').classList.toggle('off',next!=='A');
  $('rec').setAttribute('aria-hidden','true');
  state=next;$('app').dataset.state=next;$('app').dataset.prise=current().id;
  return epoch;
}
function bullets(el,data,mark){
  el.replaceChildren(...data.map(text=>{
    const li=document.createElement('li'),i=document.createElement('span'),t=document.createElement('span');
    i.className='mark';i.textContent=mark;t.textContent=text;li.append(i,t);return li;
  }));
}
function updateScroll(){
  const s=$('sheetBody');$('scrollHint').hidden=state!=='A'||s.scrollHeight-s.clientHeight<=10||s.scrollTop+s.clientHeight>=s.scrollHeight-14;
}
function describeContext(){
  const s=current(), hint=sceneText(job,idx);
  $('sceneCounter').textContent=`PRISE ${s.n}/4 · ${s.role}`;
  $('dots').replaceChildren(...scenes.map(x=>{const i=document.createElement('i');i.classList.toggle('on',x.n<=s.n);return i;}));
  $('durationLabel').textContent=s.secondes+' secondes';$('sceneTitle').textContent=s.titre;
  $('consigne').textContent=s.consigne;
  bullets($('listFilm'),s.a_filmer,'✓');bullets($('listAvoid'),s.a_eviter,'✕');
  for(const key of ['caseContext','recContext','reviewContext']){$(key).textContent=(preview||demo)&&sample?sample.details[idx]:hint;$(key).hidden=!((preview||demo)&&sample)&&!saved;}
  $('soundText').textContent=DATA.sound;$('captureConsent').textContent=DATA.consent;
  $('reviewQuestion').textContent=s.question_relecture;
  $('next').textContent=s.n===4?'VOIR MON MONTAGE':'VALIDER ET CONTINUER';
  $('reviewLabel').textContent=`PRISE ${s.n} · ${fmt(s.secondes)}`;
}
function showGuide(i=idx){
  idx=i;transition('A');describeContext();
  const ref=(preview||demo)&&reference(current());
  cam.style.display=ref?'block':'none';
  if(ref){cam.muted=true;cam.loop=!preview;cam.src=ref;if(!preview)cam.play().catch(()=>{});else on(cam,'loadedmetadata',()=>{cam.currentTime=freezeAt();},{once:true});}
  $('cta').textContent=(demo||preview&&ref)?'LIRE LA PRISE D’EXEMPLE':'COMMENCER À FILMER';
  $('cta').disabled=!!preview;
  $('cameraBtn').disabled=false;$('cameraBtn').hidden=!!preview||demo;
  $('reuseTake').hidden=!canReuse();$('reuseTake').disabled=false;
  $('micOption').hidden=!!preview||demo;
  $('takeHelp').hidden=demo||!!preview;
  $('takeHelp').textContent=`Filme en 9:16 · ${sizeAt()} s · MP4, MOV ou WebM · 40 Mio maxi.`;
  $('sheetBody').scrollTop=0;requestAnimationFrame(updateScroll);
}
function on(v,event,fn,extra={}){v.addEventListener(event,fn,{signal:eventScope.signal,...extra});}
function setProgress(t){
  const p=Math.min(t/sizeAt(),1);
  $('chronoVal').textContent=fmt(Math.min(sizeAt(),t));$('barFill').style.width=(p*100)+'%';
  $('bar').classList.toggle('hot',sizeAt()-t<=2);$('chrono').classList.toggle('hot',sizeAt()-t<=2);
}
function showB(label,cancel){
  const e=transition('B');cam.style.display='block';cam.loop=false;cam.muted=true;
  $('recordLabel').textContent=label;$('cancelCapture').hidden=!cancel;
  $('rec').classList.add('on');$('rec').setAttribute('aria-hidden','false');setProgress(0);return e;
}
function drop(s){
  if(renderId)invalidateRender();
  accepted.delete(s.id);const t=takes.get(s.id);if(t)URL.revokeObjectURL(t.url);takes.delete(s.id);
  if(s.id==='S2'&&takes.get('S3')?.reuseFrom==='S2')drop(scenes[2]);
}
function keepTake(file,meta,detailPreview=null){
  const s=current();drop(s);const t={file,meta,reuseFrom:detailPreview?'S2':null,url:URL.createObjectURL(detailPreview??file)};takes.set(s.id,t);return t;
}
async function intake(file,label){
  if(state!=='A'||preview)return;
  const e=epoch;const s=current();$('cta').disabled=$('cameraBtn').disabled=$('reuseTake').disabled=true;clearError();
  try {
    const blob=await file;
    const meta=await inspect(blob,s.secondes);
    if(epoch!==e)return;
    const t=keepTake(blob,meta);
    const started=showB(label,true);
    cam.src=t.url;
    const go=()=>{cam.play().then(clearError).catch(()=>showError('Appuie sur Réessayer pour lire la prise.',go));};
    on(cam,'error',()=>showError('La vidéo n’a pas chargé. Reviens à la consigne.',null));
    on(cam,'ended',()=>{if(epoch===started)showReview(t);});
    go();
    const tick=()=>{
      if(epoch!==started)return;
      const time=cam.currentTime;setProgress(time);
      if(time>=s.secondes-.020){showReview(t);return;}
      animation=requestAnimationFrame(tick);
    };animation=requestAnimationFrame(tick);
  } catch(err){if(epoch===e)showError(err.message);}
  finally{if(epoch===e){$('cta').disabled=$('cameraBtn').disabled=$('reuseTake').disabled=false;}}
}
async function example(s){
  if(!samples.has(s.id))samples.set(s.id,demoBlob(reference(s)).catch(e=>{samples.delete(s.id);throw e;}));
  return samples.get(s.id);
}
async function filmLive(){
  if(preview||demo||state!=='A')return;
  if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined'){showError('Caméra indisponible ici. Filme avec ton téléphone puis importe le fichier.');return;}
  const e=epoch,s=current(),audio=$('wantMic').checked;let stream;
  $('cta').disabled=$('cameraBtn').disabled=$('reuseTake').disabled=true;clearError();
  try {
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:720},height:{ideal:1280},aspectRatio:{ideal:9/16},frameRate:{ideal:30,max:30}},audio});
    if(epoch!==e){stream.getTracks().forEach(t=>t.stop());return;}
    const mimes=audio?['video/mp4','video/webm;codecs=vp8,opus','video/webm']:['video/mp4','video/webm;codecs=vp8','video/webm'];
    const mimeType=mimes.find(m=>MediaRecorder.isTypeSupported(m));
    const mr=new MediaRecorder(stream,{...(mimeType?{mimeType}:{}),videoBitsPerSecond:4500000});
    const phase=showB(audio?'Enregistrement · micro actif':'Enregistrement · micro coupé',true);
    const r={mr,stream,live:true,finished:false,parts:[]};recSession=r;
    const fail=(msg)=>{if(epoch!==phase)return;showGuide();showError(msg);};
    mr.ondataavailable=x=>{if(x.data.size)r.parts.push(x.data);};
    mr.onerror=()=>fail('La caméra a interrompu la prise. Recommence ou importe un fichier.');
    stream.getVideoTracks().forEach(t=>t.addEventListener('ended',()=>{if(!r.finished&&r.live)fail('La caméra a été interrompue.');},{once:true}));
    mr.onstop=async()=>{
      if(!r.finished||epoch!==phase)return;
      try {
        const file=new Blob(r.parts,{type:mr.mimeType||r.parts[0]?.type||'video/webm'});
        const meta=await inspect(file,s.secondes);if(epoch===phase)showReview(keepTake(file,meta));
      }catch(err){fail(err.message+' Tu peux aussi importer une prise.');}
    };
    cam.srcObject=stream;
    await cam.play();
    if(epoch!==phase)return;
    mr.start(250);const wall=performance.now();
    const tick=()=>{
      if(epoch!==phase||!r.live)return;
      const t=(performance.now()-wall)/1000;setProgress(t);
      if(t>=s.secondes+.19){r.finished=true;stopRecord(r);return;}
      animation=requestAnimationFrame(tick);
    };animation=requestAnimationFrame(tick);
  }catch(err){
    stream?.getTracks().forEach(t=>t.stop());
    if(epoch===e||state==='B'&&recSession?.stream===stream){showGuide();showError(err.name==='NotAllowedError'?'Autorisation caméra ou micro refusée. Tu peux réessayer ou importer un fichier.':'Impossible de lancer la caméra. Tu peux importer un fichier.');}
  }finally{if(epoch===e){$('cta').disabled=$('cameraBtn').disabled=$('reuseTake').disabled=false;}}
}
function cancelDetail(){
  if(!detailEditor)return;
  clearTimeout(detailEditor.timer);detailEditor.instance.terminate();detailEditor=null;
}
function previewDetail(){
  if(state!=='A'||!canReuse())return;
  const t=takes.get('S2');showB('Préparation du détail recadré…',true);cam.style.display='none';
  let instance;
  const fail=msg=>{showGuide();showError(msg+' Tu peux aussi importer ou filmer le détail.');};
  try{instance=new Worker(renderURL(),{type:'module',name:'T2 · Aperçu du détail'});}
  catch{fail('Impossible de préparer l’aperçu.');return;}
  detailEditor={instance,timer:setTimeout(()=>fail('La préparation de l’aperçu est trop longue.'),45000)};
  instance.onmessage=({data})=>{
    if(detailEditor?.instance!==instance)return;
    if(data.stage==='error'){fail(data.message);return;}
    if(data.stage==='done'){
      showReview(keepTake(t.file,t.meta,new Blob([data.buffer],{type:'video/mp4'})));
    }else if(data.completed&&data.total){
      $('barFill').style.width=100*data.completed/data.total+'%';
      $('chronoVal').textContent=Math.round(100*data.completed/data.total)+'%';
    }
  };
  instance.onerror=instance.onmessageerror=()=>fail('L’aperçu du détail n’a pas chargé.');
  instance.postMessage({kind:'detail',files:{S2:t.file}});
}
function showReview(t,{frozen=false}={}){
  transition('C');cam.style.display='none';replay.style.display='block';replay.loop=true;replay.muted=true;
  if(t.reuseFrom)$('app').dataset.detailPreview='true';
  $('review').classList.add('on');$('next').disabled=true;$('redo').disabled=!!preview;
  $('reviewMode').textContent=frozen?'Aperçu · aucune prise validée':t.reuseFrom?'Geste recadré · aperçu sans son':t.meta.hasAudio?'Son d’origine disponible':'Cette prise est muette';
  $('reviewOrigin').textContent=t.reuseFrom?'Vidéo du geste':frozen||demo?(sample?'Prise d’exemple':'Aperçu'):'Ta vidéo';
  $('reviewLabel').textContent=t.reuseFrom?'VUE 3 · DÉTAIL':`PRISE ${current().n} · ${fmt(sizeAt())}`;
  $('reviewQuestion').textContent=t.reuseFrom?'Le détail se voit-il nettement dans ces extraits recadrés ? Sinon, filme ou importe un plan plus serré.':current().question_relecture;
  $('next').textContent=t.reuseFrom?'VALIDER CE DÉTAIL':current().n===4?'VOIR MON MONTAGE':'VALIDER ET CONTINUER';
  $('toggleTakeAudio').hidden=frozen||!!t.reuseFrom||!t.meta.hasAudio;$('toggleTakeAudio').textContent='Écouter';
  let ready=false,timeout=0;
  if(!frozen){
    on(replay,'loadeddata',()=>{ready=true;clearTimeout(timeout);$('next').disabled=false;clearError();},{once:true});
    on(replay,'error',()=>{clearTimeout(timeout);$('next').disabled=true;showError('Cette prise ne se lit pas. Refais-la ou importe un autre fichier.');});
    timeout=setTimeout(()=>{if(state==='C'&&!ready)showError('La relecture n’a pas pu commencer.');},7000);
    eventScope.signal.addEventListener('abort',()=>clearTimeout(timeout),{once:true});
  }
  if(!t.url){replay.style.display='none';$('sansExtrait').hidden=false;return;}
  replay.src=t.url;
  replay.play().catch(()=>{if(!frozen&&!ready&&state==='C')showError('Relis la prise avant de valider.',()=>replay.play().catch(()=>{}));});
}
function clearResult(){
  if(!result)return;releaseVideo(ad);URL.revokeObjectURL(result.url);result=null;
}
function showResult(out){
  clearResult();
  const {result:meta,buffer}=out;
  const url=URL.createObjectURL(new Blob([buffer],{type:meta.media.mime}));result={url};
  $('app').hidden=true;$('resultPage').hidden=false;$('resultHeading').textContent=demo?'Le montage d’exemple est prêt.':'Ta vidéo est prête.';
  $('resultMeta').textContent=[job.salon,job.service,job.ville,job.tarif].filter(Boolean).join(' · ');
  $('resultCredit').hidden=!demo;
  if(demo)$('resultCredit').textContent=`Images : ${sample.credit} / Pexels · Exemple, pas une offre réelle.`;
  $('resultError').textContent='';const dest=contactAction(job);const contact=$('resultContact');contact.hidden=!dest;
  if(dest){contact.href=dest.href;contact.textContent=dest.label;}else contact.removeAttribute('href');
  const track=CORE.music.tracks.find(x=>x.id===meta.music.variant);
  const musicLink=$('musicLink');musicLink.textContent=track.title+' — '+track.artist;musicLink.href=track.source;
  $('musicLicence').href=track.licence;$('musicAi').hidden=!track.ai_disclosed;
  $('endDownload').href=url;ad.src=url;ad.muted=false;
  Object.assign($('resultPage').dataset,{revision:meta.template_version,frames:String(meta.media.frames),sources:String(meta.source_count),track:meta.music.variant,sha256:meta.media.sha256});
  $('resultEdit').href=href('index.html',ticket,{metier});state='ad';
  window.scrollTo(0,0);
}
const renderURL=()=>resourceURL(CORE.template.paths.worker);
function invalidateRender(){
  activeRun?.abort();activeRun=null;
  const id=renderId;renderId=null;
  if(id&&!demo)Promise.resolve().then(()=>releaseReservation(CORE,id)).catch(()=>{});
}
function runWorker(spec,files,signal){
  return new Promise((resolve,reject)=>{
    signal.throwIfAborted();
    let instance;
    try{instance=new Worker(renderURL(),{type:'module',name:'Export T2 · Coiffure et beauté'});}catch{reject(new RenderFault('PLATFORM'));return;}
    const close=(error,data)=>{
      clearTimeout(timer);signal.removeEventListener('abort',abort);instance.terminate();
      if(error)reject(error);else resolve(data);
    };
    const abort=()=>close(new RenderFault('CANCELLED'));
    const timer=setTimeout(()=>close(new RenderFault('TIMEOUT')),160000);
    signal.addEventListener('abort',abort,{once:true});
    instance.onmessage=({data})=>{
      if(signal.aborted)return;
      if(data.stage==='error'){
        const r=data.error;
        close(validError(r)?new RenderFault(r.code,r.message):new RenderFault('RENDER_FAILED'));return;
      }
      if(data.stage==='done'){
        try{
          if(!(data.buffer instanceof ArrayBuffer))throw new RenderFault('RENDER_FAILED');
          validateResult(data.result,spec,CORE,data.buffer.byteLength);close(null,data);
        }catch(err){close(err);}return;
      }
      if(data.completed)$('montageMeter').value=data.completed;
      $('montageStatus').textContent=data.stage==='encode'?`Images encodées : ${data.completed} / ${data.total}`:data.stage==='finalize'?'Finalisation de la vidéo et de la musique…':'Chargement du plan, des prises et du fond…';
    };
    instance.onerror=instance.onmessageerror=()=>close(new RenderFault('RENDER_FAILED'));
    try{instance.postMessage({kind:'production',job:spec,files,metier});}catch{close(new RenderFault('RENDER_FAILED'));}
  });
}
async function encode(){
  if(preview||!saved||accepted.size!==4||activeRun)return;
  for(const id of inputs)if(!accepted.has(id)||!takes.has(id))return;
  const reuseDetail=takes.get('S3').reuseFrom==='S2';
  const refs=reuseDetail?['S1','S2','S4']:inputs;
  if(reuseDetail&&takes.get('S3').file!==takes.get('S2').file){drop(scenes[2]);showGuide(2);return;}
  const id=renderId??(renderId=newId()), run=new AbortController();activeRun=run;
  const files=Object.fromEntries(refs.map(key=>[key,takes.get(key).file]));
  transition('montage');$('panelMontage').classList.add('on');
  $('montageHeading').textContent='Montage en cours';$('montageSteps').textContent=`${refs.length} vidéos · 4 vues validées · lettrage et musique, sans voix off`;
  $('montageStatus').textContent='Préparation du fond musical…';$('montageMeter').value=0;
  $('montageRetry').hidden=true;$('montageGo').hidden=true;$('montageCancel').textContent='Retour aux prises';
  try{
    if(!isSecureContext)throw new RenderFault('PLATFORM');
    const render=variant=>runWorker(createJob(CORE,{id,source:job.source,detail:reuseDetail,view:job.framing,answers:job,variant}),files,run.signal);
    const data=await (demo?render('A'):rotate(CORE,id,run.signal,render));
    if(activeRun===run&&!run.signal.aborted)showResult(data);
  }catch(err){
    if(activeRun!==run||run.signal.aborted)return;
    $('montageHeading').textContent='Le montage n’a pas abouti';
    $('montageStatus').textContent=err instanceof RenderFault?err.message:'Le montage n’a pas abouti. Tu peux réessayer sans refaire tes prises.';
    $('montageRetry').hidden=err instanceof RenderFault&&!err.retryable;
  }finally{if(activeRun===run)activeRun=null;}
}
function backToTakes(){
  if(state==='montage')invalidateRender();
  clearResult();$('resultPage').hidden=true;$('app').hidden=false;idx=3;
  const t=takes.get(current().id);if(t){describeContext();showReview(t);}else showGuide(3);
}
function init(){
  $('app').dataset.test=DATA.id;
  if(!preview&&!saved){if(ticket)$('curtainText').textContent='Cette fiche n’est plus dans cet onglet.';$('testCurtain').hidden=false;return;}
  $('testID').textContent='T2 · '+ui.get(metier).label;
  $('app').dataset.seance=sample?'oui':'non';
  $('flowLinks').hidden=!!preview;$('editFiche').href=href('index.html',ticket,{metier});$('seeScreens').href=href('ecrans.html',ticket,{metier});
  $('cta').onclick=()=>demo?intake(example(current()),'Prise d’exemple · lecture'):filmLive();
  $('cameraBtn').onclick=()=>$('takeFile').click();
  $('reuseTake').onclick=previewDetail;
  $('takeFile').onchange=e=>{const f=e.target.files[0];e.target.value='';if(f)intake(Promise.resolve(f),'Fichier importé · lecture');};
  $('cancelCapture').onclick=$('mediaBack').onclick=()=>{drop(current());showGuide();};
  $('toggleTakeAudio').onclick=()=>{replay.muted=!replay.muted;$('toggleTakeAudio').textContent=replay.muted?'Écouter':'Couper le son';replay.play().catch(()=>{});};
  $('redo').onclick=()=>{if(preview)return;drop(current());showGuide();};
  $('next').onclick=()=>{if(preview||state!=='C'||$('next').disabled||!takes.has(current().id))return;accepted.add(current().id);if(idx<3)showGuide(idx+1);else encode();};
  $('montageCancel').onclick=$('resultBack').onclick=backToTakes;$('montageRetry').onclick=encode;
  $('replayAd').onclick=()=>{ad.currentTime=0;ad.play().catch(()=>{});};
  ad.onerror=()=>{$('resultError').textContent='Le navigateur ne peut pas lire ce fichier ici. Le téléchargement reste disponible.';};
  $('scrollHint').onclick=()=>$('sheetBody').scrollBy({top:Math.max(100,$('sheetBody').clientHeight*.8)});
  $('sheetBody').addEventListener('scroll',updateScroll,{passive:true});window.addEventListener('resize',updateScroll);document.fonts.ready.then(updateScroll);
  if(preview){
    document.body.classList.add('capture','relecture-preview');showGuide(Math.floor((preview-1)/3));
    const mode=(preview-1)%3;
    if(mode===1){
      const key=showB('Aperçu du chrono',false),ref=reference(current());
      if(ref){cam.loop=true;cam.src=ref;cam.play().catch(()=>{});const tick=()=>{if(key!==epoch)return;setProgress(cam.currentTime||0);animation=requestAnimationFrame(tick);};animation=requestAnimationFrame(tick);}
      else{cam.style.display='none';$('sansExtrait').hidden=false;}
    }
    if(mode===2)showReview({url:reference(current()),meta:{hasAudio:false}},{frozen:true});
  }else showGuide();
  window.addEventListener('pagehide',()=>{if(state==='montage')invalidateRender();cancelDetail();stopRecord(recSession);});
  // État de diagnostic uniquement, sans accès à la fiche, aux vidéos ou aux coordonnées.
  window.__capture=()=>({state,screen:state==='ad'||state==='montage'?null:`${current().id}_${state}`,accepted:[...accepted],reusedDetail:takes.get('S3')?.reuseFrom==='S2'});
}
loadCore().then(core=>{
  CORE=core;DATA=core.guide;saved=restoreFiche(ticket,CORE);job=saved;demo=job?.source==='demo';
  metier=job?.metier||ui.readMetier();sample=catalogue.get(metier,'t2');scenes=ui.scenes(DATA.scenes,metier,'t2');
  if(!preview&&!job)document.querySelector('#testCurtain a').href=ui.link('index.html',metier);
  init();document.documentElement.dataset.ready='yes';
}).catch(()=>{
  $('curtainText').textContent='Impossible de charger les ressources locales du gabarit.';$('testCurtain').hidden=false;
  document.documentElement.dataset.ready='error';
});
