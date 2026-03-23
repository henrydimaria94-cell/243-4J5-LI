# Checklist de validation — Firmware LilyGO
**Étudiant :** Henri-Tadja
**Cours :** 243-4J5-LI | Projet mi-session

## Connexion matérielle
- [ ] LilyGO branché en USB
- [ ] MPU6050 connecté sur SDA (GPIO 21) et SCL (GPIO 22)
- [ ] LED rouge connectée sur GPIO 25
- [ ] BTN1 connecté sur GPIO 13
- [ ] BTN2 connecté sur GPIO 14
- [ ] BTN3 connecté sur GPIO 15
- [ ] POT1 connecté sur GPIO 32
- [ ] POT2 connecté sur GPIO 33
- [ ] POT3 connecté sur GPIO 34

## Compilation et upload
- [ ] auth.h rempli avec les vrais identifiants
- [ ] Compilation sans erreurs
- [ ] Upload réussi sur le LilyGO

## Tests MQTT
- [ ] Connexion au broker MQTT établie
- [ ] Topic buttons publié correctement
- [ ] Topic pots publié correctement
- [ ] Topic accel publié correctement (roll/pitch)
- [ ] Topic state publié correctement
- [ ] LED s'allume sur commande du RPi

## Tests capteurs
- [ ] BTN1 démarre la partie (GPIO 13)
- [ ] BTN2 met en pause (GPIO 14)
- [ ] BTN3 reset (GPIO 27)
- [ ] POT1 change la difficulté (1-3) (GPIO 32)
- [ ] POT2 change la vitesse (1-5) (GPIO 33)
- [ ] POT3 change la taille du labyrinthe (S/M/L) (GPIO 34)
- [ ] MPU6050 envoie roll et pitch correctement
- [ ] LED rouge clignote à la victoire (GPIO 25)
