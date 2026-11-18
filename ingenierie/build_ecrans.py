#!/usr/bin/env python3
"""Port isolé de la simulation T1 publique ; ne change pas le restaurant."""
from pathlib import Path
import argparse,hashlib,json
from core import ROOT,HERE,load,save
p=argparse.ArgumentParser();p.add_argument('reference',type=Path);a=p.parse_args()
s=a.reference.read_text(encoding='utf-8');orig=s

def rep(a,b):
 global s
 if s.count(a)!=1:raise ValueError(f'Point d’intégration upstream introuvable : {a[:72]}')
 s=s.replace(a,b,1)
rep('T1 Restaurants et Maquis — fiche de tournage','T1 Coiffure — test de tournage')
s=s.replace('../assets/fonts/','assets/')
rep('  .sr{','''  .test-id{position:absolute;top:12px;left:58px;color:#f7fffc;background:#0b1d25dd;padding:5px 8px;border-radius:9px;font-size:10px;letter-spacing:.08em;z-index:21;pointer-events:none}
  body.capture .test-id,#app:has(.rec.on,.adwrap.on) .test-id,#app:has(.rec.on,.adwrap.on,.panel.on) .demo-fab{display:none}
  :root{--bg:#04191b;--deep:#062629;--sheet:rgba(6,38,41,.97);--accent:#40d6a1;--cream:#f5faf3;--muted:#b1c9bf}
  .case-context{margin:-8px 0 15px;font-size:13px;color:#bdf4d8;overflow-wrap:anywhere}
  .review-question{font-size:15px;font-weight:750;line-height:1.4;margin:0;padding:9px 12px;color:#fff;background:#062629ee;border-radius:11px;border:1px solid #40d6a17a}
  .duration,.voice{background:rgba(64,214,161,.10);border-color:rgba(64,214,161,.34)}
  .duration,.voice .voice-title,.voice p{color:#bdf4d8}
  .duration svg,.voice svg{stroke:var(--accent)}
  .sheet-foot{background:#062629}
  .sheet-foot::before{background:linear-gradient(180deg,#06262900,#062629)}
  .cta,.btn.primary{color:#062629;box-shadow:0 14px 30px #40d6a125}
  .cta:disabled{opacity:.55;color:#062629}
  .chrono.hot{border-color:#40d6a1}
  .chrono.hot .dot,.meter i{background:#40d6a1;box-shadow:none}
  .panel{background:radial-gradient(600px 420px at 50% 0%,#0d5342 0%,#04191b 65%)}
  #endCta{display:block;padding:12px 10px;margin:0 0 12px;color:#bdf4d8;border:1px solid #40d6a1;border-radius:999px;text-decoration:none;font-weight:800}
  #app :is(a,button):focus-visible{outline:2px solid white;outline-offset:2px}
  @media (min-width:520px){body{background:radial-gradient(900px 600px at 50% 0%,#0d5342 0%,#04191b 65%)}}
  @media (prefers-reduced-motion:reduce){#app *,#app *::before,#app *::after{transition:none!important;animation:none!important}}
  .adwrap.on{display:flex;flex-direction:column}
  .adwrap .screenVideo{flex:1;min-height:0;position:relative}
  video#ad{object-fit:contain}
  .booking-bar{padding:10px 16px calc(12px + env(safe-area-inset-bottom));background:#062629;display:flex;gap:6px;flex-direction:column}
  .booking-bar a{display:block;text-decoration:none;text-align:center;padding:12px 14px;border-radius:14px;background:#40d6a1;color:#062629;font-size:14px;font-weight:800}
  .booking-bar small{color:#bdf4d8;font-size:10px;text-align:center}
  #testCurtain{padding:26px;text-align:center;color:white;background:#0c1320;position:absolute;inset:0;z-index:99;display:grid;place-content:center;gap:16px}
  #testCurtain[hidden]{display:none}
  #testCurtain a{color:#a1efd3}
  .sr{''')
rep('<main id="app">','''<main id="app">
  <div id="testCurtain" hidden><strong>Le cas de test est requis.</strong><a href="index.html">Ouvrir la fiche préremplie</a></div>
  <span class="test-id" id="testID" aria-hidden="true"></span>''')
