// Planificateur T3. Durées mesurées des pistes vidéo,
// pas celles des conteneurs. Ne supprime ni ne raccourcit une prise.
export function planifier(durees,options={fps:30,maxFilm:30,maxPrises:[8,10,10,8],minPrise:2}) {
 const {fps,maxFilm,maxPrises,minPrise}=options;
 if(!Number.isInteger(fps)||fps<1||!Number.isFinite(maxFilm)||maxFilm<=0||!Array.isArray(maxPrises)||maxPrises.length!==4||maxPrises.some(x=>!Number.isFinite(x)||x<=0)||!Number.isFinite(minPrise)||minPrise<=0) throw Error('Configuration invalide.');
 if(!Array.isArray(durees)||durees.length!==4) throw Error('Quatre prises sont nécessaires.');
 const scenes=durees.map((duration,index)=>{
  if(!Number.isFinite(duration)||duration<minPrise||duration>maxPrises[index]+1e-7) throw Error(`Durée invalide pour la prise ${index+1}.`);
  return {id:`S${index+1}`,dureeSource:duration,images:Math.floor(duration*fps+1e-7)};
 });
 const sourceTotal=durees.reduce((a,b)=>a+b,0);
 // Do not accept a real duration above the ceiling simply because rounding hides it.
 if(sourceTotal>maxFilm+1e-7)throw Error('Les quatre prises dépassent la durée maximale : aucune prise n’a été raccourcie.');
 let n=0;for(const scene of scenes){scene.debutImage=n;n+=scene.images;scene.finImage=n;}
 return {fps,scenes,totalImages:n,dureeFilm:n/fps,dureeSource:sourceTotal};
}
