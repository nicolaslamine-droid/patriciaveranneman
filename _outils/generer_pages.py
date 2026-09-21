"""Génère une page par œuvre (oeuvres/<slug>/index.html) et le sitemap.xml
à partir d'index.html. À relancer après toute modification des œuvres :
    python3 _outils/generer_pages.py
"""
import re, os, json, html, shutil, datetime, urllib.parse

SITE = 'https://patricia.veranneman.eu/'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
s = open('index.html', encoding='utf-8').read()
AUJ = datetime.date.today().isoformat()
EXT = re.compile(r'\.(jpe?g|png)(?=[\s,"]|$)', re.I)

def attr(tag, nom):
    m = re.search(r'\s' + re.escape(nom) + r'="([^"]*)"', tag)
    return m.group(1) if m else None

def texte(h):
    return html.unescape(re.sub(r'<[^>]+>', '', h or '')).replace('\xa0', ' ').strip()

def span(art, cls):
    m = re.search(r'<span class="' + cls + r'"(?: data-en="([^"]*)")?>(.*?)</span>(?=<span|</div>)', art, re.S)
    return (m.group(2), m.group(1)) if m else (None, None)

# ── Relevé des œuvres, galerie par galerie, dans l'ordre du site
galeries = []
for gid, nom, nom_en, art_type in [('pg', 'Peintures', 'Paintings', 'Peinture'), ('cg', 'Céramiques', 'Ceramics', 'Céramique')]:
    i = s.index('id="%s"' % gid); j = s.index('</section>', i)
    galeries.append((nom, nom_en, art_type, s[i:j]))
i = s.index('<section class="elements"'); j = s.index('</section>', i)
galeries.append(('Les quatre éléments', 'The four elements', 'Céramique', s[i:j]))

oeuvres = []
for nom, nom_en, art_type, bloc in galeries:
    liste = []
    for m in re.finditer(r'<article id="w-([^"]+)"[^>]*>(.*?)</article>', bloc, re.S):
        slug, art = m.group(1), m.group(2)
        img = re.search(r'<img\b[^>]*>', art).group(0)
        wt = re.search(r'<span class="wt">(.*?)</span>\s*<span', art, re.S).group(1)
        wt = re.sub(r'</?a\b[^>]*>', '', wt)
        wm, wm_en = span(art, 'wm')
        wd, wd_en = span(art, 'wd')
        wf = re.search(r'<span class="wf"[^>]*>.*?</span>(?=</div>)', art, re.S)
        liste.append(dict(slug=slug, titre_h=wt, titre=texte(wt), wm=wm or '', wm_en=wm_en, wd=wd or '', wd_en=wd_en,
                          wf=wf.group(0) if wf else '', src=attr(img, 'src'), srcset=attr(img, 'srcset'),
                          w=int(attr(img, 'width') or 0), h=int(attr(img, 'height') or 0),
                          alt=attr(img, 'alt') or texte(wt), full=attr(img, 'data-full') or attr(img, 'src'),
                          galerie=nom, galerie_en=nom_en, type=art_type))
    for k, o in enumerate(liste):
        o['prev'] = liste[k - 1] if len(liste) > 1 else None
        o['next'] = liste[(k + 1) % len(liste)] if len(liste) > 1 else None
    oeuvres += liste

def swap(v, e): return EXT.sub('.' + e, v)
def rel(u): return '../../' + u
def absu(u): return SITE + u

def vignette(o):
    """Image moyenne (1200 px) pour les aperçus de partage, sinon l'originale."""
    base, ext = os.path.splitext(urllib.parse.unquote(o['src']))
    moy = base + '-1200' + ext
    if os.path.exists(moy):
        r = 1200 / o['w'] if o['w'] else 1
        return urllib.parse.quote(moy), 1200, round(o['h'] * r)
    return o['src'], o['w'], o['h']

