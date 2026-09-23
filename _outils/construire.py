#!/usr/bin/env python3
"""Construit tout le site à partir de contenu/ et gabarit/.

    python3 _outils/construire.py

Produit : index.html, en/index.html, oeuvres/<id>/, en/oeuvres/<id>/,
mentions-legales/, sitemap.xml, et les images dérivées (600/1200, AVIF, WebP).
Rien d'autre ne doit être modifié à la main : tout part de contenu/.
"""
import os, re, sys, json, html, math, yaml, colorsys, datetime, urllib.parse
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageOps

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RACINE)
AUJ = datetime.date.today().isoformat()

# ─────────────────────────────── contenu
def charger(f): return yaml.safe_load(open('contenu/' + f, encoding='utf-8'))
SITE = charger('site.yaml')
TEXTES = charger('textes.yaml')
OEUVRES = charger('oeuvres.yaml')['oeuvres']
COULEURS = charger('couleurs.yaml') or {}
URL = SITE['url'].rstrip('/') + '/'
GAB = open('gabarit/index.html', encoding='utf-8').read()

GALERIES = {'peintures': dict(art='Peinture', art_en='Painting', cls='work', cap='wcap', img='wimg', ancre='peintures'),
            'ceramiques': dict(art='Céramique', art_en='Ceramic', cls='cwork', cap='ccap', img='cwimg', ancre='ceramiques'),
            'elements': dict(art='Céramique', art_en='Ceramic', cls='cwork', cap='ccap', img='cwimg', ancre='ceramiques')}
SIZES = ('(max-width:619px) calc(100vw - 2.5rem), (max-width:1099px) calc((100vw - 5rem)/2), '
         '(max-width:1799px) calc((100vw - 8rem)/3), 440px')
DISPO = {'disponible': ('Disponible', 'Available', 'disponible'),
         'vendue': ('Vendue', 'Sold', 'vendue'),
         'collection': ('Collection privée', 'Private collection', 'collection'),
         'commande': ('Sur commande', 'To order', 'commande')}

def esc(t): return re.sub(r'&(?!#?\w+;)', '&amp;', (t or '')).replace('<br>', '<br>')
def att(t):
    """Attribut : on garde les balises internes (<em>…), on protège « et &."""
    t = html.unescape(t or '')
    return re.sub(r'&(?!#?\w+;)', '&amp;', t).replace('"', '&quot;')
def enc(f): return urllib.parse.quote(f)

# ─────────────────────────────── images
def variantes(nom):
    """(fichier, largeur) disponibles, de la plus petite à l'originale."""
    base, ext = os.path.splitext(nom)
    src = 'images/' + nom
    w, h = Image.open(src).size
    out = []
    for p in (600, 1200):
        f = f'{base}-{p}{ext}'
        if w > p * 1.15 or os.path.exists('images/' + f):
            if not os.path.exists('images/' + f):
                im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
                im = im.resize((p, round(im.height * p / im.width)), Image.LANCZOS)
                im.save('images/' + f, quality=84, optimize=True, progressive=True)
                print('  variante créée :', f)
            out.append((f, p))
    out.append((nom, w))
    return out, w, h

def _convertir(f):
    base, ext = os.path.splitext(f)
    src = 'images/' + f
    if ext.lower() not in ('.jpg', '.jpeg', '.png'): return 0
    t = os.path.getmtime(src); n = 0
    todo = [('images/%s.avif' % base, 'AVIF', dict(quality=58, speed=6)),
            ('images/%s.webp' % base, 'WEBP', dict(quality=80, method=5))]
    todo = [x for x in todo if not (os.path.exists(x[0]) and os.path.getmtime(x[0]) >= t)]
    if not todo: return 0
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    for dst, fmt, kw in todo: im.save(dst, fmt, **kw); n += 1
    return n

def couleur(nom, cle):
    if cle in COULEURS: return COULEURS[cle]
    im = ImageOps.exif_transpose(Image.open('images/' + nom)).convert('RGB').resize((60, 60))
    px = [colorsys.rgb_to_hls(*[c / 255 for c in p]) for p in im.getdata()]
    x = sum(math.cos(2 * math.pi * h) * s for h, l, s in px)
    y = sum(math.sin(2 * math.pi * h) * s for h, l, s in px)
    d = {'h': round((math.atan2(y, x) / 2 / math.pi) % 1, 4),
         's': round(sum(s for h, l, s in px) / len(px), 3),
         'l': round(sum(l for h, l, s in px) / len(px), 3)}
    COULEURS[cle] = d
    return d

