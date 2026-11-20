const gal = new URL('./', import.meta.url);
const coffre = new URL('../../gabarits/coiffure-t2/', gal);
export const mediaURL = file => new URL(file, gal).href;
async function read(url) {
  const r = await fetch(url, {credentials: 'same-origin', redirect: 'error'});
  if (!r.ok) throw Error('Ressource indisponible.');
  return r.json();
}
export async function loadExample() {
  const [gallery, guide] = await Promise.all([
    read(new URL('exemple.json', gal)), read(new URL('capture/guide.json', coffre)),
  ]);
  if (gallery.schema !== 'vv.coiffure.demo-client/1' || gallery.template !== 'COIFFURE-T2' || gallery.kind !== 'stock_example' || guide.id !== gallery.template || guide.scenes.length !== 4 || guide.screens.length !== 12 || gallery.clips.length !== 4) throw Error('Exemple incompatible.');
  gallery.clips.forEach((clip, i)=>{
    const id = `S${i+1}`;
    if (guide.scenes[i].id !== id || clip.id !== id || clip.seconds !== guide.scenes[i].secondes || clip.mp4 !== `prises/${id}.mp4` || clip.poster !== `prises/${id}.jpg` || !/^[a-f0-9]{64}$/.test(clip.sha256)) throw Error('Prise manquante.');
  });
  return {gallery, guide};
}
