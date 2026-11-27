/* T3 – tout appel passe par le même atelier local. Pas de réseau tiers. */
(()=>{'use strict';
const $=id=>document.getElementById(id), cl=(n,t)=>{n.textContent=t;}, ids=['S1','S2','S3','S4'];
const form=$('fiche'), reel=$('relecture');let cfg, token, view=1, i=0, mediaUrl, resultUrl, creditUrl, cached={};
let fiche={},demo=false,prend={},ok={},pending=null,completed=null,busy=false,last=null,rev=0,canKeep=false;
let voiceFile=null,voiceUrl=null,voiceRev=0,voiceStream=null,voiceRecorder=null,voiceTimer=null,voicePending=false,voiceEpoch=0;
const section=['fiche','prises','export'];
function problem(t){const a=$('alert');a.hidden=!t;cl(a,t||'');}
function show(n){view=n;for(let j=0;j<3;j++){ $(section[j]).hidden=j!==n-1; $("step"+(j+1)).removeAttribute('aria-current'); } $('step'+n).setAttribute('aria-current','step');problem(null);if(n!==2)reel.pause();}
async function web(path,o={}){const headers={...o.headers};if(token)headers['X-T3-Session']=token;
 if('obj' in o){headers['Content-Type']='application/json';o.body=JSON.stringify(o.obj);delete o.obj;}
 const r=await fetch(path,{...o,headers,cache:'no-store'});if(!r.ok){let e;try{e=(await r.json()).erreur;}catch{e=null;}throw Error(e?.message||'L’atelier local ne répond pas.');}return r;
}
async function req(path,o){if(path==='api/config'){const r=await fetch('config.json',{cache:'no-store'});if(!r.ok)throw Error('La configuration T3 n’a pas chargé.');return r.json();}if(path==='api/session')return {session:'local'};if(o?.method==='DELETE')return {};throw Error('Action indisponible.');}
function detail(a,b){const li=document.createElement('li'),id=document.createElement('span'),name=document.createElement('span');cl(id,a);cl(name,b);li.append(id,name);return li;}
function liste(){ $('slots').replaceChildren(...ids.map((s,j)=>{const take=cfg.contrat.prises[s],x=detail(String(j+1).padStart(2,'0'),take.titre+(ok[s]?' ✓':'')),duration=document.createElement('small');cl(duration,take.secondes+' s');x.append(duration);if(ok[s])x.classList.add('kept');return x;})); }
function cible(){const present=!!form.elements.cible.value.trim();$('contactConfirmation').hidden=!present;form.elements.contactConfirme.required=present;if(!present)form.elements.contactConfirme.checked=false;}
function setFiche(data){for(const [k,v] of Object.entries(data))if(form.elements.namedItem(k))form.elements[k].value=v;cible();}
function release(){if(mediaUrl){URL.revokeObjectURL(mediaUrl);mediaUrl=null;} reel.pause();reel.removeAttribute('src');reel.load();reel.hidden=true;}
function clearResult(){const f=$('film');f.pause();f.removeAttribute('src');f.load();$('resultat').hidden=true;
 if(resultUrl)URL.revokeObjectURL(resultUrl);if(creditUrl)URL.revokeObjectURL(creditUrl);resultUrl=creditUrl=null;}
function openRep(blob,stamp){if(stamp!==rev)return;release();mediaUrl=URL.createObjectURL(blob);reel.src=mediaUrl;reel.hidden=false;reel.load();}
function prendre(j){i=j;const s=ids[i],t=cfg.contrat.prises[s],stamp=++rev;show(2);release();canKeep=false;$('garder').disabled=true;$('fichier').value='';$('fichierLabel').hidden=demo||cfg.demo;
 $('exempleSeulement').hidden=!cfg.demo;cl($('scene'),`${s} · PRISE ${i+1} SUR 4`);cl($('priseTitre'),t.titre);
 cl($('guide'),t.guide+`  ·  ${t.secondes} secondes minimum`+(fiche.modeVoixPrises==='oui'?`  ·  Avec voix des prises : seules les ${j===0?6:8} premières secondes seront gardées.`:''));cl($('question'),t.question);cl($('meta'),ok[s]?'Relis ou remplace cette prise.':demo?'Lance la relecture puis garde la prise.':'Choisis le fichier, puis regarde la prise avant de la garder.');
 if(demo){(async()=>{try{cached[s]??=await (await web('exemple/'+s+'.mp4')).blob();openRep(cached[s],stamp);}catch(e){if(stamp===rev)problem(e.message);}})();}
 else if(prend[s])openRep(prend[s],stamp);
}
function majChoix(){for(const o of $('piste').options)o.disabled=!!last&&o.value===last;if($('piste').value===last)$('piste').value='';}
function boutons(){for(const b of ['rendre','muet','retourPrises','example','piste','voiceFile','recordVoice','voiceMode'])$(b).disabled=busy||voicePending||!!voiceRecorder;for(const e of document.querySelectorAll('.takeVoiceChoice'))e.disabled=busy||voicePending||!!voiceRecorder;$('clearVoice').disabled=busy||voicePending||!!voiceRecorder||!voiceFile;}
function setprogress(d){const textes={controle:'Vérification de la fiche et des prises',prises:'Préparation des quatre prises',image:'Montage de l’image',musique:'Ajout de la musique choisie',verification:'Contrôle du MP4 et des crédits'};
 $('progressBox').hidden=false;cl($('phase'),(textes[d.phase]||'Préparation du rendu')+` · ${d.avancement||0} %`);$('progress').value=d.avancement||0;}
async function decodeAudio(file, ctx){try{return await ctx.decodeAudioData(await file.arrayBuffer());}catch{throw Error('Fichier audio illisible sur ce navigateur. Essaie un autre format.');}}
async function audioMix(track,voice,takeFiles){
 const C=window.AudioContext||window.webkitAudioContext;if(!C)throw Error('Audio indisponible sur ce navigateur.');const ctx=new C({sampleRate:48000});try{
 const resp=await fetch('audio/'+track+'.flac');if(!resp.ok)throw Error('Musique indisponible.');let bed=await decodeAudio(await resp.blob(),ctx),v=voice?await decodeAudio(voice,ctx):null;
 if(takeFiles){
  if(!takeFiles.length)throw Error('Choisis au moins une prise dont tu veux garder le son.');
  const MB=await import('./vendor/mediabunny-1.66.1.min.mjs');const slotStarts=[0,6,14,22],slotDurations=[6,8,8,8],sr=ctx.sampleRate;v=ctx.createBuffer(2,sr*30,sr);
  for(const {id,file} of takeFiles){
   const idx=ids.indexOf(id);if(idx<0)throw Error('Prise audio inconnue.');let input=new MB.Input({source:new MB.BlobSource(file),formats:[MB.MP4,MB.QTFF,MB.WEBM]}),videoStart,audioStart,audioEnd;
   try{const video=await input.getPrimaryVideoTrack(),track=await input.getPrimaryAudioTrack();if(!video||!track||!await track.canDecode())throw Error('son absent');videoStart=await video.getFirstTimestamp();audioStart=await track.getFirstTimestamp();audioEnd=await track.computeDuration();}catch{throw Error('Le son de la prise '+(idx+1)+' est absent ou illisible. Décoche cette prise ou importe une vidéo avec du son.');}finally{input.dispose();}
   let a;try{a=await ctx.decodeAudioData(await file.arrayBuffer());}catch{throw Error('Le son de la prise '+(idx+1)+' est absent ou illisible. Décoche cette prise ou importe une vidéo avec du son.');}
   // WebAudio peut retirer l'amorce d'un encodeur ; recaler le début décodé sur la fin de piste connue.
   const effectiveStart=Math.max(audioStart,audioEnd-a.duration),offset=Math.round((effectiveStart-videoStart)*sr),sourceStart=Math.max(0,-offset),destWithin=Math.max(0,offset),count=Math.min(a.length-sourceStart,slotDurations[idx]*sr-destWithin);
   if(count<=0)throw Error('Le son de la prise '+(idx+1)+' ne commence pas dans la partie conservée.');
   for(let ch=0;ch<2;ch++)v.copyToChannel(a.getChannelData(Math.min(ch,a.numberOfChannels-1)).subarray(sourceStart,sourceStart+count),ch,slotStarts[idx]*sr+destWithin);
  }
 }
 if(v&&(v.duration<.3||v.duration>30.15))throw Error('La voix doit durer entre 0,3 et 30 secondes.');
 const sr=48000,n=sr*30,left=new Float32Array(n),right=new Float32Array(n);let rms=0,vg=1;
 if(v){let energy=0,count=0,step=Math.round(sr*.4);for(let i=0;i<v.length;i+=step){let sum=0,end=Math.min(v.length,i+step);for(let c=0;c<v.numberOfChannels;c++){let samples=v.getChannelData(c);for(let j=i;j<end;j++)sum+=samples[j]*samples[j];}let k=(end-i)*v.numberOfChannels;if(sum/k>1e-5){energy+=sum;count+=k;}}rms=Math.sqrt(energy/Math.max(1,count));if(!Number.isFinite(rms)||rms<.0001)throw Error('La voix est silencieuse ou trop faible.');vg=Math.min(5,Math.pow(10,-20.5/20)/rms);}
 const bl=bed.getChannelData(0),br=bed.getChannelData(Math.min(1,bed.numberOfChannels-1)),vl=v?.getChannelData(0),vr=v?.getChannelData(Math.min(1,v.numberOfChannels-1));
 let env=0,attack=Math.exp(-1/(sr*.04)),release=Math.exp(-1/(sr*.6));for(let i=0;i<n;i++){
  let a=vl&&i<vl.length?vl[i]*vg:0,b=vr&&i<vr.length?vr[i]*vg:0,det=Math.max(Math.abs(a),Math.abs(b)),coef=det>env?attack:release;env=coef*env+(1-coef)*det;
  let duck=v?Math.max(.22,Math.min(1,Math.pow(.03/Math.max(.03,env),.70))):1,base=v?.707:1;let x=(bl[i]||0)*base*duck+a,y=(br[i]||0)*base*duck+b;
  // Conservative peak guard, no automatic gain. Voice and music stay in this browser.
  left[i]=Math.max(-.55,Math.min(.55,x));right[i]=Math.max(-.55,Math.min(.55,y));
 }return {left,right};}finally{await ctx.close()}}
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
 const audio=mode==='muet'?null:await audioMix(selected,voice,takeFiles);const worker=new Worker('render.worker.mjs',{type:'module'});
 const buffer=await new Promise((resolve,reject)=>{worker.onerror=e=>{worker.terminate();reject(Error(e.message||'Le moteur ne démarre pas.'));};worker.onmessage=e=>{let d=e.data;if(d.stage==='encode'){cl($('phase'),`Montage dans ton navigateur · ${Math.round(100*d.completed/d.total)} %`);$('progress').value=100*d.completed/d.total;}else if(d.stage==='done'){worker.terminate();resolve(d.buffer);}else if(d.stage==='error'){worker.terminate();reject(Error(d.message));}};worker.postMessage({files,fiche,audio,montageVoixPrises:!!takeFiles,credit:track?.credit||''});});
 resultUrl=URL.createObjectURL(new Blob([buffer],{type:'video/mp4'}));$('dl').href=resultUrl;$('film').src=resultUrl;cl($('titreResultat'),mode==='muet'?'Contrôle muet · 30 secondes':`${track.id} · ${track.titre}`);$('dlCredit').hidden=mode==='muet';cl($('credit'),mode==='muet'?'Montage sans piste audio.':track.credit);if(mode!=='muet'){creditUrl=URL.createObjectURL(new Blob([track.credit+'\n'],{type:'text/plain;charset=utf-8'}));$('dlCredit').href=creditUrl;last=selected;majChoix();} $('progressBox').hidden=true;$('resultat').hidden=false;
 }catch(e){$('progressBox').hidden=true;problem(e.message);}finally{busy=false;boutons();}
}
$('example').onclick=()=>{if(busy)return;setFiche(cfg.exemple);demo=true;prend={};ok={};liste();clearResult();show(1);$('real').hidden=false;$('simulationNotice').hidden=false;cl($('example'),'Exemple chargé');};
$('real').onclick=()=>{if(busy)return;demo=false;prend={};ok={};liste();clearResult();$('real').hidden=true;$('simulationNotice').hidden=true;cl($('example'),'Charger la fiche d’exemple');};
form.elements.cible.addEventListener('input',cible);
form.addEventListener('change',cible);
form.onsubmit=e=>{e.preventDefault();if(!cfg)return;
 if(cfg.demo&&!demo){problem('Sur cet aperçu, clique sur « Charger l’exemple » pour utiliser les prises de démonstration.');return;}
 fiche=cfg.demo?{...cfg.exemple}:Object.fromEntries(new FormData(form));for(const k of Object.keys(fiche))fiche[k]=fiche[k].trim();
 if(!fiche.nom||!fiche.service){problem('Indique le nom de ton activité et le produit ou service présenté.');return;}
 if(fiche.cible&&(!/^[+0-9 ()\-.]{6,32}$/.test(fiche.cible)||fiche.cible.replace(/\D/g,'').length<6)){problem('Vérifie ton numéro de téléphone.');return;}
 fiche.action='aucune';fiche.geste='';fiche.detail='';if(fiche.prix)fiche.prix='À partir de '+fiche.prix;
 $('voiceMode').value=fiche.modeVoixPrises==='oui'?'prises':'separee';document.querySelectorAll('.takeVoiceChoice').forEach(e=>e.checked=fiche.modeVoixPrises==='oui');updateVoiceMode();
 prendre(0);
};
$('fichier').onchange=async()=>{const f=$('fichier').files[0], s=ids[i];if(!f)return;
 const stamp=++rev;delete ok[s];delete prend[s];liste();problem(null);canKeep=false;$('garder').disabled=true;release();
 try{const {verifierPrise}=await import('./verifier-prise.mjs');await verifierPrise(f,cfg.contrat.prises[s].secondes);if(stamp!==rev||ids[i]!==s)return;prend[s]=f;openRep(f,stamp);}
 catch(e){if(stamp===rev&&ids[i]===s){problem(e.message);cl($('meta'),'Choisis une autre prise.');}}
};
reel.onloadedmetadata=()=>{const need=cfg.contrat.prises[ids[i]].secondes;cl($('meta'),`${reel.duration.toFixed(1).replace('.',',')} s · ${reel.duration+.05>=need?'Lance la lecture pour confirmer.':'Cette prise est trop courte.'}`);};
reel.ontimeupdate=()=>{if(view!==2||reel.hidden)return;if(reel.currentTime>.10&&reel.duration+.05>=cfg.contrat.prises[ids[i]].secondes){canKeep=true;$('garder').disabled=false;}};
reel.onerror=()=>{if(view===2&&!reel.hidden){problem('Ce navigateur ne relit pas le fichier. Essaie un MP4 H.264 lisible.');$('garder').disabled=true;canKeep=false;}};
$('garder').onclick=async()=>{if(!canKeep||busy)return;ok[ids[i]]=true;liste();
 if(i<3){prendre(i+1);return;}release();if(ids.every(s=>ok[s])){show(3);majChoix();}
};
function fermerCapture(){$('captureFrame').removeAttribute('src');$('captureBox').hidden=true;$('captureIntro').hidden=false;$('importFlow').hidden=false;}
$('captureFrame').addEventListener('load',()=>{if($('captureFrame').getAttribute('src'))$('captureFrame').contentWindow.postMessage({type:'vv-t3-fiche',fiche},location.origin);});
$('captureStart').onclick=()=>{release();$('captureIntro').hidden=true;$('importFlow').hidden=true;$('captureBox').hidden=false;$('captureFrame').src='capture.html'+(demo?'?demo=1':'');};
$('captureClose').onclick=()=>{fermerCapture();prendre(0);};
window.addEventListener('message',e=>{const d=e.data;if(e.origin!==location.origin||e.source!==$('captureFrame').contentWindow||d?.type!=='vv-t3-captures'||!Array.isArray(d.files)||d.files.length!==4||d.demo!==demo||!d.files.every(x=>x instanceof Blob&&x.size>0&&x.size<=48*1024*1024))return;
 if(!demo)prend=Object.fromEntries(ids.map((s,j)=>[s,d.files[j]]));ok=Object.fromEntries(ids.map(s=>[s,true]));liste();fermerCapture();show(3);majChoix();});
