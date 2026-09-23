# Site de Patricia Veranneman

Site statique (HTML/CSS/JS sans cadriciel) publié par GitHub Pages sur
<https://patricia.veranneman.eu>.

## Principe

Le contenu est séparé de la présentation. **On ne modifie jamais `index.html` à la
main** : il est reconstruit à partir de `contenu/` et de `gabarit/`.

```
contenu/        ← ce que l'on modifie (l'éditeur en ligne écrit ici)
  oeuvres.yaml     les œuvres, dans l'ordre d'affichage
  textes.yaml      les textes du site (FR + EN)
  site.yaml        contact, exposition en cours, mentions légales
  couleurs.yaml    teintes dominantes (calculées automatiquement)
gabarit/        ← la présentation : structure de la page, CSS, JS
images/         ← photos d'origine + variantes 600/1200 + AVIF/WebP (générées)
polices/        ← Cormorant Garamond et Jost, hébergées ici (aucun appel à Google)
_outils/        ← scripts
admin/          ← éditeur en ligne (Sveltia CMS) : /admin
```

Fichiers **générés** (ne pas modifier) : `index.html`, `en/`, `oeuvres/`,
`en/oeuvres/`, `mentions-legales/`, `sitemap.xml`, et les images dérivées.

## Reconstruire

```bash
python3 _outils/construire.py      # tout : accueil FR + EN, 78×2 pages, sitemap, images
```

Dépendances : `pillow>=12` (AVIF) et `pyyaml`.

Le script :
1. crée les variantes d'images manquantes (600 px, 1200 px) puis les versions AVIF et WebP ;
2. calcule la teinte dominante des nouvelles œuvres (tri « par couleur ») ;
3. écrit la page d'accueil française et anglaise, une page par œuvre dans chaque langue,
   les mentions légales et le sitemap.

## Publication

`.github/workflows/construire.yml` refait cette construction à chaque envoi sur `main`
et publie le résultat sur GitHub Pages. Rien à faire à la main.
Réglage unique : **Settings → Pages → Source : GitHub Actions**.

## Éditeur en ligne

`/admin` ouvre Sveltia CMS. Il écrit directement dans `contenu/` et `images/`.
Connexion par compte GitHub via une passerelle OAuth (`base_url` dans `admin/config.yml`).

## Ajouter une œuvre sans l'éditeur

Déposer la photo dans `images/`, ajouter une entrée dans `contenu/oeuvres.yaml` :

```yaml
- id: nouvelle-oeuvre        # adresse de la page : /oeuvres/nouvelle-oeuvre/
  titre: Nouvelle œuvre
  galerie: peintures         # peintures | ceramiques | elements
  image: Nouvelle_oeuvre.jpg
  technique: Acrylique
  technique_en: Acrylic
  categorie: enfance         # peintures uniquement
```

puis relancer `construire.py`.

## Règles de contenu

- Légendes : « Acrylique », « Grès » ou « Grès émaillé » — sans mention de couleur.
- Pas de description de ce que l'on voit sur l'image ; une note sert à indiquer une
  référence (« D'après Turner »), pas à décrire la scène.