def srcsets(vars_, ext=None):
    def f(v):
        n = v[0] if ext is None else re.sub(r'\.(jpe?g|png)$', '.' + ext, v[0], flags=re.I)
        return f'images/{enc(n)} {v[1]}w'
    return ', '.join(f(v) for v in vars_)

def balise_image(o, sizes, classe='', prio=False):
    vars_, w, h = o['_vars'], o['_w'], o['_h']
    un = len(vars_) == 1
    ss = '' if un else f' srcset="{srcsets(vars_)}" sizes="{sizes}"'
    autre = lambda e: 'images/' + enc(re.sub(r'\.(jpe?g|png)$', '.' + e, o['image'], flags=re.I))
    av = srcsets(vars_, 'avif') if not un else autre('avif')
    wb = srcsets(vars_, 'webp') if not un else autre('webp')
    sz = f' sizes="{sizes}"' if not un else ''
    charge = ' fetchpriority="high"' if prio else ' loading="lazy"'
    cl = f' class="{classe}"' if classe else ''
    return (f'<picture><source type="image/avif" srcset="{av}"{sz}>'
            f'<source type="image/webp" srcset="{wb}"{sz}>'
            f'<img{cl} width="{w}" height="{h}" src="images/{enc(o["image"])}" alt="{att(o.get("alt") or o["titre"])}"'
            f'{charge} decoding="async"{ss} data-full="images/{enc(o["image"])}"></picture>')

# ─────────────────────────────── fiche (année · dimensions · disponibilité)
def fiche(o):
    bouts = []
    for k in ('annee', 'dimensions', 'technique_precise'):
        if o.get(k): bouts.append('<span>%s</span>' % esc(str(o[k]).strip()))
    dispo = ''
    if o.get('disponibilite'):
        d = DISPO.get(str(o['disponibilite']).strip().lower())
        if d: dispo = f'<span class="av" data-av="{d[2]}" data-en="{d[1]}">{d[0]}</span>'
    if not bouts and not dispo: return ''
    sep = '<span class="sep">·</span>'
    corps = sep.join(bouts)
    corps = (corps + sep + dispo) if (corps and dispo) else (corps or dispo)
    return f'<span class="wf">{corps}</span>'

# ─────────────────────────────── articles
def espace(t):
    """Espace insécable avant la ponctuation double, comme en typographie française."""
    t = re.sub(r'\s+([!?;:»—])', '\u00a0\\1', t or '')
    return re.sub(r'([«])\s+', '\\1\u00a0', t)

def article(o, prefixe=''):
    g = GALERIES[o['galerie']]
    c = couleur(o['image'], o['id'])
    cls = g['cls'] + {'large': ' wide', 'double': ' w2'}.get(o.get('format', ''), '')
    cat = f' data-c="{o["categorie"]}"' if o.get('categorie') else ''
    caps = [f'<span class="wt"><a class="wlien" href="{prefixe}oeuvres/{o["id"]}/">{esc(espace(o["titre"]))}</a></span>']
    if o.get('technique'):
        en = f' data-en="{att(o.get("technique_en") or o["technique"])}"'
        caps.append(f'<span class="wm"{en}>{esc(o["technique"])}</span>')
    if o.get('note'):
        en = f' data-en="{att(o.get("note_en") or o["note"])}"'
        caps.append(f'<span class="wd"{en}>{esc(espace(o["note"]))}</span>')
    f = fiche(o)
    if f: caps.append(f)
    return (f'  <article id="w-{o["id"]}" data-h="{c["h"]}" data-s="{c["s"]}" data-l="{c["l"]}" class="{cls}"{cat}>\n'
            f'    <div class="{g["img"]}">{balise_image(o, SIZES)}</div>\n'
            f'    <div class="{g["cap"]}">{"".join(caps)}</div>\n'
            f'  </article>')

