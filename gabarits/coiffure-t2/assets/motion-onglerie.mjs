import {makeDiagonal} from './cassures.mjs?v=t2-fiche-visible-3';
/* COIFFURE‑T2 · Composition d’images uniquement : plans, fenêtres et impacts. */
export const W=720,H=1280,FPS=30,FRAMES=900;
const FULL=[0,0,W,H], roles=['S1','S2','S3','S4'];
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const lerp=(a,b,u)=>a+(b-a)*u;
const ease=u=>u*u*(3-2*u);
const assert=(v,m)=>{if(!v)throw Error(m);};
const pair=(a,min,max)=>Array.isArray(a)&&a.length===2&&a.every(v=>Number.isFinite(v)&&v>=min&&v<=max);

export const span=(layer,shot)=>layer.when??[0,shot.out-shot.in];
export const sourceFrame=(layer,n)=>layer.from+Math.floor(n*layer.rate+1e-8);
export function selectLayer(layer,reuseDetail){
  return reuseDetail&&layer.scene==='S3'?{...layer,...layer.reuse,scene:'S2',role:'S3'}:{...layer,role:layer.scene};
}

export function validatePlan(p){
  assert(p?.schema==='vv.coiffure.plan/3'&&p.template==='COIFFURE-T2'&&p.width===W&&p.height===H&&p.fps===FPS&&p.frames===FRAMES&&p.audio===false&&p.videoText===false,'Contrat vidéo invalide.');
  assert(roles.every((s,i)=>p.scenes[s]===(i?210:180)),'Durées des rôles invalides.');
  let at=0;const ids=new Set(),coverage=new Set();
  for(const shot of p.shots){
    const n=shot.out-shot.in;
    assert(shot.in===at&&Number.isInteger(shot.out)&&n>0&&!ids.has(shot.id)&&shot.layers.length>=1&&shot.layers.length<=3,'Plans non contigus ou superposition invalide.');
    ids.add(shot.id);at=shot.out;
    assert(!shot.layers[0].when&&!shot.layers[0].rect,'Le premier plan doit toujours couvrir l’image.');
    for(const [i,l] of shot.layers.entries()){
      const [a,b]=span(l,shot);const k=b-a;
      assert(roles.includes(l.scene)&&Number.isInteger(a)&&Number.isInteger(b)&&a>=0&&b<=n&&k>=2,'Intervalle de panneau hors plan.');
      assert(i===0||Array.isArray(l.rect)&&l.rect[0]?.[0]===0&&l.rect.at(-1)?.[0]===k-1&&l.rect.every(([j,x,y,w,h],q)=>Number.isInteger(j)&&(!q||j>l.rect[q-1][0])&&[x,y,w,h].every(Number.isFinite)&&x>=-W-16&&x<=W+16&&y>=-H-16&&y<=H+16&&w>=48&&w<=W&&h>=48&&h<=H),'Courbe de panneau invalide.');
      assert(l.scene!=='S3'||!!l.reuse,'Fenêtre de remplacement du détail absente.');
      for(const alt of l.scene==='S3'?[false,true]:[false]){
        const s=selectLayer(l,alt);
        assert(Number.isInteger(s.from)&&s.from>=0&&s.rate>=.2&&s.rate<=2.5&&sourceFrame(s,k-1)<p.scenes[s.scene]&&pair(s.anchor,0,1)&&pair(s.zoom??[1,1],1,1.4),'Fenêtre ou cadrage hors prise : '+shot.id+' / '+l.scene);
        assert(s.pan==null||Number.isInteger(s.pan[0])&&s.pan[0]>=0&&s.pan[0]<k-1&&pair(s.pan.slice(1),0,1),'Déplacement du recadrage invalide.');
      }
      coverage.add(l.scene);
    }
  }
  assert(at===FRAMES&&coverage.size===4&&p.shots[0].layers[0].scene==='S4'&&p.shots.at(-1).layers[0].scene==='S4','Le résultat doit ouvrir et fermer un film de 900 images.');
  const review=p.shots.filter(s=>s.layers.length===1&&s.layers[0].scene==='S3').map(s=>s.id);
  assert(review.length>=1&&JSON.stringify(p.detailReview)===JSON.stringify(review),'L’aperçu doit montrer chaque recadrage plein écran du détail.');
  let edge=0;
  for(const x of p.impacts){
    assert(p.shots.some(s=>s.in===x.at)&&[x.before,x.after].every(v=>Number.isInteger(v)&&v>=1&&v<=7)&&x.at-x.before>=edge&&x.at+x.after<FRAMES&&x.power>0&&x.power<=.27&&pair(x.pivot,.24,.76),'Impact non borné.');
    edge=x.at+x.after;
  }
  return p;
}

