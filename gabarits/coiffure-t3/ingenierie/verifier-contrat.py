#!/usr/bin/env python3
from pathlib import Path
exec(compile((Path(__file__).parent/'verifier-candidat.py').read_text(),str(Path(__file__).parent/'verifier-candidat.py'),'exec'))
