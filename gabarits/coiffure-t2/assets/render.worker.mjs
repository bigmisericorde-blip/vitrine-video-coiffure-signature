import {verifierSortie} from './verifier-sortie.mjs';
import {BufferTarget,CanvasSource,Mp4OutputFormat,Output,VideoSampleSink,AudioSampleSource,AudioSample} from './vendor/mediabunny-1.66.1.min.mjs';
import {createMotion,validatePlan,selectLayer,span,sourceFrame,W,H,FPS,FRAMES} from './motion.mjs?v=t2-fiche-visible-3';
import {createMotion as createMotionOnglerie} from './motion-onglerie.mjs?v=t2-fiche-visible-3';
import {reframeT2} from './montage-onglerie.mjs?v=t2-fiche-visible-3';
import {styleCassures} from './cassures.mjs?v=t2-fiche-visible-3';
import {readMedia,describe,inputs,LIMIT} from './media.mjs?v=t2-fiche-visible-3';
import {makeVisualPlan} from './texte/modele-visuel.mjs?v=t2-fiche-visible-3';
import {lettrageFonts,prepareCaptions,drawCaptions} from './texte/lettrage.mjs?v=t2-fiche-visible-3';
import {loadCore,loadPlan,loadFonts,digest,readBytes} from './engine/resources.mjs?v=t2-fiche-visible-3';
import {validateJob,createResult,failRecord,RenderFault,demand} from './engine/contract.mjs?v=t2-fiche-visible-3';
import {prepareBed,trackCredit} from './engine/music.mjs?v=t2-fiche-visible-3';

const codec='avc1.420020',bitrate=5_200_000;
const post=(stage,completed=0,total=FRAMES)=>self.postMessage({stage,completed,total});

