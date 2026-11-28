/* T3 – tout appel passe par le même atelier local. Pas de réseau tiers. */
(()=>{'use strict';
const $=id=>document.getElementById(id), cl=(n,t)=>{n.textContent=t;}, ids=['S1','S2','S3','S4'];
const form=$('fiche'), reel=$('relecture');let cfg, token, view=1, i=0, mediaUrl, resultUrl, creditUrl, cached={};
let draftExists=false,saveEnabled=false,savingTake=false;let fiche={},demo=false,prend={},ok={},pending=null,completed=null,busy=false,last=null,rev=0,canKeep=false;let lengths={},currentLength=0;
let voiceFile=null,voiceUrl=null,voiceRev=0,voiceStream=null,voiceRecorder=null,voiceTimer=null,voicePending=false,voiceEpoch=0;
const section=['fiche','prises','export'];
function problem(t){const a=$('alert');a.hidden=!t;cl(a,t||'');}
function annonceDraft(){$('repriseOfferte').hidden=!draftExists;}
function draftRecord(){return {version:1,contractRevision:cfg.contrat.revision,raw:Object.fromEntries(new FormData(form)),fiche:{...fiche},contact:!!form.elements.contactConfirme.checked};}
$('effacerTravail').onclick=async()=>{try{await T3Draft.clear();draftExists=false;saveEnabled=false;$('sauvegardeLocale').checked=false;annonceDraft();problem('Travail sauvegardé effacé de ce navigateur.');}catch(e){problem('Impossible d’effacer ce travail : '+e.message);}};
$('reprendreTravail').onclick=async()=>{try{let d=await T3Draft.read(),r=d.fiche;if(!r||r.version!==1||r.contractRevision!==cfg.contrat.revision||!r.raw||!r.fiche)throw Error('Ce travail ne correspond pas à cette version.');let {verifierPrise}=await import('./verifier-prise.mjs'),f={},lens={};for(const id of ids)if(d[id] instanceof Blob&&d[id].size>0&&d[id].size<=48*1024*1024){lens[id]=await verifierPrise(d[id],2,cfg.contrat.prises[id].secondes);f[id]=d[id];}let used=Object.values(lens).reduce((a,b)=>a+b,0),missing=ids.filter(id=>!f[id]).length;if(used+2*missing>cfg.contrat.media.images_max_avec_audio/30+0.00001)throw Error('Les prises sauvegardées dépassent la durée disponible.');setFiche(r.raw);fiche=r.fiche;form.elements.contactConfirme.checked=!!r.contact;prend=f;lengths=lens;ok=Object.fromEntries(Object.keys(f).map(id=>[id,true]));demo=false;saveEnabled=true;$('sauvegardeLocale').checked=true;$('repriseOfferte').hidden=true;setVoice(null);$('voiceFile').value='';$('subtitles').value='';$('voiceMode').value='separee';updateVoiceMode();$('piste').value='';for(const c of document.querySelectorAll('.takeVoiceChoice'))c.checked=false;liste();let m=ids.findIndex(id=>!ok[id]);if(m<0){show(3);majChoix();}else prendre(m);problem('Travail repris. Ajoute à nouveau la voix séparée, les sous-titres et les choix son si nécessaire.');}catch(e){problem('Impossible de reprendre ce travail : '+e.message);}};
function show(n){view=n;for(let j=0;j<3;j++){ $(section[j]).hidden=j!==n-1; $("step"+(j+1)).removeAttribute('aria-current'); } $('step'+n).setAttribute('aria-current','step');problem(null);if(n!==2)reel.pause();}
async function web(path,o={}){const headers={...o.headers};if(token)headers['X-T3-Session']=token;
 if('obj' in o){headers['Content-Type']='application/json';o.body=JSON.stringify(o.obj);delete o.obj;}
 const r=await fetch(path,{...o,headers,cache:'no-store'});if(!r.ok){let e;try{e=(await r.json()).erreur;}catch{e=null;}throw Error(e?.message||'L’atelier local ne répond pas.');}return r;
}
async function req(path,o){if(path==='api/config'){const r=await fetch('config.json',{cache:'no-store'});if(!r.ok)throw Error('La configuration T3 n’a pas chargé.');return r.json();}if(path==='api/session')return {session:'local'};if(o?.method==='DELETE')return {};throw Error('Action indisponible.');}
function detail(a,b){const li=document.createElement('li'),id=document.createElement('span'),name=document.createElement('span');cl(id,a);cl(name,b);li.append(id,name);return li;}
function liste(){ $('slots').replaceChildren(...ids.map((s,j)=>{const take=cfg.contrat.prises[s],x=detail(String(j+1).padStart(2,'0'),take.titre+(ok[s]?' ✓':'')),duration=document.createElement('small');cl(duration,'2 à '+take.secondes+' s');x.append(duration);if(ok[s])x.classList.add('kept');return x;})); }
function cible(){const present=!!form.elements.cible.value.trim();$('contactConfirmation').hidden=!present;form.elements.contactConfirme.required=present;if(!present)form.elements.contactConfirme.checked=false;}
function setFiche(data){for(const [k,v] of Object.entries(data))if(form.elements.namedItem(k))form.elements[k].value=v;cible();}
function release(){if(mediaUrl){URL.revokeObjectURL(mediaUrl);mediaUrl=null;} reel.pause();reel.removeAttribute('src');reel.load();reel.hidden=true;}
function clearResult(){const f=$('film');f.pause();f.removeAttribute('src');f.load();$('resultat').hidden=true;
 if(resultUrl)URL.revokeObjectURL(resultUrl);if(creditUrl)URL.revokeObjectURL(creditUrl);resultUrl=creditUrl=null;}
function openRep(blob,stamp){if(stamp!==rev)return;release();mediaUrl=URL.createObjectURL(blob);reel.src=mediaUrl;reel.hidden=false;reel.load();}
function disponible(j){let used=ids.reduce((a,s,k)=>a+(k===j?0:(ok[s]?lengths[s]||0:0)),0),unfilled=ids.reduce((a,s,k)=>a+(k!==j&&!ok[s]?1:0),0);return Math.min(cfg.contrat.prises[ids[j]].secondes,Math.floor((cfg.contrat.media.images_max_avec_audio/cfg.contrat.media.fps-used-2*unfilled)*30+0.00001)/30);}
function prendre(j){i=j;const s=ids[i],t=cfg.contrat.prises[s],stamp=++rev;currentLength=lengths[s]||0;show(2);release();canKeep=false;$('garder').disabled=true;$('fichier').value='';$('fichierLabel').hidden=demo||cfg.demo;
 $('exempleSeulement').hidden=!cfg.demo;cl($('scene'),`${s} · PRISE ${i+1} SUR 4`);cl($('priseTitre'),t.titre);
 cl($('guide'),t.guide+`  ·  de 2 à ${disponible(j).toFixed(1).replace('.',',')} secondes disponibles`);cl($('question'),t.question);cl($('meta'),ok[s]?'Relis ou remplace cette prise.':demo?'Lance la relecture puis garde la prise.':'Choisis le fichier, puis regarde la prise avant de la garder.');
 if(demo){(async()=>{try{cached[s]??=await (await web('exemple/'+s+'.mp4')).blob();openRep(cached[s],stamp);}catch(e){if(stamp===rev)problem(e.message);}})();}
 else if(prend[s])openRep(prend[s],stamp);
}
function majChoix(){for(const o of $('piste').options)o.disabled=!!last&&o.value===last;if($('piste').value===last)$('piste').value='';}
function boutons(){for(const b of ['rendre','muet','retourPrises','example','piste','voiceFile','recordVoice','voiceMode'])$(b).disabled=busy||voicePending||!!voiceRecorder;for(const e of document.querySelectorAll('.takeVoiceChoice'))e.disabled=busy||voicePending||!!voiceRecorder;$('clearVoice').disabled=busy||voicePending||!!voiceRecorder||!voiceFile;}
function setprogress(d){const textes={controle:'Vérification de la fiche et des prises',prises:'Préparation des quatre prises',image:'Montage de l’image',musique:'Ajout de la musique choisie',verification:'Contrôle du MP4 et des crédits'};
 $('progressBox').hidden=false;cl($('phase'),(textes[d.phase]||'Préparation du rendu')+` · ${d.avancement||0} %`);$('progress').value=d.avancement||0;}
function parseSubs(raw,duration){if(!raw.trim())return [];let last=0;return raw.trim().split(/\n/).map((line,i)=>{let m=line.match(/^\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*\|\s*(.{1,100})\s*$/);if(!m)throw Error('Sous-titre '+(i+1)+' : indique début-fin | texte.');let start=Number(m[1].replace(',','.')),end=Number(m[2].replace(',','.'));if(start<last||end<=start||end>duration)throw Error('Vérifie les sous-titres : ils doivent rester dans le film, sans chevauchement.');last=end;return {start,end,text:m[3].trim()};});}
async function lancer(mode){if(busy)return;busy=true;boutons();problem(null);clearResult();$('progressBox').hidden=false;cl($('phase'),'Préparation du montage dans ton navigateur…');$('progress').value=0;
 try{const selected=$('piste').value||ids.map((_,i)=>String(i+1).padStart(2,'0')).find(x=>x!==last),track=cfg.catalogue.find(t=>t.id===selected);if(mode!=='muet'&&!track)throw Error('Choisis une musique.');
 const files={};for(const id of ids){if(demo){let r=await fetch('exemple/'+id+'.mp4');if(!r.ok)throw Error('Mire indisponible.');files[id]=await r.blob()}else files[id]=prend[id];if(!files[id])throw Error('Garde les quatre prises avant le montage.');}
 let takeFiles=null,voice=null;if(mode!=='muet'){
  if($('voiceMode').value==='separee')voice=voiceFile;
  else if($('voiceMode').value==='prises'){
   if(demo)throw Error('La simulation utilise des images de test : choisis tes propres prises pour utiliser leur son.');
   takeFiles=[...document.querySelectorAll('.takeVoiceChoice:checked')].map(e=>({id:e.value,file:files[e.value]}));
  }
 }
 const {Input,BlobSource,MP4,QTFF,WEBM}=await import('./vendor/mediabunny-1.66.1.min.mjs');const durations=[];for(const id of ids){let m=new Input({source:new BlobSource(files[id]),formats:[MP4,QTFF,WEBM]});try{let v=await m.getPrimaryVideoTrack();if(!v||!await v.canDecode())throw Error('Une prise est illisible.');durations.push((await v.computeDuration())-(await v.getFirstTimestamp()));}finally{m.dispose()}}
 const {planifier}=await import('./plan-durees-candidat.mjs');const plan=planifier(durations,{fps:cfg.contrat.media.fps,maxFilm:cfg.contrat.media.images_max_avec_audio/cfg.contrat.media.fps,maxPrises:ids.map(id=>cfg.contrat.prises[id].secondes),minPrise:2});const duration=plan.totalImages/plan.fps;if(mode!=='muet'&&plan.totalImages>cfg.contrat.media.images_max_avec_audio)throw Error('Le son ne peut pas tenir dans le fichier sans dépasser 30 secondes. Refais une prise légèrement plus courte : aucune fin ne sera coupée.');const subtitles=parseSubs($('subtitles').value,duration);if(subtitles.length&&!voice&&!takeFiles)throw Error('Les sous-titres nécessitent une voix.');
 const r=await fetch('plan-t3-candidat.json',{cache:'no-store'});if(!r.ok)throw Error('Plan T3 indisponible.');const contrat=await r.json();const {audioMix}=await import('./audio-mix-candidat.mjs');const audio=mode==='muet'?null:await audioMix(selected,voice,plan.totalImages,takeFiles,plan.scenes.map(s=>s.images),cfg);const worker=new Worker('render.worker.mjs?v=t3-revision-30s-3',{type:'module'});
 const buffer=await new Promise((resolve,reject)=>{worker.onerror=e=>{worker.terminate();reject(Error(e.message||'Le moteur ne démarre pas.'));};worker.onmessage=e=>{let d=e.data;if(d.stage==='encode'){cl($('phase'),`Montage dans ton navigateur · ${Math.round(100*d.completed/d.total)} %`);$('progress').value=100*d.completed/d.total;}else if(d.stage==='done'){worker.terminate();resolve(d.buffer);}else if(d.stage==='error'){worker.terminate();reject(Error(d.message));}};worker.postMessage({files,fiche,audio,plan,contrat,subtitles,credit:track?.credit||''});});
 cl($('phase'),'Vérification du fichier final…');const finalBlob=new Blob([buffer],{type:'video/mp4'});const {verifierSortie}=await import('./verifier-sortie.mjs');await verifierSortie(finalBlob,!!audio);
 resultUrl=URL.createObjectURL(finalBlob);$('dl').href=resultUrl;$('film').src=resultUrl;cl($('titreResultat'),mode==='muet'?`Contrôle muet · ${duration.toFixed(1)} secondes`:`${track.id} · ${track.titre}`);$('dlCredit').hidden=mode==='muet';cl($('credit'),mode==='muet'?'Montage sans piste audio.':track.credit);if(mode!=='muet'){creditUrl=URL.createObjectURL(new Blob([track.credit+'\n'],{type:'text/plain;charset=utf-8'}));$('dlCredit').href=creditUrl;last=selected;majChoix();} $('progressBox').hidden=true;$('resultat').hidden=false;
 }catch(e){$('progressBox').hidden=true;problem(e.message);}finally{busy=false;boutons();}
}
$('example').onclick=()=>{if(busy)return;saveEnabled=false;$('sauvegardeLocale').checked=false;setFiche(cfg.exemple);demo=true;prend={};ok={};lengths={};liste();clearResult();show(1);$('real').hidden=false;$('simulationNotice').hidden=false;cl($('example'),'Exemple chargé');};
$('real').onclick=()=>{if(busy)return;demo=false;prend={};ok={};lengths={};liste();clearResult();$('real').hidden=true;$('simulationNotice').hidden=true;cl($('example'),'Charger la fiche d’exemple');};
form.elements.cible.addEventListener('input',cible);
form.addEventListener('change',cible);
form.onsubmit=async e=>{e.preventDefault();if(!cfg)return;
 if(cfg.demo&&!demo){problem('Sur cet aperçu, clique sur « Charger l’exemple » pour utiliser les prises de démonstration.');return;}
 fiche=cfg.demo?{...cfg.exemple}:Object.fromEntries(new FormData(form));for(const k of Object.keys(fiche))fiche[k]=fiche[k].trim();
 if(!fiche.nom||!fiche.service){problem('Indique le nom de ton activité et le produit ou service présenté.');return;}
 if(fiche.cible&&(!/^[+0-9 ()\-.]{6,32}$/.test(fiche.cible)||fiche.cible.replace(/\D/g,'').length<6)){problem('Vérifie ton numéro de téléphone.');return;}
 fiche.action='aucune';fiche.geste='';fiche.detail='';if(fiche.prix)fiche.prix='À partir de '+fiche.prix;
 $('voiceMode').value=fiche.modeVoixPrises==='oui'?'prises':'separee';document.querySelectorAll('.takeVoiceChoice').forEach(e=>e.checked=fiche.modeVoixPrises==='oui');updateVoiceMode();
 if(!demo&&$('sauvegardeLocale').checked){try{if(draftExists&&!saveEnabled){problem('Un travail est déjà sauvegardé. Reprends-le ou efface-le avant d’en sauvegarder un nouveau.');return;}if(saveEnabled)await T3Draft.updateFiche(draftRecord());else{await T3Draft.create(draftRecord());draftExists=true;saveEnabled=true;}annonceDraft();}catch(err){problem('Sauvegarde impossible sur cet appareil : '+err.message+' Décoche l’option pour continuer sans reprise.');return;}}else saveEnabled=false;
 $('repriseOfferte').hidden=true;prendre(ids.findIndex(id=>!ok[id])<0?0:ids.findIndex(id=>!ok[id]));
};
$('fichier').onchange=async()=>{const f=$('fichier').files[0], s=ids[i];if(!f)return;
 const stamp=++rev;delete ok[s];delete prend[s];liste();problem(null);canKeep=false;$('garder').disabled=true;release();
 try{const {verifierPrise}=await import('./verifier-prise.mjs');currentLength=await verifierPrise(f,2,disponible(i));if(stamp!==rev||ids[i]!==s)return;prend[s]=f;openRep(f,stamp);}
 catch(e){if(stamp===rev&&ids[i]===s){problem(e.message);cl($('meta'),'Choisis une autre prise.');}}
};
reel.onloadedmetadata=()=>{cl($('meta'),`${reel.duration.toFixed(1).replace('.',',')} s · Lance la lecture pour confirmer.`);};
reel.ontimeupdate=()=>{if(view!==2||reel.hidden)return;if(reel.currentTime>.10&&(demo||currentLength>=2)){canKeep=true;$('garder').disabled=false;}};
reel.onerror=()=>{if(view===2&&!reel.hidden){problem('Ce navigateur ne relit pas le fichier. Essaie un MP4 H.264 lisible.');$('garder').disabled=true;canKeep=false;}};
$('garder').onclick=async()=>{if(!canKeep||busy||savingTake)return;if(demo){try{let {verifierPrise}=await import('./verifier-prise.mjs');currentLength=await verifierPrise(cached[ids[i]],2,disponible(i));}catch(e){problem(e.message);return;}}if(saveEnabled&&!demo){savingTake=true;try{await T3Draft.saveTake(ids[i],prend[ids[i]]);}catch(e){problem('La prise n’a pas pu être sauvegardée. Libère de l’espace ou reviens à la fiche pour continuer sans sauvegarde.');return;}finally{savingTake=false;}}lengths[ids[i]]=currentLength;ok[ids[i]]=true;liste();
 let next=ids.findIndex((id,j)=>j>i&&!ok[id]);if(next<0)next=ids.findIndex(id=>!ok[id]);if(next>=0){prendre(next);return;}release();if(ids.every(s=>ok[s])){show(3);majChoix();}
};
function fermerCapture(){$('captureFrame').removeAttribute('src');$('captureBox').hidden=true;$('captureIntro').hidden=false;$('importFlow').hidden=false;}
function envoyerFicheCapture(){if($('captureFrame').getAttribute('src'))$('captureFrame').contentWindow.postMessage({type:'vv-t3-fiche',fiche,persist:saveEnabled&&!demo,files:prend,lengths,accepted:ids.filter(id=>ok[id])},location.origin);}
$('captureFrame').addEventListener('load',envoyerFicheCapture);
$('captureStart').onclick=()=>{release();$('captureIntro').hidden=true;$('importFlow').hidden=true;$('captureBox').hidden=false;$('captureFrame').src='capture.html?v=t3-revision-30s-3'+(demo?'&demo=1':'');};
$('captureClose').onclick=()=>{fermerCapture();const m=ids.findIndex(id=>!ok[id]);if(m<0){show(3);majChoix();}else prendre(m);};
window.addEventListener('message',e=>{const d=e.data;if(e.origin===location.origin&&e.source===$('captureFrame').contentWindow&&d?.type==='vv-t3-pret'){envoyerFicheCapture();return;}if(e.origin===location.origin&&e.source===$('captureFrame').contentWindow&&d?.type==='vv-t3-accepted'&&!demo&&ids.includes(d.id)&&d.file instanceof Blob&&d.file.size>0&&d.file.size<=48*1024*1024&&Number.isFinite(d.duration)&&d.duration>=2&&d.duration<=cfg.contrat.prises[d.id].secondes){prend[d.id]=d.file;lengths[d.id]=d.duration;ok[d.id]=true;liste();return;}if(e.origin!==location.origin||e.source!==$('captureFrame').contentWindow||d?.type!=='vv-t3-captures'||!Array.isArray(d.files)||d.files.length!==4||d.demo!==demo||!d.files.every(x=>x instanceof Blob&&x.size>0&&x.size<=48*1024*1024))return;
 if(!demo)prend=Object.fromEntries(ids.map((s,j)=>[s,d.files[j]]));if(Array.isArray(d.lengths)&&d.lengths.length===4)lengths=Object.fromEntries(ids.map((s,j)=>[s,d.lengths[j]]));ok=Object.fromEntries(ids.map(s=>[s,true]));liste();fermerCapture();show(3);majChoix();});
$('retourFiche').onclick=()=>{fermerCapture();release();show(1);annonceDraft();};
$('retourPrises').onclick=async()=>{if(busy)return;try{if(pending)await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;clearResult();prendre(0);}catch(e){problem(e.message);}};
$('muet').onclick=()=>lancer('muet');$('rendre').onclick=()=>lancer('musique_seule');
function setVoice(file){
 if(voiceUrl)URL.revokeObjectURL(voiceUrl);voiceUrl=null;voiceFile=null;voiceRev++;
 const p=$('voicePreview');p.pause();p.removeAttribute('src');p.load();p.hidden=true;
 if(file){
  if(!file.size||file.size>20*1024*1024){cl($('voiceStatus'),'Fichier absent ou trop lourd : maximum 20 Mio.');boutons();return;}
  voiceFile=file;voiceUrl=URL.createObjectURL(file);p.src=voiceUrl;p.hidden=false;p.load();cl($('voiceStatus'),'Voix prête. Le montage vérifie sa durée ; tu peux l’écouter si tu le souhaites.');
 }else cl($('voiceStatus'),'Aucune voix ajoutée.');boutons();
}
function updateVoiceMode(){$('takeVoice').hidden=$('voiceMode').value!=='prises';$('separateVoice').hidden=$('voiceMode').value!=='separee';}
$('voiceMode').onchange=updateVoiceMode;updateVoiceMode();
$('voiceFile').onchange=()=>{const f=$('voiceFile').files[0];if(f)setVoice(f);};
$('clearVoice').onclick=async()=>{if(busy||voicePending||voiceRecorder)return;try{if(pending){await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;}$('voiceFile').value='';setVoice(null);}catch(e){problem(e.message);}};
$('recordVoice').onclick=async()=>{
 if(busy||voicePending||voiceRecorder)return;voicePending=true;const epoch=++voiceEpoch;boutons();problem(null);
 try{
  if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined')throw Error('Le micro n’est pas disponible ici. Utilise HTTPS ou importe un fichier.');
  const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
  if(epoch!==voiceEpoch){stream.getTracks().forEach(t=>t.stop());return;}voiceStream=stream;
  const chunks=[],rec=new MediaRecorder(voiceStream);let limiteAtteinte=false;voiceRecorder=rec;
  rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  rec.onerror=()=>{cl($('voiceStatus'),'L’enregistrement a échoué. Réessaie ou importe une voix.');};
  rec.onstop=()=>{
   clearTimeout(voiceTimer);voiceStream?.getTracks().forEach(t=>t.stop());voiceStream=null;voiceRecorder=null;$('stopVoice').disabled=true;
   if(limiteAtteinte){setVoice(null);cl($('voiceStatus'),'La limite est atteinte : ta voix pourrait être coupée. Recommence et arrête avant la limite.');boutons();return;}const blob=new Blob(chunks,{type:rec.mimeType||'audio/webm'});if(blob.size)setVoice(blob);else{cl($('voiceStatus'),'Aucun son enregistré.');boutons();}
  };
  rec.start();$('stopVoice').disabled=false;boutons();cl($('voiceStatus'),'Enregistrement en cours · 30 secondes maximum.');voiceTimer=setTimeout(()=>{if(rec.state==='recording'){limiteAtteinte=true;rec.stop();}},30000);
 }catch(e){voiceStream?.getTracks().forEach(t=>t.stop());voiceStream=null;voiceRecorder=null;cl($('voiceStatus'),e.name==='NotAllowedError'?'Accès au micro refusé. Tu peux importer une voix.':e.message);}
 finally{voicePending=false;boutons();}
};
$('stopVoice').onclick=()=>{if(voiceRecorder?.state==='recording')voiceRecorder.stop();};
window.addEventListener('pagehide',()=>{voiceEpoch++;clearTimeout(voiceTimer);if(voiceRecorder?.state==='recording')voiceRecorder.stop();voiceStream?.getTracks().forEach(t=>t.stop());if(voiceUrl)URL.revokeObjectURL(voiceUrl);});
(async()=>{try{
 cfg=await req('api/config');if(cfg.contrat.media?.fps!==30||cfg.contrat.media?.secondes_max!==30||cfg.contrat.media?.images_max_avec_audio!==899||ids.some(id=>cfg.contrat.prises[id]?.secondes_min!==2))throw Error('Contrat de durée T3 invalide.');
 const qr=await fetch('formulaire/questions.json',{cache:'no-store'});if(!qr.ok)throw Error('Les questions T3 ne sont pas disponibles.');const q=await qr.json();
 const expected=['nom','service','outil','lieu','cible','prix'];if(q.template_id!=='COIFFURE-T3'||!Array.isArray(q.questions)||q.questions.length!==expected.length||q.questions.some((x,i)=>x.id!==expected[i]||typeof x.libelle!=='string'||!x.libelle.trim()||typeof x.obligatoire!=='boolean'||x.obligatoire!==cfg.contrat.fiche[x.id]?.requis))throw Error('Les questions T3 ne correspondent pas au contrat.');
 for(const item of q.questions){const field=form.elements.namedItem(item.id),label=field?.closest('label');if(!label||label.firstChild.nodeType!==Node.TEXT_NODE)throw Error('Le formulaire T3 ne correspond pas aux questions.');label.firstChild.nodeValue=item.libelle+' ';field.required=item.obligatoire;field.maxLength=cfg.contrat.fiche[item.id].max;}
 $('voicePanel').hidden=cfg.demo;if(cfg.demo){for(const el of form.querySelectorAll('input,select'))el.disabled=true;}const s=await req('api/session',{method:'POST',obj:{}});token=s.session;
 for(const x of cfg.catalogue){const li=detail(x.id,x.titre);const sm=document.createElement('small');cl(sm,x.artiste);li.lastElementChild.append(sm);$('tracks').append(li);$('piste').add(new Option(x.id+' · '+x.titre,x.id));}
 liste();try{draftExists=await T3Draft.exists();annonceDraft();}catch(e){draftExists=false;}$('example').disabled=false;$('continuer').disabled=false;
 }catch(e){problem(e.message);}})();
})();
