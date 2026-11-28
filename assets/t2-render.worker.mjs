import {verifierSortie} from './verifier-sortie.mjs';
import {validateT1,bindT1Job} from './t1-contract.mjs?v=1';
import {
  BlobSource, BufferTarget, CanvasSource, EncodedAudioPacketSource, EncodedPacketSink,
  Input, MP4, Mp4OutputFormat, Output, QTFF, WEBM, VideoSampleSink,
} from './vendor/mediabunny-1.66.1.min.mjs';
import {createMotion, loadFonts, sourceFrame, W, H} from './t2-motion.mjs?v=commercial-t1-1';

const FPS=30, FRAMES=900, SECONDS=FRAMES/FPS;
const bitrate=3_800_000, codec='avc1.42001f';
const mediaRoot=new URL('../media/',import.meta.url);
const post=(stage,completed=0)=>self.postMessage({stage,completed,total:FRAMES});
const ensure=(ok,message)=>{if(!ok)throw Error(message);};

async function localBlob(url,limit) {
  ensure(url.origin===location.origin,'Média hors du gabarit.');
  const res=await fetch(url,{redirect:'error'});
  ensure(res.ok && Number(res.headers.get('Content-Length'))<=limit,'Un média du gabarit est indisponible.');
  const data=await res.blob();
  ensure(data.size>0&&data.size<=limit,'Taille du média hors contrat.');
  return data;
}
function readInput(blob) {return new Input({source:new BlobSource(blob),formats:[MP4,QTFF,WEBM]});}
async function planFor(request,contract) {
  const res=await fetch(new URL('../'+contract.renderer.plan_path,import.meta.url),{cache:'no-cache',redirect:'error'});
  ensure(res.ok,'Le plan canonique T2 n’a pas chargé.');
  const p=await res.json();
  ensure(p?.schema==='vv.coiffure.plan/1.0'&&p.template_id==='T2'&&/^\d+\.\d+\.\d+$/.test(p.version)
    && /^[a-z][a-z0-9-]+$/.test(p.audio_profile) && p.shots?.length===12&&p.cuts?.length===11,'Le plan de montage T2 est invalide.');
  ensure(!request.track||p.audio_profile===request.profile,'Le catalogue ne correspond pas au profil sonore du T2.');
  const scenes=request.scenes, ids=scenes.map(s=>s.id);
  ensure(scenes.length===4&&ids.join(',')===contract.renderer.requires_scenes.join(',')&&scenes.every((s,i)=>s.secondes===contract.capture.scenes[i].secondes),'Les quatre prises du contrat sont nécessaires.');
  let cursor=0;
  for(const [i,s] of p.shots.entries()){
    const n=ids.indexOf(s.scene);
    ensure(n>=0&&s.in===cursor&&s.out>cursor&&s.src>=0&&s.speed>0&&sourceFrame(s,s.out-1)<scenes[n].secondes*FPS,
      'Une fenêtre sort de la prise prévue.');
    ensure(i===0||p.cuts[i-1]?.at===s.in,'Raccord non aligné sur une coupe.');
    cursor=s.out;
  }
  ensure(cursor===FRAMES&&p.shots.at(-1).out-p.shots.at(-1).in>=99,'Durée ou carton final hors contrat.');
  return p;
}
async function render(request) {
  post('prepare');
  ensure(typeof OffscreenCanvas!=='undefined'&&typeof VideoEncoder!=='undefined'&&typeof VideoDecoder!=='undefined',
    'L’export MP4 demande un navigateur avec encodage H.264 (essaie une version récente de Chrome, Edge ou Safari).');
  const capability=await VideoEncoder.isConfigSupported({codec,width:W,height:H,bitrate,framerate:FPS,hardwareAcceleration:'no-preference',avc:{format:'avc'}});
  ensure(capability.supported,'Ce navigateur ou appareil ne sait pas encoder le MP4 H.264 en 720 × 1280.');
  const contractResponse=await fetch(new URL('../config/t1-beaute.json',import.meta.url),{cache:'no-cache',redirect:'error'});
  ensure(contractResponse.ok,'Le contrat T1 n’a pas chargé.');
  const contract=validateT1(await contractResponse.json()), job=bindT1Job(request.job,contract);
  const p=await planFor(request,contract);
  await loadFonts(self.fonts);
  const canvas=new OffscreenCanvas(W,H);
  const compose=createMotion(canvas,p,job,{demo:request.demo});
  const target=new BufferTarget();
  const writer=new Output({format:new Mp4OutputFormat({fastStart:'in-memory'}),target});
  let frames=0, packets=0;
  const video=new CanvasSource(canvas,{codec:'avc',fullCodecString:codec,bitrate,keyFrameInterval:2,latencyMode:'quality',onEncodedPacket:()=>packets++});
  writer.addVideoTrack(video,{frameRate:FPS});
  const track=request.track, audio=track?new EncodedAudioPacketSource('aac'):null;
  if(audio)writer.addAudioTrack(audio,{languageCode:'und'});
  const credit=track?`${track.titre} — ${track.auteur}. ${track.source} | ${track.licence_nom} ${track.licence}. ${track.modifications}`:'';
  const picCredit=request.demo?'Prises d’exemple : Pavel Danilyuk / Pexels — https://www.pexels.com/license/. ':'';
  writer.setMetadataTags({title:request.job.salon+' — '+request.job.service,
    ...(credit||picCredit?{comment:picCredit+credit}:{}),creationTime:null});
  await writer.start();
  try {
    let source=null, currentTrack=null;
    try {
      for (const shot of p.shots) {
        const s=request.scenes.find(s=>s.id===shot.scene);
        if(currentTrack?.scene!==s.id){
          source?.dispose();source=null;
          let blob=s.file;
          if(!blob){
            ensure(request.demo,'Importe les quatre prises avant de monter.');
            blob=await localBlob(new URL(s.id+'.mp4',mediaRoot),12*1024*1024);
          }
          ensure(blob instanceof Blob&&blob.size<=24*1024*1024,`Prise ${s.n} trop volumineuse (24 Mo maximum).`);
          source=readInput(blob);
          const v=await source.getPrimaryVideoTrack();
          ensure(v&&await v.canDecode(),`Prise ${s.n} : format non lisible sur cet appareil. Essaie un MP4 H.264.`);
          const [w,h,start,end]=await Promise.all([v.getDisplayWidth(),v.getDisplayHeight(),v.getFirstTimestamp(),v.computeDuration()]);
          ensure(w>=240&&h>=240&&w*h<=1920*1080,`Prise ${s.n} : utilise une vidéo HD ou Full HD, pas de 4K.`);
          ensure(end-start>=s.secondes-0.025,`Prise ${s.n} : filme au moins ${s.secondes} secondes.`);
          currentTrack={scene:s.id,sink:new VideoSampleSink(v),start};
        }
        const times=(function*(){for(let f=shot.in;f<shot.out;f++)yield currentTrack.start+(sourceFrame(shot,f)+.20)/FPS;})();
        let f=shot.in;
        for await (const sample of currentTrack.sink.samplesAtTimestamps(times)) {
          ensure(sample,`Prise ${s.n} : image manquante. Essaie un autre fichier.`);
          try {compose(sample,shot,f);} finally {sample.close();}
          await video.add(f/FPS,1/FPS);
          f++;frames++;
          if (frames%15===0)post('image',frames);
        }
        ensure(f===shot.out,`Prise ${s.n} interrompue.`);
      }
    } finally {source?.dispose();}
    video.close();
    if (audio) {
      post('audio',frames);
      ensure(/^[a-z0-9-]+$/.test(track.id)&&track.video===`media/afrobeat/${track.id}.mp4`&&/^[a-f0-9]{64}$/.test(track.sha256),
        'Piste non référencée.');
      const blob=await localBlob(new URL(`afrobeat/${track.id}.mp4`,mediaRoot),16*1024*1024);
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer())),b=>b.toString(16).padStart(2,'0')).join('');
      ensure(hash===track.sha256,'Le fond calibré n’a pas passé le contrôle d’intégrité.');
      const media=readInput(blob);
      try {
        const a=await media.getPrimaryAudioTrack();
        ensure(a&&await a.getCodec()==='aac','Pas de piste AAC dans le fond calibré.');
        const config=await a.getDecoderConfig();
        ensure(config?.sampleRate===48000&&config.numberOfChannels===2,'Profil du fond calibré non conforme.');
        let added=0;
        for await (const packet of new EncodedPacketSink(a).packets()) {
          if (packet.timestamp>=SECONDS-1e-6)break;
          const dur=Math.min(packet.duration,SECONDS-packet.timestamp);
          // Pas de réencodage, d’étirement temporel ou de modification du gain.
          await audio.add(dur===packet.duration?packet:packet.clone({duration:dur}),added++?undefined:{decoderConfig:config});
        }
        ensure(added>1000,'Le fond calibré est incomplet.');
        audio.close();
      } finally {media.dispose();}
    }
    post('finalize',frames);
    await writer.finalize();
    ensure(frames===FRAMES&&packets===FRAMES&&target.buffer?.byteLength>65536,'Le MP4 ne contient pas les 900 images attendues.');
    await verifierSortie(new Blob([target.buffer],{type:'video/mp4'}),true);
    self.postMessage({stage:'done',buffer:target.buffer,frames,seconds:SECONDS,template:{id:p.template_id,version:p.version,profile:p.audio_profile}},[target.buffer]);
  } catch(e) {
    await writer.cancel().catch(()=>{});
    throw e;
  }
}

self.onmessage=async e=>{
  self.onmessage=null;
  try {await render(e.data);}
  catch(error){
    const message=error?.name==='QuotaExceededError'?'Mémoire insuffisante pour encoder. Ferme les autres onglets et réessaie.':String(error?.message||error);
    self.postMessage({stage:'error',message});
  }
};
