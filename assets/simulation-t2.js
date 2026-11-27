'use strict';
const $ = id => document.getElementById(id);
const DATA=window.CONSIGNES_T2, FICHE=window.VVFicheT2, rotation=window.VVAfrobeat;
const cam=$('cam'), replay=$('replay'), ad=$('ad');
const params=new URLSearchParams(location.search), id=params.get('fiche');
const saved=FICHE.restore(id), job=saved||FICHE.initial;
const linked=params.get('test')===DATA.id&&(!id||!!saved);
const requestedScreen=Number(params.get('ecran'));
const previewNumber=linked&&Number.isInteger(requestedScreen)&&requestedScreen>=1&&requestedScreen<=12?requestedScreen:0;
const personal=!previewNumber&&job.source==='client';
const SCENES=DATA.scenes.map(s=>({...s,video:`media/${s.media}`}));
const validated=new Set(), files=new Map();
let idx=0, rafId=null, recording=false, state='A', activeRender, result=null, lastTrack=null, inputTicket=0;
const fmt=sec=>`${Math.floor(sec/60)}:${String(Math.floor(sec%60)).padStart(2,'0')}`;
const sceneSource=s=>files.has(s.id)?{...s,video:files.get(s.id).url}:s;

function updateState(value){state=value;$('app').dataset.state=value;}
function renderCard(i){
  const s=FICHE.sceneGuide(previewNumber&&saved?{...saved,source:"demo"}:saved, i, SCENES[i]), hint=FICHE.sceneText(job,i);
  $('app').dataset.prise=s.id;
  $('sceneCounter').textContent=`SCÈNE ${s.n}/${s.total}`;
  $('dots').replaceChildren(...SCENES.map(x=>{let dot=document.createElement('i');dot.classList.toggle('on',x.n<=s.n);return dot;}));
  $('durationLabel').textContent=`${s.secondes} secondes`;
  $('sceneTitle').textContent=s.titre;
  $('consigne').textContent=s.consigne;
  const list=(id,items,icon)=>$(id).replaceChildren(...items.map(t=>{
    const li=document.createElement('li'),mark=document.createElement('span'),txt=document.createElement('span');
    mark.className='mark';mark.textContent=icon;txt.textContent=t;li.append(mark,txt);return li;
  }));
  list('listFilm',s.a_filmer,'✓');
  list('listAvoid',s.a_eviter,'✕');
  for (const id of ['caseContext','recContext','reviewContext']){$(id).textContent=saved?hint:'';$(id).hidden=!saved;}
  $('reviewQuestion').textContent=s.question_relecture;
  $('voiceText').textContent=personal?'Tu peux garder tes prises muettes. Ajoute ta voix après le montage, dans la langue de ton choix.':DATA.mention_voix_commune;
  $('exempleText').textContent=`« ${s.exemple} »`;
  $('cta').textContent=personal?'Importer une vidéo':DATA.bouton_principal;
  $('recordLabel').textContent=personal?'Vérification de la prise':'Enregistrement simulé';
  $('reviewMode').textContent=personal?'Aperçu de ta prise · sans son':'Lecture muette en boucle · test';
  $('takeHelp').hidden=!personal;
  $('takeHelp').textContent=personal?`Prise ${s.n} : ${s.secondes} s minimum · MP4, MOV ou WebM HD, 24 Mo max.`:'';
  $('cameraBtn').hidden=!personal||!matchMedia('(pointer: coarse)').matches;
  $('next').textContent=s.n===s.total?'VOIR MON MONTAGE':'SCÈNE SUIVANTE';
  $('reviewLabel').textContent=`PRISE ${s.n} · ${fmt(s.secondes)}`;
}
function hideAll(){
  inputTicket++;
  $('sheet').classList.add('hidden');
  for(const id of ['rec','review','panelMontage','panelEnd','adwrap'])$(id).classList.remove('on');
  $('rec').setAttribute('aria-hidden','true');
  clearPicture();cam.pause();ad.pause();replay.pause();replay.style.display='none';
}
function clearResult(){
  if(!result)return;
  ad.pause();ad.removeAttribute('src');ad.load();
  $('endDownload').removeAttribute('href');URL.revokeObjectURL(result.url);result=null;
}
function applyContact(){
  const destination=saved?FICHE.destination(job):DATA.display.route+'?test='+encodeURIComponent(DATA.id);
  for(const name of ['caCta','endCta']){
    const a=$(name);a.hidden=!destination;
    if(destination){
      a.href=destination;a.textContent=saved?job.cta:DATA.display.cta;
      if(saved&&/^https?:/.test(destination)){a.target='_blank';a.rel='noopener noreferrer';}
    }
  }
}
async function importTake(input){
  const file=input.files[0];input.value='';
  if(!file||!personal||state!=='A')return;
  const s=SCENES[idx], ticket=++inputTicket;
  const fail=msg=>showPictureNotice(msg,null);
  if(!file.size||file.size>24*1024*1024)return fail('Choisis un fichier vidéo de 24 Mo au maximum.');
  const url=URL.createObjectURL(file), probe=document.createElement('video');
  let keep=false;
  $('cta').disabled=$('cameraBtn').disabled=true;
  try {
    await new Promise((resolve,reject)=>{
      const timeout=setTimeout(()=>reject(Error('Le fichier met trop de temps à s’ouvrir.')),7000);
      probe.onloadedmetadata=()=>{clearTimeout(timeout);resolve();};
      probe.onerror=()=>{clearTimeout(timeout);reject(Error('Cette vidéo ne se lit pas. Essaie un MP4 H.264.'));};
      probe.preload='metadata';probe.src=url;
    });
    if(ticket!==inputTicket)return;
    if(!Number.isFinite(probe.duration)||probe.duration<s.secondes-.025)throw Error(`Prise trop courte : il faut au moins ${s.secondes} secondes.`);
    if(probe.videoWidth<240||probe.videoHeight<240||probe.videoWidth*probe.videoHeight>1920*1080)throw Error('Choisis une vidéo HD ou Full HD, pas de 4K.');
    if(files.has(s.id))URL.revokeObjectURL(files.get(s.id).url);
    files.set(s.id,{file,url});keep=true;validated.delete(s.id);
    startRecording();
  } catch(e){if(ticket===inputTicket)fail(e.message);}
  finally {
    probe.removeAttribute('src');probe.load();
    if(!keep)URL.revokeObjectURL(url);
    $('cta').disabled=$('cameraBtn').disabled=!!previewNumber;
  }
}

