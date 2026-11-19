'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const c = window.CONSIGNES_T2, silent = 'media/' + c.sortie.file, video = $('clip');
  const options = new URLSearchParams(location.search), audio = window.VVAfrobeat;
  const soundEnabled = audio?.tracks.length === 4 && options.get('muet') !== '1';
  let track = null, lastDraw = null;

  function apply(t) {
    track = t;
    const src = track?.video || silent;
    video.pause();
    video.defaultMuted = video.muted = !track;
    video.setAttribute('aria-label', 'Le passage vert, film de trente secondes ' + (track ? 'avec musique' : 'sans son'));
    video.src = src;
    $('download').href = src;
    $('download').textContent = track ? 'Télécharger ce montage' : 'Télécharger le MP4 muet';
    $('filmMode').textContent = `SIGNATURE COIFFURE / ${track ? 'AVEC MUSIQUE' : 'TEST MUET'}`;
    $('sonCredit').hidden = !track;
    $('tirageActions').hidden = !soundEnabled;
    $('muet').hidden = !soundEnabled;
    if (track) {
      lastDraw = track.id;
      const badge = track.content_id === 'enregistre' ? ' · Content ID enregistré' : '';
      $('sonInfo').textContent = `Musique : ${track.titre} — ${track.auteur}${badge}`;
      $('sonSource').href = track.source;
      $('sonSource').textContent = audio.provider(track);
      $('sonLicence').href = track.licence;
      $('sonLicence').textContent = track.licence_nom;
      $('sonModifications').textContent = track.modifications;
      options.set('piste', track.id);
      try {history.replaceState(null, '', '?' + options);} catch {}
    }
  }

  const message = text => {$('filmMessage').textContent = text; $('filmMessage').hidden = !text;};
  video.addEventListener('error', () => {
    if (track) {
      apply(null);
      message('Ce montage avec musique n’a pas chargé. Le master muet reste disponible.');
    } else message('Le film n’a pas chargé. Tu peux réessayer en rechargeant cette page.');
  });
  $('retirer').onclick = () => {
    message('');
    apply(lastDraw ? audio.choose(lastDraw) : audio.choose());
    video.play().catch(() => {});
  };
  if (options.get('muet') === '1' && audio?.tracks.length === 4) {
    $('muet').textContent = 'Revenir au film avec musique';
    $('muet').href = '?test=' + encodeURIComponent(c.id);
  }
  apply(soundEnabled ? audio.byId(options.get('piste')) || audio.choose() : null);
  if (options.get('muet') === '1' && audio?.tracks.length === 4) $('muet').hidden = false;
  $('booking').href = c.display.route + '?test=' + encodeURIComponent(c.id);
  $('booking').textContent = c.display.cta;
})();
