'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const form = $('form'), player = $('result'), rotation = window.VVAfrobeat;
  const only = (id,visible) => {$(id).hidden = !visible;};
  const value = name => form.querySelector(`input[name=${name}]:checked`).value;
  const key = 'vv-beaute-t1-atelier-client';
  const renderKey = 'vv-beaute-t1-atelier-dernier-mp4';
  const linked=new URLSearchParams(location.search).get('source')==='montage-t1';
  let source=null;
  if(linked){
    only('imageModes',false);only('linkedVideo',true);
    $('linkedVideo').textContent='En attente de ton montage T1…';
    $('trackHint').textContent='Cet habillage garde le fond déjà choisi. Il baisse pendant la parole, puis remonte dans les pauses.';
    $('music').nextElementSibling.textContent='Conserver ce fond musical';
    player.removeAttribute('src');
    $('resultInfo').textContent='Ton MP4 T1 sera repris ici, sans remplacer l’image.';
  }
  let visitor, caps, recording, timer, micBlob, micURL, stream, busy = false, requesting = false;
  try {visitor = localStorage.getItem(key);} catch {}
  if (!/^[a-f0-9]{32}$/.test(visitor || '')) {
    visitor = Array.from(crypto.getRandomValues(new Uint8Array(16)),x => x.toString(16).padStart(2,'0')).join('');
    try {localStorage.setItem(key,visitor);} catch {}
  }
  const status = (text,error=false) => {$('status').textContent=text;$('status').classList.toggle('error',error);};
  function stopAudio() {if (recording?.state === 'recording') recording.stop();}
  function update() {
    const personal = value('imageMode') === 'file', mode = value('voiceMode');
    only('videoZone',personal&&!linked); only('voiceZone',mode === 'audio'); only('textZone',mode === 'texte'); only('noVoice',mode === 'sans');
    $('originalVoice').disabled = !personal||linked;
    if ((!personal||linked) && $('entry').value === 'video') $('entry').value = 'mic';
    const entry = $('entry').value;
    only('micZone',entry === 'mic'); only('audioZone',entry === 'file'); only('keepHelp',entry === 'video');
    $('prompterCopy').textContent = $('script').value.trim();
    only('prompter',entry === 'mic' && !!$('prompterCopy').textContent);
    if (mode !== 'audio' || entry !== 'mic') stopAudio();
    const canRead = caps?.langues_texte.some(t => t.code === $('lang').value);
    $('langHelp').textContent = canRead ? 'Le moteur lit ton texte dans cette langue. Aucune traduction automatique.'
      : 'Pas de lecture automatique dans cette langue. Enregistre ton texte dans ta langue ou importe la voix.';
    only('speakInstead',mode === 'texte' && !canRead);
    $('music').disabled=linked&&!source?.track;
    $('render').disabled = !caps || (linked&&(!source||!caps.liaison_t2)) || busy || requesting || recording?.state === 'recording' || (mode === 'texte' && !canRead);
    $('count').textContent = `${$('script').value.length} / 550`;
  }
  form.addEventListener('change',update);$('script').addEventListener('input',update);
  $('speakInstead').onclick = () => {
    form.querySelector('input[name=voiceMode][value=audio]').checked = true;$('entry').value = 'mic';update();$('record').focus();
  };
  $('record').onclick = async () => {
    if (recording?.state === 'recording') {stopAudio();return;}
    if (requesting || busy) return;
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      $('micState').textContent='Le micro n’est pas accessible ici. Ouvre l’atelier directement en HTTPS ou importe un fichier voix.';return;
    }
    let local;
    requesting=true;update();$('micState').textContent='En attente de l’autorisation du micro…';
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true},video:false});
      if (value('voiceMode') !== 'audio' || $('entry').value !== 'mic') {
        stream.getTracks().forEach(t=>t.stop());$('micState').textContent='';return;
      }
      const mime = ['audio/webm;codecs=opus','audio/mp4','audio/ogg;codecs=opus'].find(t=>MediaRecorder.isTypeSupported(t));
      if (!mime) throw Error('format');
      local = new MediaRecorder(stream,{mimeType:mime});
      recording = local;
      const chunks = [];
      local.ondataavailable = e => {if(e.data.size) chunks.push(e.data);};
      local.onstop = () => {
        clearInterval(timer);stream?.getTracks().forEach(t => t.stop());stream=null;
        if (micURL) URL.revokeObjectURL(micURL);
        micBlob = new Blob(chunks,{type:local.mimeType});
        if (micBlob.size) {micURL = URL.createObjectURL(micBlob);$('micListen').src = micURL;}
        only('micListen',!!micBlob.size);$('record').innerHTML='<span class="record-dot" aria-hidden="true"></span> Réenregistrer';
        $('micState').textContent=micBlob.size?'Voix prête à écouter avant le mixage.':'Enregistrement vide : réessaie.';update();
      };
      local.onerror = () => {stopAudio();$('micState').textContent='Le micro a interrompu l’enregistrement.';};
      local.start(200);
      const start=performance.now();
      $('clock').textContent='00:00';
      timer=setInterval(() => {
        const sec=(performance.now()-start)/1000;
        $('clock').textContent=`00:${String(Math.min(29,Math.floor(sec))).padStart(2,'0')}`;
        if (sec >= 29.5) stopAudio();
      },100);
      $('record').textContent='Arrêter l’enregistrement';$('micState').textContent='Le micro enregistre.';only('micListen',false);
    } catch {
      stream?.getTracks().forEach(t=>t.stop());stream=null;
      $('micState').textContent='Micro non accessible. Autorise-le ou importe un fichier voix.';
    } finally {requesting=false;update();}
  };
  window.addEventListener('pagehide',()=>{stopAudio();stream?.getTracks().forEach(t=>t.stop());if(micURL)URL.revokeObjectURL(micURL);});

  function show(r,refreshRotation=false) {
    if (!/^api\/montages\/[a-f0-9]{32}\.mp4$/.test(r?.url)) return;
    player.pause();player.src=r.url;player.defaultMuted=player.muted=false;
    $('download').href=r.url+'?download=1';only('download',true);only('expire',true);
    $('resultInfo').textContent=`${r.duree_s.toLocaleString('fr-FR')} s · ${r.voix.presente?'Voix mixée sans changer son débit':r.piste?'Musique sans voix':'Version muette'}`;
    only('track',!!r.piste);only('credits',!!r.piste);only('synthCredit',!!r.voix.synthese);
    if (r.piste) {
      $('track').textContent=`${r.piste.titre} — ${r.piste.auteur}`;
      $('musicSource').href=r.piste.source;$('musicLicense').href=r.piste.licence;$('musicLicense').textContent=r.piste.licence_nom;
      if (refreshRotation) rotation?.remember(r.piste.id);
    }
    $('synthCredit').textContent=r.voix.synthese?.credit||'';
    $('render').textContent=linked?'Refaire le mixage voix':'Créer un nouveau montage →';
  }
  player.addEventListener('error',()=>{if (!$('download').hidden) status('Ce lien temporaire ne se lit plus. Crée un nouveau montage.',true);});

  form.onsubmit = async e => {
    e.preventDefault();if (busy || !caps) return;
    const mode=value('voiceMode');const data=new FormData();
    const file=linked?source?.blob:$('sourceVideo').files[0];
    const selectedVideo=linked||value('imageMode') === 'file';
    if (selectedVideo) {
      if (!file || file.size > caps.max_video_octets) return status('Importe une vidéo de 64 Mo maximum.',true);
      data.set('video',file,file.name||'montage-t2.mp4');
      if(linked){data.set('liaison','t2');data.set('fond',source.track);}
    }
    if (mode === 'audio') {
      const entry=$('entry').value;
      if (entry === 'video') data.set('mode','video');
      else {
        const voice=entry === 'file' ? $('sourceAudio').files[0] : micBlob;
        if (!voice?.size || voice.size > caps.max_voix_octets) return status('Enregistre ou importe ta voix (12 Mo max.).',true);
        data.set('mode','audio');data.set('voix',voice,voice.name||'voix');
      }
    } else {
      data.set('mode',mode);
      if (mode === 'texte') {
        const text=$('script').value.trim();
        if (text.length < 3) {$('script').focus();return status('Écris ton texte avant de lancer le montage.',true);}
        data.set('texte',text);data.set('lang',$('lang').value);
      }
    }
    data.set('browser',visitor);data.set('music',$('music').checked?'1':'0');data.set('precedente',rotation?.last()||'');
    busy=true;$('controls').disabled=true;update();player.pause();$('micListen').pause();
    status(mode==='texte'?'Lecture de ton texte, puis mixage du MP4…':'Calage du son et préparation du MP4…');
    try {
      const res=await fetch('api/montages',{method:'POST',body:data,cache:'no-store'});const r=await res.json();
      if (!res.ok) throw Error(r.error||'Montage en échec.');
      show(r,!linked);status('Montage prêt : l’aperçu et le téléchargement utilisent le même fichier.');
      if(!linked)try {sessionStorage.setItem(renderKey,JSON.stringify(r));} catch {}
    } catch(e) {status(e instanceof SyntaxError?'Le serveur de montage est indisponible. Réessaie.':e.message,true);}
    finally {busy=false;$('controls').disabled=false;update();}
  };

  fetch('api/atelier/config',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(async r=>{
    caps=r;
    $('lang').replaceChildren(...r.langues_texte.map(x=>new Option(x.label,x.code)),new Option('Fon — enregistrer','fon'),new Option('Yoruba — enregistrer','yo'),new Option('Autre langue — enregistrer','autre'));
    status(linked?'La vidéo et ta voix ne sont envoyées au moteur qu’au lancement du mixage.':'');update();
    if(linked)return;
    let last;try {last=JSON.parse(sessionStorage.getItem(renderKey));} catch {}
    if (/^api\/montages\/[a-f0-9]{32}\.mp4$/.test(last?.url||'')) {
      const res=await fetch(last.url,{method:'HEAD',cache:'no-store'}).catch(()=>null);
      if(res?.ok && !busy && $('download').hidden) show(last);
    }
  }).catch(()=>{status(linked?'La voix off demande un serveur de montage en ligne. Ton MP4 T2 reste disponible dans l’écran précédent.':'Cette page a besoin du serveur de montage. Le film exemple reste accessible.',true);update();});
  if(linked && parent!==window){
    window.addEventListener('message',event=>{
      const data=event.data;
      if(event.origin!==location.origin||event.source!==parent||data?.type!=='vv-t2-voice-source'||source||
         !(data.blob instanceof Blob)||data.blob.type!=='video/mp4'||(data.track&&!rotation?.byId(data.track)))return;
      source={blob:data.blob,track:data.track,url:URL.createObjectURL(data.blob)};
      player.src=source.url;$('music').checked=!!source.track;
      $('linkedVideo').textContent=String(data.title).slice(0,45)+' · ton MP4 T2, 30 s';
      $('resultInfo').textContent='Montage personnalisé avant ajout de la voix off.';
      update();
    });
    parent.postMessage({type:'vv-t2-voice-ready'},location.origin);
    window.addEventListener('pagehide',()=>{if(source)URL.revokeObjectURL(source.url);});
  }else if(linked){$('linkedVideo').textContent='Ouvre l’atelier depuis le MP4 de la fiche T2.';}
  update();
})();
