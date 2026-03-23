# Checklist de validation — Interface Raspberry Pi
**Étudiant :** Henri-Tadja
**Cours :** 243-4J5-LI | Projet mi-session

## Installation
- [ ] pip3 install -r requirements.txt réussi
- [ ] pygame installé correctement
- [ ] paho-mqtt installé correctement

## Connexion MQTT
- [ ] Connexion au broker MQTT établie
- [ ] Topic buttons reçu correctement
- [ ] Topic pots reçu correctement
- [ ] Topic accel reçu correctement (roll/pitch)
- [ ] Topic state reçu correctement
- [ ] Commande LED envoyée au LilyGO

## Affichage pygame
- [ ] Fenêtre pygame s'ouvre correctement
- [ ] Labyrinthe généré et affiché
- [ ] Balle dorée visible au départ
- [ ] HUD affiché en bas (état, temps, meilleur temps)
- [ ] Sortie verte visible

## Logique du jeu
- [ ] Balle se déplace selon le roll/pitch du MPU6050
- [ ] Balle bloquée par les murs du labyrinthe
- [ ] Chronomètre démarre avec la partie
- [ ] Victoire détectée quand balle atteint la sortie
- [ ] Meilleur temps sauvegardé
- [ ] LED clignote à la victoire

## Boutons tactiles
- [ ] Bouton Start fonctionne
- [ ] Bouton Pause fonctionne
- [ ] Bouton Reset fonctionne

## Service systemd
- [ ] iot-interface.service copié dans /etc/systemd/system/
- [ ] Service activé avec systemctl enable
- [ ] Service démarre automatiquement au boot