async function render(payload,core){
  const {kind,job,files,voicePcm}=payload||{};
  const metier=payload?.metier??'coiffure';
  demand(globalThis.VVBeaute.profiles.some(p=>p.id===metier));
  const onglerie=metier==='manucure';
  const detail=kind==='detail';demand(detail||kind==='production');
  const spec=detail?null:validateJob(job,core);
  demand(detail?!voicePcm:(job.voice===true)===Boolean(voicePcm));
  if(voicePcm)demand(voicePcm.left instanceof Float32Array&&voicePcm.right instanceof Float32Array&&voicePcm.left.length===1440000&&voicePcm.right.length===1440000,'AUDIO_INVALID');
  const refs=detail?['S2']:spec.slots;
  const reuseDetail=detail||spec.reuse;
  demand(files&&typeof files==='object'&&Object.keys(files).length===refs.length&&refs.every(id=>inputs.includes(id)&&files[id] instanceof Blob&&files[id].size>0&&files[id].size<=LIMIT));
  demand(typeof OffscreenCanvas!=='undefined'&&typeof VideoEncoder!=='undefined'&&typeof VideoDecoder!=='undefined','PLATFORM');
  const support=await VideoEncoder.isConfigSupported({codec,width:W,height:H,bitrate,framerate:FPS,avc:{format:'avc'}});
  demand(support.supported,'PLATFORM','Encodage H.264 720 × 1280 indisponible sur cet appareil.');
  let plan,captionPlan;
  try{
    plan=validatePlan(await loadPlan(core));
    if(onglerie)plan=validatePlan(styleCassures(reframeT2(plan)));
    demand(plan.revision===core.template.base.revision,'RESOURCE_INVALID');
    if(!detail){
      let habillage=core.habillage;
      if(onglerie){
        const bytes=await readBytes('formulaire/habillage-onglerie.json','da425f22db70e8abf116214471757f7f5a8d3e875ffb7967be3c7faa6fe418db');
        habillage=JSON.parse(new TextDecoder().decode(bytes));
        demand(habillage.schema==='vv.coiffure.habillage/1'&&habillage.revision==='beaute-fr-01'&&habillage.base===core.template.base.revision,'RESOURCE_INVALID');
      }
      captionPlan=makeVisualPlan(spec.fields,spec.track.id,habillage,core.questions);
      await lettrageFonts(...await loadFonts(core));
    }
  }catch{throw new RenderFault('RESOURCE_INVALID');}
  const shots=detail?plan.detailReview.map(id=>plan.shots.find(shot=>shot.id===id)):plan.shots;
  const total=shots.reduce((n,shot)=>n+shot.out-shot.in,0);
  const canvas=new OffscreenCanvas(W,H),compose=(onglerie?createMotionOnglerie:createMotion)(canvas,detail?{...plan,impacts:[]}:plan,job?.framing);
  const ctx=canvas.getContext('2d',{alpha:false}), overlays=detail?null:prepareCaptions(captionPlan);
  const target=new BufferTarget(),out=new Output({format:new Mp4OutputFormat({fastStart:'in-memory'}),target});
  const media=new Map(),views=new Map();
  let packets=0,n=0;
  const source=new CanvasSource(canvas,{codec:'avc',fullCodecString:codec,bitrate:detail?3_600_000:bitrate,keyFrameInterval:2,latencyMode:'quality',onEncodedPacket:()=>packets++});
  out.addVideoTrack(source,{frameRate:FPS});
  try{
    for(const id of refs){
      try{
        const m=readMedia(files[id]);media.set(id,m);views.set(id,await describe(m,plan.scenes[id]/FPS));
      }catch{throw new RenderFault('UNSUPPORTED_MEDIA',`La prise ${id} ne respecte pas le format ou la durée attendue.`);}
    }
    let bed=null;
    if(!detail&&voicePcm){
      const {registerAacEncoder}=await import('./vendor/mediabunny-aac-encoder.min.mjs');registerAacEncoder();
      const aac=new AudioSampleSource({codec:'aac',bitrate:160000});out.addAudioTrack(aac);let audioPos=0;
      bed={async through(seconds){const end=Math.min(1438976,Math.round(seconds*48000));while(audioPos<end){let len=Math.min(48000,end-audioPos),data=new Float32Array(len*2);data.set(voicePcm.left.subarray(audioPos,audioPos+len));data.set(voicePcm.right.subarray(audioPos,audioPos+len),len);const sample=new AudioSample({format:'f32-planar',sampleRate:48000,numberOfChannels:2,timestamp:audioPos/48000,data});try{await aac.add(sample);}finally{sample.close();}audioPos+=len;}},close(){demand(audioPos===1438976,'AUDIO_INVALID');aac.close();}};
    }else if(!detail)bed=await prepareBed(out,spec.track);
    const comment=detail?undefined:(job.mode==='technical_fixture'?'Recette : images graphiques fictives. ':'')+trackCredit(spec.track)+(job.voice?' Voix personnelle importée et mixée localement.':'');
    out.setMetadataTags({title:detail?'COIFFURE-T2 — Détail recadré':'COIFFURE-T2',creationTime:null,...(comment?{comment}:{})});
    await out.start();
    for(const shot of shots){
      const streams=shot.layers.map(l=>{
        const [a,b]=span(l,shot),length=b-a,layer=selectLayer(l,reuseDetail);
        const {video,start}=views.get(layer.scene);
        const sink=new VideoSampleSink(video);
        const times=function*(){for(let i=0;i<length;i++)yield start+(sourceFrame(layer,i)+.18)/FPS;};
        return {a,b,length,layer,iter:sink.samplesAtTimestamps(times())[Symbol.asyncIterator]()};
      });
      try{
        for(let f=shot.in;f<shot.out;f++){
          const loc=f-shot.in;
          const pieces=await Promise.allSettled(streams.map(async s=>{
            if(loc<s.a||loc>=s.b)return null;
            const next=await s.iter.next();
            demand(!next.done&&next.value,'UNSUPPORTED_MEDIA',`Image non lisible dans la prise ${s.layer.scene}.`);
            return {sample:next.value,layer:s.layer,n:loc-s.a,length:s.length};
          }));
          try{
            const error=pieces.find(p=>p.status==='rejected');if(error)throw error.reason;
            compose(pieces.map(p=>p.value),shot,f);
            if(overlays)drawCaptions(ctx,overlays,f);
          }finally{for(const p of pieces)p.value?.sample.close();}
          await source.add(n/FPS,1/FPS);n++;
          if(n%30===0){if(bed)await bed.through(n/FPS);post('encode',n,total);}
        }
      }finally{await Promise.allSettled(streams.map(s=>s.iter.return?.()));}
    }
    source.close();bed?.close();post('finalize',n,total);await out.finalize();
    const buffer=target.buffer;
    demand(packets===total&&n===total&&buffer?.byteLength>15000,'RENDER_FAILED');
    if(detail)self.postMessage({stage:'done',buffer,frames:n,seconds:n/FPS,revision:plan.revision,sourceCount:refs.length},[buffer]);
    else{
      demand(n===core.template.media.frames,'RENDER_FAILED');
      await verifierSortie(new Blob([buffer],{type:'video/mp4'}),true);
      const result=createResult(job,core,buffer.byteLength,await digest(buffer));
      self.postMessage({stage:'done',buffer,result},[buffer]);
    }
  }catch(e){await out.cancel().catch(()=>{});throw e;}
  finally{for(const m of media.values())m.dispose();}
}
self.onmessage=async e=>{
  self.onmessage=null;post('prepare');let core;
  try{
    try{core=await loadCore();}catch{throw new RenderFault('RESOURCE_INVALID');}
    await render(e.data,core);
  }catch(err){
    const error=failRecord(err,core,e.data?.job?.job_id);
    self.postMessage({stage:'error',error,message:error.message});
  }
};
