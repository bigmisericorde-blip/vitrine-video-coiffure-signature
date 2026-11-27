// Remultiplexage AAC-LC : la prise originale et toute synthèse restent hors export.
import {BufferSource,Input,MP4,EncodedAudioPacketSource,EncodedPacketSink} from '../vendor/mediabunny-1.66.1.min.mjs';
import {demand,RenderFault} from './contract.mjs?v=t2-fiche-visible-3';
import {loadBed} from './resources.mjs?v=t2-fiche-visible-3';

const SAMPLE_RATE=48000, CLIP_SECS=30;
export async function prepareBed(output,track){
  let input;
  try{
    input=new Input({source:new BufferSource(await loadBed(track)),formats:[MP4]});
    const audio=await input.getPrimaryAudioTrack();
    demand(audio&&!(await input.getPrimaryVideoTrack())&&(await input.getAudioTracks()).length===1,'AUDIO_INVALID');
    const [codec,conf,start,end]=await Promise.all([audio.getCodec(),audio.getDecoderConfig(),audio.getFirstTimestamp(),audio.computeDuration()]);
    demand(codec==='aac'&&conf?.codec==='mp4a.40.2'&&conf.sampleRate===SAMPLE_RATE&&conf.numberOfChannels===2&&Math.abs(end-CLIP_SECS)<1/SAMPLE_RATE&&start>=-.03&&start<=0,'AUDIO_INVALID');
    const packets=[];
    let last=start;
    for await(const packet of new EncodedPacketSink(audio).packets()){
      demand(packets.length<1500&&packet.data.byteLength>0&&packet.duration>0&&Math.abs(packet.timestamp-last)<1/SAMPLE_RATE,'AUDIO_INVALID');
      packets.push(packet);
      last=packet.timestamp+packet.duration;
    }
    demand(packets.length>=1407&&Math.abs(last-CLIP_SECS)<1/SAMPLE_RATE,'AUDIO_INVALID');
    const source=new EncodedAudioPacketSource('aac');output.addAudioTrack(source);
    let cursor=0;
    return {
      async through(seconds){
        try {
          while(cursor<packets.length&&packets[cursor].timestamp<seconds+1e-8){
            // Conserve aussi le paquet d’amorce AAC : il reste hors du temps de présentation.
            await source.add(packets[cursor],cursor?undefined:{decoderConfig:conf}); cursor++;
          }
        }catch{throw new RenderFault('AUDIO_INVALID');}
      },
      close(){demand(cursor===packets.length,'AUDIO_INVALID');source.close();},
    };
  }catch(error){
    if(error instanceof RenderFault)throw error;
    throw new RenderFault('AUDIO_INVALID');
  }finally{input?.dispose();}
}
export function trackCredit(track){
  return `Fond musical : ${track.title} — ${track.artist} | ${track.source} | CC BY 4.0 ${track.licence} | Extrait de 30 s, niveau et fondus ajustés, sans changement de tempo${track.ai_disclosed?' | Usage d’IA déclaré par l’auteur':''}.`;
}