GROUPES = {'enfance': 'ENFANCE & FAMILLE', 'lieu': 'LIEUX & LUMIÈRE', 'dessin': 'DESSINS', 'portrait': 'PORTRAITS'}

def grille(nom):
    out, vues = [], set()
    for o in [x for x in OEUVRES if x['galerie'] == nom]:
        c = o.get('categorie')
        if c and c not in vues:
            vues.add(c)
            out.append(f'\n  <!-- ── {GROUPES.get(c, c.upper())} ── -->')
        out.append(article(o))
    return '\n'.join(out)

# ─────────────────────────────── JSON-LD
def jsonld():
    a = SITE['artiste']
    g = [{"@type": "Person", "@id": URL + "#artiste", "name": a['nom'], "alternateName": a.get('autre_nom'),
          "jobTitle": a['metier'], "nationality": a.get('nationalite'), "email": "mailto:" + a['email'],
          "telephone": a['telephone'], "url": URL, "knowsAbout": a.get('savoirs'),
          "image": URL + a['portrait'], "sameAs": a.get('reseaux')},
         {"@type": "WebSite", "url": URL, "name": SITE['titre'], "inLanguage": "fr-BE", "about": {"@id": URL + "#artiste"}},
         {"@type": "CollectionPage", "@id": URL + "#collection", "url": URL, "name": "Galerie",
          "hasPart": [{"@type": "VisualArtwork", "name": o['titre'], "artform": GALERIES[o['galerie']]['art'],
                       "artMedium": o.get('technique'), "image": URL + 'images/' + enc(o['image']),
                       "url": f"{URL}oeuvres/{o['id']}/",
                       "creator": {"@type": "Person", "name": a['nom']}} for o in OEUVRES]}]
    for e in SITE.get('expositions') or []:
        g.append({"@type": "Event", "name": e['titre'], "startDate": str(e['debut']), "endDate": str(e.get('fin') or e['debut']),
                  "eventStatus": "https://schema.org/EventScheduled",
                  "location": {"@type": "Place", "name": e['lieu'], "address": e.get('adresse') or e['lieu']},
                  "performer": {"@id": URL + "#artiste"}, "url": e.get('lien') or URL + '#expositions'})
    def net(x):
        if isinstance(x, dict): return {k: net(v) for k, v in x.items() if v is not None}
        if isinstance(x, list): return [net(i) for i in x]
        return x
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@graph": net(g)}, ensure_ascii=False, separators=(',', ':'))
            + '</script>')

# ─────────────────────────────── page d'accueil
def paragraphes(cle):
    out = []
    for p in TEXTES.get(cle) or []:
        en = f' data-en="{att(espace(p["en"]))}"' if p.get('en') else ''
        out.append(f'<p{en}>{esc(espace(p["fr"]))}</p>')
    return '\n    '.join(out)

