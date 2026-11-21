/* Même mise en page que les états A/B/C de Signature. Lecture d’extraits ; aucun accès caméra ou micro. */
(()=>{'use strict';
const $=id=>document.getElementById(id), cfg=JSON.parse($('vv-prise-data').textContent), parts=cfg.parts, demo=cfg.demo;
// The media Blob belongs to this frame, including when the viewer sandbox gives it an opaque origin.
for(const p of parts){if(!p.b64)continue;const raw=atob(p.b64),bytes=new Uint8Array(raw.length);for(let j=0;j<bytes.length;j++)bytes[j]=raw.charCodeAt(j);p.url=URL.createObjectURL(new Blob([bytes],{type:'video/mp4'}));delete p.b64;}
const cam=$('cam'), replay=$('replay'), app=$('app'), body=$('sheetBody');
let i=(cfg.n-1)/3|0,state='A',version=0,events=new AbortController(),raf=0,ended=false,didRead=false,kept=new Set();
const punctuation=s=>s.replace(/ (?=[?!])/g,'\u202f');
const cur=()=>parts[i], fmt=x=>`0:${String(Math.max(0,Math.floor(x))).padStart(2,'0')}`, exact=x=>x.toFixed(1).replace('.',',')+' s';
function p(key,s){$(key).textContent=s;}
function listen(v,k,f,opts={}){v.addEventListener(k,f,{signal:events.signal,...opts});}
function clear(v){v.pause();v.removeAttribute('src');v.load();v.style.display='none';}
function reset(next){
 version++;events.abort();events=new AbortController();cancelAnimationFrame(raf);clear(cam);clear(replay);ended=false;didRead=false;
 state=next;app.dataset.state=next;app.dataset.prise=cur().id;app.dataset.seance='oui';app.classList.remove('media-error');
 $('sheet').classList.toggle('hidden',next!=='A');$('scrim').classList.toggle('off',next!=='A');$('rec').classList.toggle('on',next==='B');$('review').classList.toggle('on',next==='C');$('rec').setAttribute('aria-hidden',String(next!=='B'));$('mediaFeedback').hidden=true;
}
function labelList(id,lines,s){const ul=$(id);ul.replaceChildren(...lines.map(x=>{const li=document.createElement('li'), sign=document.createElement('span'), txt=document.createElement('span');sign.className='mark';sign.textContent=s;txt.textContent=x;li.append(sign,txt);return li;}));}
function scrollHint(){$('scrollHint').hidden=state!=='A'||body.scrollHeight-body.clientHeight<=11||body.scrollTop+body.clientHeight>=body.scrollHeight-13;}
function labels(){const x=cur();p('testID','T3 · SOIN DU VISAGE');p('sceneCounter',`PRISE ${i+1}/4 · ${i===3?'Fin':x.role}`);[...$('dots').children].forEach((a,j)=>a.classList.toggle('on',j<=i));
 p('durationLabel',`${x.duree_filmer_s} secondes`);p('sceneTitle',x.titre.toLocaleUpperCase('fr'));p('consigne',x.repere);labelList('listFilm',x.consignes,'✓');labelList('listAvoid',[x.a_eviter],'✕');
 p('caseContext',x.exemple);$('caseContext').hidden=false;
 p('soundText',`Cet extrait de ${exact(x.duree)} est muet. Le chrono et la relecture utilisent le même extrait du montage. Aucune caméra ni micro.`);p('captureConsent','Avant de filmer quelqu’un, demande son accord.');
 p('recContext',x.exemple);$('recContext').hidden=false;p('reviewContext',x.exemple);$('reviewContext').hidden=false;p('reviewQuestion',punctuation(x.question));
 p('reviewLabel',`PRISE ${i+1} · ${exact(x.duree)}`);p('reviewOrigin','Prise d’exemple');p('next',demo?(i===3?'GARDER ET VOIR LE FILM':'GARDER ET CONTINUER'):(i===3?'VOIR MON MONTAGE':'VALIDER ET CONTINUER'));
}
function failure(what){$('next').disabled=true;didRead=false;app.classList.add('media-error');p('mediaMessage',what);$('mediaFeedback').hidden=false;$('mediaBack').hidden=!demo;}
function use(v,loop,freeze=false){const mark=version;v.muted=true;v.loop=loop;v.style.display='block';
 listen(v,'error',()=>failure('Impossible de lire l’extrait. Aucune prise n’a été validée.'),{once:true});
 if(freeze)listen(v,'loadedmetadata',()=>{if(mark===version)v.currentTime=Math.min(cur().freeze,Math.max(0,v.duration-.09));},{once:true});
 v.src=cur().url;v.load();
 if(!freeze)v.play().catch(e=>{if(mark===version&&e.name!=='AbortError')failure('La lecture n’a pas démarré. Ouvre l’écran seul ou relance l’essai.');});
}
function guide(){reset('A');labels();$('cta').disabled=!demo;p('cta','LIRE LA PRISE D’EXEMPLE');use(cam,false,true);body.scrollTop=0;requestAnimationFrame(scrollHint);}
function progress(t){const max=cur().duree,j=Math.min(1,t/max);p('chronoVal',fmt(t));$('barFill').style.width=(100*j)+'%';$('bar').classList.toggle('hot',max-t<=2);$('chrono').classList.toggle('hot',max-t<=2);}
function chrono(){reset('B');labels();p('recordLabel',demo?'Prise d’exemple · lecture':'Aperçu du chrono');$('cancelCapture').hidden=!demo;progress(0);use(cam,!demo);const v=version;
 const tick=()=>{if(v!==version)return;progress(cam.currentTime||0);raf=requestAnimationFrame(tick);};tick();
 if(demo)listen(cam,'ended',()=>{if(v!==version)return;review();},{once:true});
}
function review(){reset('C');labels();p('reviewMode',demo?'Extrait muet · relecture':'Aperçu · aucune prise validée');$('redo').disabled=!demo;$('next').disabled=true;
 if(demo)listen(replay,'timeupdate',()=>{if(!didRead&&replay.currentTime>.12){didRead=true;$('next').disabled=false;}});use(replay,true);
}
$('cta').onclick=()=>{if(!demo||state!=='A')return;kept.delete(cur().id);chrono();};
$('redo').onclick=$('cancelCapture').onclick=$('mediaBack').onclick=()=>{if(!demo)return;kept.delete(cur().id);guide();};
$('next').onclick=()=>{if(!demo||state!=='C'||!didRead||$('next').disabled)return;kept.add(cur().id);if(i<3){i++;guide();}else if(kept.size===4){clear(replay);parent.postMessage({type:'vv-t3-film',token:cfg.token,prises:kept.size},'*');}};
$('scrollHint').onclick=()=>body.scrollBy({top:Math.max(100,body.clientHeight*.8)});body.addEventListener('scroll',scrollHint,{passive:true});window.addEventListener('resize',scrollHint);document.fonts.ready.then(scrollHint);
window.__capture=()=>({state,prise:cur().id,accepted:[...kept],demo,source:(state==='C'?replay:cam).currentSrc});
const mode=(cfg.n-1)%3; if(demo||mode===0)guide();else if(mode===1)chrono();else review();document.documentElement.dataset.ready='yes';
})();
