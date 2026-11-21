/* T3 – tout appel passe par le même atelier local. Pas de réseau tiers. */
(()=>{'use strict';
const $=id=>document.getElementById(id), cl=(n,t)=>{n.textContent=t;}, ids=['S1','S2','S3','S4'];
const form=$('fiche'), reel=$('relecture');let cfg, token, view=1, i=0, mediaUrl, resultUrl, creditUrl, cached={};
let fiche={},demo=false,prend={},ok={},pending=null,completed=null,busy=false,last=null,rev=0,canKeep=false;
const section=['fiche','prises','export'];
function problem(t){const a=$('alert');a.hidden=!t;cl(a,t||'');}
function show(n){view=n;for(let j=0;j<3;j++){ $(section[j]).hidden=j!==n-1; $("step"+(j+1)).removeAttribute('aria-current'); } $('step'+n).setAttribute('aria-current','step');problem(null);if(n!==2)reel.pause();}
async function web(path,o={}){const headers={...o.headers};if(token)headers['X-T3-Session']=token;
 if('obj' in o){headers['Content-Type']='application/json';o.body=JSON.stringify(o.obj);delete o.obj;}
 const r=await fetch(path,{...o,headers,cache:'no-store'});if(!r.ok){let e;try{e=(await r.json()).erreur;}catch{e=null;}throw Error(e?.message||'L’atelier local ne répond pas.');}return r;
}
async function req(path,o){return (await web(path,o)).json();}
function detail(a,b){const li=document.createElement('li'),id=document.createElement('span'),name=document.createElement('span');cl(id,a);cl(name,b);li.append(id,name);return li;}
function liste(){ $('slots').replaceChildren(...ids.map((s,j)=>{const x=detail(s,cfg.contrat.prises[s].titre+(ok[s]?' ✓':''));if(ok[s])x.classList.add('kept');return x;})); }
function cible(){const ss=form.elements.action.value, target=form.elements.cible; $('cibleLabel').hidden=!ss||ss==='aucune'; if(ss==='aucune')target.value='';}
function setFiche(data){for(const [k,v] of Object.entries(data))if(form.elements.namedItem(k))form.elements[k].value=v;cible();}
function release(){if(mediaUrl){URL.revokeObjectURL(mediaUrl);mediaUrl=null;} reel.pause();reel.removeAttribute('src');reel.load();reel.hidden=true;}
function clearResult(){const f=$('film');f.pause();f.removeAttribute('src');f.load();$('resultat').hidden=true;
 if(resultUrl)URL.revokeObjectURL(resultUrl);if(creditUrl)URL.revokeObjectURL(creditUrl);resultUrl=creditUrl=null;}
function openRep(blob,stamp){if(stamp!==rev)return;release();mediaUrl=URL.createObjectURL(blob);reel.src=mediaUrl;reel.hidden=false;reel.load();}
function prendre(j){i=j;const s=ids[i],t=cfg.contrat.prises[s],stamp=++rev;show(2);release();canKeep=false;$('garder').disabled=true;$('fichier').value='';$('fichierLabel').hidden=demo||cfg.demo;
 $('exempleSeulement').hidden=!cfg.demo;cl($('scene'),`${s} · PRISE ${i+1} SUR 4`);cl($('priseTitre'),t.titre);
 cl($('guide'),t.guide+`  ·  ${t.secondes} secondes minimum`);cl($('question'),t.question);cl($('meta'),ok[s]?'Relis ou remplace cette prise.':demo?'Lance la relecture puis garde la prise.':'Choisis le fichier, puis regarde la prise avant de la garder.');
 if(demo){(async()=>{try{cached[s]??=await (await web('exemple/'+s+'.mp4')).blob();openRep(cached[s],stamp);}catch(e){if(stamp===rev)problem(e.message);}})();}
 else if(prend[s])openRep(prend[s],stamp);
}
function majChoix(){for(const o of $('piste').options)o.disabled=!!last&&o.value===last;if($('piste').value===last)$('piste').value='';}
function boutons(){for(const b of ['rendre','muet','retourPrises','example','piste'])$(b).disabled=busy;}
function setprogress(d){const textes={controle:'Vérification de la fiche et des prises',prises:'Préparation des quatre prises',image:'Montage de l’image',musique:'Ajout de la musique choisie',verification:'Contrôle du MP4 et des crédits'};
 $('progressBox').hidden=false;cl($('phase'),(textes[d.phase]||'Préparation du rendu')+` · ${d.avancement||0} %`);$('progress').value=d.avancement||0;}
async function result(d){const r=d.resultat,m=r.musique,url='api/jobs/'+r.job_id;resultUrl=URL.createObjectURL(await (await web(url+'/film.mp4')).blob());
 $('dl').href=resultUrl;$('film').src=resultUrl;cl($('titreResultat'),m?`${m.piste} · ${m.titre}`:'Contrôle muet · 30 secondes');
 $('dlCredit').hidden=!m;cl($('credit'),m?m.credit:'Fiche et quatre prises → image H.264, sans piste audio.');
 if(m){creditUrl=URL.createObjectURL(await (await web(url+'/credit.txt')).blob());$('dlCredit').href=creditUrl;last=m.piste;majChoix();}
 completed=r.job_id;pending=null;$('progressBox').hidden=true;$('resultat').hidden=false;
}
async function lancer(mode){if(busy)return;busy=true;boutons();problem(null);clearResult();
 const body={fiche,mode,piste:mode==='muet'?null:$('piste').value||null,exemple:demo},key=JSON.stringify(body);
 try{
  if(completed){await req('api/jobs/'+completed,{method:'DELETE'});completed=null;}
  if(pending&&pending.key!==key){await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;}
  if(!pending){let q=await req('api/jobs',{method:'POST',obj:body});pending={job:q.job,key,uploads:demo};}
  const endpoint='api/jobs/'+pending.job;
  if(!pending.uploads){for(const s of ids){setprogress({phase:'prises',avancement:0});await req(endpoint+'/'+s,{method:'PUT',headers:{'Content-Type':'application/octet-stream'},body:prend[s]});}pending.uploads=true;}
  await req(endpoint+'/rendre',{method:'POST',obj:{}});
  for(let attempts=0;attempts<220;attempts++){
   const d=await req(endpoint); if(d.phase==='termine'){await result(d);return;}
   if(d.phase==='echec')throw Error(d.erreur?.message||'Le rendu a échoué.');
   setprogress(d);await new Promise(r=>setTimeout(r,700));
  }throw Error('Le rendu prend trop de temps. Relance l’atelier si nécessaire.');
 }catch(e){$('progressBox').hidden=true;problem(e.message);}
 finally{busy=false;boutons();}
}
$('example').onclick=()=>{if(busy)return;setFiche(cfg.exemple);demo=true;prend={};ok={};liste();clearResult();show(1);cl($('example'),'Exemple chargé');};
form.addEventListener('change',cible);
form.onsubmit=e=>{e.preventDefault();if(!cfg)return;
 if(cfg.demo&&!demo){problem('Sur cet aperçu, clique sur « Charger l’exemple » pour utiliser les prises de démonstration.');return;}
 fiche=Object.fromEntries(new FormData(form));for(const k of Object.keys(fiche))fiche[k]=fiche[k].trim();
 prendre(0);
};
$('fichier').onchange=()=>{const f=$('fichier').files[0], s=ids[i];if(!f)return;
 if(f.size===0||f.size>48*1024*1024){problem('Prise absente ou trop lourde (48 Mio par vidéo).');return;}
 prend[s]=f;delete ok[s];liste();problem(null);canKeep=false;$('garder').disabled=true;openRep(f,++rev);
};
reel.onloadedmetadata=()=>{const need=cfg.contrat.prises[ids[i]].secondes;cl($('meta'),`${reel.duration.toFixed(1).replace('.',',')} s · ${reel.duration+.10>=need?'Lance la lecture pour confirmer.':'Cette prise est trop courte.'}`);};
reel.ontimeupdate=()=>{if(view!==2||reel.hidden)return;if(reel.currentTime>.10&&reel.duration+.10>=cfg.contrat.prises[ids[i]].secondes){canKeep=true;$('garder').disabled=false;}};
reel.onerror=()=>{if(view===2&&!reel.hidden){problem('Ce navigateur ne relit pas le fichier. Essaie un MP4 H.264 lisible.');$('garder').disabled=true;canKeep=false;}};
$('garder').onclick=async()=>{if(!canKeep||busy)return;ok[ids[i]]=true;liste();
 if(i<3){prendre(i+1);return;}release();if(ids.every(s=>ok[s])){show(3);majChoix();}
};
$('retourFiche').onclick=()=>{release();show(1);};
$('retourPrises').onclick=async()=>{if(busy)return;try{if(pending)await req('api/jobs/'+pending.job,{method:'DELETE'});pending=null;clearResult();prendre(0);}catch(e){problem(e.message);}};
$('muet').onclick=()=>lancer('muet');$('rendre').onclick=()=>lancer('musique_seule');
(async()=>{try{
 cfg=await req('api/config');const s=await req('api/session',{method:'POST',obj:{}});token=s.session;
 for(const [k,v] of Object.entries(cfg.contrat.fiche.action.choix))form.elements.action.add(new Option(v||'Rien de particulier',k));
 for(const x of cfg.catalogue){const li=detail(x.id,x.titre);const sm=document.createElement('small');cl(sm,x.artiste);li.lastElementChild.append(sm);$('tracks').append(li);$('piste').add(new Option(x.id+' · '+x.titre,x.id));}
 liste();$('example').disabled=false;$('continuer').disabled=false;
 }catch(e){problem(e.message);}})();
})();
