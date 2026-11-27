import {BlobSource, Input, MP4, QTFF, WEBM} from './vendor/mediabunny-1.66.1.min.mjs';
export const LIMIT=40*1024*1024;
export const inputs=['S1','S2','S3','S4'];
export const takeSeconds=[6,7,7,7];
export function readMedia(file){return new Input({source:new BlobSource(file),formats:[MP4,QTFF,WEBM]});}
export async function describe(media,seconds){
  const video=await media.getPrimaryVideoTrack();
  if(!video||!await video.canDecode())throw Error('Vidéo illisible. Essaie une prise MP4 H.264 ou WebM.');
  const [width,height,start,end]=await Promise.all([video.getDisplayWidth(),video.getDisplayHeight(),video.getFirstTimestamp(),video.computeDuration()]);
  if(!Number.isFinite(start)||!Number.isFinite(end)||end-start<seconds-.017)throw Error(`Prise trop courte : il faut au moins ${seconds} s.`);
  if(width<360||height<640||width*height>1920*1080||height/width<1.35)throw Error('Filme en vertical, en HD ou Full HD, sans 4K.');
  if(end-start>120)throw Error('Prends un extrait de moins de deux minutes.');
  return {video,width,height,start,end};
}
export async function inspect(file,seconds){
  if(!(file instanceof Blob)||!file.size||file.size>LIMIT) throw Error('Choisis une vidéo de 40 Mo au maximum.');
  const m=readMedia(file);
  try {const x=await describe(m,seconds);return {width:x.width,height:x.height,duration:x.end-x.start,hasAudio:!!await m.getPrimaryAudioTrack()};}
  finally{m.dispose();}
}
export async function demoBlob(id){
  if(!inputs.includes(id))throw Error('Prise inconnue.');
  const response=await fetch(new URL('../fixtures/media/'+id+'.mp4',import.meta.url),{redirect:'error'});
  if(!response.ok||Number(response.headers.get('Content-Length'))>LIMIT)throw Error('La prise d’exemple n’a pas chargé.');
  const blob=await response.blob();if(!blob.size||blob.size>LIMIT)throw Error('Fichier de démonstration invalide.');return blob;
}
