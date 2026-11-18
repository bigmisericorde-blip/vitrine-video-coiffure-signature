'use strict';
const c=window.CONSIGNES_T1, m='media/'+c.sortie.file;
document.getElementById('clip').src=m;document.getElementById('download').href=m;
const a=document.getElementById('booking');a.href=c.display.route+'?test='+encodeURIComponent(c.id);a.textContent=c.display.cta;
