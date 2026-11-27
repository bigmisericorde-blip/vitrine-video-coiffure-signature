/* Parcours T3 : même cadre A/B/C que la galerie approuvée ; prises au choix caméra ou import. */
(()=>{'use strict';
const $=id=>document.getElementById(id), params=new URLSearchParams(location.search), n=Number(params.get('ecran'));
const preview=Number.isInteger(n)&&n>=1&&n<=12, ids=['S1','S2','S3','S4']; let demo=params.get('demo')==='1';
const cam=$('cam'),replay=$('replay'),app=$('app'),body=$('sheetBody');
let cfg,fiche=null,idx=preview?Math.floor((n-1)/3):0,state='A',events=new AbortController(),epoch=0,timer=null,raf=0,record=null,stream=null,sourceUrl=null,candidate=null,files={},accepted=new Set();
window.addEventListener('message',e=>{if(e.source!==parent||e.origin!==location.origin||e.data?.type!=='vv-t3-fiche'||typeof e.data.fiche!=='object')return;fiche=e.data.fiche;if(fiche.modeVoixPrises==='oui')$('wantMic').checked=true;if(cfg)labels();});
const cur=()=>cfg.contrat.prises[ids[idx]],fmt=n=>`0:${String(Math.max(0,Math.floor(n))).padStart(2,'0')}`;
function stopStream(){clearTimeout(timer);if(record&&record.state!=='inactive')record.stop();record=null;stream?.getTracks().forEach(x=>x.stop());stream=null;}
function clear(v){v.pause();v.srcObject=null;v.removeAttribute('src');v.load();v.style.display='none';}
function reset(next){epoch++;events.abort();events=new AbortController();cancelAnimationFrame(raf);clearTimeout(timer);clear(cam);clear(replay);if(sourceUrl){URL.revokeObjectURL(sourceUrl);sourceUrl=null;}
 state=next;app.dataset.state=state;app.dataset.prise=ids[idx];$('sheet').classList.toggle('hidden',next!=='A');$('scrim').classList.toggle('off',next!=='A');$('rec').classList.toggle('on',next==='B');$('review').classList.toggle('on',next==='C');$('rec').setAttribute('aria-hidden',String(next!=='B'));$('mediaFeedback').hidden=true;}
function on(x,e,fn){x.addEventListener(e,fn,{signal:events.signal});}
function text(id,s){$(id).textContent=s;}
function list(id,lines,mark){$(id).replaceChildren(...lines.map(x=>{const li=document.createElement('li'),a=document.createElement('span'),b=document.createElement('span');a.className='mark';a.textContent=mark;b.textContent=x;li.append(a,b);return li;}));}
function fail(s){stopStream();$('mediaFeedback').hidden=false;text('mediaMessage',s);$('mediaBack').hidden=preview;$('mediaRetry').hidden=true;}
function updateScroll(){$('scrollHint').hidden=state!=='A'||body.scrollHeight-body.clientHeight<=10||body.scrollTop+body.clientHeight>=body.scrollHeight-14;}
function labels(){const c=cur(),title=['Départ','Travail ou utilisation','Détail','Dernière vue'][idx];
 const hints=[
  ['Cadre assez large.',['Montre le produit ou le service et ce que tu vas faire.','Garde le téléphone droit et laisse un peu de place autour.'],'Ne commence pas trop près.'],
  ['Montre ton travail.',['Filme ton produit en cours d’utilisation ou une étape de ton service.','Garde les mains et ce que tu fais dans l’image.'],'Ne cache pas ce que tu fais.'],
  ['Approche-toi et reste stable.',['Filme de près un détail réel de ton produit ou de ton travail.','Laisse le temps de bien le voir. Garde le téléphone immobile.'],'N’ajoute pas de filtre qui cache le détail.'],
  ['Garde une image calme.',['Filme ton produit ou ton travail. S’il y a un résultat visible, montre-le.','Garde une image stable et bien éclairée.'],'Ne change pas de produit ou de service.']];
 const h=hints[idx], f=fiche||(preview||demo?cfg.exemple:null),context=f&&[f.service,f.outil?('Tu utilises : '+f.outil):f.service,f.service,f.service][idx];
 text('testID','T3 · '+(preview?'EXEMPLE SOIN DU VISAGE':demo?'SIMULATION':'MES PRISES'));text('sceneCounter',`PRISE ${idx+1}/4 · ${title}`);[...$('dots').children].forEach((d,i)=>d.classList.toggle('on',i<=idx));text('durationLabel',`${c.secondes} secondes`);text('sceneTitle',title.toLocaleUpperCase('fr'));text('consigne',h[0]);list('listFilm',h[1],'✓');list('listAvoid',[h[2]],'✕');
 for(const id of ['caseContext','recContext','reviewContext']){text(id,context?String(context).slice(0,80):'');$(id).hidden=!context;}
 text('soundText',fiche?.modeVoixPrises==='oui'?`Active le micro pour parler. Pour garder la voix synchronisée, le film utilise les ${idx===0?6:8} premières secondes de cette prise. Termine ta phrase avant ce moment ; le reste de la prise ne sera pas utilisé dans ce mode.`:'Le son est facultatif. Tu peux activer le micro ou ajouter une voix séparée au montage.');text('captureConsent','Demande l’accord des personnes avant de filmer et diffuser les images.');text('reviewQuestion',c.question);text('reviewLabel',`PRISE ${idx+1} · ${fmt(c.secondes)}`);text('reviewOrigin','Prise à relire');text('next',idx===3?'GARDER ET CONTINUER':'GARDER LA PRISE');}
// Les douze écrans illustrent le film validé, sans prétendre montrer une capture réelle.
const demoRanges=[[0.7,3.35],[4.7,8.15],[11.45,14.15],[25.3,29.4]];
function ref(){return preview?'reference/soin-du-visage-sans-texte.mp4':`exemple/${ids[idx]}.mp4`;}
function startPreviewVideo(v,playing){const [start,end]=demoRanges[idx];v.style.display='block';v.muted=true;v.loop=false;v.poster=`reference/apercu-S${idx+1}.jpg`;v.src=ref();const begin=()=>{v.currentTime=start;if(playing)v.play().catch(()=>{});};on(v,'loadedmetadata',begin);on(v,'timeupdate',()=>{if(playing&&v.currentTime>=end)v.currentTime=start;if(playing&&state==='B')progress(Math.max(0,v.currentTime-start));});}
function guide(){stopStream();candidate=null;reset('A');labels();$('cta').disabled=preview;text('cta',demo?'LIRE LA MIRE DE TEST':'COMMENCER À FILMER');$('cameraBtn').hidden=preview||demo;$('cameraBtn').disabled=false;$('reuseTake').hidden=true;$('micOption').hidden=preview||demo;$('flowLinks').hidden=true;$('takeHelp').hidden=demo||preview; text('takeHelp','Tu peux aussi importer une prise déjà filmée.');if(preview){startPreviewVideo(cam,false);}else{cam.style.display='block';cam.src=ref();cam.muted=true;on(cam,'loadedmetadata',()=>{cam.currentTime=Math.min(1,Math.max(0,(cam.duration||1)-.1));});}body.scrollTop=0;requestAnimationFrame(updateScroll);}
function progress(t){const s=cur().secondes,v=Math.max(0,Math.min(1,t/s));text('chronoVal',fmt(t));$('barFill').style.width=(v*100)+'%';$('bar').classList.toggle('hot',s-t<=2);$('chrono').classList.toggle('hot',s-t<=2);}
async function readCandidate(blob,origin){if(!blob||!blob.size||blob.size>48*1024*1024){fail('Prise absente ou supérieure à 48 Mio.');return;}const ticket=++epoch;try{const {verifierPrise}=await import('./verifier-prise.mjs');await verifierPrise(blob,cur().secondes);}catch(e){if(ticket===epoch)fail(e.message);return;}if(ticket!==epoch)return;candidate={blob,origin};reset('B');labels();$('cancelCapture').hidden=false;text('recordLabel',origin+' · lecture');cam.style.display='block';cam.muted=true;sourceUrl=URL.createObjectURL(blob);cam.src=sourceUrl;progress(0);const my=epoch;
 on(cam,'timeupdate',()=>{progress(cam.currentTime);if(my===epoch&&cam.currentTime>=cur().secondes){cam.pause();showReview();}});
 on(cam,'ended',()=>{if(my===epoch){if(cam.currentTime+0.05>=cur().secondes)showReview();else fail(`La prise est trop courte : ${cur().secondes} secondes minimum.`);}});
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
  reset('B');labels();cam.style.display='block';cam.srcObject=st;cam.muted=true;await cam.play();text('recordLabel','Enregistrement caméra');$('cancelCapture').hidden=false;let start=performance.now();const mine=epoch;const tick=()=>{if(mine!==epoch)return;progress((performance.now()-start)/1000);raf=requestAnimationFrame(tick);};tick();r.start(250);
  timer=setTimeout(()=>{if(r.state==='recording')r.stop();},cur().secondes*1000+650);
  $('cancelCapture').onclick=()=>{cancelled=true;stopStream();guide();};
 }catch(e){stream?.getTracks().forEach(t=>t.stop());stream=null;record=null;guide();fail(e.name==='NotAllowedError'?'Accès caméra ou micro refusé. Tu peux importer une vidéo.':e.message);}
}
$('cta').onclick=async()=>{if(preview)return;if(!demo){await live();return;}try{const r=await fetch(ref());if(!r.ok)throw Error('Mire indisponible.');readCandidate(await r.blob(),'Mire de test');}catch(e){fail(e.message);}};
$('cameraBtn').onclick=()=>$('takeFile').click();$('takeFile').onchange=()=>{const f=$('takeFile').files[0];$('takeFile').value='';if(f)readCandidate(f,'Import');};
$('redo').onclick=()=>{accepted.delete(ids[idx]);delete files[ids[idx]];guide();};$('mediaBack').onclick=guide;
$('cancelCapture').onclick=()=>{stopStream();guide();};
$('toggleTakeAudio').onclick=()=>{replay.muted=!replay.muted;text('toggleTakeAudio',replay.muted?'Écouter le son':'Couper le son');replay.play().catch(()=>{});};
$('next').onclick=()=>{if(preview||state!=='C'||$('next').disabled||!candidate)return;files[ids[idx]]=candidate.blob;accepted.add(ids[idx]);if(idx<3){idx++;guide();return;}if(accepted.size===4)parent.postMessage({type:'vv-t3-captures',files:ids.map(k=>files[k]),demo},location.origin);};
$('scrollHint').onclick=()=>body.scrollBy({top:Math.max(100,body.clientHeight*.8)});body.addEventListener('scroll',updateScroll,{passive:true});window.addEventListener('resize',updateScroll);window.addEventListener('pagehide',stopStream);
window.__capture=()=>({state,prise:ids[idx],accepted:[...accepted],preview,demo});
fetch('config.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(x=>{cfg=x;demo=demo||cfg.demo;guide();if(preview){const kind=(n-1)%3;if(kind===1){reset('B');labels();text('recordLabel','Aperçu fictif · extrait du film');$('cancelCapture').hidden=true;startPreviewVideo(cam,true);}else if(kind===2){reset('C');labels();$('next').disabled=true;$('redo').disabled=true;$('toggleTakeAudio').hidden=true;text('reviewMode','Extrait du film · aucune prise enregistrée');startPreviewVideo(replay,true);}}document.documentElement.dataset.ready='yes';}).catch(()=>{text('curtainText','Le service local T3 ne répond pas.');$('testCurtain').hidden=false;document.documentElement.dataset.ready='error';});
})();
