// Profil de cadrage dérivé, partagé par les deux ateliers. Les plans de base restent intacts.
// L'image importante est centrée au tournage : aucun point d'ancrage sur la tête, le dos ou la barbe.
const center=[.5,.5];
const gentle=(zoom=[1,1],factor=.28)=>zoom.map(x=>1+(x-1)*factor);
export function reframeT1(plan){
  return {...plan,shots:plan.shots.map(s=>({...s,anchor:center,zoom:gentle(s.zoom)}))};
}
export function reframeT2(plan){
  return {...plan,
    shots:plan.shots.map(s=>({...s,layers:s.layers.map(({pan,...l})=>{
      const original=l.reuse;
      const next={...l,anchor:center,zoom:gentle(l.zoom,.20)};
      if(original){
        const {from,rate}=original;
        // Le vrai gros plan reste préférable. Si S2 sert de détail, montrer
        // exactement ce cadrage centré à la relecture, puis au montage.
        next.reuse={from,rate,anchor:center,zoom:[1.14,1.19]};
      }
      return next;
    })})),
    // Garder les cassures, sans le coup de zoom calibré sur une coiffure précise.
    impacts:plan.impacts.map(i=>({...i,pivot:center,power:i.power*.44}))};
}
