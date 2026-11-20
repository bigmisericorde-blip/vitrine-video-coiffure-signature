import {loadExample,mediaURL} from './donnees.mjs';
const $=id=>document.getElementById(id);
const extract=Number(new URLSearchParams(location.search).get('ecran'));
const n=Number.isInteger(extract)&&extract>=1&&extract<=12?extract:1;
const i=Math.floor((n-1)/3), state='ABC'[(n-1)%3];
const navigate=target=>{
  if(window!==parent) parent.postMessage({type:'coiffure-demo/choose',from:n,screen:target},location.origin);
  else location.href=target===13?'ecrans.html#resultat':`prise.html?ecran=${target}`;
};
const fmt=s=>`0:${String(Math.floor(s)).padStart(2,'0')}`;
function notice(text,retry){
  $('mediaMessage').textContent=text;$('mediaFeedback').hidden=false;
  $('mediaRetry').hidden=!retry;$('mediaRetry').onclick=retry??null;
}
function list(id,values,mark) {
  $(id).replaceChildren(...values.map(value=>{
    const li=document.createElement('li'),m=document.createElement('span'),t=document.createElement('span');
    m.className='mark';m.textContent=mark;t.textContent=value;li.append(m,t);return li;
  }));
}
function guideCard(scene,clip,source){
  $('sceneCounter').textContent=`SCÈNE ${i+1}/4`;
  $('dots').replaceChildren(...source.scenes.map(({n})=>{const e=document.createElement('i');e.classList.toggle('on',n<=i+1);return e;}));
  $('durationLabel').textContent=`${clip.seconds} secondes`;
  $('sceneTitle').textContent=scene.titre;$('consigne').textContent=scene.consigne;
  $('caseContext').textContent=`Dans l’exemple : ${clip.illustration}`;
  list('listFilm',scene.a_filmer,'✓');list('listAvoid',scene.a_eviter,'✕');
  $('soundText').textContent=source.sound;$('captureConsent').textContent=source.consent;
  const cam=$('cam');cam.poster=mediaURL(clip.poster);cam.hidden=false;
  $('sheet').classList.remove('hidden');$('scrim').classList.remove('off');
  $('cta').onclick=()=>navigate(n+1);
  const body=$('sheetBody'), hint=$('scrollHint');
  // Laisser un peu de marge pour que l’apparition du bouton ne fasse pas osciller la hauteur.
  const scroll=()=>{hint.hidden=body.scrollHeight-body.clientHeight<=16||body.scrollTop+body.clientHeight>=body.scrollHeight-15;};
  hint.onclick=()=>body.scrollBy({top:Math.max(90,body.clientHeight*.76)});
  body.addEventListener('scroll',scroll,{passive:true});window.addEventListener('resize',scroll);document.fonts.ready.then(scroll);requestAnimationFrame(scroll);
}
function playCard(scene,clip){
  const recording=state==='B', video=$(recording?'cam':'replay'), btn=$('clipPlayer');
  let started=false;
  video.hidden=false;video.style.display='block';video.poster=mediaURL(clip.poster);video.preload='auto';video.muted=true;video.playsInline=true;
  const clean=()=>{$('mediaFeedback').hidden=true;};
  const sync=()=>{
    if (recording){const t=Math.min(clip.seconds,Math.max(0,video.currentTime));$('chronoVal').textContent=fmt(t);$('barFill').style.width=`${t/clip.seconds*100}%`;}
    btn.textContent=video.ended?'Relire la prise':video.paused?(recording?'Lire la prise':'Lire la relecture'):'Pause';
  };
  const start=()=>{
    if(!started||video.ended)video.currentTime=0;
    started=true;video.play().then(clean).catch(()=>{if(video.error)failed();sync();});
  };
  const retry=()=>{started=false;video.load();video.addEventListener('loadeddata',start,{once:true});};
  const failed=()=>notice('La prise n’a pas chargé. Tu peux réessayer.',retry);
  for(const e of ['playing','pause','ended','seeked','timeupdate']) video.addEventListener(e,sync);
  video.addEventListener('error',failed);video.addEventListener('loadeddata',clean);
  if(recording){$('rec').classList.add('on');$('rec').setAttribute('aria-hidden','false');}
  else {
    $('review').classList.add('on');$('reviewLabel').textContent=`PRISE ${i+1} · ${fmt(clip.seconds)}`;$('reviewQuestion').textContent=scene.question_relecture;
    if(i===3)$('next').textContent='VOIR LE MONTAGE';
    $('redo').onclick=()=>navigate(n-2);$('next').onclick=()=>{video.pause();navigate(n+1);};
  }
  btn.hidden=false;btn.onclick=()=>video.paused?start():video.pause();
  if(recording&&!matchMedia('(prefers-reduced-motion:reduce)').matches){
    // Ne pas faire défiler le chrono avant que le cadre soit visible dans la galerie.
    if('IntersectionObserver' in window){
      const observer=new IntersectionObserver(entries=>{
        if(!entries.some(e=>e.isIntersecting && e.intersectionRatio>=.45))return;
        observer.disconnect();
        if(video.readyState>=2){if(!started)start();}
        else video.addEventListener('loadeddata',()=>{if(!started)start();},{once:true});
      },{threshold:.45});
      observer.observe(video);
    } else video.addEventListener('loadeddata',()=>{if(!started)start();},{once:true});
  }
  video.src=mediaURL(clip.mp4);sync();
}
async function main(){
  const {guide,gallery}=await loadExample(),scene=guide.scenes[i],clip=gallery.clips[i];
  $('app').dataset.prise=clip.id;$('app').dataset.state=state;$('app').dataset.mediaSha=clip.sha256;
  if(window===parent){$('returnGallery').href=`ecrans.html#${n}`;$('returnGallery').hidden=false;}
  document.title=`Écran ${n}/12 · Prise ${i+1} · COIFFURE-T2`;
  if(state==='A')guideCard(scene,clip,guide);else playCard(scene,clip);
  document.documentElement.dataset.ready='yes';
}
main().catch(()=>{notice('L’exemple n’a pas chargé. Recharge cette page.',()=>location.reload());document.documentElement.dataset.ready='error';});
