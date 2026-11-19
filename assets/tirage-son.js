/* Un fond par nouveau montage. Relecture et export ne tirent jamais. */
(() => {
  'use strict';
  const key = 'vv-coiffure-rotation-v4';
  const list = window.VV_AFROBEAT_CATALOGUE;
  function validOrigin(t) {
    const cc = t.licence === 'https://creativecommons.org/licenses/by/4.0/' && t.licence_nom === 'CC BY 4.0' && t.content_id === 'non-verifie';
    if (t.plateforme === 'fma') return cc && /^fma-\d{5,8}$/.test(t.id) &&
      /^https:\/\/freemusicarchive\.org\/music\/(?:[a-z0-9-]+\/){3}$/.test(t.source);
    if (t.plateforme === 'freevibevault') return cc && /^fvv-[a-z0-9]{24}$/.test(t.id) &&
      t.source === 'https://freevibevault.com/track/' + t.id.slice(4);
    return t.plateforme === 'pixabay' && /^\d{5,8}$/.test(t.id) &&
      new RegExp(`^https://pixabay\\.com/music/[a-z0-9-]+-${t.id}/$`).test(t.source) &&
      t.licence === 'https://pixabay.com/service/license-summary/' && t.licence_nom === 'Pixabay Content License' &&
      ['enregistre','badge-non-affiche'].includes(t.content_id);
  }
  const valid = t => t && ['id','titre','auteur','source','modifications','sha256'].every(k => typeof t[k] === 'string' && t[k].trim()) &&
    t.video === `media/afrobeat/${t.id}.mp4` && /^[0-9a-f]{64}$/.test(t.sha256) && Number.isFinite(t.bpm) && validOrigin(t);
  const tracks = Array.isArray(list) && list.length === 4 && list.every(valid) && new Set(list.map(t => t.id)).size === 4
    ? Object.freeze(list.map(t => Object.freeze({...t}))) : Object.freeze([]);
  const byId = id => tracks.find(t => t.id === id) || null;
  const provider = t => ({fma:'Free Music Archive',pixabay:'Pixabay',freevibevault:'FreeVibeVault'})[t?.plateforme] || 'Source';
  let memory = {last:null,used:[]};
  function read() {
    let x;
    try {x = JSON.parse(localStorage.getItem(key));} catch {}
    if (!x) return memory;
    return {last:byId(x.last)?.id || null,used:Array.isArray(x.used) ? x.used.filter(byId) : []};
  }
  function write(last,used) {
    memory = {last,used:[...new Set(used)]};
    try {localStorage.setItem(key,JSON.stringify(memory));} catch {}
  }
  function propose(previous) {
    let {last,used} = read();
    const allowed = tracks.filter(t => t.id !== last && t.id !== previous);
    let pool = allowed.filter(t => !used.includes(t.id));
    if (!pool.length) {used = []; pool = allowed;}
    if (!pool.length) return null;
    const pick = pool[Math.floor(Math.random() * pool.length)];
    return {track:pick,commit:()=>write(pick.id,[...used,pick.id])};
  }
  function choose(previous) {
    const pending=propose(previous);pending?.commit();return pending?.track||null;
  }
  function remember(id) {
    if (!byId(id)) return;
    const {last,used} = read();
    if (last !== id) write(id,used.length >= tracks.length ? [id] : [...used,id]);
  }
  window.VVAfrobeat = Object.freeze({tracks,choose,propose,byId,provider,remember,last:() => read().last});
})();