def accueil():
    s = GAB
    for nom in GALERIES:
        s = s.replace(f'<!--OEUVRES:{nom}-->', grille(nom))
    for cle in ('apropos', 'installation', 'expositions'):
        s = s.replace(f'<!--TEXTES:{cle}-->', paragraphes(cle))
    def txt(m):
        cle = m.group(2); t = TEXTES[cle]
        return f'<p class="{m.group(1)}" data-en="{att(espace(t["en"]))}">{esc(espace(t["fr"]))}</p>'
    s = re.sub(r'<p class="([\w-]+)" data-txt="([\w-]+)"></p>', txt, s)
    nb = {k: sum(1 for o in OEUVRES if o['galerie'] == k) for k in GALERIES}
    s = s.replace('<span class="n" data-nb="peintures"></span>', f'<span class="n">{nb["peintures"]}</span>')
    s = s.replace('<span class="n" data-nb="ceramiques"></span>', f'<span class="n">{nb["ceramiques"]}</span>')
    s = s.replace('<div class="shint" data-nb="peintures"></div>',
                  f'<div class="shint" data-en="Acrylic · Drawing<br>{nb["peintures"]} works">Acrylique · Dessin<br>{nb["peintures"]} œuvres</div>')
    s = s.replace('<div class="shint" data-nb="ceramiques"></div>',
                  f'<div class="shint" data-en="Stoneware &amp; glazed stoneware<br>{nb["ceramiques"]} works">Grès &amp; grès émaillé<br>{nb["ceramiques"]} œuvres</div>')
    # images de l'introduction
    def intro(m):
        slug, num = m.group(1), m.group(2)
        o = PAR_ID[slug]; g = GALERIES[o['galerie']]
        lab = f'{num} · {g["art"]} · {espace(o["titre"])}'
        lab_en = f'{num} · {g["art_en"]} · {espace(o.get("titre_en") or o["titre"])}'
        return (f'<div class="io" data-w="w-{slug}">\n        {balise_image(o, "(max-width:900px) 40vw, 22vw")}\n      </div>\n'
                f'      <span class="iolab" data-en="{att(lab_en)}">{esc(lab)}</span>')
    s = re.sub(r'<div class="io" data-w="w-[^"]+" data-intro="([^"]+)" data-num="(\d+)"></div>', intro, s)
    s = s.replace('<!--JSONLD-->', jsonld())
    s = s.replace('<button class="lang" id="lang" type="button" aria-label="Switch to English" title="English">EN</button>',
                  '<a class="lang" id="lang" href="en/" hreflang="en" aria-label="Switch to English" title="English">EN</a>')
    s = s.replace('<link rel="canonical" href="%s">' % URL,
                  f'<link rel="canonical" href="{URL}">\n<link rel="alternate" hreflang="fr" href="{URL}">\n'
                  f'<link rel="alternate" hreflang="en" href="{URL}en/">\n<link rel="alternate" hreflang="x-default" href="{URL}">')
    return s

PAR_ID = {}

# ─────────────────────────────── version anglaise
def en_version(s, prefixe='../'):
    def swap(m):
        tag, inner = m.group(1), m.group(3)
        en = re.search(r'data-en="([^"]*)"', tag)
        if not en: return m.group(0)
        fr = inner.replace('"', '&quot;')
        tag2 = tag.replace(en.group(0), f'data-en="{en.group(1)}" data-fr="{fr}"')
        return f'<{tag2}>{html.unescape(en.group(1))}</{m.group(2)}>'
    s = re.sub(r'<(([a-z]+)[^>]*\bdata-en="[^"]*"[^>]*)>((?:(?!<\2[ >])[\s\S])*?)</\2>', swap, s)
    s = s.replace('<html lang="fr">', '<html lang="en">')
    s = re.sub(r'(src|href|srcset)="(images/|polices/|mentions-legales/)', lambda m: f'{m.group(1)}="{prefixe}{m.group(2)}', s)
    s = re.sub(r'url\("images/', f'url("{prefixe}images/', s)
    s = s.replace('<a class="lang" id="lang" href="en/"', f'<a class="lang" id="lang" href="{prefixe}"')
    s = s.replace('hreflang="en" aria-label="Switch to English" title="English">EN</a>',
                  'hreflang="fr" aria-label="Afficher en français" title="Français">FR</a>')
    s = s.replace(f'<link rel="canonical" href="{URL}">', f'<link rel="canonical" href="{URL}en/">')
    s = re.sub(r'<title>.*?</title>', f'<title>{esc(SITE["titre_en"])}</title>', s, flags=re.S)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{att(SITE["description_en"])}">', s)
    s = s.replace('"inLanguage":"fr-BE"', '"inLanguage":"en"')
    return s


# ─────────────────────────────── pages d'œuvres
CSS_O = open('gabarit/oeuvre.css', encoding='utf-8').read()
JS_O = open('gabarit/oeuvre.js', encoding='utf-8').read()
ICONE = re.search(r'<link rel="icon"[^>]*>', GAB).group(0)
MOTS = {'fr': dict(retour='Retour à la galerie', interesse="Cette œuvre m'intéresse", partager='Partager',
                   prec='Précédente', suiv='Suivante', toutes='Toutes les œuvres', autres='Autres œuvres',
                   pleine="Voir l'image en pleine résolution", galeries={'peintures': 'Peintures', 'ceramiques': 'Céramiques', 'elements': 'Les quatre éléments'}),
        'en': dict(retour='Back to the gallery', interesse="I'm interested in this work", partager='Share',
                   prec='Previous', suiv='Next', toutes='All works', autres='Other works',
                   pleine='View the full-resolution image', galeries={'peintures': 'Paintings', 'ceramiques': 'Ceramics', 'elements': 'The four elements'})}

