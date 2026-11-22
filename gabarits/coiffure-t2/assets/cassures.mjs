// Finition de la copie Coiffure et beauté. Un seul style T2, avec les prises du métier choisi.
// Aucune décision de montage ne dépend de l'exemple ou du profil métier.
export const types = Object.freeze(['Zoom sec','Balayage diagonal','Cadres qui claquent']);
const zooms = Object.freeze({24:.235,147:.22,389:.225,581:.205,721:.215});
const wipes = Object.freeze({61:1,221:-1});

export function styleCassures(plan){
  const shots=plan.shots.map(s=>{
    const rects={
      'geste-en-cadres':[
        [[0,724,707,348,545],[4,363,707,348,545],[8,351,713,348,545],[55,351,713,348,545]],
        [[0,-568,66,564,579],[5,38,57,564,579],[9,25,68,564,579],[53,25,68,564,579],[59,14,43,621,789],[64,3,12,690,1120],[67,0,0,720,1280]],
      ],
      'travail-vers-resultat':[
        [[0,-282,666,282,583],[5,30,657,282,583],[8,23,666,282,583],[43,23,666,282,583],[53,-284,666,282,583]],
        [[0,245,1285,453,803],[5,243,292,453,803],[9,240,314,453,803],[25,240,314,453,803],[31,139,151,583,1066],[36,0,0,720,1280]],
      ],
      'resultat-compare':[
        [[0,-280,76,275,501],[4,33,76,275,501],[7,24,81,275,501],[33,24,81,275,501],[40,-280,81,275,501]],
      ],
    }[s.id];
    return rects?{...s,layers:s.layers.map((l,i)=>i?{...l,rect:rects[i-1]}:l)}:s;
  });
  const impacts=plan.impacts.map(b=>wipes[b.at] ?
    {...b,kind:'diagonale',before:1,after:7,direction:wipes[b.at]} :
    {...b,kind:'zoom',before:2,after:6,power:zooms[b.at]??.21,pivot:[.5,.49]});
  return {...plan,shots,impacts,cassures:'beaute-cassures-01'};
}

// La dernière image sortante sert uniquement au raccord (sept images maximum).
// Ce raccord est tracé sur les prises avant le lettrage, sans flash ou écran de couleur.
export function makeDiagonal(canvas,ctx,plan){
  const W=canvas.width,H=canvas.height;
  const bands=plan.impacts.filter(i=>i.kind==='diagonale');
  if(!bands.length)return ()=>{};
  const last=new OffscreenCanvas(W,H),saved=last.getContext('2d',{alpha:false});
  let stored=-1;
  return f=>{
    const incoming=bands.find(i=>i.at===f+1);
    if(incoming){saved.drawImage(canvas,0,0);stored=incoming.at;return;}
    const b=bands.find(i=>f>=i.at&&f<i.at+i.after);
    if(!b||stored!==b.at)return;
    const t=(f-b.at+1)/(b.after+1),ease=t*t*(3-2*t),tilt=146;
    const left=-tilt+(W+2*tilt)*ease;
    const path=()=>{ctx.moveTo(left-tilt,0);ctx.lineTo(W+4,0);ctx.lineTo(W+4,H);ctx.lineTo(left+tilt,H);ctx.closePath();};
    ctx.save();
    if(b.direction<0){ctx.translate(W,0);ctx.scale(-1,1);}
    ctx.beginPath();path();ctx.clip();
    if(b.direction<0){ctx.scale(-1,1);ctx.translate(-W,0);}
    ctx.drawImage(last,0,0);ctx.restore();
    ctx.save();
    if(b.direction<0){ctx.translate(W,0);ctx.scale(-1,1);}
    ctx.lineWidth=4;ctx.strokeStyle='rgba(255,240,209,.88)';
    ctx.beginPath();ctx.moveTo(left-tilt,0);ctx.lineTo(left+tilt,H);ctx.stroke();ctx.restore();
  };
}