function encode(request,signal,onProgress){
  return new Promise((resolve,reject)=>{
    signal.throwIfAborted();
    if(!isSecureContext||typeof Worker==='undefined')throw Error('Ouvre cette page en HTTPS pour créer le MP4.');
    const worker=new Worker('assets/t2-render.worker.mjs?v=commercial-t1-1',{type:'module',name:'Export T2'});
    const timeout=setTimeout(()=>end(reject,Error('L’encodeur ne répond plus. Essaie un autre appareil ou des vidéos plus légères.')),240000);
    const abort=()=>end(reject,signal.reason);
    function end(fn,value){clearTimeout(timeout);signal.removeEventListener('abort',abort);worker.terminate();fn(value);}
    signal.addEventListener('abort',abort,{once:true});
    worker.onmessage=({data})=>{
      if(data.stage==='error')end(reject,Error(data.message));
      else if(data.stage==='done')end(resolve,data);
      else onProgress(data);
    };
    worker.onerror=()=>end(reject,Error('Le moteur vidéo n’a pas chargé. Vérifie ta connexion et recharge la page.'));
    worker.onmessageerror=()=>end(reject,Error('La mémoire du navigateur n’a pas permis de récupérer le MP4.'));
    worker.postMessage(request);
  });
}
function progress(data){
  const meter=$('montageMeter');
  if(data.stage==='prepare'){
    meter.removeAttribute('value');$('montageStatus').textContent='Chargement du plan de montage et de la typographie…';
  }else{
    meter.value=data.completed;
    $('montageStatus').textContent=data.stage==='audio'?'Ajout de la bande-son sélectionnée…':data.stage==='finalize'?'Vérification du fichier MP4…':`Encodage du montage : ${data.completed} / ${data.total} images.`;
  }
}
function acceptResult(blob,track,out){
  const url=URL.createObjectURL(blob);result={blob,url,track,template:out.template};
  ad.defaultMuted=ad.muted=!track;ad.src=url;
  $('endDownload').href=url;
  $('adBadge').textContent=track?'Avec musique · 30 s':'Sans son · 30 s';
  $('adNotice').textContent=personal?'MP4 personnalisé · 30 secondes':'Images d’exemple · fiche incrustée';
  $('endSound').textContent=track?`Fond : ${track.titre} — ${track.auteur}`:'Aucune piste audio';
  $('endSoundCredits').hidden=!track;
  if(track){
    $('endSource').href=track.source;$('endSource').textContent=rotation.provider(track);
    $('endLicence').href=track.licence;$('endLicence').textContent=track.licence_nom;
    $('endChanges').textContent=track.modifications+(track.content_id==='enregistre'?' Content ID signalé par la source.':'');
  }
  $('endMeta').textContent=[job.salon,job.service,job.ville,'30 s'].filter(Boolean).join(' · ');
  $('endMeta').dataset.template=out.template.id+'@'+out.template.version;
  $('endMeta').dataset.track=track?.id||'';
}
async function showMontage(silent=params.get('muet')==='1'){
  if(!linked||previewNumber||validated.size!==SCENES.length||activeRender)return;
  stopRecording();hideAll();clearResult();updateState('montage');
  const controller=new AbortController();activeRender=controller;
  const signal=controller.signal;
  $('montageHeading').textContent='Montage en cours';
  $('montageGo').disabled=true;$('montageGo').textContent='VOIR MA PUBLICITÉ';
  $('montageRetry').hidden=$('montageSilent').hidden=true;
  $('montageCancel').textContent='Annuler';$('panelMontage').classList.add('on');
  $('montageSteps').textContent='4 prises validées · textes et transitions incrustés · MP4 vertical';
  $('montageMeter').removeAttribute('value');$('montageStatus').textContent='Préparation du rendu…';
  const triedMusic=!silent;
  const work=async()=>{
    signal.throwIfAborted();
    const plan= !silent ? rotation?.propose(lastTrack) : null;
    if(!silent&&!plan)throw Error('Le catalogue des quatre instrumentaux n’a pas chargé.');
    const track=plan?.track||null;
    const scenes=SCENES.map(({id,n,secondes})=>({id,n,secondes,file:personal?files.get(id)?.file:undefined}));
    const out=await encode({job,scenes,track,profile:window.VV_COIFFURE_AUDIO_PROFILE,demo:!personal},signal,progress);
    signal.throwIfAborted();
    acceptResult(new Blob([out.buffer],{type:'video/mp4'}),track,out);
    plan?.commit();if(track)lastTrack=track.id;
  };
  try {
    // Deux onglets capables de Web Locks ne peuvent pas valider le même tirage simultanément.
    if(!silent&&navigator.locks)await navigator.locks.request('vv-t2-montage-son',{signal},work);
    else await work();
    $('montageMeter').value=900;$('montageHeading').textContent='Montage prêt';
    $('montageStatus').textContent='Le MP4 contient ta fiche et les quatre prises validées.';
    $('montageCancel').textContent='Retour aux prises';$('montageGo').disabled=false;$('montageGo').focus();
  } catch(e){
    if(signal.aborted)return;
    $('montageHeading').textContent='Le rendu n’a pas abouti';$('montageStatus').textContent=e.message;
    $('montageMeter').value=0;$('montageRetry').hidden=false;$('montageSilent').hidden=!triedMusic;
    $('montageCancel').textContent='Retour aux prises';
  } finally {if(activeRender===controller)activeRender=null;}
}
function openAd(){
  if(!result)return;
  hideAll();updateState('ad');$('adwrap').classList.add('on');
  ad.currentTime=0;ad.play().catch(()=>{});
}
function endAd(){if(!result)return;hideAll();updateState('end');$('panelEnd').classList.add('on');}
function goBack(){activeRender?.abort();activeRender=null;clearResult();validated.delete(SCENES.at(-1).id);showCard(SCENES.length-1);}
function closeVoice(){
  $('voiceWorkshop').hidden=true;$('voiceFrame').removeAttribute('src');$('voiceOpen').focus();
}

