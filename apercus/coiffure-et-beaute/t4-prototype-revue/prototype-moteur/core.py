"""Adaptateur local limité pour le mixeur historique T1, sans contrat T1/T2."""
import shutil
def ffmpeg():
    p = shutil.which("ffmpeg")
    if not p: raise RuntimeError("FFmpeg est requis")
    return p