rep('>enregistrement</p>','>enregistrement simulé</p>')
rep('>LE PLAT</h1>','>TOI AU TRAVAIL</h1>')
rep('      <p class="consigne" id="consigne"></p>', '      <p class="consigne" id="consigne"></p>\n      <p id="caseContext" class="case-context" hidden></p>')
rep('    <div class="btns">', '    <p id="reviewQuestion" class="review-question"></p>\n    <div class="btns">')
rep('<!-- ÉTAT C — validation de la prise, avec le son -->','<!-- ÉTAT C — validation de la prise muette du test -->')
rep('Lecture avec le son, en boucle','Lecture muette en boucle · test')
rep('Les 4 prises sont réunies dans l\'ordre, avec les textes et le son.','Les 4 prises sont validées. Préparation de la lecture du montage de démonstration, rendu à l’avance.')
rep('Publicité finale · 30 s · démonstration','Test muet · 30 s')
rep('    <video id="ad" playsinline controls preload="auto"></video>','''    <div class="screenVideo"><video id="ad" playsinline muted controls preload="metadata"></video></div>
    <div class="booking-bar"><a id="caCta"></a><small>Simulation — aucun rendez-vous réel</small></div>''')
rep('4 prises · 30 secondes · <strong>Maquis Démo</strong> — données de démonstration fictives.','<span id="endMeta"></span> — démonstration.')
rep('4 prises filmées (6 / 8 / 7 / 9 s)','4 prises validées pour le test')
rep('>Voix et musique mixées</', '>Rendu sans piste audio</')
rep('Prête à partager','Rendu disponible pour la revue')
rep('    <button class="cta" id="restart">','    <a id="endCta"></a>\n    <button class="cta" id="restart">')
rep('  </div>\n\n  <!-- Outils de démonstration','''    <a href="index.html" style="color:#b9c7da;margin-top:18px;font-size:13px">Revenir au cas de test</a>
  </div>

  <!-- Outils de démonstration''')
rep('<script src="consignes.js"></script>','<script src="cas-demo.js"></script>')
rep(' * Textes : une seule source — capture-guide/consignes_T1.json,\n * compilé en simulation/consignes.js par tools/build_consignes.py.',' * Cas VV-COIF : ingenierie/cas-test.json → cas-demo.js + master du même plan.\n * Parcours A/B/C repris du T1 public ; rendu déjà calculé et validé hors navigateur.')
rep('  video: `media/S${s.n}.mp4`,\n  voix: `media/voix${s.n}.mp3`','  video: `media/${s.media}`')
rep('const cam = $("cam"), replay = $("replay"), ad = $("ad"), audioVoix = new Audio();','''const cam = $("cam"), replay = $("replay"), ad = $("ad");
const film = `media/${DATA.sortie.file}`;
const params = new URLSearchParams(location.search);
const linked = params.get("test") === DATA.id;
const fiche = (() => {
  if (!linked || params.get("fiche") !== "1") return null;
  try { return JSON.parse(sessionStorage.getItem("vv-fiche-" + DATA.id) || "null"); }
  catch { return null; }
})();
const validated = new Set();
let montageTimer = null;
$("app").dataset.test = DATA.id;
$("testID").textContent = DATA.id + " · SIMULATION";
$("caCta").textContent = DATA.display.cta;
$("caCta").href = DATA.display.route + "?test=" + encodeURIComponent(DATA.id);
$("endCta").href = $("caCta").getAttribute("href");
$("endCta").textContent = DATA.display.cta;
$("endMeta").textContent = `4 prises · ${DATA.plan.duration} secondes · ${DATA.display.salon}`;''')
rep('  ad.pause(); replay.pause(); replay.style.display = "none";','''  if (montageTimer !== null) {clearInterval(montageTimer); montageTimer = null;}
  ad.pause(); replay.pause(); replay.style.display = "none";''')
rep('''  $("listFilm").innerHTML = s.a_filmer.map((t) => `<li><span class="mark">✓</span><span>${t}</span></li>`).join("");
  $("listAvoid").innerHTML = s.a_eviter.map((t) => `<li><span class="mark">✕</span><span>${t}</span></li>`).join("");''', '''  const list = (id, items, icon) => $(id).replaceChildren(...items.map(t => {
    const li = document.createElement("li"), mark = document.createElement("span"), txt = document.createElement("span");
    mark.className = "mark"; mark.textContent = icon; txt.textContent = t;
    li.append(mark, txt); return li;
  }));
  list("listFilm",s.a_filmer,"✓"); list("listAvoid",s.a_eviter,"✕");''')
