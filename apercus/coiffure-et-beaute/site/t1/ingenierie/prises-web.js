/* Les trois états des prises T2. Le chrono suit la vidéo, jamais l’horloge murale. */
let pictureHooks=null, pictureTimer=null;
function hidePictureNotice(){
  clearTimeout(pictureTimer);pictureTimer=null;$("mediaFeedback").hidden=true;
}
function clearPicture(){
  pictureHooks?.abort();pictureHooks=null;hidePictureNotice();
}
function showPictureNotice(message,retry){
  $("mediaMessage").textContent=message;$("mediaRetry").hidden=!retry;
  $("mediaRetry").onclick=retry||null;$("mediaBack").hidden=previewNumber!==0;
  $("mediaFeedback").hidden=false;
}
function sameSource(video,s){return video.src===new URL(s.video,document.baseURI).href;}
function watchPicture(video,s,{frozen=false,review=false,onFinish=null,retry}){
  clearPicture();const hooks=new AbortController();pictureHooks=hooks;
  const on=(name,fn)=>video.addEventListener(name,fn,{signal:hooks.signal});
  const ready=()=>{
    hidePictureNotice();
    if(review&&!previewNumber)$("next").disabled=false;
  };
  const unavailable=()=>{
    clearTimeout(pictureTimer);
    showPictureNotice("La vidéo n’a pas chargé. Réessaie ou reviens à la consigne.",retry);
  };
  const waiting=()=>{
    if(hooks.signal.aborted)return;
    clearTimeout(pictureTimer);
    showPictureNotice("La vidéo charge…",null);
    pictureTimer=setTimeout(()=>showPictureNotice("La vidéo met du temps à charger.",retry),6500);
  };
  on("error",unavailable);on("waiting",waiting);
  if(frozen){
    on("loadeddata",()=>{if(!video.seeking)ready();});on("seeked",ready);
  }else on("playing",ready);
  if(onFinish)on("ended",onFinish);
  if(review&&personal){
    const loop=()=>{if(video.currentTime>=s.secondes){video.currentTime=0;video.play().catch(()=>{});}};
    on("timeupdate",loop);
  }
  video.pause();video.muted=true;video.playsInline=true;
  if(!sameSource(video,s))video.src=s.video;
  else if(video.error)video.load();
  waiting();
  if(frozen){
    const place=()=>{video.currentTime=s.secondes*.4;if(video.readyState>=2&&!video.seeking)ready();};
    if(video.readyState>=1)place();else on("loadedmetadata",place);
  }else{
    video.currentTime=0;
    video.play().catch(err=>{
      if(hooks.signal.aborted||err.name==="AbortError")return;
      if(video.error)unavailable();
      else{clearTimeout(pictureTimer);showPictureNotice("Appuie sur le bouton pour lire la vidéo.",retry);}
    });
  }
}

/* A — consigne ; elle reste lisible, même sans vidéo dans le fond. */
function showCard(i){
  if(!SCENES[i])return;
  stopRecording();hideAll();idx=i;updateState("A");
  const ready=!personal||files.has(SCENES[i].id), s=sceneSource(SCENES[i]);
  $("sansExtrait").hidden=true;
  cam.style.display=ready&&s.video?"block":"none";cam.muted=true;cam.loop=!previewNumber;
  if(ready&&s.video){
    if(!sameSource(cam,s))cam.src=s.video;
    cam.currentTime=0;
    if(!personal&&!previewNumber)cam.play().catch(()=>{});
    if(previewNumber){const still=()=>{cam.currentTime=s.secondes*.38;}; if(cam.readyState>=1)still();else cam.addEventListener("loadedmetadata",still,{once:true});}
  } else {cam.removeAttribute("src");cam.load();}
  $("scrim").classList.remove("off");
  renderCard(i);$("sheetBody").scrollTop=0;$("sheet").classList.remove("hidden");
  requestAnimationFrame(()=>window.majRepereDefilement?.());
}

function openRecording(s){
  stopRecording();hideAll();updateState("B");$("app").dataset.prise=s.id;
  cam.style.display="block";cam.loop=false;
  $("scrim").classList.add("off");$("rec").classList.add("on");$("rec").setAttribute("aria-hidden","false");
  $("chrono").classList.remove("hot");$("bar").classList.remove("hot");
  $("chronoVal").textContent="0:00";$("barFill").style.width="0%";
}

/* B — quand le clip est arrêté, le chrono et la barre sont arrêtés. */
function startRecording(){
  if(previewNumber)return;
  if(personal&&!files.has(SCENES[idx].id))return;
  const s=sceneSource(SCENES[idx]);openRecording(s);recording=true;
  watchPicture(cam,s,{onFinish:()=>{if(recording&&state==="B")finishRecording();},retry:startRecording});
  const tick=()=>{
    if(!recording)return;
    const t=Math.min(s.secondes,Math.max(0,Number(cam.currentTime)||0));
    $("chronoVal").textContent=fmt(t);$("barFill").style.width=`${100*t/s.secondes}%`;
    $("chrono").classList.toggle("hot",s.secondes-t<=3);$("bar").classList.toggle("hot",s.secondes-t<=3);
    if(t>=s.secondes){finishRecording();return;}
    rafId=requestAnimationFrame(tick);
  };rafId=requestAnimationFrame(tick);
}
function showFrozenRecording(){
  const s=SCENES[idx];openRecording(s);
  if(!s.video){$("sansExtrait").hidden=false;cam.style.display="none";return;}
  cam.loop=true;recording=true;
  watchPicture(cam,s,{retry:showFrozenRecording});
  const tick=()=>{if(!recording)return;const t=Math.min(s.secondes,cam.currentTime||0);$("chronoVal").textContent=fmt(t);$("barFill").style.width=`${100*t/s.secondes}%`;rafId=requestAnimationFrame(tick);};rafId=requestAnimationFrame(tick);
}
function stopRecording(){recording=false;if(rafId!==null)cancelAnimationFrame(rafId);rafId=null;}

/* C — un clip illisible ne peut pas être validé. Refaire reste possible. */
function finishRecording(){
  stopRecording();hideAll();updateState("C");const s=sceneSource(SCENES[idx]);
  replay.style.display="block";replay.loop=true;$("next").disabled=true;
  $("review").classList.add("on");
  if(s.video)watchPicture(replay,s,{review:true,retry:finishRecording});
  else {replay.style.display="none";$("sansExtrait").hidden=false;}
  if(!previewNumber){try{if(navigator.vibrate)navigator.vibrate([18,40,18]);}catch{}}
}