function rectangle(keys,n){
  if(!keys)return FULL;
  const i=keys.findIndex(x=>x[0]>=n);
  if(i<=0)return keys[i===0?0:keys.length-1].slice(1);
  const a=keys[i-1],b=keys[i],u=ease((n-a[0])/(b[0]-a[0]));
  return a.slice(1).map((v,j)=>lerp(v,b[j+1],u));
}

export function createMotion(canvas,plan,aim){
  const ctx=canvas.getContext('2d',{alpha:false});
  ctx.imageSmoothingEnabled=true;ctx.imageSmoothingQuality='high';
  const requestedClose=['contours','detail'].includes(aim);
  const diagonal=makeDiagonal(canvas,ctx,plan);
  return (rows,shot,f)=>{
    const impact=plan.impacts.find(x=>x.kind!=='diagonale'&&f>=x.at-x.before&&f<x.at+x.after);
    for(const [i,row] of rows.entries()){
      if(!row)continue;
      const {sample,layer,n,length}=row;
      const [x,y,w,h]=rectangle(layer.rect,n);
      if(x>=W||x+w<=0||y>=H||y+h<=0)continue;
      const t=sample.rotation===90||sample.rotation===270;
      const sw=t?sample.squarePixelHeight:sample.squarePixelWidth;
      const sh=t?sample.squarePixelWidth:sample.squarePixelHeight;
      const [a,b]=layer.zoom??[1,1];
      let z=lerp(a,b,ease(n/(length-1)));
      if(requestedClose&&shot.id==='resultat-dos')z+=.018;
      const scale=Math.max(w/sw,h/sh)*z,dw=sw*scale,dh=sh*scale;
      const [ax,ay]=layer.anchor;
      const [start,ex,ey]=layer.pan??[0,ax,ay];
      const u=ease(clamp((n-start)/(length-1-start),0,1));
      const dx=(w-dw)*lerp(ax,ex,u),dy=(h-dh)*lerp(ay,ey,u);
      // Cadre visible au claquement, bord retiré progressivement avant le plein écran.
      const border=layer.rect?ease(clamp(Math.max((W-w)/130,(H-h)/180),0,1)):0;
      const radius=17*border;
      ctx.save();
      if(layer.rect){ctx.beginPath();ctx.roundRect(x,y,w,h,radius);ctx.clip();}
      const effect=i===0?impact:null;
      if(!effect){sample.draw(ctx,x+dx,y+dy,dw,dh);}
      else{
        const p=f<effect.at?1-(effect.at-f)/(effect.before+1):1-(f-effect.at)/effect.after;
        const power=effect.power*p**1.46;
        const [u,v]=effect.pivot,px=w*u,py=h*v;
        const draw=(grow,alpha)=>{
          ctx.globalAlpha=alpha;
          const ww=dw*grow,hh=dh*grow;
          sample.draw(ctx,x+clamp(px+(dx-px)*grow,w-ww,0),y+clamp(py+(dy-py)*grow,h-hh,0),ww,hh);
        };
        // Traînée radiale brève et localisée : aucune carte, flash ou insertion noire.
        draw(1+power,1);
        if(power>.02){draw(1+power*1.32,p*.23);draw(1+power*1.64,p*.11);}
      }
      ctx.restore();
      if(border>.01){
        ctx.save();ctx.globalAlpha=border;
        ctx.strokeStyle='#fff1d9';ctx.lineWidth=3.6;
        ctx.beginPath();ctx.roundRect(x+1.9,y+1.9,w-3.8,h-3.8,Math.max(0,radius-1.9));ctx.stroke();
        ctx.restore();
      }
    }
    diagonal(f);
  };
}