def picture(o, sizes, cls='', prio=False):
    base = o['srcset'] or o['src']
    rs = lambda v: ', '.join(rel(p.strip()) for p in v.split(','))
    extra = ' fetchpriority="high"' if prio else ' loading="lazy"'
    return (f'<picture><source type="image/avif" srcset="{rs(swap(base, "avif"))}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{rs(swap(base, "webp"))}" sizes="{sizes}">'
            f'<img{(" class=%s" % chr(34) + cls + chr(34)) if cls else ""} src="{rel(o["src"])}"'
            + (f' srcset="{rs(o["srcset"])}" sizes="{sizes}"' if o['srcset'] else '')
            + f' width="{o["w"]}" height="{o["h"]}" alt="{html.escape(o["alt"], quote=True)}" decoding="async"{extra}></picture>')

head_commun = s[s.index('<link rel="icon"'):s.index('\n', s.index('<link rel="icon"'))]

CSS = r'''
:root{--w:#fff;--cream:#FAF8F5;--warm:#F4EFE8;--k:#0D0D0D;--mid:#888;--line:#E5E0D8;--gold:#9A7040;--ink:#1C1915;--t2:#555;--t3:#6b6b6b;
--S:'Cormorant Garamond',Georgia,serif;--s:'Jost','Helvetica Neue',system-ui,-apple-system,sans-serif;--ease:cubic-bezier(.25,.46,.45,.94)}
:root[data-theme="dark"]{--w:#131214;--cream:#171619;--warm:#1C1B1E;--k:#EDE9E2;--mid:#8C8880;--line:#2C2A2E;--gold:#C4A06B;--ink:#F6F3ED;--t2:#B8B4AC;--t3:#9C9890}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--s);font-weight:300;background:var(--w);color:var(--k);line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit}
img{display:block;max-width:100%}
picture{display:contents}
.top{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:1rem;
  height:calc(60px + env(safe-area-inset-top,0px));padding:env(safe-area-inset-top,0px) calc(2rem + env(safe-area-inset-right,0px)) 0 calc(2rem + env(safe-area-inset-left,0px));
  background:var(--w);border-bottom:1px solid var(--line)}
.logo{font-family:var(--S);font-size:1.1rem;letter-spacing:.04em;text-decoration:none;padding:.6rem 0}
.back{font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mid);text-decoration:none;display:inline-flex;align-items:center;gap:.5rem;min-height:44px}
.back:hover{color:var(--k)}
.oeuvre{display:grid;grid-template-columns:minmax(0,1fr) 380px;min-height:calc(100vh - 60px);border-bottom:1px solid var(--line)}
.vue{background:var(--cream);display:flex;align-items:center;justify-content:center;padding:3rem}
.vue a{display:block;cursor:zoom-in}
.vue img{max-height:calc(100vh - 60px - 6rem);width:auto;height:auto;object-fit:contain;box-shadow:0 30px 80px rgba(0,0,0,.14);background:var(--warm)}
.fiche{padding:4rem 3rem;display:flex;flex-direction:column;justify-content:center;border-left:1px solid var(--line)}
.kick{font-size:.6rem;letter-spacing:.28em;text-transform:uppercase;color:var(--gold)}
h1{font-family:var(--S);font-weight:400;font-style:italic;font-size:clamp(2rem,3.2vw,3rem);line-height:1.1;margin:1rem 0 1.25rem;color:var(--ink)}
.tech{font-size:.66rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mid)}
.desc{font-family:var(--S);font-style:italic;font-size:1.15rem;color:var(--t2);margin-top:1.25rem}
.wf{display:block;margin-top:1.25rem;font-size:.8rem;color:var(--t3)}
.wf .av{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--mid);margin-right:.35rem;vertical-align:middle}
.wf .av[data-av="dispo"]{background:#5f8f5a}.wf .av[data-av="vendu"]{background:#a44}
.act{display:flex;flex-direction:column;gap:.9rem;margin-top:2.5rem;align-items:flex-start}
.cta{display:inline-flex;align-items:center;min-height:48px;padding:0 1.8rem;font-size:.62rem;letter-spacing:.22em;text-transform:uppercase;
  text-decoration:none;color:var(--w);background:var(--k);border:1px solid var(--k);transition:background .3s var(--ease),color .3s var(--ease)}
.cta:hover{background:transparent;color:var(--k)}
.lien{font-size:.62rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mid);text-decoration:none;border:0;background:none;cursor:pointer;
  font-family:inherit;padding:.4rem 0;border-bottom:1px solid var(--line)}
.lien:hover{color:var(--k);border-color:var(--k)}
.suite{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid var(--line)}
.suite a{display:flex;align-items:center;gap:1.25rem;padding:2rem;text-decoration:none;transition:background .3s}
.suite a+a{border-left:1px solid var(--line);flex-direction:row-reverse;text-align:right}
.suite a:hover{background:var(--cream)}
.suite .mini{width:84px;height:84px;flex:0 0 84px;overflow:hidden;background:var(--warm)}
.suite .mini img{width:100%;height:100%;object-fit:cover}
.suite small{display:block;font-size:.58rem;letter-spacing:.22em;text-transform:uppercase;color:var(--mid);margin-bottom:.3rem}
.suite span{font-family:var(--S);font-style:italic;font-size:1.15rem;line-height:1.25}
footer{padding:2.5rem 2rem calc(2.5rem + env(safe-area-inset-bottom,0px));text-align:center;font-size:.6rem;letter-spacing:.2em;text-transform:uppercase;color:var(--mid)}
footer a{text-decoration:none;border-bottom:1px solid var(--line)}
@media(max-width:900px){
  .oeuvre{grid-template-columns:1fr;min-height:0}
  .vue{padding:1.25rem}
  .vue img{max-height:72vh}
  .fiche{border-left:0;border-top:1px solid var(--line);padding:2.25rem 1.5rem 2.75rem}
  .top{padding-left:1.25rem;padding-right:1.25rem}
  .suite a{padding:1.25rem;gap:.9rem}
  .suite .mini{width:60px;height:60px;flex-basis:60px}
  .suite span{font-size:1rem}
}
@media(max-width:480px){.back span{display:none}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
'''

