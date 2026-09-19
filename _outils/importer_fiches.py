#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intègre dans index.html le fichier Excel rempli par Patricia.

    python3 _outils/importer_fiches.py "chemin/vers/Veranneman_fiches_oeuvres.xlsx"

Feuille « Œuvres »           -> ligne année · dimensions · disponibilité sous chaque légende
Feuille « Parcours & expositions » -> section Parcours (qui s'affiche alors dans le menu)

Le script est sans effet de bord : il se relance autant de fois qu'on veut,
il remplace simplement ce qu'il avait posé la fois précédente.
"""
import io, re, sys, html, unicodedata
from openpyxl import load_workbook

RACINE = __file__.rsplit('/_outils/', 1)[0]
HTML = RACINE + '/index.html'

DISPO = {
    'disponible': ('Disponible', 'Available', 'disponible'),
    'vendue': ('Vendue', 'Sold', 'vendue'),
    'collection privée': ('Collection privée', 'Private collection', 'collection'),
    'collection privee': ('Collection privée', 'Private collection', 'collection'),
    'non à vendre': ('Non à vendre', 'Not for sale', 'collection'),
    'non a vendre': ('Non à vendre', 'Not for sale', 'collection'),
    'commande': ('Sur commande', 'Commission', 'commande'),
}

def slug(t):
    t = unicodedata.normalize('NFKD', t or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9]+', '-', t).strip('-').lower()

def esc(t):
    return html.escape(str(t), quote=True)

def lire_oeuvres(ws):
    entetes = [c.value for c in ws[5]]
    idx = {v: i for i, v in enumerate(entetes) if v}
    out = {}
    for row in ws.iter_rows(min_row=7, values_only=True):
        titre = row[idx['Titre']] if 'Titre' in idx else None
        if not titre or '— exemple —' in str(titre):
            continue
        g = lambda k: (row[idx[k]] if k in idx and idx[k] < len(row) else None)
        out[slug(titre)] = {
            'annee': g('Année'), 'dim': g('Dimensions (cm)'),
            'tech': g('Technique précise'), 'dispo': g('Disponibilité'),
            'lieu': g('Lieu / collection'),
        }
    return out

def ligne_fiche(d):
    """Construit le <span class="wf"> ; renvoie '' si rien à afficher."""
    bouts_fr, bouts_en = [], []
    if d.get('annee'):
        a = str(d['annee']).strip().split('.')[0]
        bouts_fr.append('<span>%s</span>' % esc(a)); bouts_en.append(esc(a))
    if d.get('dim'):
        bouts_fr.append('<span>%s</span>' % esc(str(d['dim']).strip()))
        bouts_en.append(esc(str(d['dim']).strip()))
    if d.get('tech'):
        bouts_fr.append('<span>%s</span>' % esc(str(d['tech']).strip()))
        bouts_en.append(esc(str(d['tech']).strip()))
    dispo_html = ''
    if d.get('dispo'):
        cle = str(d['dispo']).strip().lower()
        if cle in DISPO:
            fr, en, code = DISPO[cle]
            dispo_html = '<span class="av" data-av="%s" data-en="%s">%s</span>' % (code, en, fr)
    if not bouts_fr and not dispo_html:
        return ''
    sep = '<span class="sep">·</span>'
    corps = sep.join(bouts_fr)
    if dispo_html:
        corps = (corps + sep + dispo_html) if corps else dispo_html
    return '<span class="wf">%s</span>' % corps

def lire_parcours(ws):
    lignes = []
    for row in ws.iter_rows(min_row=5, values_only=True):
        annee, typ, intitule, lieu, ville, prec = (list(row) + [None] * 6)[:6]
        if not (intitule or lieu):
            continue
        if intitule and '— exemple —' in str(intitule):
            continue
        lignes.append({'annee': annee, 'type': (typ or 'Exposition'), 'intitule': intitule,
                       'lieu': lieu, 'ville': ville, 'prec': prec})
    return lignes

def bloc_parcours(lignes):
    ordre = ['Exposition personnelle', 'Exposition collective', 'Collection publique',
             'Prix / distinction', 'Formation']
    groupes = {}
    for l in lignes:
        groupes.setdefault(str(l['type']).strip(), []).append(l)
    clefs = [k for k in ordre if k in groupes] + [k for k in groupes if k not in ordre]
    out = []
    for k in clefs:
        items = sorted(groupes[k], key=lambda x: str(x['annee'] or ''), reverse=True)
        corps = []
        for l in items:
            an = str(l['annee'] or '').strip().split('.')[0]
            ou = ' — '.join([x for x in [l['lieu'], l['ville']] if x])
            note = ('<span class="cv-note">%s</span>' % esc(l['prec'])) if l['prec'] else ''
            corps.append(
                '    <div class="cv-line"><span class="cv-year">%s</span>'
                '<span><span class="cv-what">%s</span>'
                '<span class="cv-where">%s</span>%s</span></div>'
                % (esc(an), esc(l['intitule'] or ''), esc(ou), note))
        out.append('  <div class="cv-group">\n    <h3>%s</h3>\n%s\n  </div>'
                   % (esc(k), '\n'.join(corps)))
    return '\n'.join(out)

def main(chemin):
    wb = load_workbook(chemin, data_only=True)
    oeuvres = lire_oeuvres(wb['Œuvres']) if 'Œuvres' in wb.sheetnames else {}
    parcours = lire_parcours(wb['Parcours & expositions']) if 'Parcours & expositions' in wb.sheetnames else []

    s = io.open(HTML, encoding='utf-8').read()
    s = re.sub(r'<span class="wf">.*?</span>\s*(?=</div>)', '', s, flags=re.S)  # repart à zéro

    posees = 0
    for cle, d in oeuvres.items():
        ligne = ligne_fiche(d)
        if not ligne:
            continue
        motif = re.compile(r'(<article id="w-%s"[^>]*>.*?<div class="(?:wcap|ccap)">.*?)(</div>)' % re.escape(cle), re.S)
        s, n = motif.subn(lambda m: m.group(1) + ligne + m.group(2), s, count=1)
        posees += n

    if parcours:
        s = re.sub(r'(<section class="cv" id="parcours"[^>]*?)\s+hidden(>)', r'\1\2', s)
        s = re.sub(r'(class="nav-cv"[^>]*?)\s+hidden', r'\1', s)
        s = re.sub(r'(class="nmlink nav-cv"[^>]*?)\s+hidden', r'\1', s)
        s = re.sub(r'(<div class="cv-wrap" id="cv-wrap">).*?(</div>\s*</section>)',
                   lambda m: m.group(1) + '\n' + bloc_parcours(parcours) + '\n' + m.group(2), s, flags=re.S)
        s = re.sub(r'(<div class="shint" id="cv-hint">).*?(</div>)',
                   r'\g<1>%d entrées\g<2>' % len(parcours), s)

    io.open(HTML, 'w', encoding='utf-8').write(s)
    print('Fiches posées   : %d / %d œuvres du fichier' % (posees, len(oeuvres)))
    print('Parcours        : %d entrées' % len(parcours))
    print('\nRelis le rendu, puis publie avec GitHub Desktop.')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Usage : python3 _outils/importer_fiches.py <fichier.xlsx>')
    main(sys.argv[1])
