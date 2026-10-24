# 🎵 VLC Overlay Controller

[![Platform Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg?logo=windows)](https://github.com/je-tu-il/Vlc-musique-controler/releases)
[![Release](https://img.shields.io/github/v/release/je-tu-il/Vlc-musique-controler?color=success&include_prereleases)](https://github.com/je-tu-il/Vlc-musique-controler/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg?logo=python)](requirements.txt)
[![UI CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Prenez le contrôle de votre musique sans encombrer votre écran.  
> Une interface overlay HUD élégante et semi-transparente pour VLC qui permet de gérer la progression, la vitesse et le volume à la molette, et qui **disparaît automatiquement** dès que vous ne l'utilisez pas.

---

## ⚡ Téléchargement 1-Clic (Sans Python)

👉 **[Télécharger VLC_Ctrl.exe (Dernière Version)](https://github.com/je-tu-il/Vlc-musique-controler/releases/latest)**

1. Téléchargez `VLC_Ctrl.exe` (ou le fichier `.zip` portable).
2. Activez l'interface web dans VLC (voir étape ci-dessous, 20 secondes montre en main).
3. Lancez `VLC_Ctrl.exe` !

---

## ⚙️ Configuration Rapide de VLC (Une seule fois)

Pour que l'overlay communique avec votre lecteur VLC :
1. Dans VLC, ouvrez **Outils** > **Préférences** (ou `Ctrl + P`).
2. En bas à gauche, sous *Afficher les paramètres*, cochez **Tous** au lieu de *Simple*.
3. Déroulez **Interface** > **Interfaces principales**.
4. Cochez **Web** dans la liste des interfaces.
5. Cliquez sur la sous-catégorie **Lua** (sous *Interfaces principales*).
6. Dans la case **Mot de passe**, tapez : `vlc`.
7. Cliquez sur **Enregistrer**, puis redémarrez VLC.

---

## ✨ Fonctionnalités Clés

- 👻 **Discrétion Totale (Auto-Hide)** :
  - L'overlay s'affiche automatiquement au changement de piste, lors de l'utilisation de la molette ou avec le raccourci **`Alt + é`**.
  - S'estompe et disparaît tout seul après 3 secondes d'inactivité.
- 🎚️ **Contrôle Volume à la Molette** :
  - Survolez l'overlay et tournez simplement la molette de votre souris pour ajuster le volume sonore.
- ⏭️ **Contrôles Complets** :
  - Play / Pause (icône dynamique)
  - Piste Suivante / Précédente
  - Barre de progression cliquable pour naviguer dans le morceau
  - Sélecteur de vitesse de lecture (0.5x, 1.0x, 1.25x, 1.5x, 1.7x, 2.0x)
- 🖼️ **Affichage de la Pochette & Métadonnées** :
  - Récupération dynamique de la jaquette de l'album via l'API locale de VLC.
- 📍 **Repositionnable d'un Geste** :
  - Cliquez et glissez l'overlay n'importe où sur vos écrans.

---

## 🛠️ Lancement pour Développeurs (Code Source)

```bash
git clone https://github.com/je-tu-il/Vlc-musique-controler.git
cd Vlc-musique-controler
pip install -r requirements.txt
python main.py
```

---

## 📄 Licence

Ce projet est sous licence MIT. Libre d'utilisation et de modification.