def voisines(o):
    l = [x for x in OEUVRES if x['galerie'] == o['galerie']]
    if len(l) < 2: return None, None
    i = l.index(o)
    return l[i - 1], l[(i + 1) % len(l)]

def vignette_partage(o):
    base, ext = os.path.splitext(o['image'])
    f = f'{base}-1200{ext}'
    if os.path.exists('images/' + f):
        return enc(f), 1200, round(o['_h'] * 1200 / o['_w'])
    return enc(o['image']), o['_w'], o['_h']

def page_oeuvre(o, lang='fr'):
    M = MOTS[lang]; g = GALERIES[o['galerie']]
    pre = '../../' if lang == 'fr' else '../../../'
    racine = '../../' if lang == 'fr' else '../../'      # vers l'accueil de la langue
    t = espace(o['titre'])
    tech = (o.get('technique_en') or o.get('technique') or '') if lang == 'en' else (o.get('technique') or '')
    note = (o.get('note_en') or o.get('note') or '') if lang == 'en' else (o.get('note') or '')
    url_fr = f"{URL}oeuvres/{o['id']}/"; url_en = f"{URL}en/oeuvres/{o['id']}/"
    url = url_fr if lang == 'fr' else url_en
    art = g['art'] if lang == 'fr' else g['art_en']
    if lang == 'fr':
        desc = f"{t} — {(tech or art).lower()}. Œuvre de Patricia Veranneman, artiste peintre et céramiste belge."
    else:
        desc = f"{t} — {(tech or art).lower()}. Work by Patricia Veranneman, Belgian painter and ceramicist."
    vig, vw, vh = vignette_partage(o)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "VisualArtwork", "@id": url + "#oeuvre", "name": o['titre'], "url": url,
         "image": URL + 'images/' + enc(o['image']), "artform": art, "artMedium": tech or None,
         "description": note or None, "dateCreated": str(o['annee']) if o.get('annee') else None,
         "creator": {"@type": "Person", "@id": URL + "#artiste", "name": SITE['artiste']['nom']},
         "isPartOf": {"@id": URL + "#collection"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE['artiste']['nom'], "item": URL if lang == 'fr' else URL + 'en/'},
            {"@type": "ListItem", "position": 2, "name": M['galeries'][o['galerie']],
             "item": (URL if lang == 'fr' else URL + 'en/') + '#' + g['ancre']},
            {"@type": "ListItem", "position": 3, "name": o['titre'], "item": url}]}]}
    ld['@graph'][0] = {k: v for k, v in ld['@graph'][0].items() if v is not None}
    sizes = '(max-width:900px) 100vw, calc(100vw - 380px)'
    img = balise_image(o, sizes, prio=True).replace('images/', pre + 'images/')
    p, n = voisines(o)
    nav = ''
    if p and n:
        def mini(x):
            b = dict(x); b['_vars'] = [v for v in x['_vars'] if v[1] <= 600] or x['_vars'][:1]
            return balise_image(b, '84px').replace('images/', pre + 'images/')
        nav = (f'<nav class="suite" aria-label="{M["autres"]}">'
               f'<a href="../{p["id"]}/" rel="prev"><span class="mini">{mini(p)}</span><div><small>{M["prec"]}</small>'
               f'<span>{esc(espace(p["titre"]))}</span></div></a>'
               f'<a href="../{n["id"]}/" rel="next"><span class="mini">{mini(n)}</span><div><small>{M["suiv"]}</small>'
               f'<span>{esc(espace(n["titre"]))}</span></div></a></nav>')
    f = fiche(o)
    if f and lang == 'en':
        f = re.sub(r'<span class="av"([^>]*)data-en="([^"]*)">[^<]*</span>', r'<span class="av"\1>\2</span>', f)
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(t)} — Patricia Veranneman</title>
<meta name="description" content="{att(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="fr" href="{url_fr}">
<link rel="alternate" hreflang="en" href="{url_en}">
<link rel="alternate" hreflang="x-default" href="{url_fr}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Patricia Veranneman">
<meta property="og:title" content="{att(t)} — Patricia Veranneman">
<meta property="og:description" content="{att(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{URL}images/{vig}">
<meta property="og:image:width" content="{vw}">
<meta property="og:image:height" content="{vh}">
<meta property="og:locale" content="{'fr_BE' if lang == 'fr' else 'en_GB'}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0D0D0D">
{ICONE}
<script>try{{if(localStorage.getItem('pv-theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
<link rel="stylesheet" href="{pre}polices/polices.css">
<style>{CSS_O}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body>
<header class="top">
  <a class="logo" href="{racine}">Patricia Veranneman</a>
  <span class="haut-droite">
    <a class="lang" href="{'../../en/oeuvres/' + o['id'] + '/' if lang == 'fr' else '../../../oeuvres/' + o['id'] + '/'}" hreflang="{'en' if lang == 'fr' else 'fr'}">{'EN' if lang == 'fr' else 'FR'}</a>
    <a class="back" href="{racine}#w-{o['id']}"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M13 8H3M7.5 3.5 3 8l4.5 4.5"/></svg><span>{M['retour']}</span></a>
  </span>
</header>
<main class="oeuvre">
  <div class="vue"><a href="{pre}images/{enc(o['image'])}" aria-label="{M['pleine']}">{img}</a></div>
  <div class="fiche">
    <span class="kick">{esc(M['galeries'][o['galerie']])}</span>
    <h1>{esc(t)}</h1>
    {f'<span class="tech">{esc(tech)}</span>' if tech else ''}
    {f'<p class="desc">{esc(espace(note))}</p>' if note else ''}
    {f}
    <div class="act">
      <a class="cta" href="{racine}?oeuvre={o['id']}#contact">{M['interesse']}</a>
      <button type="button" class="lien" id="partager">{M['partager']}</button>
    </div>
  </div>
</main>
{nav}
<footer>© {datetime.date.today().year} Patricia Veranneman · <a href="{racine}">{M['toutes']}</a> · <a href="{racine}#contact">Contact</a> · <a href="{pre}mentions-legales/">{'Mentions légales' if lang == 'fr' else 'Legal notice'}</a></footer>
<script>{JS_O}</script>
</body>
</html>
'''

# ─────────────────────────────── mentions légales
def page_mentions():
    a = SITE['artiste']; m = SITE.get('mentions') or {}
    adresse = f"<p>{esc(m['adresse'])}</p>" if m.get('adresse') else ''
    tva = f"<p>Numéro d'entreprise&nbsp;: {esc(m['tva'])}</p>" if m.get('tva') else ''
    corps = f'''<h1>Mentions légales</h1>
  <h2>Éditeur du site</h2>
  <p>{esc(m.get('responsable') or a['nom'])} — {esc(a['metier'].lower())}</p>
  {adresse}
  <p>{esc(m.get('pays', 'Belgique'))}</p>
  <p>Courriel&nbsp;: <a href="mailto:{a['email']}">{a['email']}</a><br>Téléphone&nbsp;: {a['telephone']}</p>
  {tva}
  <h2>Hébergement</h2>
  <p>GitHub Pages — GitHub,&nbsp;Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis.</p>
  <h2>Propriété intellectuelle</h2>
  <p>L'ensemble des œuvres, photographies et textes présentés sur ce site est la propriété de {esc(a['nom'])}.
     Toute reproduction, même partielle, est soumise à son autorisation écrite préalable.</p>
  <h2>Données personnelles</h2>
  <p>Ce site ne dépose aucun cookie, n'utilise aucun traceur publicitaire et ne mesure pas l'audience.
     Les polices de caractères sont servies depuis ce site&nbsp;: aucune donnée n'est transmise à un service tiers.
     Le formulaire de contact ouvre votre logiciel de messagerie&nbsp;: aucune donnée n'est enregistrée sur le site.
     Les messages reçus servent uniquement à répondre à votre demande. Vous pouvez demander leur suppression
     à l'adresse ci-dessus (règlement européen 2016/679, dit RGPD).</p>
  <h2>Photographies</h2>
  <p>Photographies des œuvres&nbsp;: {esc(a['nom'])}, sauf mention contraire.</p>'''
    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Mentions légales — Patricia Veranneman</title>
<meta name="description" content="Mentions légales du site de Patricia Veranneman, artiste peintre et céramiste.">
<link rel="canonical" href="{URL}mentions-legales/">
<meta name="robots" content="noindex,follow">
{ICONE}
<script>try{{if(localStorage.getItem('pv-theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
<link rel="stylesheet" href="../polices/polices.css">
<style>{CSS_O}</style>
</head>
<body>
<header class="top">
  <a class="logo" href="../">Patricia Veranneman</a>
  <a class="back" href="../"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M13 8H3M7.5 3.5 3 8l4.5 4.5"/></svg><span>Retour au site</span></a>
</header>
<main class="mentions">
  {corps}
</main>
<footer>© {datetime.date.today().year} Patricia Veranneman · <a href="../">Toutes les œuvres</a></footer>
</body>
</html>
'''

# ─────────────────────────────── sitemap
def sitemap():
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
         'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1" '
         'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    def bloc(loc, alt_fr, alt_en, prio, image=None):
        img = f'<image:image><image:loc>{image}</image:loc></image:image>' if image else ''
        return (f'  <url><loc>{loc}</loc><lastmod>{AUJ}</lastmod><priority>{prio}</priority>'
                f'<xhtml:link rel="alternate" hreflang="fr" href="{alt_fr}"/>'
                f'<xhtml:link rel="alternate" hreflang="en" href="{alt_en}"/>{img}</url>')
    L.append(bloc(URL, URL, URL + 'en/', '1.0'))
    L.append(bloc(URL + 'en/', URL, URL + 'en/', '0.8'))
    for o in OEUVRES:
        f_, e_ = f"{URL}oeuvres/{o['id']}/", f"{URL}en/oeuvres/{o['id']}/"
        img = URL + 'images/' + enc(o['image'])
        L.append(bloc(f_, f_, e_, '0.7', img))
        L.append(bloc(e_, f_, e_, '0.5'))
    L.append('</urlset>')
    return '\n'.join(L) + '\n'

def ecrire(chemin, contenu):
    os.makedirs(os.path.dirname(chemin) or '.', exist_ok=True)
    ancien = open(chemin, encoding='utf-8').read() if os.path.exists(chemin) else None
    if ancien != contenu:
        open(chemin, 'w', encoding='utf-8').write(contenu)
        return 1
    return 0

def tout():
    n = 0
    for o in OEUVRES:
        n += ecrire(f"oeuvres/{o['id']}/index.html", page_oeuvre(o, 'fr'))
        n += ecrire(f"en/oeuvres/{o['id']}/index.html", page_oeuvre(o, 'en'))
    ecrire('mentions-legales/index.html', page_mentions())
    ecrire('sitemap.xml', sitemap())
    connus = {o['id'] for o in OEUVRES}
    for base in ('oeuvres', 'en/oeuvres'):
        if os.path.isdir(base):
            for d in os.listdir(base):
                if d not in connus: print('  page orpheline :', base + '/' + d)
    print(len(OEUVRES) * 2, 'pages d\'œuvres,', n, 'mises à jour ; sitemap et mentions légales écrits')

if __name__ == '__main__':
    print(len(OEUVRES), 'œuvres')
    # images : variantes + formats modernes
    for o in OEUVRES:
        o['_vars'], o['_w'], o['_h'] = variantes(o['image'])
        PAR_ID[o['id']] = o
    fichiers = sorted({v[0] for o in OEUVRES for v in o['_vars']} | {SITE['artiste']['portrait'].split('/')[-1]})
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        n = sum(ex.map(_convertir, fichiers, chunksize=4))
    if n: print(n, 'fichiers AVIF/WebP créés')
    yaml.safe_dump(COULEURS, open('contenu/couleurs.yaml', 'w', encoding='utf-8'), allow_unicode=True, sort_keys=True)
    fr = accueil()
    open('index.html', 'w', encoding='utf-8').write(fr)
    os.makedirs('en', exist_ok=True)
    open('en/index.html', 'w', encoding='utf-8').write(en_version(fr))
    print('accueil FR + EN écrits')
    tout()