JS = r'''
(function(){
  try{ if(localStorage.getItem('pv-lang')==='en'){
    document.documentElement.lang='en';
    document.querySelectorAll('[data-en]').forEach(function(e){ e.innerHTML=e.getAttribute('data-en'); });
  } }catch(e){}
  var b=document.getElementById('partager');
  if(b) b.addEventListener('click',function(){
    var u=location.href.split('#')[0], t=document.title;
    if(navigator.share){ navigator.share({title:t,url:u}).catch(function(){}); return; }
    var ok=function(){ b.textContent = document.documentElement.lang==='en' ? 'Link copied' : 'Lien copié'; };
    if(navigator.clipboard) navigator.clipboard.writeText(u).then(ok,function(){});
  });
})();
'''

def page(o):
    t = o['titre']
    kick_fr = texte(o['wm']) or o['type']
    desc_txt = texte(o['wd'])
    meta_desc = f"{t} — {texte(o['wm']).lower() or o['type'].lower()}. Œuvre de Patricia Veranneman, artiste peintre et céramiste belge."
    if desc_txt: meta_desc = f"{t} ({desc_txt.rstrip('.')}) — {texte(o['wm']).lower()}. Œuvre de Patricia Veranneman, artiste peintre et céramiste belge."
    url = f"{SITE}oeuvres/{o['slug']}/"
    vig, vw, vh = vignette(o)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "VisualArtwork", "@id": url + "#oeuvre", "name": t, "url": url,
         "image": absu(o['full']), "artform": o['type'], "artMedium": texte(o['wm']) or None,
         "description": desc_txt or None,
         "creator": {"@type": "Person", "@id": SITE + "#artiste", "name": "Patricia Veranneman"},
         "isPartOf": {"@id": SITE + "#collection"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Patricia Veranneman", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": o['galerie'], "item": SITE + ('#ceramiques' if o['type'] == 'Céramique' else '#peintures')},
            {"@type": "ListItem", "position": 3, "name": t, "item": url}]}]}
    for g in ld['@graph']:
        for k in [k for k, v in g.items() if v is None]: del g[k]
    sizes = '(max-width:900px) 100vw, calc(100vw - 380px)'
    wm_en = f' data-en="{o["wm_en"]}"' if o['wm_en'] else ''
    nav = ''
    if o['prev'] and o['next']:
        p, n = o['prev'], o['next']
        mini = lambda x: picture(dict(x, srcset=None, src=re.sub(r'(\.[A-Za-z]+)$', r'-600\1', x['src']) if os.path.exists(urllib.parse.unquote(re.sub(r'(\.[A-Za-z]+)$', r'-600\1', x['src']))) else x['src']), '84px')
        nav = (f'<nav class="suite" aria-label="Autres œuvres">'
               f'<a href="../{p["slug"]}/" rel="prev"><span class="mini">{mini(p)}</span><div><small data-en="Previous">Précédente</small><span>{p["titre_h"]}</span></div></a>'
               f'<a href="../{n["slug"]}/" rel="next"><span class="mini">{mini(n)}</span><div><small data-en="Next">Suivante</small><span>{n["titre_h"]}</span></div></a></nav>')
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(t)} — Patricia Veranneman</title>
<meta name="description" content="{html.escape(meta_desc, quote=True)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Patricia Veranneman">
<meta property="og:title" content="{html.escape(t, quote=True)} — Patricia Veranneman">
<meta property="og:description" content="{html.escape(meta_desc, quote=True)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{absu(vig)}">
<meta property="og:image:width" content="{vw}">
<meta property="og:image:height" content="{vh}">
<meta property="og:image:alt" content="{html.escape(o['alt'], quote=True)}">
<meta property="og:locale" content="fr_BE">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0D0D0D">
{head_commun}
<script>try{{if(localStorage.getItem('pv-theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;1,400&family=Jost:wght@300;400&display=swap">
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body>
<header class="top">
  <a class="logo" href="../../">Patricia Veranneman</a>
  <a class="back" href="../../#w-{o['slug']}"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M13 8H3M7.5 3.5 3 8l4.5 4.5"/></svg><span data-en="Back to the gallery">Retour à la galerie</span></a>
</header>
<main class="oeuvre">
  <div class="vue"><a href="{rel(o['full'])}" aria-label="Voir l'image en pleine résolution">{picture(o, sizes, prio=True)}</a></div>
  <div class="fiche">
    <span class="kick" data-en="{o['galerie_en']}">{o['galerie']}</span>
    <h1>{o['titre_h']}</h1>
    <span class="tech"{wm_en}>{html.escape(kick_fr)}</span>
    {f'<p class="desc"{(" data-en=%s" % chr(34) + o["wd_en"] + chr(34)) if o["wd_en"] else ""}>{o["wd"]}</p>' if o['wd'] else ''}
    {o['wf']}
    <div class="act">
      <a class="cta" href="../../?oeuvre={o['slug']}#contact" data-en="I'm interested in this work">Cette œuvre m'intéresse</a>
      <button type="button" class="lien" id="partager" data-en="Share">Partager</button>
    </div>
  </div>
</main>
{nav}
<footer>© Patricia Veranneman · <a href="../../" data-en="All works">Toutes les œuvres</a> · <a href="../../#contact">Contact</a></footer>
<script>{JS}</script>
</body>
</html>
'''

# ── Écriture
if os.path.isdir('oeuvres'):
    for d in os.listdir('oeuvres'):
        if d not in {o['slug'] for o in oeuvres}:
            print('page orpheline (à supprimer à la main) :', d)
for o in oeuvres:
    os.makedirs(f"oeuvres/{o['slug']}", exist_ok=True)
    open(f"oeuvres/{o['slug']}/index.html", 'w', encoding='utf-8').write(page(o))

# ── Sitemap (avec les images, pour Google Images)
L = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
     f'  <url><loc>{SITE}</loc><lastmod>{AUJ}</lastmod><priority>1.0</priority></url>']
for o in oeuvres:
    L.append(f"  <url><loc>{SITE}oeuvres/{o['slug']}/</loc><lastmod>{AUJ}</lastmod><priority>0.7</priority>"
             f"<image:image><image:loc>{html.escape(absu(o['full']))}</image:loc></image:image></url>")
L.append('</urlset>')
open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print(len(oeuvres), 'pages générées + sitemap.xml')
