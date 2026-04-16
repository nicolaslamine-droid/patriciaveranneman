#!/bin/bash
# ─────────────────────────────────────────────
# Script de renommage des images — Patricia Veranneman
# Fais glisser ce fichier dans le dossier "images/"
# puis double-clique dessus (ou exécute-le dans Terminal)
# ─────────────────────────────────────────────

cd "$(dirname "$0")"

rename_if_exists() {
  if [ -f "$1" ]; then
    mv "$1" "$2"
    echo "✓ $1 → $2"
  fi
}

# PEINTURES
rename_if_exists "1 Children.jpg"                                  "1_Children.jpg"
rename_if_exists "1 Suzy Paternotte.jpg"                           "1_Suzy_Paternotte.jpg"
rename_if_exists "Against Evil.JPG"                                "Against_Evil.JPG"
rename_if_exists "Applique wc.JPG"                                 "Applique_wc.JPG"
rename_if_exists "Automne Cambre.JPG"                              "Automne_Cambre.JPG"
rename_if_exists "Détail Air.jpg"                                  "Détail_Air.jpg"
rename_if_exists "DSC_0023 (2).JPG"                                "DSC_0023__2_.JPG"
rename_if_exists "DSC_0027 (2).JPG"                                "DSC_0027__2_.JPG"
rename_if_exists "DSC_0067 (2).JPG"                                "DSC_0067__2_.JPG"
rename_if_exists "DSC_0426 - Copie.JPG"                            "DSC_0426_-_Copie.JPG"
rename_if_exists "EAJean-Charles Veranneman de Watervliet.JPG"     "EAJean-Charles_Veranneman_de_Watervliet.JPG"
rename_if_exists "Emerence Pardo de Fremicourt.JPG"                "Emerence_Pardo_de_Fremicourt.JPG"
rename_if_exists "Empathie .jpg"                                   "Empathie_.jpg"
rename_if_exists "expo Den Blank l'Air.jpg"                        "expo_Den_Blank_l_Air.jpg"
rename_if_exists "Fenêtre.JPG"                                     "Fenêtre.JPG"
rename_if_exists "Fils et vieux père.jpg"                          "Fils_et_vieux_père.jpg"
rename_if_exists "Hiver etangs d'Ixelles 1.JPG"                   "Hiver_etangs_d_Ixelles_1.JPG"
rename_if_exists "Hiver Etangs d'Ixelles.JPG"                     "Hiver_Etangs_d_Ixelles.JPG"
rename_if_exists "In the arms .jpg"                                "In_the_arms__.jpg"
rename_if_exists "In the dark.jpg"                                 "In_the_dark.jpg"
rename_if_exists "Je m informe.JPG"                                "Je_m_informe.JPG"
rename_if_exists "Je m'informe.JPG"                                "Je_m_informe.JPG"
rename_if_exists "Jesus and the bird (Murillo).jpg"                "Jesus_and_the_bird__Murillo_.jpg"
rename_if_exists "Joie de la mer.JPG"                              "Joie_de_la_mer.JPG"
rename_if_exists "L enfant qui dort.JPG"                           "L_enfant_qui_dort.JPG"
rename_if_exists "L'enfant qui dort.JPG"                           "L_enfant_qui_dort.JPG"
rename_if_exists "Laetitia.jpg"                                    "Laetitia.jpg"
rename_if_exists "Le manège.JPG"                                   "Le_manège.JPG"
rename_if_exists "Le transat.JPG"                                  "Le_transat.JPG"
rename_if_exists "LLN Bibliothèque.JPG"                            "LLN_Bibliothèque.JPG"
rename_if_exists "LLN Musée Hergé.JPG"                             "LLN_Musée_Hergé.JPG"
rename_if_exists "Look    Turner .jpg"                             "Look____Turner_.jpg"
rename_if_exists "Look (Turner).jpg"                               "Look____Turner_.jpg"
rename_if_exists "Mise en place d une boule sur un pilastre .jpg"  "Mise_en_place_d_une_boule_sur_un_pilastre_.jpg"
rename_if_exists "Mise en place d'une boule sur un pilastre .jpg"  "Mise_en_place_d_une_boule_sur_un_pilastre_.jpg"
rename_if_exists "Old couple.jpg"                                  "Old_couple.jpg"
rename_if_exists "Papa et fils plage.jpg"                          "Papa_et_fils_plage.jpg"
rename_if_exists "Patricia et Stéphanie.jpg"                       "Patricia_et_Stéphanie.jpg"
rename_if_exists "Père François.JPG"                               "Père_François.JPG"
rename_if_exists "Prend le train de la vie .jpg"                   "Prend_le_train_de_la_vie__.jpg"
rename_if_exists "Raymond Veranneman de Watervliet.JPG"            "Raymond_Veranneman_de_Watervliet.JPG"
rename_if_exists "Stéphanie1.jpg"                                  "Stéphanie1.jpg"
rename_if_exists "Tempête.jpg"                                     "Tempête.jpg"
rename_if_exists "Voiture Patricia Raymond1.jpg"                   "Voiture_Patricia_Raymond1.jpg"
rename_if_exists "Vue sur mer.JPG"                                 "Vue_sur_mer.JPG"
rename_if_exists "Wall Street.JPG"                                 "Wall_Street.JPG"
rename_if_exists "Where are we going Dad .jpg"                     "Where_are_we_going_Dad_.jpg"
rename_if_exists "Where are we going, Dad?.jpg"                    "Where_are_we_going_Dad_.jpg"

echo ""
echo "✅ Renommage terminé !"
echo "Tu peux fermer cette fenêtre."
read -p "Appuie sur Entrée pour quitter..."
