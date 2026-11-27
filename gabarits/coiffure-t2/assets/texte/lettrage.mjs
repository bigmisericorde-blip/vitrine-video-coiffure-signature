// Sous-titres gravés dans le MP4. Le Worker charge les deux polices vérifiées avant de peindre.
export const W=720,H=1280;
export const SUBTITLE_FAMILY='VVDancingScript';
const SIGNATURE_FAMILY='VVLecture';

export async function lettrageFonts(script,sans){
  const set=globalThis.document?.fonts||globalThis.fonts;
  if(!set||!(script instanceof ArrayBuffer)||!(sans instanceof ArrayBuffer))throw Error('Polices locales attendues.');
  const faces=[new FontFace(SUBTITLE_FAMILY,script,{weight:'400 700'}),new FontFace(SIGNATURE_FAMILY,sans,{weight:'400 800'})];
  await Promise.all(faces.map(face=>face.load()));
  for(const face of faces)set.add(face);
}

// On garde la cascade de l’accroche, les repères du montage et le carton de fin.
// Les zones de lecture restent en retrait des bords ; les lignes variables peuvent se répartir sur deux rangées.
const SLOTS={
  i0:{x:72,bottom:1086,s:104,max:470,maxh:82,rise:79},
  i1:{x:242,bottom:1156,s:89,max:372,maxh:66,rise:60},
  i2:{right:277,bottom:1225,s:62,max:170,maxh:47,rise:45},
  i3:{x:289,bottom:1225,s:95,max:346,maxh:62,rise:49},
  single:{x:74,y:1053,s:76,max:564,maxh:117,rise:45,wrap:true},
  upper:{x:74,y:1019,s:68,max:564,maxh:77,rise:38},
  lower:{x:111,y:1112,s:62,max:526,maxh:100,rise:31,wrap:true},
  close:{x:74,y:1053,s:73,max:564,maxh:80,rise:40},
  closeWithNumber:{x:74,y:1000,s:68,max:564,maxh:76,rise:40},
  credit0:{x:78,y:1112,s:30,max:525,maxh:28,rise:12},
  credit1:{x:78,y:1147,s:31,max:525,maxh:30,rise:13},
  credit2:{x:78,y:1186,s:32,max:525,maxh:30,rise:12},
};

function layerCanvas(w,h){
  if(typeof OffscreenCanvas!=='undefined')return new OffscreenCanvas(w,h);
  return Object.assign(document.createElement('canvas'),{width:w,height:h});
}
function font(size,info,secondary){
  return `${info?720:secondary?650:700} ${size}px ${info?SIGNATURE_FAMILY:SUBTITLE_FAMILY}`;
}
function measure(ctx,lines,size,info,secondary){
  ctx.font=font(size,info,secondary);ctx.textBaseline='alphabetic';
  const gap=Math.ceil(size*.14), rows=[];let y=0,w=0;
  for(const text of lines){
    const m=ctx.measureText(text), width=Math.max(1,m.actualBoundingBoxLeft+m.actualBoundingBoxRight);
    const h=Math.max(1,m.actualBoundingBoxAscent+m.actualBoundingBoxDescent);
    rows.push({text,y,asc:m.actualBoundingBoxAscent,left:m.actualBoundingBoxLeft});w=Math.max(w,width);y+=h+gap;
  }
  return {size,rows,w,h:y-gap};
}
function fit(ctx,text,slot,info,secondary){
  const M=(lines,size)=>measure(ctx,lines,size,info,secondary);
  const search=lines=>{
    let lo=1,hi=2*slot.s;
    while(lo<hi){
      const mid=Math.ceil((lo+hi)/2),m=M(lines,mid/2);
      if(m.w<=slot.max&&m.h<=slot.maxh)lo=mid;else hi=mid-1;
    }
    return M(lines,lo/2);
  };
  let best=search([text]);
  if(!slot.wrap||best.size>=slot.s*.91)return best;
  const words=text.split(' ');
  for(let i=1;i<words.length;i++){
    const next=search([words.slice(0,i).join(' '),words.slice(i).join(' ')]);
    if(next.size>best.size+1)best=next;
  }
  return best;
}
function sprite(text,slot,info,intro,secondary,motion){
  // La casse originale préserve les liaisons de la cursive, notamment dans la saisie utilisateur.
  const m=fit(layerCanvas(2,2).getContext('2d'),text,slot,info,secondary);
  const x=slot.right?slot.right-Math.ceil(m.w):slot.x,y=slot.bottom?slot.bottom-m.h:slot.y;
  const pad=22,cw=Math.ceil(m.w+pad*2+10),ch=Math.ceil(m.h+pad*2+10);
  const puff=intro?Math.min(1.35,m.size*.022):0;
  const paint=(extra)=>{
    const c=layerCanvas(cw,ch),ctx=c.getContext('2d');
    ctx.font=font(m.size,info,secondary);ctx.textBaseline='alphabetic';ctx.lineJoin='round';ctx.lineCap='round';
    const outline=info?3.1:Math.max(3,Math.min(6,m.size*.076));
    for(const row of m.rows){
      const X=pad+row.left,Y=pad+row.y+row.asc;
      ctx.shadowBlur=info?4:6.5;ctx.shadowColor='rgba(20,17,26,.76)';ctx.shadowOffsetY=2.4;
      ctx.lineWidth=outline+2*extra;ctx.strokeStyle=info?'#31292f':'rgba(33,26,39,.91)';ctx.strokeText(row.text,X,Y);
      ctx.shadowColor='transparent';
      ctx.fillStyle=info?'#fffdf8':secondary?'#fff8ec':'#fff4dc';
      if(extra>.01){ctx.lineWidth=2*extra;ctx.strokeStyle=ctx.fillStyle;ctx.strokeText(row.text,X,Y);}
      ctx.fillText(row.text,X,Y);
    }
    return c;
  };
  const n=Math.max(2,motion.entryFrames);
  const frames=intro?Array.from({length:n},(_,i)=>paint(puff*(1-i/(n-1))**1.25)):[paint(0)];
  return {frames,x,y,sx:1,sy:1,w:m.w,h:m.h,size:m.size,pad,rise:slot.rise,puff,lines:m.rows.map(r=>r.text)};
}

export function prepareCaptions(plan){
  return plan.captions.map(item=>{
    const slot=SLOTS[item.slot];if(!slot)throw Error('Placement inconnu.');
    const info=item.role==='info';
    const v=sprite(item.text,slot,info,item.role==='intro',item.slot==='lower',plan.animation);
    return {...item,...v,family:info?SIGNATURE_FAMILY:SUBTITLE_FAMILY,motion:plan.animation,ink:[Math.round(v.x),Math.round(v.y),Math.ceil(v.w+6),Math.ceil(v.h+8)]};
  });
}
export function poseCaption(a,n){
  if(n<a.on||n>=a.off)return null;
  const intro=a.role==='intro',steps=Math.max(2,a.motion.entryFrames);
  const index=Math.min(steps-1,n-a.on),u=index/(steps-1),still=1-u;
  const bulge=intro?1+Math.min(.11,a.motion.chiselFrom-1)*still**1.35:1;
  const edge=a.puff*still**1.25;
  return {index,horizontal:bulge,vertical:intro?.91+.09*u:1,drop:a.rise*still**2.1,edge,
    alpha:(.49+.51*Math.sin(u*Math.PI/2))*(a.off===900?1:Math.min(1,(a.off-n)/a.motion.releaseFrames))};
}
export function makePoses(items,n){
  const placed=[];
  for(const a of items){
    const p=poseCaption(a,n);if(!p)continue;
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
