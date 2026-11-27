/* Parcours T4 : même cadre A/B/C que la galerie approuvée ; prises au choix caméra ou import. */
(()=>{'use strict';
const $=id=>document.getElementById(id), params=new URLSearchParams(location.search), n=Number(params.get('ecran'));
const preview=Number.isInteger(n)&&n>=1&&n<=12, ids=['S1','S2','S3','S4']; let demo=params.get('demo')==='1';
const cam=$('cam'),replay=$('replay'),app=$('app'),body=$('sheetBody');
let cfg,fiche=null,idx=preview?Math.floor((n-1)/3):0,state='A',events=new AbortController(),epoch=0,timer=null,raf=0,record=null,stream=null,sourceUrl=null,candidate=null,files={},accepted=new Set();
window.addEventListener('message',e=>{if(e.source!==parent||e.origin!==location.origin||e.data?.type!=='vv-t4-fiche'||typeof e.data.fiche!=='object')return;fiche=e.data.fiche;if(cfg)labels();});
const cur=()=>cfg.contrat.prises[ids[idx]],fmt=n=>`0:${String(Math.max(0,Math.floor(n))).padStart(2,'0')}`;
function stopStream(){clearTimeout(timer);if(record&&record.state!=='inactive')record.stop();record=null;stream?.getTracks().forEach(x=>x.stop());stream=null;}
function clear(v){v.pause();v.srcObject=null;v.removeAttribute('src');v.removeAttribute('poster');v.load();v.style.display='none';}
function reset(next){epoch++;events.abort();events=new AbortController();cancelAnimationFrame(raf);clearTimeout(timer);clear(cam);clear(replay);if(sourceUrl){URL.revokeObjectURL(sourceUrl);sourceUrl=null;}
 state=next;app.dataset.state=state;app.dataset.prise=ids[idx];$('sheet').classList.toggle('hidden',next!=='A');$('scrim').classList.toggle('off',next!=='A');$('rec').classList.toggle('on',next==='B');$('review').classList.toggle('on',next==='C');$('rec').setAttribute('aria-hidden',String(next!=='B'));$('mediaFeedback').hidden=true;$('stopCapture').hidden=true;}
function on(x,e,fn){x.addEventListener(e,fn,{signal:events.signal});}
function text(id,s){$(id).textContent=s;}
function list(id,lines,mark){$(id).replaceChildren(...lines.map(x=>{const li=document.createElement('li'),a=document.createElement('span'),b=document.createElement('span');a.className='mark';a.textContent=mark;b.textContent=x;li.append(a,b);return li;}));}
function fail(s){stopStream();$('mediaFeedback').hidden=false;text('mediaMessage',s);$('mediaBack').hidden=preview;$('mediaRetry').hidden=true;}
function updateScroll(){$('scrollHint').hidden=state!=='A'||body.scrollHeight-body.clientHeight<=10||body.scrollTop+body.clientHeight>=body.scrollHeight-14;}
function labels(){const c=cur(),title=['Découvrir','Présenter','Détail','Terminer'][idx];
 const hints=[
  ['Cadre assez large.',['Montre le produit ou le service et ce que tu vas faire.','Garde le téléphone droit et laisse un peu de place autour.'],'Ne commence pas trop près.'],
  ['Change de cadrage pour présenter.',['Montre le même produit sous un autre angle ou la préparation du service.','Garde le téléphone stable et l’offre visible.'],'Ne change pas de produit ou de service.'],
  ['Approche-toi et reste stable.',['Montre de près le détail choisi dans ta fiche.','Laisse le temps de bien le voir. Garde le téléphone immobile.'],'N’ajoute pas de filtre qui cache le détail.'],
  ['Laisse de la place pour le texte de fin.',['Filme une dernière vue du même produit ou service.','Garde une image calme et bien éclairée.'],'Ne change pas de produit ou de service en cours de vidéo.']];
 const h=hints[idx], f=fiche||(preview||demo?cfg.exemple:null),context=f&&[f.service,f.geste,f.detail,f.service][idx];
 text('testID','T4 · '+(preview?'APERÇU MAQUILLAGE':demo?'SIMULATION':'MES PRISES'));text('sceneCounter',`PRISE ${idx+1}/4 · ${title}`);[...$('dots').children].forEach((d,i)=>d.classList.toggle('on',i<=idx));text('durationLabel',`2 à ${c.secondes} secondes`);text('sceneTitle',title.toLocaleUpperCase('fr'));text('consigne',h[0]);list('listFilm',h[1],'✓');list('listAvoid',[h[2]],'✕');
 for(const id of ['caseContext','recContext','reviewContext']){text(id,context?String(context).slice(0,80):'');$(id).hidden=!context;}
 text('soundText','Le son original peut être écouté en relecture. Il ne sera pas repris automatiquement dans le film.');text('captureConsent','Demande l’accord des personnes avant de filmer et diffuser les images.');text('reviewQuestion',c.question);text('reviewLabel',`PRISE ${idx+1} · ${fmt(candidate?.duration??c.secondes)}`);text('reviewOrigin','Prise à relire');text('next',idx===3?'GARDER ET CONTINUER':'GARDER LA PRISE');}
function ref(){return `exemple/${ids[idx]}.mp4`;}
function still(){return `reference/maquillage-${idx+1}.jpg`;}
function guide(){stopStream();candidate=null;reset('A');labels();$('cta').disabled=preview;text('cta',demo?'LIRE LA MIRE DE TEST':'COMMENCER À FILMER');$('cameraBtn').hidden=preview||demo;$('cameraBtn').disabled=false;$('reuseTake').hidden=true;$('micOption').hidden=preview||demo;$('flowLinks').hidden=true;$('takeHelp').hidden=demo||preview; text('takeHelp','Arrête quand tu as fini : au moins 2 secondes, sans dépasser la durée indiquée. Tu peux aussi importer une prise déjà filmée.');cam.style.display='block';cam.muted=true;if(demo&&!preview){cam.src=ref();on(cam,'loadedmetadata',()=>{cam.currentTime=Math.min(1,Math.max(0,(cam.duration||1)-.1));});}else cam.poster=still();body.scrollTop=0;requestAnimationFrame(updateScroll);}
function progress(t){const s=cur().secondes,v=Math.max(0,Math.min(1,t/s));text('chronoVal',fmt(t));$('barFill').style.width=(v*100)+'%';$('bar').classList.toggle('hot',s-t<=2);$('chrono').classList.toggle('hot',s-t<=2);}
async function readCandidate(blob,origin){if(!blob||!blob.size||blob.size>48*1024*1024){fail('Prise absente ou supérieure à 48 Mio.');return;}let input;const stamp=epoch,need=cur().secondes;let duration=0;try{const {Input,BlobSource,MP4,QTFF,WEBM}=await import('./vendor/mediabunny-1.66.1.min.mjs');input=new Input({source:new BlobSource(blob),formats:[MP4,QTFF,WEBM]});const v=await input.getPrimaryVideoTrack();if(!v||!await v.canDecode())throw Error('Vidéo illisible.');const start=await v.getFirstTimestamp(),end=await v.computeDuration();duration=end-start;if(stamp!==epoch)return;if(end-start<2){fail('La vidéo est trop courte : filme au moins 2 secondes.');return;}if(end-start>need+.80){fail(`La vidéo est trop longue : coupe-la à ${need} secondes avant de l’importer.`);return;}}catch(e){if(stamp===epoch)fail('Impossible de vérifier cette vidéo. Essaie un autre fichier.');return;}finally{input?.dispose()}candidate={blob,origin,duration};reset('B');labels();$('cancelCapture').hidden=false;text('recordLabel',origin+' · lecture');cam.style.display='block';cam.muted=true;sourceUrl=URL.createObjectURL(blob);cam.src=sourceUrl;progress(0);const my=epoch;
 on(cam,'timeupdate',()=>{progress(cam.currentTime);if(my===epoch&&cam.currentTime>=cur().secondes){cam.pause();showReview();}});
 on(cam,'ended',()=>{if(my===epoch){showReview();}});
 on(cam,'error',()=>fail('Le navigateur ne peut pas lire cette prise. Essaie un autre fichier.'));
 cam.play().catch(()=>fail('Impossible de lire cette prise. Réessaie.'));
}
function showReview(){if(!candidate)return;reset('C');labels();replay.style.display='block';sourceUrl=URL.createObjectURL(candidate.blob);replay.src=sourceUrl;replay.loop=true;replay.muted=true;const button=$('next');button.disabled=true;text('reviewOrigin',candidate.origin);text('reviewMode','Relis la prise avant de la garder.');$('redo').disabled=false;$('toggleTakeAudio').hidden=false;text('toggleTakeAudio','Écouter le son');on(replay,'timeupdate',()=>{if(replay.currentTime>.15)button.disabled=false;});on(replay,'error',()=>fail('Impossible de relire cette prise.'));replay.play().catch(()=>fail('La relecture ne démarre pas. Réessaie.'));}
async function live(){if(state!=='A')return;let epochStart=epoch;$('cta').disabled=true;
 try{
  if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined')throw Error('Caméra indisponible : utilise HTTPS ou importe une vidéo.');
  const st=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:720},height:{ideal:1280}},audio:$('wantMic').checked});
  if(epochStart!==epoch){st.getTracks().forEach(t=>t.stop());return;}stream=st;const opts=['video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/mp4'].find(x=>MediaRecorder.isTypeSupported(x));const r=new MediaRecorder(st,opts?{mimeType:opts}:undefined),chunks=[];record=r;let cancelled=false;
  r.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  r.onerror=()=>{cancelled=true;fail('Enregistrement interrompu. Réessaie ou importe une vidéo.');};
  r.onstop=()=>{st.getTracks().forEach(t=>t.stop());if(stream===st)stream=null;if(record===r)record=null;clearTimeout(timer);if(!cancelled&&state==='B'){const blob=new Blob(chunks,{type:r.mimeType||'video/webm'});if(blob.size)readCandidate(blob,'Caméra');else fail('Enregistrement vide.');}};
  reset('B');labels();cam.style.display='block';cam.srcObject=st;cam.muted=true;await cam.play();text('recordLabel','Enregistrement caméra · arrête quand tu as fini');$('cancelCapture').hidden=false;$('stopCapture').hidden=false;$('stopCapture').onclick=()=>{if(r.state==='recording')r.stop();};let start=performance.now();const mine=epoch;const tick=()=>{if(mine!==epoch)return;progress((performance.now()-start)/1000);raf=requestAnimationFrame(tick);};tick();r.start(250);
  timer=setTimeout(()=>{if(r.state==='recording')r.stop();},cur().secondes*1000+650);
  $('cancelCapture').onclick=()=>{cancelled=true;stopStream();guide();};
 }catch(e){stream?.getTracks().forEach(t=>t.stop());stream=null;record=null;guide();fail(e.name==='NotAllowedError'?'Accès caméra ou micro refusé. Tu peux importer une vidéo.':e.message);}
}
$('cta').onclick=async()=>{if(preview)return;if(!demo){await live();return;}try{const r=await fetch(ref());if(!r.ok)throw Error('Mire indisponible.');readCandidate(await r.blob(),'Mire de test');}catch(e){fail(e.message);}};
$('cameraBtn').onclick=()=>$('takeFile').click();$('takeFile').onchange=()=>{const f=$('takeFile').files[0];$('takeFile').value='';if(f)readCandidate(f,'Import');};
$('redo').onclick=()=>{accepted.delete(ids[idx]);delete files[ids[idx]];guide();};$('mediaBack').onclick=guide;
$('cancelCapture').onclick=()=>{stopStream();guide();};
$('toggleTakeAudio').onclick=()=>{replay.muted=!replay.muted;text('toggleTakeAudio',replay.muted?'Écouter le son':'Couper le son');replay.play().catch(()=>{});};
$('next').onclick=()=>{if(preview||state!=='C'||$('next').disabled||!candidate)return;files[ids[idx]]=candidate.blob;accepted.add(ids[idx]);if(idx<3){idx++;guide();return;}if(accepted.size===4)parent.postMessage({type:'vv-t4-captures',files:ids.map(k=>files[k]),demo},location.origin);};
$('scrollHint').onclick=()=>body.scrollBy({top:Math.max(100,body.clientHeight*.8)});body.addEventListener('scroll',updateScroll,{passive:true});window.addEventListener('resize',updateScroll);window.addEventListener('pagehide',stopStream);
window.__capture=()=>({state,prise:ids[idx],accepted:[...accepted],preview,demo});
fetch('config.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(x=>{cfg=x;demo=demo||cfg.demo;guide();if(preview){const kind=(n-1)%3;if(kind===1){reset('B');labels();text('recordLabel','Aperçu fictif · film maquillage');$('cancelCapture').hidden=true;$('stopCapture').hidden=true;cam.style.display='block';cam.muted=true;cam.poster=still();progress(Math.min(2,cur().secondes));}else if(kind===2){reset('C');labels();$('next').disabled=true;$('redo').disabled=true;$('toggleTakeAudio').hidden=true;text('reviewMode','Aperçu du film · aucune prise réelle');text('reviewOrigin','Image du film');replay.style.display='block';replay.muted=true;replay.poster=still();}}document.documentElement.dataset.ready='yes';}).catch(()=>{text('curtainText','La configuration T4 ne répond pas.');$('testCurtain').hidden=false;document.documentElement.dataset.ready='error';});
})();
