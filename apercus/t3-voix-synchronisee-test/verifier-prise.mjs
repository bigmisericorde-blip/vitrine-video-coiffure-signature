import {Input,BlobSource,MP4,QTFF,WEBM} from './vendor/mediabunny-1.66.1.min.mjs';
// Applique à l'entrée le même contrôle de piste vidéo que le moteur, avant de pouvoir garder la prise.
export async function verifierPrise(file,seconds){
 if(!(file instanceof Blob)||!file.size||file.size>48*1024*1024)throw Error('Prise absente ou trop lourde : 48 Mio maximum.');
 let input;
 try{
  input=new Input({source:new BlobSource(file),formats:[MP4,QTFF,WEBM]});
  let video=await input.getPrimaryVideoTrack();
  if(!video||!await video.canDecode())throw Error('Cette vidéo ne peut pas être décodée. Essaie un autre fichier.');
  let start=await video.getFirstTimestamp(),end=await video.computeDuration();
  if(!Number.isFinite(start)||!Number.isFinite(end)||end-start<seconds-.05)throw Error(`La prise est trop courte : ${seconds} secondes minimum.`);
 }catch(e){if(e?.message?.includes('trop courte')||e?.message?.includes('décodée'))throw e;throw Error('Cette vidéo ne peut pas être décodée. Essaie un autre fichier.');}
 finally{input?.dispose();}
}
