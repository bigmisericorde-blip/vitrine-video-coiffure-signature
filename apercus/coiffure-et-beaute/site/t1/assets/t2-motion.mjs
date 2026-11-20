/* T2 : la timeline et les paramètres de coupe viennent de ingenierie/plan.json.
   Chaque composition est peinte dans le canevas transmis à l’encodeur, pas dans le DOM. */
const clamp = t => Math.min(1,Math.max(0,t));
const ease = t => 1-(1-clamp(t))**3;
const smooth = t => (t=clamp(t),t*t*(3-2*t));
const mix = (a,b,t) => a+(b-a)*t;
export const sourceFrame = (shot, frame) => shot.src+Math.floor((frame-shot.in)*shot.speed);
export const W=720, H=1280;

export async function loadFonts(fonts) {
  await Promise.all([
    ['T2Script','fonts-t2/PinyonScript-Regular.ttf'],
    ['T2Serif','fonts-t2/DMSerifDisplay-Regular.ttf'],
    ['T2Sans','PlusJakartaSans-Variable.ttf','200 800'],
  ].map(async ([name,file,weight]) => {
    const url=new URL(file,import.meta.url).href;
    const face=await new FontFace(name,`url(${url})`,{weight:weight||'400'}).load();
    fonts.add(face);
  }));
}

