// Mixage T3 dérivé du mixage T4 ; aucun service de transcription.
async function decodeAudio(file,ctx){try{return await ctx.decodeAudioData(await file.arrayBuffer());}catch{throw Error('Fichier audio illisible sur ce navigateur.');}}
export async function audioMix(track,voice,frames,takeFiles,sceneFrames,cfg){
 const ids=['S1','S2','S3','S4'];
 const C=window.AudioContext||window.webkitAudioContext;if(!C)throw Error('Audio indisponible sur ce navigateur.');const ctx=new C({sampleRate:48000});try{
 if(ctx.sampleRate!==48000)throw Error('Ce navigateur ne peut pas préparer le son au bon rythme. Essaie Chrome ou Edge récent sur un autre appareil.');
 const resp=await fetch('audio/'+track+'.flac');if(!resp.ok)throw Error('Musique indisponible.');let bed=await decodeAudio(await resp.blob(),ctx),v=voice?await decodeAudio(voice,ctx):null;
 const duration=frames/cfg.contrat.media.fps;
 if(takeFiles){
  if(!takeFiles.length)throw Error('Choisis au moins une prise dont tu veux garder le son.');
  const MB=await import('./vendor/mediabunny-1.66.1.min.mjs');const sr=ctx.sampleRate;v=ctx.createBuffer(2,frames*1600,sr);let sums=[0],carryUntil=0;for(const k of sceneFrames)sums.push(sums.at(-1)+k);
  for(const {id,file} of takeFiles){const idx=ids.indexOf(id);let input=new MB.Input({source:new MB.BlobSource(file),formats:[MB.MP4,MB.QTFF,MB.WEBM]}),videoStart,audioStart,audioEnd;
   try{let video=await input.getPrimaryVideoTrack(),source=await input.getPrimaryAudioTrack();if(!video||!source||!await source.canDecode())throw Error();videoStart=await video.getFirstTimestamp();audioStart=await source.getFirstTimestamp();audioEnd=await source.computeDuration();}catch{throw Error('Le son de la prise '+(idx+1)+' est absent ou illisible. Décoche cette prise ou importe une vidéo avec du son.');}finally{input.dispose()}
   if(audioEnd-videoStart>sceneFrames[idx]/30+.5)throw Error('Le son de la prise '+(idx+1)+' dépasse son image. Raccourcis ou remplace cette prise pour ne pas perdre la fin du son.');
   let a;try{a=await ctx.decodeAudioData(await file.arrayBuffer());}catch{throw Error('Le son de la prise '+(idx+1)+' est absent ou illisible. Décoche cette prise ou importe une vidéo avec du son.');}
   const effectiveStart=Math.max(audioStart,audioEnd-a.duration),offset=Math.round((effectiveStart-videoStart)*sr),sourceStart=Math.max(0,-offset),destWithin=Math.max(0,offset);
   // Ne conserver que les échantillons réellement présentés (hors bourrage du codec).
   const presented=Math.max(0,Math.min(a.length,Math.round((audioEnd-effectiveStart)*sr)));
   const destination=sums[idx]*1600+destWithin;
   if(sourceStart>=presented||destWithin>=sceneFrames[idx]*1600)throw Error('Le son de la prise '+(idx+1)+' ne commence pas pendant l’image.');
   const hasSignal=(from,to)=>{for(let ch=0;ch<a.numberOfChannels;ch++){const q=a.getChannelData(ch);for(let j=from;j<to;j++)if(Math.abs(q[j])>1e-7)return true;}return false;};
   if(sourceStart&&hasSignal(0,sourceStart))throw Error('Le son de la prise '+(idx+1)+' commence avant l’image. Remplace la prise pour ne perdre aucun son.');
   const fullCount=Math.min(presented-sourceStart,v.length-destination);
   if(fullCount<=0)throw Error('Le son de la prise '+(idx+1)+' ne commence pas pendant l’image.');
   if(sourceStart+fullCount<presented&&hasSignal(sourceStart+fullCount,presented))throw Error('Le son de la prise '+(idx+1)+' dépasse la fin du film. Remplace la prise pour ne pas perdre sa fin.');
   // Le son continue à 1x même si une image est arrondie à la frontière de scène.
   // Si deux sons se chevauchent réellement, refuser au lieu d'écraser le premier.
   const overlap=Math.min(fullCount,Math.max(0,carryUntil-destination));
   if(overlap){let conflicting=false;for(let ch=0;ch<2&&!conflicting;ch++){const dest=v.getChannelData(ch),src=a.getChannelData(Math.min(ch,a.numberOfChannels-1));for(let j=0;j<overlap;j++){if(Math.abs(dest[destination+j])>1e-7&&Math.abs(src[sourceStart+j])>1e-7){conflicting=true;break;}}}if(conflicting)throw Error('Les sons des prises '+idx+' et '+(idx+1)+' se chevauchent. Refais ou remplace une prise pour conserver les deux sons.');}
   const lastWindow=Math.round(cfg.contrat.duree_regles.silence_fin_ms*sr/1000),windowInScene=Math.max(destWithin,sceneFrames[idx]*1600-lastWindow),first=sourceStart+Math.max(0,windowInScene-destWithin),last=Math.min(presented,sourceStart+Math.max(0,sceneFrames[idx]*1600-destWithin));let endEnergy=0,endCount=0;
   for(let ch=0;ch<a.numberOfChannels;ch++){let samples=a.getChannelData(ch);for(let j=first;j<last;j++){endEnergy+=samples[j]*samples[j];endCount++;}}
   if(endCount&&Math.sqrt(endEnergy/endCount)>cfg.contrat.duree_regles.seuil_rms)throw Error('On entend encore du son à la fin de la prise '+(idx+1)+'. Refais ou remplace la vidéo : termine ta phrase, puis attends un instant avant d’arrêter. Un bruit peut aussi déclencher ce contrôle.');
   for(let ch=0;ch<2;ch++){const dest=v.getChannelData(ch),src=a.getChannelData(Math.min(ch,a.numberOfChannels-1));for(let j=0;j<fullCount;j++)dest[destination+j]+=src[sourceStart+j];}
   carryUntil=Math.max(carryUntil,destination+fullCount);
  }
 }
 if(v&&!takeFiles&&(v.duration<.3||v.duration>duration))throw Error('Ta voix est plus longue que le film ('+duration.toFixed(1)+' s) ou trop courte. Raccourcis la voix ou refais des prises plus longues.');
 if(v&&!takeFiles){let sum=0,count=0,window=Math.round(cfg.contrat.duree_regles.silence_fin_ms*v.sampleRate/1000),first=Math.max(0,v.length-window);for(let c=0;c<v.numberOfChannels;c++){let z=v.getChannelData(c);for(let i=first;i<z.length;i++){sum+=z[i]*z[i];count++}}if(count&&Math.sqrt(sum/count)>cfg.contrat.duree_regles.seuil_rms)throw Error('On entend encore du son à la fin de ta voix. Refais ou remplace la voix : termine ta phrase, puis attends un instant avant d’arrêter. Un bruit peut aussi déclencher ce contrôle.');}
 const sr=48000,n=frames*1600,left=new Float32Array(n),right=new Float32Array(n);let rms=0,vg=1;
 if(v){let energy=0,count=0,step=Math.round(sr*.4);for(let i=0;i<v.length;i+=step){let sum=0,end=Math.min(v.length,i+step);for(let c=0;c<v.numberOfChannels;c++){let samples=v.getChannelData(c);for(let j=i;j<end;j++)sum+=samples[j]*samples[j];}let k=(end-i)*v.numberOfChannels;if(sum/k>1e-5){energy+=sum;count+=k;}}rms=Math.sqrt(energy/Math.max(1,count));if(!Number.isFinite(rms)||rms<.0001)throw Error('La voix est silencieuse ou trop faible.');vg=Math.min(5,Math.pow(10,-20.5/20)/rms);}
 const bl=bed.getChannelData(0),br=bed.getChannelData(Math.min(1,bed.numberOfChannels-1)),vl=v?.getChannelData(0),vr=v?.getChannelData(Math.min(1,v.numberOfChannels-1));
 let peak=0,env=0,attack=Math.exp(-1/(sr*.04)),release=Math.exp(-1/(sr*.6));for(let i=0;i<n;i++){
  let a=vl&&i<vl.length?vl[i]*vg:0,b=vr&&i<vr.length?vr[i]*vg:0,det=Math.max(Math.abs(a),Math.abs(b)),coef=det>env?attack:release;env=coef*env+(1-coef)*det;
  let duck=v?Math.max(.22,Math.min(1,Math.pow(.03/Math.max(.03,env),.70))):1,base=v?.707:1;// The packaged music is 30 s. Crossfade into a 9 s interior excerpt at 25–27 s, then fade at the end.
  const t=i/sr, loopIndex=i-22*sr;let ml=bl[i]||0,mr=br[i]||0;
  if(t>=25){const q=Math.min(1,(t-25)/2),j=Math.max(0,Math.min(bl.length-1,loopIndex));ml=ml*(1-q)+(bl[j]||0)*q;mr=mr*(1-q)+(br[j]||0)*q;}
  const finish=Math.min(1,Math.max(0,(duration-t)/1.5));let x=ml*finish*base*duck+a,y=mr*finish*base*duck+b;
  // Accumulate the un-clipped mix; one gain for the whole clip preserves dynamics and balance.
  left[i]=x;right[i]=y;peak=Math.max(peak,Math.abs(x),Math.abs(y));
 }
 if(!Number.isFinite(peak))throw Error('Le son de la vidéo est illisible.');
 if(peak>.5){const gain=.5/peak;for(let i=0;i<n;i++){left[i]*=gain;right[i]*=gain;}}
 return {left,right};}finally{await ctx.close()}}
