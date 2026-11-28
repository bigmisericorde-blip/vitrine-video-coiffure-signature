/* T4 – tout appel passe par le même atelier local. Pas de réseau tiers. */
(()=>{'use strict';
const $=id=>document.getElementById(id), cl=(n,t)=>{n.textContent=t;}, ids=['S1','S2','S3','S4'];
const form=$('fiche'), reel=$('relecture');let cfg, token, view=1, i=0, mediaUrl, resultUrl, creditUrl, cached={};
let fiche={},demo=false,prend={},ok={},pending=null,completed=null,busy=false,last=null,rev=0,canKeep=false;
let voiceFile=null,voiceUrl=null,voiceRev=0,voiceStream=null,voiceRecorder=null,voiceTimer=null,voicePending=false,voiceEpoch=0;
let currentBlob=null, videoDurationOK=false;
let saveEnabled=false,draftExists=false,savingTake=false,ready=false;
const section=['fiche','prises','export'];
function problem(t){const a=$('alert');a.hidden=!t;cl(a,t||'');}
function ficheBrute(){return Object.fromEntries(new FormData(form));}
function draftRecord(){return {version:1,contractRevision:cfg.contrat.revision,raw:ficheBrute(),fiche:{...fiche},confirmations:{action:$('actionOk').checked,telephone:$('telephoneOk').checked,prix:$('prixOk').checked,cible:$('cibleOk').checked}};}
function annonceDraft(){ $('repriseOfferte').hidden=!draftExists; }
$('effacerTravail').onclick=async()=>{try{await T4Draft.clear();draftExists=false;saveEnabled=false;$('sauvegardeLocale').checked=false;annonceDraft();problem('Travail sauvegardé effacé de ce navigateur.');}catch(e){problem('Impossible d’effacer le travail sauvegardé : '+e.message);}};
$('reprendreTravail').onclick=async()=>{try{let d=await T4Draft.read(),r=d.fiche;if(!r||r.version!==1||r.contractRevision!==cfg.contrat.revision||!r.fiche||!r.raw)throw Error('Ce travail ne correspond pas à cette version.');
 setFiche(r.raw);fiche=r.fiche;for(const [k,id] of Object.entries({action:'actionOk',telephone:'telephoneOk',prix:'prixOk',cible:'cibleOk'}))$(id).checked=!!r.confirmations?.[k];
 prend={};ok={};for(const id of ids)if(d[id] instanceof Blob&&d[id].size>0&&d[id].size<=48*1024*1024){prend[id]=d[id];ok[id]=true;}
 demo=false;saveEnabled=true;setVoice(null);$('voiceFile').value='';$('subtitles').value='';$('voiceMode').value='separee';updateVoiceMode();$('piste').value='';for(const c of document.querySelectorAll('.takeVoiceChoice'))c.checked=false;$('sauvegardeLocale').checked=true;$('repriseOfferte').hidden=true;liste();let missing=ids.findIndex(id=>!ok[id]);if(missing<0)show(3);else prendre(missing);problem('Travail repris. Vérifie la fiche et ajoute à nouveau la voix séparée, les sous-titres et les choix son si nécessaire.');
 }catch(e){problem('Impossible de reprendre ce travail : '+e.message);}};

function show(n){view=n;for(let j=0;j<3;j++){ $(section[j]).hidden=j!==n-1; $("step"+(j+1)).removeAttribute('aria-current'); } $('step'+n).setAttribute('aria-current','step');problem(null);if(n!==2)reel.pause();}
async function web(path,o={}){const headers={...o.headers};if(token)headers['X-T4-Session']=token;
 if('obj' in o){headers['Content-Type']='application/json';o.body=JSON.stringify(o.obj);delete o.obj;}
 const r=await fetch(path,{...o,headers,cache:'no-store'});if(!r.ok){let e;try{e=(await r.json()).erreur;}catch{e=null;}throw Error(e?.message||'L’atelier local ne répond pas.');}return r;
}
async function req(path,o){if(path==='api/config')return (await fetch('config.json',{cache:'no-cache'})).json();if(path==='api/session')return {session:'local'};if(o?.method==='DELETE')return {};throw Error('Action indisponible.');}
function detail(a,b){const li=document.createElement('li'),id=document.createElement('span'),name=document.createElement('span');cl(id,a);cl(name,b);li.append(id,name);return li;}
function liste(){ $('slots').replaceChildren(...ids.map((s,j)=>{const take=cfg.contrat.prises[s],x=detail(String(j+1).padStart(2,'0'),take.titre+(ok[s]?' ✓':'')),duration=document.createElement('small');cl(duration,'jusqu’à '+take.secondes+' s');x.append(duration);if(ok[s])x.classList.add('kept');return x;})); }
function cible(){const ss=form.elements.action.value, target=form.elements.cible; $('cibleLabel').hidden=!ss||ss==='aucune'; if(ss==='aucune')target.value='';}
function setFiche(data){for(const [k,v] of Object.entries(data))if(form.elements.namedItem(k))form.elements[k].value=v;cible();}
function release(){currentBlob=null;videoDurationOK=false;if(mediaUrl){URL.revokeObjectURL(mediaUrl);mediaUrl=null;} reel.pause();reel.removeAttribute('src');reel.load();reel.hidden=true;}
function clearResult(){const f=$('film');f.pause();f.removeAttribute('src');f.load();$('resultat').hidden=true;
 if(resultUrl)URL.revokeObjectURL(resultUrl);if(creditUrl)URL.revokeObjectURL(creditUrl);resultUrl=creditUrl=null;}
function openRep(blob,stamp){if(stamp!==rev)return;release();currentBlob=blob;mediaUrl=URL.createObjectURL(blob);reel.src=mediaUrl;reel.hidden=false;reel.load();}
function prendre(j){i=j;const s=ids[i],t=cfg.contrat.prises[s],stamp=++rev;show(2);release();canKeep=false;$('garder').disabled=true;$('fichier').value='';$('fichierLabel').hidden=demo||cfg.demo;
 $('exempleSeulement').hidden=!demo;cl($('scene'),`${s} · PRISE ${i+1} SUR 4`);cl($('priseTitre'),t.titre);
 cl($('guide'),t.guide+`  ·  de ${t.secondes_min} à ${t.secondes} secondes`+(i===1&&fiche.geste?` · Pour : ${fiche.geste}`:''));cl($('question'),t.question);cl($('meta'),ok[s]?'Relis ou remplace cette prise.':demo?'Lance la relecture puis garde la prise.':'Choisis le fichier, puis regarde la prise avant de la garder.');
 if(demo){(async()=>{try{cached[s]??=await (await web('exemple/'+s+'.mp4')).blob();openRep(cached[s],stamp);}catch(e){if(stamp===rev)problem(e.message);}})();}
 else if(prend[s])openRep(prend[s],stamp);
}
function majChoix(){/* choix explicite toujours autorisé ; rotation seule évite la répétition */}
function boutons(){for(const b of ['rendre','muet','retourPrises','example','piste','voiceFile','recordVoice'])$(b).disabled=busy||voicePending||!!voiceRecorder;$('clearVoice').disabled=busy||voicePending||!!voiceRecorder||!voiceFile;}
function setprogress(d){const textes={controle:'Vérification de la fiche et des prises',prises:'Préparation des quatre prises',image:'Montage de l’image',musique:'Ajout de la musique choisie',verification:'Contrôle du MP4 et des crédits'};
 $('progressBox').hidden=false;cl($('phase'),(textes[d.phase]||'Préparation du rendu')+` · ${d.avancement||0} %`);$('progress').value=d.avancement||0;}
async function decodeAudio(file, ctx){try{return await ctx.decodeAudioData(await file.arrayBuffer());}catch{throw Error('Fichier audio illisible sur ce navigateur. Essaie un autre format.');}}
async function audioMix(track,voice,frames,takeFiles,sceneFrames){
 const C=window.AudioContext||window.webkitAudioContext;if(!C)throw Error('Audio indisponible sur ce navigateur.');const ctx=new C({sampleRate:48000});try{
 const resp=await fetch('audio/'+track+'.flac');if(!resp.ok)throw Error('Musique indisponible.');let bed=await decodeAudio(await resp.blob(),ctx),v=voice?await decodeAudio(voice,ctx):null;
 const duration=frames/cfg.contrat.media.fps;
 if(takeFiles){
  if(!takeFiles.length)throw Error('Choisis au moins une prise dont tu veux garder le son.');
  const MB=await import('./vendor/mediabunny-1.66.1.min.mjs');const sr=ctx.sampleRate;v=ctx.createBuffer(2,frames*1600,sr);let sums=[0],carryUntil=0;for(const k of sceneFrames)sums.push(sums.at(-1)+k);
  for(const {id,file} of takeFiles){const idx=ids.indexOf(id);let input=new MB.Input({source:new MB.BlobSource(file),formats:[MB.MP4,MB.QTFF,MB.WEBM]}),videoStart,audioStart,audioEnd;
   try{let video=await input.getPrimaryVideoTrack(),source=await input.getPrimaryAudioTrack();if(!video||!source||!await source.canDecode())throw Error();videoStart=await video.getFirstTimestamp();audioStart=await source.getFirstTimestamp();audioEnd=await source.computeDuration();}catch{throw Error('Le son de la prise '+(idx+1)+' est absent ou illisible. Décoche cette prise ou importe une vidéo avec du son.');}finally{input.dispose()}
   if(audioEnd-videoStart>sceneFrames[idx]/30+.5)throw Error('Le son de la prise '+(idx+1)+' dépasse son image. Raccourcis ou remplace cette prise pour ne pas perdre la fin du son.');
   let a;try{a=await ctx.decodeAudioData(await file.arrayBuffer());}catch{throw Error('Le son de la prise '+(idx+1)+' est absent ou illisible. Décoche cette prise ou importe une vidéo avec du son.');}
   const effectiveStart=Math.max(audioStart,audioEnd-a.duration),offset=Math.round((effectiveStart-videoStart)*sr),sourceStart=Math.max(0,-offset),destWithin=Math.max(0,offset);
   // Ne conserver que les échantillons réellement présentés (hors bourrage du codec).
   const presented=Math.max(0,Math.min(a.length,Math.round((audioEnd-effectiveStart)*sr)));
   const destination=sums[idx]*1600+destWithin;
   if(sourceStart>=presented||destWithin>=sceneFrames[idx]*1600)throw Error('Le son de la prise '+(idx+1)+' ne commence pas pendant l’image.');
   const hasSignal=(from,to)=>{for(let ch=0;ch<a.numberOfChannels;ch++){const q=a.getChannelData(ch);for(let j=from;j<to;j++)if(Math.abs(q[j])>1e-7)return true;}return false;};
   if(sourceStart&&hasSignal(0,sourceStart))throw Error('Le son de la prise '+(idx+1)+' commence avant l’image. Remplace la prise pour ne perdre aucun son.');
   const fullCount=Math.min(presented-sourceStart,v.length-destination);
   if(fullCount<=0)throw Error('Le son de la prise '+(idx+1)+' ne commence pas pendant l’image.');
   if(sourceStart+fullCount<presented&&hasSignal(sourceStart+fullCount,presented))throw Error('Le son de la prise '+(idx+1)+' dépasse la fin du film. Remplace la prise pour ne pas perdre sa fin.');
   // Le son continue à 1x même si une image est arrondie à la frontière de scène.
   // Si deux sons se chevauchent réellement, refuser au lieu d'écraser le premier.
   const overlap=Math.min(fullCount,Math.max(0,carryUntil-destination));
   if(overlap){let conflicting=false;for(let ch=0;ch<2&&!conflicting;ch++){const dest=v.getChannelData(ch),src=a.getChannelData(Math.min(ch,a.numberOfChannels-1));for(let j=0;j<overlap;j++){if(Math.abs(dest[destination+j])>1e-7&&Math.abs(src[sourceStart+j])>1e-7){conflicting=true;break;}}}if(conflicting)throw Error('Les sons des prises '+idx+' et '+(idx+1)+' se chevauchent. Refais ou remplace une prise pour conserver les deux sons.');}
   const lastWindow=Math.round(cfg.contrat.duree_regles.silence_fin_ms*sr/1000),windowInScene=Math.max(destWithin,sceneFrames[idx]*1600-lastWindow),first=sourceStart+Math.max(0,windowInScene-destWithin),last=Math.min(presented,sourceStart+Math.max(0,sceneFrames[idx]*1600-destWithin));let endEnergy=0,endCount=0;
   for(let ch=0;ch<a.numberOfChannels;ch++){let samples=a.getChannelData(ch);for(let j=first;j<last;j++){endEnergy+=samples[j]*samples[j];endCount++;}}
   if(endCount&&Math.sqrt(endEnergy/endCount)>cfg.contrat.duree_regles.seuil_rms)throw Error('On entend encore du son à la fin de la prise '+(idx+1)+'. Refais ou remplace la vidéo : termine ta phrase, puis attends un instant avant d’arrêter. Un bruit peut aussi déclencher ce contrôle.');
   for(let ch=0;ch<2;ch++){const dest=v.getChannelData(ch),src=a.getChannelData(Math.min(ch,a.numberOfChannels-1));for(let j=0;j<fullCount;j++)dest[destination+j]+=src[sourceStart+j];}
   carryUntil=Math.max(carryUntil,destination+fullCount);
  }
 }
 if(v&&!takeFiles&&(v.duration<.3||v.duration>duration))throw Error('Ta voix est plus longue que le film ('+duration.toFixed(1)+' s) ou trop courte. Raccourcis la voix ou refais des prises plus longues.');
 if(v&&!takeFiles){let sum=0,count=0,window=Math.round(cfg.contrat.duree_regles.silence_fin_ms*v.sampleRate/1000),first=Math.max(0,v.length-window);for(let c=0;c<v.numberOfChannels;c++){let z=v.getChannelData(c);for(let i=first;i<z.length;i++){sum+=z[i]*z[i];count++}}if(count&&Math.sqrt(sum/count)>cfg.contrat.duree_regles.seuil_rms)throw Error('On entend encore du son à la fin de ta voix. Refais ou remplace la voix : termine ta phrase, puis attends un instant avant d’arrêter. Un bruit peut aussi déclencher ce contrôle.');}
 const sr=48000,n=frames*1600,left=new Float32Array(n),right=new Float32Array(n);let rms=0,vg=1;
 if(v){let energy=0,count=0,step=Math.round(sr*.4);for(let i=0;i<v.length;i+=step){let sum=0,end=Math.min(v.length,i+step);for(let c=0;c<v.numberOfChannels;c++){let samples=v.getChannelData(c);for(let j=i;j<end;j++)sum+=samples[j]*samples[j];}let k=(end-i)*v.numberOfChannels;if(sum/k>1e-5){energy+=sum;count+=k;}}rms=Math.sqrt(energy/Math.max(1,count));if(!Number.isFinite(rms)||rms<.0001)throw Error('La voix est silencieuse ou trop faible.');vg=Math.min(5,Math.pow(10,-20.5/20)/rms);}
 const bl=bed.getChannelData(0),br=bed.getChannelData(Math.min(1,bed.numberOfChannels-1)),vl=v?.getChannelData(0),vr=v?.getChannelData(Math.min(1,v.numberOfChannels-1));
 let env=0,attack=Math.exp(-1/(sr*.04)),release=Math.exp(-1/(sr*.6));for(let i=0;i<n;i++){
  let a=vl&&i<vl.length?vl[i]*vg:0,b=vr&&i<vr.length?vr[i]*vg:0,det=Math.max(Math.abs(a),Math.abs(b)),coef=det>env?attack:release;env=coef*env+(1-coef)*det;
  let duck=v?Math.max(.22,Math.min(1,Math.pow(.03/Math.max(.03,env),.70))):1,base=v?.707:1;// The packaged music is 30 s. Crossfade into a 9 s interior excerpt at 25–27 s, then fade at the end.
  const t=i/sr, loopIndex=i-22*sr;let ml=bl[i]||0,mr=br[i]||0;
  if(t>=25){const q=Math.min(1,(t-25)/2),j=Math.max(0,Math.min(bl.length-1,loopIndex));ml=ml*(1-q)+(bl[j]||0)*q;mr=mr*(1-q)+(br[j]||0)*q;}
  const finish=Math.min(1,Math.max(0,(duration-t)/1.5));let x=ml*finish*base*duck+a,y=mr*finish*base*duck+b;
  // Conservative peak guard, no automatic gain. Voice and music stay in this browser.
  left[i]=Math.max(-.55,Math.min(.55,x));right[i]=Math.max(-.55,Math.min(.55,y));
 }return {left,right};}finally{await ctx.close()}}
function parseSubs(raw,duration){if(!raw.trim())return [];let last=0;return raw.trim().split(/\n/).map((line,i)=>{let m=line.match(/^\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*\|\s*(.{1,100})\s*$/);if(!m)throw Error('Sous-titre ligne '+(i+1)+' : utilise début-fin | texte.');let start=Number(m[1].replace(',','.')),end=Number(m[2].replace(',','.'));if(start<last||end<=start||end>duration)throw Error('Vérifie les sous-titres : ils doivent finir avant la fin du film ('+duration.toFixed(1)+' s), sans chevauchement.');last=end;return {start,end,text:m[3].trim()};});}
async function lancer(mode){if(busy)return;busy=true;boutons();problem(null);clearResult();$('progressBox').hidden=false;cl($('phase'),'Préparation du montage dans ton navigateur…');$('progress').value=0;
 try{const selected=$('piste').value||cfg.catalogue.map(x=>x.id).find(x=>x!==last),track=cfg.catalogue.find(t=>t.id===selected);if(mode!=='muet'&&!track)throw Error('Choisis une musique.');
 const files={};for(const id of ids){if(demo){let r=await fetch('exemple/'+id+'.mp4');if(!r.ok)throw Error('Mire indisponible.');files[id]=await r.blob()}else files[id]=prend[id];if(!files[id])throw Error('Garde les quatre prises avant le montage.');}
 const {Input,BlobSource,MP4,QTFF,WEBM}=await import('./vendor/mediabunny-1.66.1.min.mjs');const frames=[];for(let j=0;j<4;j++){let m=new Input({source:new BlobSource(files[ids[j]]),formats:[MP4,QTFF,WEBM]});try{let v=await m.getPrimaryVideoTrack();if(!v||!await v.canDecode())throw Error('Prise illisible.');let len=(await v.computeDuration())-(await v.getFirstTimestamp()),max=cfg.contrat.prises[ids[j]].secondes;if(len<cfg.contrat.prises[ids[j]].secondes_min||len>max+cfg.contrat.duree_regles.maximum_images_supplementaires/cfg.contrat.media.fps+.00001)throw Error('Durée de la prise '+(j+1)+' invalide.');frames.push(Math.min(max*cfg.contrat.media.fps,Math.floor(len*cfg.contrat.media.fps+0.00001)));}finally{m.dispose()}}const total=frames.reduce((a,b)=>a+b,0),duration=total/cfg.contrat.media.fps;
 const subtitles=parseSubs($('subtitles').value,duration);let voice=null,takeFiles=null;if(mode!=='muet'&&!demo){if($('voiceMode').value==='separee')voice=voiceFile;else if($('voiceMode').value==='prises')takeFiles=[...document.querySelectorAll('.takeVoiceChoice:checked')].map(e=>({id:e.value,file:files[e.value]}));}const audio=mode==='muet'?null:await audioMix(selected,voice,total,takeFiles,frames);const worker=new Worker('render.worker.mjs?v=t4-publication-continuite-1',{type:'module'});
 const buffer=await new Promise((resolve,reject)=>{worker.onerror=e=>{worker.terminate();reject(Error(e.message||'Le moteur ne démarre pas.'));};worker.onmessage=e=>{let d=e.data;if(d.stage==='encode'){cl($('phase'),`Montage dans ton navigateur · ${Math.round(100*d.completed/d.total)} %`);$('progress').value=100*d.completed/d.total;}else if(d.stage==='done'){worker.terminate();resolve(d.buffer);}else if(d.stage==='error'){worker.terminate();reject(Error(d.message));}};worker.postMessage({files,frames,contrat:cfg.contrat,fiche,audio,subtitles,credit:track?.credit||''});});
 // Contrôle final du fichier : vérifier les pistes ET les métadonnées du conteneur,
 // car l'encodage AAC peut ajouter quelques millisecondes au-delà de la vidéo.
 const outputBlob=new Blob([buffer],{type:'video/mp4'}),check=new Input({source:new BlobSource(outputBlob),formats:[MP4]});
 try{const tracks=await check.getTracks(),ends=await Promise.all(tracks.map(t=>t.computeDuration())),meta=await check.getDurationFromMetadata(),max=Math.max(meta||0,...ends);if(!Number.isFinite(max)||max<=0||max>30.000001)throw Error('Le fichier dépasse 30 secondes après encodage. Raccourcis une prise sans couper une phrase, puis réessaie.');}finally{check.dispose();}
 resultUrl=URL.createObjectURL(outputBlob);$('dl').href=resultUrl;$('film').src=resultUrl;cl($('titreResultat'),mode==='muet'?`Contrôle muet · ${duration.toFixed(1)} secondes`:`${track.id} · ${track.titre}`);$('dlCredit').hidden=mode==='muet';cl($('credit'),mode==='muet'?'Montage sans piste audio.':track.credit);if(mode!=='muet'){creditUrl=URL.createObjectURL(new Blob([track.credit+'\n'],{type:'text/plain;charset=utf-8'}));$('dlCredit').href=creditUrl;last=selected;majChoix();} $('progressBox').hidden=true;$('resultat').hidden=false;
 }catch(e){$('progressBox').hidden=true;problem(e.message);}finally{busy=false;boutons();}
}
$('example').onclick=()=>{if(busy)return;saveEnabled=false;$('sauvegardeLocale').checked=false;setFiche(cfg.exemple);demo=true;prend={};ok={};$('actionOk').checked=true;$('demoNotice').hidden=false;$('real').hidden=false;liste();clearResult();show(1);cl($('example'),'Exemple chargé');};
$('real').onclick=()=>{demo=false;prend={};ok={};$('demoNotice').hidden=true;$('real').hidden=true;liste();clearResult();};
form.addEventListener('change',cible);
form.onsubmit=async e=>{e.preventDefault();if(!cfg||!ready)return;
 if(cfg.demo&&!demo){problem('Sur cet aperçu, clique sur « Charger l’exemple » pour utiliser les prises de démonstration.');return;}
 fiche=cfg.demo?{...cfg.exemple}:Object.fromEntries(new FormData(form));for(const k of Object.keys(fiche))fiche[k]=fiche[k].trim();
 if(fiche.action!=='aucune'&&!$('actionOk').checked){problem('Confirme que l’action choisie est réellement possible.');return;}
 if(fiche.telephone&&!$('telephoneOk').checked){problem('Autorise l’affichage du numéro ou laisse le champ vide.');return;}
 if(fiche.cible&&!$('cibleOk').checked){problem('Autorise explicitement la diffusion du moyen de contact ou laisse le champ vide.');return;}
 if(fiche.prix){if(!/^\d+(?:[.,]\d{1,2})?$/.test(fiche.prix)||!fiche.devise||!fiche.type_prix||!$('prixOk').checked){problem('Pour afficher un prix, indique un montant valide, la monnaie, le type et confirme-le.');return;}fiche.prix=(fiche.type_prix==='depart'?'À partir de ':'')+fiche.prix+' '+fiche.devise;}
 if(!demo&&$('sauvegardeLocale').checked){try{if(draftExists&&!saveEnabled){problem('Un travail est déjà sauvegardé. Reprends-le ou efface-le avant d’en sauvegarder un nouveau.');return;}if(saveEnabled)await T4Draft.updateFiche(draftRecord());else{await T4Draft.create(draftRecord());draftExists=true;saveEnabled=true;}annonceDraft();}catch(err){problem('Sauvegarde impossible sur cet appareil : '+err.message+' Décoche l’option pour continuer sans reprise.');return;}}else saveEnabled=false;
 $('repriseOfferte').hidden=true;prendre(0);
};
$('fichier').onchange=()=>{const f=$('fichier').files[0], s=ids[i];if(!f)return;
 if(f.size===0||f.size>48*1024*1024){problem('Prise absente ou trop lourde (48 Mio par vidéo).');return;}
 prend[s]=f;delete ok[s];liste();problem(null);canKeep=false;$('garder').disabled=true;openRep(f,++rev);
};
reel.onloadedmetadata=async()=>{const stamp=rev,need=cfg.contrat.prises[ids[i]].secondes,blob=currentBlob;videoDurationOK=false;canKeep=false;$('garder').disabled=true;cl($('meta'),'Vérification de la vidéo…');let input;
 try{const {Input,BlobSource,MP4,QTFF,WEBM}=await import('./vendor/mediabunny-1.66.1.min.mjs');input=new Input({source:new BlobSource(blob),formats:[MP4,QTFF,WEBM]});const v=await input.getPrimaryVideoTrack();if(!v||!await v.canDecode())throw Error('Cette vidéo ne peut pas être lue.');let start=await v.getFirstTimestamp(),end=await v.computeDuration();if(stamp!==rev)return;let len=end-start;videoDurationOK=(len>=cfg.contrat.prises[ids[i]].secondes_min&&len<=need+cfg.contrat.duree_regles.maximum_images_supplementaires/cfg.contrat.media.fps+.00001);cl($('meta'),videoDurationOK?`${len.toFixed(1).replace('.',',')} s d’image · ${len>need?`Les ${need} premières secondes seront utilisées.`:'La durée de la prise sera utilisée.'} Lance la lecture pour confirmer.`:len<cfg.contrat.prises[ids[i]].secondes_min?'Cette vidéo est trop courte : filme au moins 2 secondes.':`Cette vidéo est trop longue : raccourcis-la à ${String(need).replace('.',',')} secondes sans couper une phrase, ou filme de nouveau.`);if(videoDurationOK&&reel.currentTime>.10){canKeep=true;$('garder').disabled=false;}}
 catch(e){if(stamp===rev){videoDurationOK=false;problem('Impossible de vérifier cette vidéo. Essaie un autre fichier.');}}finally{input?.dispose()}};
reel.ontimeupdate=()=>{if(view!==2||reel.hidden)return;if(reel.currentTime>.10&&videoDurationOK){canKeep=true;$('garder').disabled=false;}};
reel.onerror=()=>{if(view===2&&!reel.hidden){problem('Ce navigateur ne relit pas le fichier. Essaie un MP4 H.264 lisible.');$('garder').disabled=true;canKeep=false;}};
$('garder').onclick=async()=>{if(!canKeep||busy||savingTake)return;savingTake=true;try{if(saveEnabled&&!demo)await T4Draft.saveTake(ids[i],prend[ids[i]]);}catch(e){problem('La prise n’a pas pu être sauvegardée sur cet appareil. Libère de l’espace ou reviens à la fiche pour continuer sans sauvegarde.');return;}finally{savingTake=false;}ok[ids[i]]=true;liste();
 if(i<3){prendre(i+1);return;}release();if(ids.every(s=>ok[s])){show(3);majChoix();}
};
function fermerCapture(){$('captureFrame').removeAttribute('src');$('captureBox').hidden=true;$('captureIntro').hidden=false;$('importFlow').hidden=false;}
$('captureFrame').addEventListener('load',()=>{if($('captureFrame').getAttribute('src'))$('captureFrame').contentWindow.postMessage({type:'vv-t4-fiche',fiche,persist:saveEnabled&&!demo,files:ids.map(id=>ok[id]?prend[id]:null)},location.origin);});
$('captureStart').onclick=()=>{release();$('captureIntro').hidden=true;$('importFlow').hidden=true;$('captureBox').hidden=false;$('captureFrame').src='capture.html?v=t4-publication-continuite-1'+(demo?'&demo=1':'');};
$('captureClose').onclick=()=>{fermerCapture();let next=ids.findIndex(id=>!ok[id]);prendre(next<0?0:next);};
window.addEventListener('message',e=>{let d=e.data;if(e.origin!==location.origin||e.source!==$('captureFrame').contentWindow||d?.type!=='vv-t4-accepted'||demo||!ids.includes(d.id)||!(d.file instanceof Blob)||d.file.size===0||d.file.size>48*1024*1024)return;prend[d.id]=d.file;ok[d.id]=true;liste();});
window.addEventListener('message',e=>{const d=e.data;if(e.origin!==location.origin||e.source!==$('captureFrame').contentWindow||d?.type!=='vv-t4-captures'||!Array.isArray(d.files)||d.files.length!==4||d.demo!==demo||!d.files.every(x=>x instanceof Blob&&x.size>0&&x.size<=48*1024*1024))return;
 if(!demo)prend=Object.fromEntries(ids.map((s,j)=>[s,d.files[j]]));ok=Object.fromEntries(ids.map(s=>[s,true]));liste();fermerCapture();show(3);majChoix();});
$('retourFiche').onclick=()=>{fermerCapture();release();show(1);annonceDraft();};
$('retourPrises').onclick=async()=>{if(busy)return;try{if(pending)await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;clearResult();prendre(0);}catch(e){problem(e.message);}};
$('muet').onclick=()=>lancer('muet');$('rendre').onclick=()=>lancer('musique_seule');
function updateVoiceMode(){$('takeVoice').hidden=$('voiceMode').value!=='prises';$('separateVoice').hidden=$('voiceMode').value!=='separee';}
$('voiceMode').onchange=updateVoiceMode;updateVoiceMode();
function setVoice(file){
 if(voiceUrl)URL.revokeObjectURL(voiceUrl);voiceUrl=null;voiceFile=null;voiceRev++;
 const p=$('voicePreview');p.pause();p.removeAttribute('src');p.load();p.hidden=true;
 if(file){
  if(!file.size||file.size>20*1024*1024){cl($('voiceStatus'),'Fichier absent ou trop lourd : maximum 20 Mio.');boutons();return;}
  voiceFile=file;voiceUrl=URL.createObjectURL(file);p.src=voiceUrl;p.hidden=false;p.load();cl($('voiceStatus'),'Voix prête : écoute-la avant de créer ton MP4. Le montage vérifie sa durée.');
 }else cl($('voiceStatus'),'Aucune voix ajoutée.');boutons();
}
$('voiceFile').onchange=()=>{const f=$('voiceFile').files[0];if(f)setVoice(f);};
$('clearVoice').onclick=async()=>{if(busy||voicePending||voiceRecorder)return;try{if(pending){await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;}$('voiceFile').value='';setVoice(null);}catch(e){problem(e.message);}};
$('recordVoice').onclick=async()=>{
 if(busy||voicePending||voiceRecorder)return;voicePending=true;const epoch=++voiceEpoch;boutons();problem(null);
 try{
  if(!navigator.mediaDevices?.getUserMedia||typeof MediaRecorder==='undefined')throw Error('Le micro n’est pas disponible ici. Utilise HTTPS ou importe un fichier.');
  const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
  if(epoch!==voiceEpoch){stream.getTracks().forEach(t=>t.stop());return;}voiceStream=stream;
  let autoStopped=false;const chunks=[],rec=new MediaRecorder(voiceStream);voiceRecorder=rec;
  rec.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
  rec.onerror=()=>{cl($('voiceStatus'),'L’enregistrement a échoué. Réessaie ou importe une voix.');};
  rec.onstop=()=>{
   clearTimeout(voiceTimer);voiceStream?.getTracks().forEach(t=>t.stop());voiceStream=null;voiceRecorder=null;$('stopVoice').disabled=true;
   const blob=new Blob(chunks,{type:rec.mimeType||'audio/webm'});if(autoStopped){setVoice(null);cl($('voiceStatus'),'Limite atteinte : la fin peut être coupée. Enregistre de nouveau et arrête un peu plus tôt.');}else if(blob.size)setVoice(blob);else{cl($('voiceStatus'),'Aucun son enregistré.');boutons();}
  };
  rec.start();$('stopVoice').disabled=false;boutons();cl($('voiceStatus'),'Enregistrement en cours · 29,9 secondes maximum.');voiceTimer=setTimeout(()=>{if(rec.state==='recording'){autoStopped=true;rec.stop();}},cfg.contrat.media.secondes_max*1000);
 }catch(e){voiceStream?.getTracks().forEach(t=>t.stop());voiceStream=null;voiceRecorder=null;cl($('voiceStatus'),e.name==='NotAllowedError'?'Accès au micro refusé. Tu peux importer une voix.':e.message);}
 finally{voicePending=false;boutons();}
};
$('stopVoice').onclick=()=>{if(voiceRecorder?.state==='recording')voiceRecorder.stop();};
window.addEventListener('pagehide',()=>{voiceEpoch++;clearTimeout(voiceTimer);if(voiceRecorder?.state==='recording')voiceRecorder.stop();voiceStream?.getTracks().forEach(t=>t.stop());if(voiceUrl)URL.revokeObjectURL(voiceUrl);});
(async()=>{try{
 cfg=await req('api/config');const [q,g]=await Promise.all([fetch('formulaire/questions.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Questions T4 indisponibles.');return r.json();}),fetch('capture/guide.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Guide T4 indisponible.');return r.json();})]);T4Contrats.questions(q,cfg.contrat);T4Contrats.guide(g);for(const item of q.questions){const el=form.elements.namedItem(item.id),label=el?.closest('label');if(!label||label.firstChild.nodeType!==Node.TEXT_NODE)throw Error('Formulaire T4 invalide.');label.firstChild.nodeValue=item.libelle+' ';}const c=cfg.contrat, fps=c?.media?.fps, mins=ids.reduce((n,id)=>n+(c.prises[id]?.secondes_min||0),0), maxs=ids.reduce((n,id)=>n+(c.prises[id]?.secondes||0),0);if(c.schema!==2||fps!==30||c.media.largeur!==720||c.media.hauteur!==1280||c.media.duree_mode!=='variable'||c.media.secondes_min!==mins||c.media.secondes_max!==maxs||c.media.secondes!==maxs||c.media.images_min!==mins*fps||c.media.images_max!==maxs*fps||c.media.images!==maxs*fps||c.duree_regles?.fps_sortie!==fps||c.duree_regles?.maximum_images_supplementaires!==1||c.duree_regles?.fin_fichier_maximum_coupee_images!==1||c.duree_regles?.arrondi_frames!=='inferieur'||c.duree_regles?.duree_sortie!=='somme_frames_des_prises'||c.duree_regles?.controle_fin_son!=='niveau_sonore_sans_reconnaissance_des_paroles'||c.duree_regles?.silence_fin_ms!==250||c.duree_regles?.seuil_rms!==0.002||c.duree_regles?.controle_fin_prises_selectionnees!==true||c.duree_regles?.controle_fin_voix_separee!==true||ids.some(id=>c.prises[id].secondes_min!==2))throw Error('Le contrat de durée ne correspond pas au moteur.');$('voicePanel').hidden=cfg.demo;if(cfg.demo){for(const el of form.querySelectorAll('input,select'))el.disabled=true;}const s=await req('api/session',{method:'POST',obj:{}});token=s.session;
 for(const [k,v] of Object.entries(cfg.contrat.fiche.action.choix))form.elements.action.add(new Option(v||'Ne rien ajouter',k));form.elements.action.value='aucune';
 for(const x of cfg.catalogue){const li=detail(x.id,x.titre);const sm=document.createElement('small');cl(sm,x.artiste);li.lastElementChild.append(sm);$('tracks').append(li);$('piste').add(new Option(x.id+' · '+x.titre,x.id));}
 liste();try{draftExists=await T4Draft.exists();annonceDraft();}catch(e){draftExists=false;} ready=true;$('example').disabled=false;$('continuer').disabled=false;
 }catch(e){problem(e.message);}})();
})();