rep('  $("voiceText").textContent = DATA.mention_voix_commune;', '''  const hint = i === 3 && fiche?.resultat ? fiche.resultat : fiche?.service;
  $("caseContext").hidden = typeof hint !== "string" || !hint.trim();
  $("caseContext").textContent = $("caseContext").hidden ? "" : (i === 3 && fiche?.resultat ? "À la fin : " : "Ton travail : ") + hint.slice(0, 80);
  $("reviewQuestion").textContent = s.question_relecture;
  $("voiceText").textContent = DATA.mention_voix_commune;''')
rep('  state = "B";','  state = "B";\n  $("app").dataset.prise = s.id;')
rep('replay.loop = true; replay.muted = false;','replay.loop = true; replay.muted = true;')
rep('  audioVoix.src = s.voix; audioVoix.currentTime = 0; audioVoix.volume = 0.9;\n  audioVoix.play().catch(() => {});\n','')
rep('  const steps = ["4 prises réunies", "Textes et prix ajoutés", "Voix et musique mixées", "Export 30 s", "Prêt à partager"];','  const steps = ["4 prises de test", "Textes et offre liés au cas", "Transitions appliquées", "Export 30 s sans son", "Prêt à visionner"];')
rep('  const iv = setInterval(() => {','  montageTimer = setInterval(() => {')
rep('    if (p >= 100) { clearInterval(iv); go.disabled = false; go.textContent = "VOIR MA PUBLICITÉ"; }','''    if (p >= 100) {
      clearInterval(montageTimer); montageTimer = null;
      const ready=()=>{go.disabled=false;go.textContent="VOIR MA PUBLICITÉ";};
      if (!ad.src.endsWith(film)) ad.src=film;
      if (ad.readyState>=1) ready();
      else ad.addEventListener("loadedmetadata",ready,{once:true});
      ad.addEventListener("error",()=>{go.textContent="RENDU INDISPONIBLE";},{once:true});
    }''')
rep('$("next").onclick = () => (idx < SCENES.length - 1 ? showCard(idx + 1) : showMontage());','''$("next").onclick = () => {
  if (state !== "C") return;
  validated.add(SCENES[idx].id);
  if (idx < SCENES.length - 1) showCard(idx+1);
  else if (validated.size === SCENES.length) showMontage();
  else showCard(SCENES.findIndex((s)=>!validated.has(s.id)));
};''')
rep('  ad.src = "media/publicite_T1_demo.mp4";','  if (!ad.src.endsWith(film)) ad.src = film;\n  ad.currentTime = 0;')
rep('$("restart").onclick = () => showCard(0);','$("restart").onclick = () => {validated.clear();showCard(0);};')
rep('  nav.classList.toggle("demo-nav");\n','')
rep('    setTimeout(() => { stopRecording(); $("rec").classList.remove("on"); }, 30);','    setTimeout(() => { stopRecording(); window.__demo.setProgress(40); cam.pause(); }, 45);')
rep('  if (e === "ad") { hideAll(); state = "ad"; $("adwrap").classList.add("on"); ad.src = "media/publicite_T1_demo.mp4"; }','  if (e === "ad") { hideAll(); state = "ad"; $("adwrap").classList.add("on"); ad.src = film; }')
rep('  state: () => state','  state: () => state,\n  validations: () => [...validated],\n  test: () => DATA.id')
rep('showCard(0);\n\n/* Repère','''if (!linked) $("testCurtain").hidden = false;
else {
  const num = Number(params.get("ecran"));
  if (Number.isInteger(num) && num >= 1 && num <= 12) {
    const i = Math.floor((num-1)/3), mode = (num-1)%3;
    document.body.classList.add("capture");
    showCard(i);
    if (mode === 1) {
      startRecording(); stopRecording(); window.__demo.setProgress(40);
      const pausePrise = () => { cam.pause(); cam.currentTime = SCENES[i].secondes*.4; };
      if (cam.readyState >= 1) pausePrise(); else cam.addEventListener("loadedmetadata",pausePrise,{once:true});
    } else if (mode === 2) finishRecording();
    for (const id of ["cta","redo","next","demoFab"]) $(id).disabled = true;
  } else showCard(0);
}

/* Repère''')
(ROOT/'simulation.html').write_text(s,encoding='utf-8')
save(HERE/'provenance-ecrans.json',{'base_commit':'ad4ff15a76dcba7bd08b7e8f56052e842b3e794f','base_path':'simulation/index.html','sha256_source':hashlib.sha256(orig.encode()).hexdigest(),'adapter':'ingenierie/build_ecrans.py','output':'simulation.html','sha256_output':hashlib.sha256(s.encode()).hexdigest(),'etats':['A','B','C','montage','ad','end']})
