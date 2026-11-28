import {registerAacEncoder} from './vendor/mediabunny-aac-encoder.min.mjs';
import {BufferTarget,CanvasSource,Mp4OutputFormat,Output,VideoSampleSink,BlobSource,Input,MP4,QTFF,WEBM,AudioSampleSource,AudioSample} from './vendor/mediabunny-1.66.1.min.mjs';
const W=720,H=1280,FPS=30,ids=['S1','S2','S3','S4'];
const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{x=clamp(x);return x*x*(3-2*x)};
async function font(name,url){const f=new FontFace(name,`url(${url})`);await f.load();self.fonts.add(f)}
function panel(ctx,s,zoom=1){let t=s.rotation===90||s.rotation===270,sw=t?s.squarePixelHeight:s.squarePixelWidth,sh=t?s.squarePixelWidth:s.squarePixelHeight,k=Math.max(W/sw,H/sh)*zoom;s.draw(ctx,(W-sw*k)/2,(H-sh*k)/2,sw*k,sh*k)}
function title(ctx,text,y,size,opacity=1,max=3,family='Cormorant',color='#fff0df'){
 if(!text||opacity<=0)return;ctx.save();ctx.globalAlpha=clamp(opacity);ctx.textAlign='center';ctx.textBaseline='top';let lines=[];
 for(;size>=22;size-=2){ctx.font=`600 ${size}px ${family}`;let row='';lines=[];let bad=false;for(const word of String(text).split(/\s+/)){if(ctx.measureText(word).width>625){bad=true;break}let t=(row+' '+word).trim();if(row&&ctx.measureText(t).width>625){lines.push(row);row=word}else row=t}if(row)lines.push(row);if(!bad&&lines.length<=max)break}
 if(size<22)throw Error('Un texte dépasse le cadre. Raccourcis-le.');ctx.shadowColor='rgba(15,2,9,.9)';ctx.shadowBlur=7;ctx.lineWidth=2;ctx.strokeStyle='rgba(20,4,10,.7)';ctx.fillStyle=color;for(const [i,line] of lines.entries()){ctx.strokeText(line,360,y+i*size*1.1);ctx.fillText(line,360,y+i*size*1.1)}ctx.restore();
}
function shade(ctx,top,bottom){const g=ctx.createLinearGradient(0,top,0,bottom);g.addColorStop(0,'rgba(22,7,15,.57)');g.addColorStop(1,'rgba(22,7,15,0)');ctx.fillStyle=g;ctx.fillRect(0,top,W,bottom-top)}
function leak(ctx,f,a,b,power=.32){let q=(f-a)/(b-a),x=-500+1700*q;ctx.save();ctx.globalAlpha=power*(.45+.55*Math.sin(Math.PI*q));ctx.fillStyle='#f47548';ctx.beginPath();ctx.moveTo(x-180,0);ctx.lineTo(x+10,0);ctx.lineTo(x+640,H);ctx.lineTo(x+450,H);ctx.closePath();ctx.fill();ctx.restore()}
const plate=new OffscreenCanvas(W,H),pc=plate.getContext('2d',{alpha:false});const held=new OffscreenCanvas(W,H),hc=held.getContext('2d',{alpha:false});const last=new OffscreenCanvas(W,H),lc=last.getContext('2d',{alpha:false});
function artwork(frame,ctx,s,x,subs,seg){
 const sub=(subs||[]).find(z=>frame/FPS>=z.start&&frame/FPS<z.end);
 // Remap only effect timing; actual input media timestamps stay at 1.0x.
 const f=Math.floor(seg.oldStart+(frame-seg.a)*seg.oldLength/(seg.b-seg.a));
 const z=(f>=376&&f<408)?1.10:(f>=226&&f<256)?1+.045*smooth((f-226)/30):1;
 pc.clearRect(0,0,W,H);panel(pc,s[0],z);ctx.drawImage(plate,0,0);
 if(f<66){let q=smooth(f/65),reach=q*1050;ctx.save();ctx.fillStyle=`rgba(28,8,21,${.83*(1-q)})`;ctx.fillRect(0,0,W,H);ctx.beginPath();ctx.moveTo(360,640);ctx.lineTo(360-reach,640-reach);ctx.lineTo(360+reach,640-reach);ctx.closePath();ctx.moveTo(360,640);ctx.lineTo(360-reach,640+reach);ctx.lineTo(360+reach,640+reach);ctx.closePath();ctx.clip();ctx.drawImage(plate,0,0);ctx.restore()}
 if(f>=82&&f<94){let arr=[[0,212],[212,373],[373,682],[682,855],[855,H]];for(let i=0;i<arr.length;i++){let [t,b]=arr[i],dx=(i%2?-1:1)*(12+Math.round(15*Math.sin(f*.8+i)));ctx.save();ctx.beginPath();ctx.rect(0,t,W,b-t);ctx.clip();ctx.drawImage(plate,dx,0);ctx.restore()}}
 if(f>=145&&f<158)leak(ctx,f,145,158,.50);
 if(f<197)hc.drawImage(plate,0,0);
 if(f>=197&&f<213){let q=smooth((f-197)/15);ctx.drawImage(held,0,0);for(let [t,b,d] of [[0,251,0],[251,505,.13],[505,734,.23],[734,991,.35],[991,H,.45]]){let h=Math.round((b-t)*smooth((q-d)/.55));if(h>0)ctx.drawImage(plate,0,t,W,h,0,t,W,h)}}
 if(f>=226&&f<256){let q=(f-226)/30;ctx.fillStyle=`rgba(22,11,25,${.22*Math.sin(Math.PI*q)**2})`;ctx.fillRect(0,0,W,H)}
 if(f>=282&&f<300){let x=-400+1600*smooth((f-282)/18);ctx.fillStyle='rgba(43,8,33,.48)';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(x,0);ctx.lineTo(x-360,H);ctx.lineTo(0,H);ctx.closePath();ctx.fill()}
 if(f>=322&&f<342)leak(ctx,f,322,342,.30);
 if(f>=488&&f<521){ctx.drawImage(plate,0,210,W,640,0,0,W,640);ctx.drawImage(plate,0,210,W,640,0,640,W,640)}
 if(f<727)lc.drawImage(plate,0,0);
 if(f>=727&&f<755){let q=smooth((f-727)/28),edge=W*(1-q)*1.7-260;ctx.drawImage(last,0,0);ctx.save();ctx.beginPath();ctx.moveTo(edge,0);ctx.lineTo(W,0);ctx.lineTo(W,H);ctx.lineTo(edge-.23*H,H);ctx.closePath();ctx.clip();ctx.drawImage(plate,0,0);ctx.restore()}
 if(f>=892){ctx.fillStyle=`rgba(0,0,0,${.34*smooth((f-892)/8)})`;ctx.fillRect(0,0,W,H)}
 if(f>=30&&f<130){if(!sub)shade(ctx,0,400);title(ctx,x.accroche||x.service,sub?1000:110,sub?52:78,Math.min(smooth((f-30)/10),smooth((130-f)/10)))}
 if(x.geste&&f>=200&&f<320){title(ctx,x.geste,1000,52,Math.min(smooth((f-200)/10),smooth((320-f)/10)),3,'DMSans','#fff')}
 if(f>=336&&f<413){if(!sub)shade(ctx,0,400);title(ctx,x.service,sub?1000:110,sub?52:78,Math.min(smooth((f-336)/12),smooth((413-f)/10)))}
 if(f>=538&&f<596){if(!sub)shade(ctx,0,400);title(ctx,x.detail,sub?1000:110,sub?52:76,Math.min(smooth((f-538)/10),smooth((596-f)/10)))}
 if(f>=755){let q=smooth((f-755)/20),actions={appeler:'Appelez-nous.',ecrire:'Écrivez-nous.',commande:'Passez commande.',rendez_vous:'Prenez rendez-vous.',conseil:'Demandez conseil.',essai:'Demandez un essai.',visite:'Passez nous voir.',devis:'Demandez un devis.',aucune:''};let action=actions[x.action]||'';if(action)title(ctx,action,850,58,q,2,'DMSans','#fff');let signature=[x.nom,x.lieu,x.prix,x.telephone,x.cible].filter(Boolean).join(' · ');if(signature){let g=ctx.createLinearGradient(0,950,0,1280);g.addColorStop(0,'rgba(22,7,15,0)');g.addColorStop(1,'rgba(22,7,15,.75)');ctx.fillStyle=g;ctx.fillRect(0,950,W,330);title(ctx,signature,1010,28,q,5,'DMSans')}}
 if(sub){shade(ctx,0,320);title(ctx,sub.text,84,39,1,3,'DMSans','#fff')}
}