export function createMotion(canvas,plan,job,{demo=false}={}) {
  const g=canvas.getContext('2d',{alpha:false});
  const previous=new OffscreenCanvas(W,H), prev=previous.getContext('2d',{alpha:false});
  const p=plan.design.palette, safe=plan.design.safe;
  const left=safe[0], right=safe[2], width=right-left, mid=(left+right)/2;
  const ivory='#fff5df', gold='#dbc393', goldDark='#877348';
  const cuts=new Map(plan.cuts.map(x=>[x.at,x]));
  const stage=Object.fromEntries(plan.shots.map(x=>[x.stage,x.in]));
  const font={script:'"T2Script", Georgia, serif',serif:'"T2Serif", Georgia, serif',sans:'"T2Sans", system-ui, sans-serif'};
  const stored=new Map();
  g.imageSmoothingQuality='high';
  function color(c,x,y,w,h) {g.fillStyle=c;g.fillRect(x,y,w,h);}
  function line(c,x,y,w){color(c,x,y,w,1.5);}
  function round(fill,x,y,w,h,r,stroke){
    g.beginPath();g.roundRect(x,y,w,h,Math.min(r,w/2,h/2));
    g.fillStyle=fill;g.fill();
    if(stroke){g.strokeStyle=stroke;g.lineWidth=1;g.stroke();}
  }
  function layout(value,face,size,max,maxLines) {
    const k=JSON.stringify([value,face,size,max,maxLines]);
    if(stored.has(k))return stored.get(k);
    const weight=face==='sans'?650:400;
    let lines=[value], n=size;
    function arrange() {
      g.font=`${weight} ${n}px ${font[face]}`;
      if(g.measureText(value).width<=max)return [value];
      const out=[]; let row='';
      for(const word of value.split(' ')) {
        if(row&&g.measureText(row+' '+word).width>max){out.push(row);row='';}
        if(g.measureText(word).width<=max){row+=(row?' ':'')+word;continue;}
        // Un contact sans espace reste entier, même lorsqu’il dépasse une ligne.
        for(const chr of Array.from(word)) {
          if(row&&g.measureText(row+chr).width>max){out.push(row);row='';}
          row+=chr;
        }
      }
      if(row)out.push(row);
      return out;
    }
    for(;n>16;n-=2){lines=arrange();if(lines.length<=maxLines)break;}
    if(n<=16){n=16;lines=arrange();}
    const css=g.font, span=Math.max(...lines.map(l=>g.measureText(l).width));
    const out={lines,css,n,span,height:Math.ceil(n*(face==='script'?0.92:1.16))};
    stored.set(k,out);return out;
  }
  function title(value,x,y,{face='serif',size=52,max=width-10,rows=1,align='left',c=ivory,t=1}={}) {
    if(!value||t<=0)return;
    const spec=layout(value,face,size,max,rows);
    g.save();g.font=spec.css;g.textBaseline='alphabetic';g.textAlign=align;
    const offset=14*(1-ease(t)), from=align==='center'?x-spec.span/2:x;
    const startY=y+offset-(spec.lines.length-1)*spec.height/2;
    if(t<1){
      g.beginPath();g.rect(from-12,startY-spec.n*1.12,(spec.span+24)*ease(t),spec.height*(spec.lines.length+1.1)+18);
      g.clip();g.globalAlpha=Math.min(1,t*3.5);
    }
    const relief=face!=='sans', shadow=face==='script'?7:5;
    for(let i=0;i<spec.lines.length;i++){
      const row=spec.lines[i], by=startY+i*spec.height;
      if(relief){
        g.lineJoin='round';g.strokeStyle='#1a211a';g.lineWidth=face==='script'?2.4:2.0;
        g.shadowColor='#000c';g.shadowBlur=shadow;g.shadowOffsetY=3.1;
        g.strokeText(row,x,by+2);
        g.shadowBlur=g.shadowOffsetY=0;
        g.fillStyle=goldDark;g.fillText(row,x+.7,by+1.9);
        const tint=g.createLinearGradient(x,by-spec.n*.69,x,by+spec.n*.16);
        tint.addColorStop(0,'#fffbf0');tint.addColorStop(.55,c);tint.addColorStop(1,gold);
        g.fillStyle=tint;
      } else {g.fillStyle=c;}
      g.fillText(row,x,by);
    }
    g.restore();
  }
  function small(s,x,y,opt={}) {title(s,x,y,{face:'sans',size:23,c:gold,max:width,...opt});}
  function backdrop() {
    const bg=g.createLinearGradient(0,0,W,H);
    bg.addColorStop(0,p.dark);bg.addColorStop(.51,p.deep);bg.addColorStop(1,p.pine);
    color(bg,0,0,W,H);
    g.strokeStyle='#dcfff313';g.lineWidth=1;
    for(let x=-640;x<W;x+=76){g.beginPath();g.moveTo(x,0);g.lineTo(x+650,H);g.stroke();}
  }
  function wash(bottom=.86) {
    const grad=g.createLinearGradient(0,0,0,H);
    grad.addColorStop(0,'rgba(3,22,21,.45)');grad.addColorStop(.26,'rgba(3,22,21,0)');
    grad.addColorStop(.46,'rgba(3,22,21,0)');grad.addColorStop(.83,`rgba(3,22,21,${bottom})`);
    grad.addColorStop(1,'#041a1b');color(grad,0,0,W,H);
  }
  function picture(sample,shot,t,x=0,y=0,w=W,h=H,radius=0) {
    const flip=sample.rotation===90||sample.rotation===270;
    const sw=flip?sample.squarePixelHeight:sample.squarePixelWidth;
    const sh=flip?sample.squarePixelWidth:sample.squarePixelHeight;
    const scale=Math.max(w/sw,h/sh)*mix(shot.zoom[0],shot.zoom[1],smooth(t));
    g.save();
    g.beginPath();g.roundRect(x,y,w,h,Math.min(radius,w/2,h/2));g.clip();
    const [cx,cy]=shot.anchor;
    if(w/h>.75&&sh/sw>1.35){
      // Un carton large ne doit pas couper les doigts, le visage ou la finition d’une prise verticale.
      color('#0a2829',x,y,w,h);
      g.save();g.globalAlpha=.48;g.filter='blur(18px)';
      const bw=sw*scale*1.16,bh=sh*scale*1.16;
      sample.draw(g,x+(w-bw)/2,y+(h-bh)/2,bw,bh);g.restore();
      const fit=Math.min(w/sw,h/sh),fw=sw*fit,fh=sh*fit;
      sample.draw(g,x+(w-fw)/2,y+(h-fh)/2,fw,fh);
    }else sample.draw(g,x-(sw*scale-w)*cx,y-(sh*scale-h)*cy,sw*scale,sh*scale);
    color('#0b3f3e0c',x,y,w,h);g.restore();
  }
  function emblem(label){
    round('#062629e8',left,safe[1],Math.min(width,31+label.length*13),44,10,'#c4ae77ac');
    small(label,left+15,safe[1]+29,{size:19});
  }
  function markPrice(f) {
    if(!job.prix||f<stage.cut||f>=stage.lockup)return;
    round('#062629ed',right-260,safe[1],260,59,13,'#dec38e80');
    title(job.prix,right-130,safe[1]+40,{face:'sans',size:29,max:228,align:'center',c:ivory});
  }
  const reveal=(f,start,n=19)=>clamp((f-start)/n);
  function compose(sample,shot,f) {
    const dt=f-shot.in,t=dt/Math.max(1,shot.out-shot.in-1), name=shot.stage;
    if(name==='hook'){
      picture(sample,shot,t);wash(.89);emblem('01  /  AVANT');
      const at=plan.design.motion.hook_ease;
      const a=reveal(f,1,at+7);
      if(a>0)line(gold,left+width*.35,825,width*.30*ease(a));
      title(job.salon,mid,937,{face:'script',size:116,max:width-26,rows:2,align:'center',t:a});
      title(job.service,mid,1042,{size:52,rows:2,max:width-20,align:'center',t:reveal(f,10,at+6)});
      small(job.ville,mid,1108,{align:'center',max:width-35,t:reveal(f,17,17)});
    } else if(name==='offer'){
      const a=smooth((dt+1)/cuts.get(shot.in).frames);
      backdrop();picture(sample,shot,t,mix(0,left,a),mix(0,165,a),mix(W,width,a),mix(H,607,a),26*a);
      emblem('01  /  PRESTATION');
      const x=mix(W+18,left,a), y=794+50*(1-a);
      round('#092d2b',x,y,width,298,22,'#dbc393aa');line(gold,x+25,y+28,52);
      small('LA PRESTATION',x+27,y+67,{max:width-54});
      title(job.service,x+27,y+128,{size:49,max:width-54,rows:2,t:reveal(f,shot.in+4)});
      if(job.prix)title(job.prix,x+27,y+221,{size:66,max:width-54,t:reveal(f,shot.in+11)});
      small(job.ville,x+27,y+265,{max:width-54,t:reveal(f,shot.in+19)});
    } else if(name==='booking'){
      backdrop(); const a=smooth((dt+1)/cuts.get(shot.in).frames);
      emblem('04  /  APRÈS');markPrice(f);
      picture(sample,shot,t,left,227,width,624,23);
      const y=mix(982,862,a);
      round('#082e2a',left,y,width,234,17,'#d8c2927a');
      small(job.ville,left+26,y+46,{max:width-52});
      title(job.cta||job.service,left+26,y+107,{size:51,max:width-52,rows:2,t:reveal(f,shot.in+2)});
      const dot=dt/(shot.out-shot.in)>plan.design.motion.booking_select_at;
      line(dot?gold:p.light,left+27,y+141,80);
      title(job.contact||job.service,left+26,y+190,{face:'sans',size:25,max:width-52,rows:2,c:p.mint,t:reveal(f,shot.in+11)});
    } else if(name==='lockup'){
      backdrop();picture(sample,shot,t,0,0,W,618);
      color(gold,0,617,W,2);emblem('04  /  APRÈS');
      title(job.salon,mid,743,{face:'script',size:102,max:width-22,rows:2,align:'center'});
      title(job.service,mid,821,{size:47,max:width-20,rows:2,align:'center'});
      small([job.ville,job.prix].filter(Boolean).join('  ·  '),mid,883,{size:24,max:width-25,align:'center',rows:2});
      if(job.cta){
        round('#062629',left,916,width,178,18,'#dbc393a6');
        title(job.cta,mid,975,{size:39,align:'center',max:width-44});
        if(job.contact)title(job.contact,mid,1043,{face:'sans',size:25,c:p.mint,rows:3,align:'center',max:width-44});
        else line(gold,mid-34,1031,68);
      } else {line(gold,mid-35,961,70);}
      if(demo)small('PRISES D’EXEMPLE',mid,1131,{size:17,align:'center'});
    } else {
      picture(sample,shot,t);wash();
      const kind=name.startsWith('cut')?'cut':name.startsWith('detail')?'detail':name.startsWith('result')?'result':'action';
      const label={cut:'02  /  LE GESTE',detail:'03  /  LE DÉTAIL',result:'04  /  APRÈS',action:'04  /  APRÈS'}[kind];
      emblem(label);markPrice(f);
      const a=reveal(f,stage[kind]+3,22);
      line(gold,left,898,84*ease(a));
      if(kind==='action'){
        title(job.cta||job.salon,left,989,{size:61,max:width-18,rows:2,t:a});
        title(job.contact||job.ville,left,1071,{face:'sans',size:28,max:width-18,rows:3,c:p.mint,t:reveal(f,stage[kind]+14)});
      } else {
        const head=kind==='result'?'Le résultat':kind==='detail'?'Tout est dans le détail':job.service;
        title(head,left,984,{size:56,rows:2,t:a});
        const sub=kind==='result'?job.resultat:kind==='detail'?job.service:job.salon;
        title(sub,left,1069,{face:'sans',size:31,max:width-14,rows:2,c:p.mint,t:reveal(f,stage[kind]+12,23)});
      }
    }
  }
  const [ix,iy]=plan.design.motion.iris_center;
  const far=Math.hypot(Math.max(ix,W-ix),Math.max(iy,H-iy))+2;
  const irises=plan.cuts.filter(c=>c.id==='iris_vert');
  const push=plan.cuts.find(c=>c.id==='ui_push');
  return (sample,shot,f) => {
    const iris=irises.find(c=>f>=c.at-c.frames/2&&f<c.at+c.frames/2);
    if(iris){
      const q=(f-(iris.at-iris.frames/2)+1)/(iris.frames+1);
      if(f<iris.at){
        compose(sample,shot,f);
        const r=far*smooth(q/.52);
        g.beginPath();g.arc(ix,iy,r+15,0,Math.PI*2);g.fillStyle=p.deep;g.fill();
        g.beginPath();g.arc(ix,iy,r,0,Math.PI*2);g.fillStyle=p.green;g.fill();
        g.strokeStyle=p.light;g.lineWidth=2;g.stroke();
      }else{
        color(p.green,0,0,W,H);
        g.save();g.beginPath();g.arc(ix,iy,far*smooth((q-.52)/.48),0,Math.PI*2);g.clip();
        compose(sample,shot,f);g.restore();
      }
      return;
    }
    if(f>=push.at&&f<push.at+push.frames){
      g.drawImage(previous,0,0);
      const t=smooth((f-push.at+1)/push.frames), x=mix(W+44,-44,t);
      g.save();g.beginPath();g.moveTo(x+42,0);g.lineTo(W,0);g.lineTo(W,H);g.lineTo(x-42,H);g.closePath();g.clip();
      compose(sample,shot,f);g.restore();
      g.beginPath();g.moveTo(x+42,0);g.lineTo(x-42,H);g.strokeStyle=p.light;g.lineWidth=3;g.stroke();
      return;
    }
    compose(sample,shot,f);
    if(f===push.at-1)prev.drawImage(canvas,0,0);
  };
}
