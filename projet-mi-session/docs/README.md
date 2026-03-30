# Documentation - Shield ESP32

## Structure du dossier

Ce dossier contient la documentation visuelle et multimédia du projet.

```
docs/
├── photos/              # Photos du prototype
├── screenshots/         # Captures d'écran de l'interface
└── demo-video.mp4      # Vidéo de démonstration (optionnel)
```

## Photos du prototype

Le dossier `photos/` devrait contenir :

### Photos breadboard (prototypage initial)
- `breadboard-overview.jpg` - Vue d'ensemble du montage sur breadboard
- `breadboard-wiring.jpg` - Détails du câblage
- `breadboard-components.jpg` - Vue rapprochée des composants

### Photos PCB assemblé
- `pcb-top-view.jpg` - Vue de dessus du PCB assemblé
- `pcb-bottom-view.jpg` - Vue de dessous du PCB
- `pcb-angle-view.jpg` - Vue en angle montrant les composants
- `pcb-with-modules.jpg` - PCB avec modules ESP32 et MPU-6050 installés

### Photos fonctionnelles
- `system-running.jpg` - Système en fonctionnement avec LEDs allumées
- `raspberry-pi-setup.jpg` - Configuration Raspberry Pi avec l'interface
- `complete-setup.jpg` - Configuration complète (ESP32 + Raspberry Pi + alimentation)

### Conseils pour les photos
- Utiliser un bon éclairage (lumière naturelle ou LED blanc froid)
- Nettoyer le PCB avant les photos (alcool isopropylique)
- Utiliser un fond neutre (blanc, noir ou gris)
- Prendre plusieurs angles pour chaque sujet
- Résolution minimum : 1920×1080 pixels
- Format recommandé : JPEG ou PNG

## Screenshots de l'interface

Le dossier `screenshots/` devrait contenir :

### Interface Python
- `interface-main.png` - Vue principale de l'interface Tkinter
- `interface-led-on.png` - Interface avec LED allumée
- `interface-led-off.png` - Interface avec LED éteinte
- `interface-potentiometer.png` - Interface montrant les valeurs du potentiomètre
- `interface-connected.png` - État connecté au broker MQTT
- `interface-disconnected.png` - État déconnecté

### Moniteur série / Logs
- `serial-monitor-boot.png` - Messages de démarrage ESP32
- `serial-monitor-mqtt-connect.png` - Connexion MQTT réussie
- `serial-monitor-data-stream.png` - Flux de données en temps réel

### Broker MQTT (optionnel)
- `mqtt-explorer-topics.png` - Vue des topics MQTT
- `mqtt-messages.png` - Messages MQTT en temps réel

### Conseils pour les screenshots
- Utiliser des outils de capture d'écran de qualité
- Capturer en pleine résolution
- Annoter si nécessaire (flèches, labels)
- Format recommandé : PNG pour la qualité
- Inclure la date/heure si pertinent

## Vidéo de démonstration (optionnel)

### Contenu suggéré pour la vidéo
1. **Introduction** (10-15 secondes)
   - Vue d'ensemble du projet
   - Composants principaux

2. **Hardware** (20-30 secondes)
   - PCB assemblé
   - Modules connectés
   - Vue des composants (LEDs, potentiomètres, boutons)

3. **Démonstration logicielle** (30-45 secondes)
   - Lancement de l'interface Python
   - Connexion MQTT
   - Contrôle des LEDs via l'interface
   - Lecture du potentiomètre en temps réel
   - Interaction avec les boutons

4. **Tests fonctionnels** (20-30 secondes)
   - Tourner le potentiomètre et voir les valeurs changer
   - Allumer/éteindre la LED depuis l'interface
   - Presser les boutons et observer les réactions

5. **Conclusion** (5-10 secondes)
   - Récapitulatif rapide
   - Remerciements

### Spécifications techniques vidéo
- **Durée**: 1-2 minutes maximum
- **Résolution**: 1080p (1920×1080) minimum
- **Format**: MP4 (H.264)
- **Framerate**: 30 fps minimum
- **Audio**: Optionnel (musique de fond ou narration)
- **Taille de fichier**: < 100 MB si possible

### Outils recommandés
- **Capture d'écran**: OBS Studio (gratuit, multi-plateforme)
- **Montage**: DaVinci Resolve (gratuit), iMovie, Windows Video Editor
- **Compression**: HandBrake (pour réduire la taille)

## Organisation des fichiers

### Nomenclature recommandée
```
photos/
├── prototype/
│   ├── 01-breadboard-overview.jpg
│   ├── 02-breadboard-wiring.jpg
│   └── 03-breadboard-components.jpg
├── pcb/
│   ├── 01-pcb-top.jpg
│   ├── 02-pcb-bottom.jpg
│   ├── 03-pcb-angle.jpg
│   └── 04-pcb-assembled.jpg
└── system/
    ├── 01-complete-setup.jpg
    ├── 02-system-running.jpg
    └── 03-interface-connected.jpg

screenshots/
├── interface/
│   ├── 01-main-window.png
│   ├── 02-led-control.png
│   └── 03-potentiometer-reading.png
├── serial-monitor/
│   ├── 01-boot-sequence.png
│   └── 02-mqtt-connection.png
└── mqtt/
    └── 01-mqtt-explorer.png
```

## Checklist documentation

Avant la soumission finale, vérifier:

- [ ] Au moins 3 photos du prototype breadboard
- [ ] Au moins 4 photos du PCB assemblé
- [ ] Au moins 5 screenshots de l'interface
- [ ] Screenshot du moniteur série (boot + MQTT)
- [ ] Photos nettes et bien éclairées
- [ ] Screenshots en haute résolution
- [ ] Nomenclature cohérente des fichiers
- [ ] README.md mis à jour avec liste des fichiers
- [ ] Vidéo de démo (optionnel mais recommandé)

## Copyright et licence

Toutes les photos et vidéos de ce projet sont soumises à la même licence que le projet principal.

**Auteur**: [Votre nom]  
**Date**: 2026-03-30  
**Projet**: Shield ESP32 - Projet Mi-Session
