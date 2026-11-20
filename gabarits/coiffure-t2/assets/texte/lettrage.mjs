// Lettrage ballon : peinture partagée par l’atelier interactif et l’export 30 i/s.
export const W=720,H=1280;
const SCRIPT='VVChewy', SANS='VVLecture';
export async function lettrageFonts(script,sans){
  for(const [name,bin,other] of [[SCRIPT,script,{}],[SANS,sans,{weight:'400 800'}]]){
    const face=new FontFace(name,typeof bin==='string'?`url(${JSON.stringify(bin)})`:bin,other);
    await face.load(); (globalThis.document?.fonts||globalThis.fonts).add(face);
  }
}
const SLOTS={
  i0:{x:72 ,bottom:1086,s:110,max:470,maxh:80,thin:.99,rise:79},
  i1:{x:251,bottom:1156,s:93,max:346,maxh:64,thin:.97,rise:60},
  i2:{right:274,bottom:1227,s:54,max:164,maxh:46,thin:.96,rise:45},
  i3:{x:293,bottom:1226,s:94,max:324,maxh:60,thin:.98,rise:49},
  single:{x:74,y:1069,s:88,max:534,maxh:91,thin:.96,rise:45},
  upper:{x:74,y:1019,s:78,max:534,maxh:76,thin:.96,rise:38},
  lower:{x:117,y:1113,s:85,max:485,maxh:88,thin:.95,rise:31},
  close:{x:74,y:1053,s:85,max:534,maxh:80,thin:.97,rise:40},
  credit1:{x:78,y:1147,s:31,max:525,maxh:30,thin:1,rise:13},
  credit2:{x:78,y:1186,s:32,max:525,maxh:30,thin:1,rise:12},
};
const font=(s,info)=>info?`720 ${s}px ${SANS}`:`${s}px ${SCRIPT}`;
function layerCanvas(w,h){
  if(typeof OffscreenCanvas!=='undefined')return new OffscreenCanvas(w,h);
  return Object.assign(document.createElement('canvas'),{width:w,height:h});
}
function metrics(ctx,t,s,info){
  ctx.font=font(s,info);ctx.textBaseline='alphabetic';const m=ctx.measureText(t);
  return {w:Math.max(1,m.actualBoundingBoxLeft+m.actualBoundingBoxRight),h:Math.max(1,m.actualBoundingBoxAscent+m.actualBoundingBoxDescent),l:m.actualBoundingBoxLeft,a:m.actualBoundingBoxAscent};
}
function shape(c,mask,radius){
  // Distance intérieure suivie d’un modelé local. La lumière suit les courbes des glyphes
  // (y compris les accents), pas un dégradé plat appliqué au mot entier.
  const w=c.width,h=c.height,src=mask.getImageData(0,0,w,h),px=src.data,dist=new Float32Array(w*h);
  for(let i=0;i<dist.length;i++)dist[i]=px[i*4+3]>=128?1000:0;
  for(let y=1;y<h;y++)for(let x=1;x<w-1;x++){
    const i=y*w+x;if(!dist[i])continue;
    dist[i]=Math.min(dist[i],dist[i-1]+1,dist[i-w]+1,dist[i-w-1]+1.42,dist[i-w+1]+1.42);
  }
  for(let y=h-2;y>=0;y--)for(let x=w-2;x>=1;x--){
    const i=y*w+x;if(!dist[i])continue;
    dist[i]=Math.min(dist[i],dist[i+1]+1,dist[i+w]+1,dist[i+w+1]+1.42,dist[i+w-1]+1.42);
  }
  for(let y=1;y<h-1;y++)for(let x=1;x<w-1;x++){
    const i=y*w+x,j=4*i;if(!px[j+3])continue;
    const d=Math.min(1,dist[i]/radius),gx=(dist[i+1]-dist[i-1])*.5,gy=(dist[i+w]-dist[i-w])*.5;
    const facing=Math.max(-1,Math.min(1,gx*.53+gy*.71));
    const bevel=1-Math.sin(d*Math.PI/2),sheen=Math.exp(-(((d-.41)*5.5)**2));
    const b=247 + (facing*.23-.33)*bevel*101 + Math.max(0,facing)*sheen*13 + (7/h)*(h*.5-y);
    px[j]=b+2;px[j+1]=b+1;px[j+2]=b+Math.max(1,-facing*5);
  }
  mask.putImageData(src,0,0);
}
function sprite(original,slot,info,intro,motion){
  const t=info?original:original.toLocaleUpperCase('fr');
  const ref=layerCanvas(2,2).getContext('2d');let sz=slot.s,m=metrics(ref,t,sz,info);
  const sy=info?1:1.18;
  if(m.h*sy>slot.maxh)sz*=slot.maxh/(m.h*sy);
  m=metrics(ref,t,sz,info);
  if(m.w*(info?1:.79)>slot.max){sz*=slot.max/(m.w*(info?1:.79));m=metrics(ref,t,sz,info);}
  const sx=Math.min(slot.thin,slot.max/m.w),w=m.w*sx,h=m.h*sy;
  const x=slot.right?slot.right-Math.ceil(w):slot.x,y=slot.bottom?slot.bottom-h:slot.y;
  const pad=23,cw=Math.ceil(m.w+pad*2+11),ch=Math.ceil(m.h+pad*2+12),X=pad+m.l,Y=pad+m.a;
  const puff=intro?Math.min(5.5,sz*.068):0;
  const paint=(radius)=>{
    const c=layerCanvas(cw,ch),ctx=c.getContext('2d');
    ctx.font=font(sz,info);ctx.textBaseline='alphabetic';ctx.lineJoin='round';ctx.lineCap='round';
    if(info){
      ctx.shadowBlur=4;ctx.shadowColor='rgba(17,13,23,.82)';ctx.shadowOffsetY=2;
      ctx.lineWidth=3.1;ctx.strokeStyle='#31292f';ctx.strokeText(t,X,Y);
      ctx.shadowColor='transparent';ctx.fillStyle='#fffdf8';ctx.fillText(t,X,Y);return c;
    }
    ctx.shadowBlur=7.5;ctx.shadowColor='rgba(22,16,28,.66)';ctx.shadowOffsetY=2.7;ctx.shadowOffsetX=1;
    ctx.lineWidth=2.7+2*radius;ctx.strokeStyle='#6e6271';ctx.strokeText(t,X+1.65,Y+3.45);ctx.shadowColor='transparent';
    ctx.lineWidth=1.6+2*radius;ctx.strokeStyle='#a7a0ac';ctx.fillStyle='#a7a0ac';
    for(let i=4;i>0;i--){ctx.strokeText(t,X+i*.46,Y+i*.8);ctx.fillText(t,X+i*.46,Y+i*.8);}
    const s=layerCanvas(cw,ch),mask=s.getContext('2d',{willReadFrequently:true});
    mask.font=font(sz,false);mask.textBaseline='alphabetic';mask.lineJoin='round';mask.lineCap='round';
    if(radius>.05){mask.lineWidth=2*radius;mask.strokeText(t,X,Y);}mask.fillText(t,X,Y);
    shape(s,mask,Math.max(4.8,Math.min(12.5,sz*.112+radius*.52)));ctx.drawImage(s,0,0);
    return c;
  };
  return {frames:intro?Array.from({length:motion.entryFrames},(_,i)=>paint(puff*(1-i/(motion.entryFrames-1))**1.25)):[paint(0)],x,y,sx,sy,w,h,size:sz,pad,rise:slot.rise,puff};
}
export function prepareCaptions(plan){
  return plan.captions.map(item=>{
    const slot=SLOTS[item.slot];if(!slot)throw Error('Placement inconnu.');
    const v=sprite(item.text,slot,item.role==='info',item.role==='intro',plan.animation);
    return {...item,...v,motion:plan.animation,ink:[Math.round(v.x),Math.round(v.y),Math.ceil(v.w+6),Math.ceil(v.h+8)]};
  });
}
export function poseCaption(a,n){
  if(n<a.on||n>=a.off)return null;
  const intro=a.role==='intro', index=Math.min(a.motion.entryFrames-1,n-a.on),u=index/(a.motion.entryFrames-1),still=1-u;
  const bulge=intro?1+(a.motion.chiselFrom-1)*still**1.35:1;
  const edge=a.puff*still**1.25;
  // On conserve la respiration des lignes étagées. Si un groupe long empiète
  // horizontalement, la chute est plafonnée au moment de la peinture.
  return {index,horizontal:bulge,vertical:intro?.89+.11*u:1,drop:a.rise*still**2.1,edge,
    alpha:(.49+.51*Math.sin(u*Math.PI/2))*(a.off===900?1:Math.min(1,(a.off-n)/a.motion.releaseFrames))};
}
export function makePoses(items,n){
  const placed=[];
  for(const a of items){
    const p=poseCaption(a,n);if(!p)continue;
    // Le gonflement initial ne peut pas déborder de la zone de lecture à droite.
    const sx=Math.min(a.sx*p.horizontal,(680-a.x)/(a.w/a.sx+2*p.edge+6)),sy=a.sy*p.vertical;
    const left=a.x-p.edge*sx,right=a.x+(a.w/a.sx+p.edge+3)*sx;
    let y=a.y-p.drop;
    for(const b of placed){
      const overlap=Math.min(right,b.right)-Math.max(left,b.left);
      if(overlap>8&&a.y>b.a.y+16)y=Math.max(y,Math.min(a.y,b.bottom+5+p.edge*sy));
    }
    placed.push({...p,a,x:a.x,y,sx,sy,left,right,top:y-p.edge*sy,bottom:y+(a.h/a.sy+p.edge+5)*sy});
  }
  return placed;
}
export function drawCaptions(ctx,items,n){
  const placed=makePoses(items,n);
  for(const {a,sx,sy,x,y,alpha,index} of placed){
    const sprite=a.frames[index]||a.frames[0];
    ctx.globalAlpha=alpha;
    ctx.drawImage(sprite,x-a.pad*sx,y-a.pad*sy,sprite.width*sx,sprite.height*sy);
  }
  ctx.globalAlpha=1;
  return placed.length;
}