$('retourFiche').onclick=()=>{fermerCapture();release();show(1);};
$('retourPrises').onclick=async()=>{if(busy)return;try{if(pending)await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;clearResult();prendre(0);}catch(e){problem(e.message);}};
$('muet').onclick=()=>lancer('muet');$('rendre').onclick=()=>lancer('musique_seule');
function setVoice(file){
 if(voiceUrl)URL.revokeObjectURL(voiceUrl);voiceUrl=null;voiceFile=null;voiceRev++;
 const p=$('voicePreview');p.pause();p.removeAttribute('src');p.load();p.hidden=true;
 if(file){
  if(!file.size||file.size>20*1024*1024){cl($('voiceStatus'),'Fichier absent ou trop lourd : maximum 20 Mio.');boutons();return;}
  voiceFile=file;voiceUrl=URL.createObjectURL(file);p.src=voiceUrl;p.hidden=false;p.load();cl($('voiceStatus'),'Voix prête : écoute-la avant de créer ton MP4. Le montage vérifie sa durée.');
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
  const chunks=[],rec=new MediaRecorder(voiceStream);voiceRecorder=rec;
  rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  rec.onerror=()=>{cl($('voiceStatus'),'L’enregistrement a échoué. Réessaie ou importe une voix.');};
  rec.onstop=()=>{
   clearTimeout(voiceTimer);voiceStream?.getTracks().forEach(t=>t.stop());voiceStream=null;voiceRecorder=null;$('stopVoice').disabled=true;
   const blob=new Blob(chunks,{type:rec.mimeType||'audio/webm'});if(blob.size)setVoice(blob);else{cl($('voiceStatus'),'Aucun son enregistré.');boutons();}
  };
  rec.start();$('stopVoice').disabled=false;boutons();cl($('voiceStatus'),'Enregistrement en cours · 30 secondes maximum.');voiceTimer=setTimeout(()=>{if(rec.state==='recording')rec.stop();},29500);
 }catch(e){voiceStream?.getTracks().forEach(t=>t.stop());voiceStream=null;voiceRecorder=null;cl($('voiceStatus'),e.name==='NotAllowedError'?'Accès au micro refusé. Tu peux importer une voix.':e.message);}
 finally{voicePending=false;boutons();}
};
$('stopVoice').onclick=()=>{if(voiceRecorder?.state==='recording')voiceRecorder.stop();};
window.addEventListener('pagehide',()=>{voiceEpoch++;clearTimeout(voiceTimer);if(voiceRecorder?.state==='recording')voiceRecorder.stop();voiceStream?.getTracks().forEach(t=>t.stop());if(voiceUrl)URL.revokeObjectURL(voiceUrl);});
(async()=>{try{
 cfg=await req('api/config');$('voicePanel').hidden=cfg.demo;if(cfg.demo){for(const el of form.querySelectorAll('input,select'))el.disabled=true;}const s=await req('api/session',{method:'POST',obj:{}});token=s.session;
 for(const x of cfg.catalogue){const li=detail(x.id,x.titre);const sm=document.createElement('small');cl(sm,x.artiste);li.lastElementChild.append(sm);$('tracks').append(li);$('piste').add(new Option(x.id+' · '+x.titre,x.id));}
 liste();$('example').disabled=false;$('continuer').disabled=false;
 }catch(e){problem(e.message);}})();
})();
