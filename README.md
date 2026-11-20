# VLC Musique Controller — Apple Liquid Edition

Une interface overlay **Apple Liquid** ultra-légère, esthétique et non-intrusive pour contrôler VLC lorsqu'il tourne en arrière-plan.

---

## ⚡ Installation 100% Automatique

Aucune intervention requise :
1. Double-cliquez sur **`install.bat`**
2. Le script s'occupe de tout en silence :
   - Détection et installation automatique de VLC (via winget si absent)
   - Installation silencieuse des dépendances Python
   - Ajout du raccourci au démarrage de Windows (`shell:startup`)
   - Lancement immédiat du widget en arrière-plan !

*(Vous pouvez aussi simplement lancer `Vlcctrl.pyw` directement : il auto-installe ses dépendances en tâche de fond).*

---

## ✨ Fonctionnalités Clés

- **🍏 Design Apple Liquid** : Fond sombre Glassmorphism (`#121215`), coins arrondis modernes (26px), micro-animations sans saccades.
- **🖼️ Grande Pochette (136x136 px)** : Coins arrondis (18px), lecture de la pochette VLC ou détection automatique locale (`folder.jpg`, `cover.jpg`) dans le dossier de la musique.
- **⏱️ Barre de Progression Interactive (Seekable)** : Cliquez n'importe où ou faites glisser le curseur pour naviguer instantanément dans le morceau avec prévisualisation en temps réel.
- **⏩ Sélecteur de Vitesse Apple** :
  - Détection automatique de la vitesse réelle de VLC dès le démarrage.
  - Ajustable à la **molette** au survol ou par simple **clic** pour cycler (`0.5x`, `0.75x`, `1.0x`, `1.25x`, `1.5x`, `2.0x`).
- **🎛️ Contrôles Complets** : Précédent, Pause / Play dynamique, Suivant.
- **🔊 Volume Système à la Molette** : Ajustez le volume général en scrollant sur l'interface (avec toast visuel).
- **⚙️ Menu Contextuel (Clic Droit)** : Clic droit sur n'importe quel élément de l'interface pour accéder aux Paramètres complets, contrôler la lecture ou quitter.
- **🎚️ Paramètres Exhaustifs** :
  - Raccourci clavier personnalisé avec capture interactive de touches
  - Choix parmi les couleurs d'accent Apple (Orange, Bleu, Violet, Vert, Rose, Rouge, Or)
  - Mode Sombre / Clair / Système
  - Transparence et délai de disparition configurables
  - Toggles iOS pour chaque élément (Pochette, Progression, Contrôles, Vitesse, Titre défilant)
  - Option **Fixation au bureau** (le widget reste intégré au fond d'écran sans disparaître)
- **🌿 Consommation CPU Ultra-Légère (< 0.2%)** :
  - Polling adaptatif (2s en veille masquée, 3s si VLC éteint, 800ms quand actif)
  - Marquee arrêté en veille
  - Mise en pause complète des rafraîchissements graphiques lorsque le widget est masqué.
