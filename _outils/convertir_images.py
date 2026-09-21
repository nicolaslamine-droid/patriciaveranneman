"""Crée les versions AVIF et WebP de toutes les images utilisées par index.html.
Usage : python3 _outils/convertir_images.py   (depuis la racine du site)
Les fichiers déjà à jour sont ignorés ; à relancer après tout ajout de photo."""
import re, os, sys, urllib.parse
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps

def refs():
    s = open('index.html', encoding='utf-8').read()
    out = set()
    for m in re.finditer(r'srcset="([^"]+)"', s):
        for part in m.group(1).split(','):
            out.add(urllib.parse.unquote(part.strip().split(' ')[0]))
    for m in re.finditer(r'(?:src|data-full)="(images/[^"]+)"', s):
        out.add(urllib.parse.unquote(m.group(1)))
    return sorted(r for r in out if r.startswith('images/') and r.lower().endswith(('.jpg', '.jpeg', '.png')) and os.path.exists(r))

def un(src):
    base = os.path.splitext(src)[0]
    t = os.path.getmtime(src)
    todo = [(base + '.avif', 'AVIF', dict(quality=58, speed=6)), (base + '.webp', 'WEBP', dict(quality=80, method=5))]
    todo = [x for x in todo if not (os.path.exists(x[0]) and os.path.getmtime(x[0]) >= t)]
    if not todo: return 0
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert('RGB')
    for dst, fmt, kw in todo:
        im.save(dst, fmt, **kw)
    return len(todo)

if __name__ == '__main__':
    lst = refs()
    n = 0
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i, k in enumerate(ex.map(un, lst, chunksize=4)):
            n += k
            if i % 20 == 0: print(f'{i+1}/{len(lst)}', flush=True)
    print('terminé :', n, 'fichiers créés', flush=True)
