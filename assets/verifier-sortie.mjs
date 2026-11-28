import {Input,BlobSource,MP4} from './vendor/mediabunny-1.66.1.min.mjs';
/* Refuse un fichier invalide ou trop long sans le raccourcir. */
export async function verifierSortie(blob,avecAudio){
 const check=new Input({source:new BlobSource(blob),formats:[MP4]});
 try{
  const vd=await check.getPrimaryVideoTrack(),ad=await check.getPrimaryAudioTrack();
  const reported=await check.getDurationFromMetadata(),measured=await check.computeDuration();
  if(!vd||!Number.isFinite(reported)||!Number.isFinite(measured)||reported<=0||measured<=0)throw Error('Le fichier final est illisible. Réessaie le montage.');
  if(reported>30+1e-7||measured>30+1e-7)throw Error('Le fichier final dépasse 30 secondes. Refais une prise un peu plus courte : aucune fin ne sera coupée.');
  if(!!avecAudio!==!!ad)throw Error('La piste audio du fichier final est incomplète. Réessaie le montage.');
  return {reported,measured};
 }finally{check.dispose();}
}
