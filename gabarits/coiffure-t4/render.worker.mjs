import {registerAacEncoder} from './vendor/mediabunny-aac-encoder.min.mjs';
import {BufferTarget,CanvasSource,Mp4OutputFormat,Output,VideoSampleSink,BlobSource,Input,MP4,QTFF,WEBM,AudioSampleSource,AudioSample} from './vendor/mediabunny-1.66.1.min.mjs';
const W=720,H=1280,FPS=30,N=900,ids=['S1','S2','S3','S4'],dur=[6,13,8,7];
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
function artwork(f,ctx,s,x,subs){
 const z=(f>=376&&f<408)?1.10:(f>=226&&f<256)?1+.045*smooth((f-226)/30):1;
 pc.clearRect(0,0,W,H);panel(pc,s[0],z);ctx.drawImage(plate,0,0);
 if(f<66){let q=smooth(f/65),reach=q*1050;ctx.save();ctx.fillStyle=`rgba(28,8,21,${.83*(1-q)})`;ctx.fillRect(0,0,W,H);ctx.beginPath();ctx.moveTo(360,640);ctx.lineTo(360-reach,640-reach);ctx.lineTo(360+reach,640-reach);ctx.closePath();ctx.moveTo(360,640);ctx.lineTo(360-reach,640+reach);ctx.lineTo(360+reach,640+reach);ctx.closePath();ctx.clip();ctx.drawImage(plate,0,0);ctx.restore()}
 if(f>=82&&f<94){let arr=[[0,212],[212,373],[373,682],[682,855],[855,H]];for(let i=0;i<arr.length;i++){let [t,b]=arr[i],dx=(i%2?-1:1)*(12+Math.round(15*Math.sin(f*.8+i)));ctx.save();ctx.beginPath();ctx.rect(0,t,W,b-t);ctx.clip();ctx.drawImage(plate,dx,0);ctx.restore()}}
 if(f>=145&&f<158)leak(ctx,f,145,158,.50);
 if(f===196)hc.drawImage(plate,0,0);
 if(f>=197&&f<213){let q=smooth((f-197)/15);ctx.drawImage(held,0,0);for(let [t,b,d] of [[0,251,0],[251,505,.13],[505,734,.23],[734,991,.35],[991,H,.45]]){let h=Math.round((b-t)*smooth((q-d)/.55));if(h>0)ctx.drawImage(plate,0,t,W,h,0,t,W,h)}}
 if(f>=226&&f<256){let q=(f-226)/30;ctx.fillStyle=`rgba(22,11,25,${.22*Math.sin(Math.PI*q)**2})`;ctx.fillRect(0,0,W,H)}
 if(f>=282&&f<300){let x=-400+1600*smooth((f-282)/18);ctx.fillStyle='rgba(43,8,33,.48)';ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(x,0);ctx.lineTo(x-360,H);ctx.lineTo(0,H);ctx.closePath();ctx.fill()}
 if(f>=322&&f<342)leak(ctx,f,322,342,.30);
 if(f>=488&&f<521){ctx.drawImage(plate,0,210,W,640,0,0,W,640);ctx.drawImage(plate,0,210,W,640,0,640,W,640)}
 if(f===726)lc.drawImage(plate,0,0);
 if(f>=727&&f<755){let q=smooth((f-727)/28),edge=W*(1-q)*1.7-260;ctx.drawImage(last,0,0);ctx.save();ctx.beginPath();ctx.moveTo(edge,0);ctx.lineTo(W,0);ctx.lineTo(W,H);ctx.lineTo(edge-.23*H,H);ctx.closePath();ctx.clip();ctx.drawImage(plate,0,0);ctx.restore()}
 if(f>=30&&f<130){shade(ctx,0,400);title(ctx,x.accroche||x.service,110,78,Math.min(smooth((f-30)/10),smooth((130-f)/10)))}
 if(f>=336&&f<413){shade(ctx,0,400);title(ctx,x.service,110,78,Math.min(smooth((f-336)/12),smooth((413-f)/10)))}
 if(f>=538&&f<596){shade(ctx,0,400);title(ctx,x.detail,110,76,Math.min(smooth((f-538)/10),smooth((596-f)/10)))}
 if(f>=755){let q=smooth((f-755)/20),actions={conseil:'Demandez conseil.',essai:'Demandez un essai.',commande:'Passez commande.',rendez_vous:'Prenez rendez-vous.',visite:'Passez nous voir.',devis:'Demandez un devis.',aucune:''};shade(ctx,0,400);title(ctx,actions[x.action]||x.service,110,78,q);let signature=[x.nom,x.lieu,x.prix,x.cible].filter(Boolean).join(' · ');if(signature){let g=ctx.createLinearGradient(0,950,0,1280);g.addColorStop(0,'rgba(22,7,15,0)');g.addColorStop(1,'rgba(22,7,15,.75)');ctx.fillStyle=g;ctx.fillRect(0,950,W,330);title(ctx,signature,1010,28,q,5,'DMSans')}if(f>=886){ctx.fillStyle=`rgba(0,0,0,${smooth((f-886)/14)})`;ctx.fillRect(0,0,W,H)}}
 let sub=(subs||[]).find(z=>f/FPS>=z.start&&f/FPS<z.end);if(sub){ctx.fillStyle='rgba(15,8,10,.65)';ctx.fillRect(40,850,640,125);title(ctx,sub.text,868,36,1,2,'DMSans','#fff')}
}
const segments=[{a:0,b:152,refs:[['S1',f=>f]]},{a:152,b:521,refs:[['S2',f=>f-152]]},{a:521,b:727,refs:[['S3',f=>f-521]]},{a:727,b:900,refs:[['S4',f=>f-727]]}];
self.onmessage=async({data})=>{const media=[];let out;try{
 await Promise.all([font('Cormorant','CormorantGaramond.ttf'),font('DMSans','DMSans.ttf')]);
 if(!self.VideoEncoder||!self.VideoDecoder||!self.OffscreenCanvas)throw Error('Ce navigateur ne prend pas en charge le montage local. Essaie Chrome ou Edge récent.');
 let codec='avc1.420020',support=await VideoEncoder.isConfigSupported({codec,width:W,height:H,framerate:30,bitrate:5200000,avc:{format:'avc'}});if(!support.supported)throw Error('Encodage H.264 indisponible sur cet appareil.');
 const views={};for(let i=0;i<4;i++){let file=data.files[ids[i]];if(!(file instanceof Blob)||!file.size||file.size>48*1024*1024)throw Error('Prise '+ids[i]+' absente ou trop lourde.');let m=new Input({source:new BlobSource(file),formats:[MP4,QTFF,WEBM]});media.push(m);let video=await m.getPrimaryVideoTrack();if(!video||!await video.canDecode())throw Error('Prise '+ids[i]+' illisible.');let start=await video.getFirstTimestamp(),end=await video.computeDuration();if(end-start<dur[i]-.05)throw Error('Prise '+ids[i]+' trop courte.');views[ids[i]]={video,start}}
 const canvas=new OffscreenCanvas(W,H),ctx=canvas.getContext('2d',{alpha:false});ctx.imageSmoothingEnabled=true;
 let target=new BufferTarget();out=new Output({format:new Mp4OutputFormat({fastStart:'in-memory'}),target});let vs=new CanvasSource(canvas,{codec:'avc',fullCodecString:codec,bitrate:5200000,keyFrameInterval:2,latencyMode:'quality'});out.addVideoTrack(vs,{frameRate:30});let as;if(data.audio){registerAacEncoder();as=new AudioSampleSource({codec:'aac',bitrate:160000});out.addAudioTrack(as)}out.setMetadataTags({title:'BEAUTE-T4',comment:data.credit||'Contrôle muet'});await out.start();let n=0, audioPos=0;
 for(const seg of segments){let streams=seg.refs.map(([id,func])=>{let {video,start}=views[id];let times=function*(){for(let f=seg.a;f<seg.b;f++)yield start+(func(f)+.18)/30};return new VideoSampleSink(video).samplesAtTimestamps(times())[Symbol.asyncIterator]()});try{for(let f=seg.a;f<seg.b;f++){let rows=await Promise.all(streams.map(i=>i.next()));let samples=rows.map(v=>v.value);try{if(rows.some(r=>r.done||!r.value))throw Error('Une image de prise manque au montage.');artwork(f,ctx,samples,data.fiche,data.subtitles);await vs.add(f/30,1/30)}finally{samples.forEach(s=>s?.close())}n++;if(n%30===0){if(as){let end=Math.min(data.audio.left.length,n*1600);while(audioPos<end){let len=Math.min(48000,end-audioPos),p=new Float32Array(len*2);p.set(data.audio.left.subarray(audioPos,audioPos+len),0);p.set(data.audio.right.subarray(audioPos,audioPos+len),len);let a=new AudioSample({format:'f32-planar',sampleRate:48000,numberOfChannels:2,timestamp:audioPos/48000,data:p});await as.add(a);a.close();audioPos+=len}}self.postMessage({stage:'encode',completed:n,total:N})}}}finally{await Promise.allSettled(streams.map(i=>i.return?.()))}}
 vs.close();as?.close();await out.finalize();if(n!==900||!target.buffer||target.buffer.byteLength<15000)throw Error('Export incomplet.');self.postMessage({stage:'done',buffer:target.buffer},[target.buffer]);
 }catch(e){if(out)await out.cancel().catch(()=>{});self.postMessage({stage:'error',message:e?.message||'Le montage a échoué.'})}finally{media.forEach(m=>m.dispose())}};