function init(){
  $('testID').textContent=personal?'T2 · MES PRISES':'T2 · PRISES D’EXEMPLE';
  $('app').dataset.test=DATA.id;
  if(!linked){if(id)$('curtainText').textContent='La fiche n’est pas disponible dans cet onglet.';$('testCurtain').hidden=false;return;}
  applyContact();
  $('editFiche').href=$('endEdit').href=FICHE.href('index.html',id);
  $('seeScreens').href=FICHE.href('ecrans.html',id);
  $('flowLinks').hidden=!!previewNumber;
  $('cta').onclick=()=>personal?$('takeFile').click():startRecording();
  $('cameraBtn').onclick=()=>$('takeCamera').click();
  for(const input of [$('takeFile'),$('takeCamera')])input.onchange=()=>importTake(input);
  $('redo').onclick=()=>{validated.delete(SCENES[idx].id);showCard(idx);};
  $('mediaBack').onclick=()=>showCard(idx);
  $('next').onclick=()=>{
    if(state!=='C'||$('next').disabled||previewNumber)return;
    validated.add(SCENES[idx].id);
    if(idx<SCENES.length-1)showCard(idx+1);
    else if(validated.size===SCENES.length)showMontage();
  };
  $('montageGo').onclick=$('replayAd').onclick=openAd;
  $('adClose').onclick=ad.onended=endAd;
  ad.onerror=()=>{if(result&&state==='ad'){endAd();$('endMeta').textContent='La lecture intégrée a échoué. Tu peux télécharger le MP4.';}};
  $('montageCancel').onclick=goBack;
  $('montageRetry').onclick=()=>showMontage();
  $('montageSilent').onclick=()=>showMontage(true);
  $('restart').onclick=()=>{validated.clear();clearResult();files.forEach(f=>URL.revokeObjectURL(f.url));files.clear();showCard(0);};
  $('voiceOpen').onclick=()=>{if(result){$('voiceWorkshop').hidden=false;$('voiceFrame').src='atelier.html?source=t2';$('voiceClose').focus();}};
  $('voiceClose').onclick=closeVoice;
  window.addEventListener('message',event=>{
    if(event.origin!==location.origin||event.source!==$('voiceFrame').contentWindow||event.data?.type!=='vv-t2-voice-ready'||!result||$('voiceWorkshop').hidden)return;
    event.source.postMessage({type:'vv-t2-voice-source',blob:result.blob,track:result.track?.id||'',title:job.salon},location.origin);
  });
  // Les commandes de test n’acceptent ni validation ni export à partir d’un aperçu.
  window.__demo={state:()=>state,validations:()=>[...validated],test:()=>DATA.id};
  if(previewNumber){
    const i=Math.floor((previewNumber-1)/3), mode=(previewNumber-1)%3;
    document.body.classList.add('capture');showCard(i);
    if(mode===1)showFrozenRecording();else if(mode===2)finishRecording();
    for(const id of ['cta','redo','next'])$(id).disabled=true;
  }else showCard(0);
  $('sheetBody').addEventListener('scroll',updateScroll,{passive:true});
  $('scrollHint').onclick=()=>$('sheetBody').scrollBy({top:Math.max(110,$('sheetBody').clientHeight*.75),behavior:'auto'});
  document.fonts.ready.then(updateScroll);window.addEventListener('resize',updateScroll);updateScroll();
}
function updateScroll(){
  const el=$('sheetBody');$('scrollHint').hidden=el.scrollHeight-el.clientHeight<=10||el.scrollTop+el.clientHeight>=el.scrollHeight-16;
}
init();
