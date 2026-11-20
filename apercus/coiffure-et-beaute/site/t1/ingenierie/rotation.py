"""Tirage transactionnel : un nouveau montage réussi, jamais le même fond deux fois."""
from contextlib import contextmanager, closing
from pathlib import Path
import json
import os
import secrets
import sqlite3


def state_path():
    home = Path(os.environ.get('XDG_STATE_HOME') or Path.home()/'.local/state')
    return Path(os.environ.get('VV_ROTATION_STATE') or home/'vitrine-video/rotation.sqlite')


@contextmanager
def next_track(tracks, atelier, path=None, previous=None, choose=secrets.choice):
    """Rejouer/télécharger ne passe pas ici ; un rendu en erreur ne consomme rien."""
    db = Path(path) if path is not None else state_path()
    db.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    entries = {t['id']:t for t in tracks}
    if len(entries) < 2 or len(entries) != len(tracks):
        raise ValueError('La rotation exige plusieurs fonds distincts.')
    with closing(sqlite3.connect(db, timeout=42)) as con:
        con.execute('CREATE TABLE IF NOT EXISTS rotation (atelier TEXT PRIMARY KEY, dernier TEXT, joues TEXT NOT NULL)')
        con.execute('BEGIN IMMEDIATE')
        try:
            row = con.execute('SELECT dernier,joues FROM rotation WHERE atelier=?',(atelier,)).fetchone()
            last, played = (row[0],json.loads(row[1])) if row else (None,[])
            used = {k for k in played if k in entries}
            eligible = [k for k in entries if k not in (last,previous)]
            if not eligible: eligible = [k for k in entries if k != last]
            pool = [k for k in eligible if k not in used]
            if not pool:
                used = set()
                pool = eligible
            selected = choose(pool)
            yield entries[selected]
            used.add(selected)
            con.execute('INSERT INTO rotation(atelier,dernier,joues) VALUES (?,?,?) '
                        'ON CONFLICT(atelier) DO UPDATE SET dernier=excluded.dernier,joues=excluded.joues',
                        (atelier,selected,json.dumps(sorted(used))))
            con.commit()
        except BaseException:
            con.rollback()
            raise