self.onmessage=async({data})=>{const media=[];let out;try{
 await Promise.all([font('Cormorant','CormorantGaramond.ttf'),font('DMSans','DMSans.ttf')]);
 if(!self.VideoEncoder||!self.VideoDecoder||!self.OffscreenCanvas)throw Error('Ce navigateur ne prend pas en charge le montage local. Essaie Chrome ou Edge récent.');
 let codec='avc1.420020',support=await VideoEncoder.isConfigSupported({codec,width:W,height:H,framerate:30,bitrate:5200000,avc:{format:'avc'}});if(!support.supported)throw Error('Encodage H.264 indisponible sur cet appareil.');
 const c=data.contrat;if(c?.schema!==2||c.media.fps!==FPS||c.media.duree_mode!=='variable')throw Error('Contrat incompatible avec le moteur.');const views={};for(let i=0;i<4;i++){let file=data.files[ids[i]];if(!(file instanceof Blob)||!file.size||file.size>48*1024*1024)throw Error('Prise '+ids[i]+' absente ou trop lourde.');let m=new Input({source:new BlobSource(file),formats:[MP4,QTFF,WEBM]});media.push(m);let video=await m.getPrimaryVideoTrack();if(!video||!await video.canDecode())throw Error('Prise '+ids[i]+' illisible.');let start=await video.getFirstTimestamp(),end=await video.computeDuration();let count=data.frames?.[i];if(!Number.isInteger(count)||count<c.prises[ids[i]].secondes_min*FPS||count>c.prises[ids[i]].secondes*FPS||end-start+0.001<count/FPS||end-start>c.prises[ids[i]].secondes+c.duree_regles.maximum_images_supplementaires/FPS+.00001)throw Error('Durée de la prise '+ids[i]+' invalide.');views[ids[i]]={video,start}}
 let total=0;const oldStarts=[0,152,521,727],oldLengths=[152,369,206,173];const segments=ids.map((id,i)=>{let a=total,b=total+=data.frames[i];return {a,b,oldStart:oldStarts[i],oldLength:oldLengths[i],refs:[[id,f=>f-a]]}});const N=total;if(N>c.media.images_max)throw Error('Montage trop long.');
 const canvas=new OffscreenCanvas(W,H),ctx=canvas.getContext('2d',{alpha:false});ctx.imageSmoothingEnabled=true;
 let target=new BufferTarget();out=new Output({format:new Mp4OutputFormat({fastStart:'in-memory'}),target});let vs=new CanvasSource(canvas,{codec:'avc',fullCodecString:codec,bitrate:5200000,keyFrameInterval:2,latencyMode:'quality'});out.addVideoTrack(vs,{frameRate:30});let as;if(data.audio){registerAacEncoder();as=new AudioSampleSource({codec:'aac',bitrate:160000});out.addAudioTrack(as)}out.setMetadataTags({title:'BEAUTE-T4',comment:data.credit||'Contrôle muet'});await out.start();let n=0, audioPos=0;
 for(const seg of segments){let streams=seg.refs.map(([id,func])=>{let {video,start}=views[id];let times=function*(){for(let f=seg.a;f<seg.b;f++)yield start+(func(f)+.18)/30};return new VideoSampleSink(video).samplesAtTimestamps(times())[Symbol.asyncIterator]()});try{for(let f=seg.a;f<seg.b;f++){let rows=await Promise.all(streams.map(i=>i.next()));let samples=rows.map(v=>v.value);try{if(rows.some(r=>r.done||!r.value))throw Error('Une image de prise manque au montage.');artwork(f,ctx,samples,data.fiche,data.subtitles,seg);await vs.add(f/30,1/30)}finally{samples.forEach(s=>s?.close())}n++;if(n%30===0){if(as){let end=Math.min(data.audio.left.length,n*1600);while(audioPos<end){let len=Math.min(48000,end-audioPos),p=new Float32Array(len*2);p.set(data.audio.left.subarray(audioPos,audioPos+len),0);p.set(data.audio.right.subarray(audioPos,audioPos+len),len);let a=new AudioSample({format:'f32-planar',sampleRate:48000,numberOfChannels:2,timestamp:audioPos/48000,data:p});await as.add(a);a.close();audioPos+=len}}self.postMessage({stage:'encode',completed:n,total:N})}}}finally{await Promise.allSettled(streams.map(i=>i.return?.()))}}
 if(as&&audioPos<data.audio.left.length){let len=data.audio.left.length-audioPos,p=new Float32Array(len*2);p.set(data.audio.left.subarray(audioPos),0);p.set(data.audio.right.subarray(audioPos),len);let a=new AudioSample({format:'f32-planar',sampleRate:48000,numberOfChannels:2,timestamp:audioPos/48000,data:p});await as.add(a);a.close()}vs.close();as?.close();await out.finalize();if(n!==N||!target.buffer||target.buffer.byteLength<15000)throw Error('Export incomplet.');self.postMessage({stage:'done',buffer:target.buffer},[target.buffer]);
 }catch(e){if(out)await out.cancel().catch(()=>{});self.postMessage({stage:'error',message:e?.message||'Le montage a échoué.'})}finally{media.forEach(m=>m.dispose())}};
