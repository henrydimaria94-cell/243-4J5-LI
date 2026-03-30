# Guide de Fabrication PCB - Shield ESP32

## Vue d'ensemble

Ce guide décrit le processus de fabrication du PCB pour le shield ESP32. Le PCB est conçu pour être fabriqué par un service de fabrication standard (JLCPCB, PCBWay, OSH Park, etc.).

## Spécifications du PCB

### Caractéristiques générales
- **Dimensions**: 210 × 140 mm
- **Nombre de couches**: 2 (Top et Bottom)
- **Épaisseur**: 1.6 mm
- **Matériau**: FR-4
- **Finition de surface**: HASL (Hot Air Solder Leveling) ou ENIG recommandé
- **Couleur du masque de soudure**: Vert (standard) ou au choix
- **Couleur de la sérigraphie**: Blanc

### Caractéristiques électriques
- **Largeur minimale de piste**: 0.25 mm
- **Espacement minimal**: 0.2 mm
- **Diamètre minimal de via**: 0.6 mm
- **Diamètre de perçage via**: 0.3 mm
- **Classe de règles**: IPC Class 2 (standard)

## Fichiers Gerber

Les fichiers Gerber sont situés dans le dossier `gerbers/` et incluent:

| Fichier | Description | Couche |
|---------|-------------|--------|
| `projet-F_Cu.gtl` | Cuivre face avant | Top Copper (L1) |
| `projet-B_Cu.gbl` | Cuivre face arrière | Bottom Copper (L2) |
| `projet-F_Mask.gts` | Masque de soudure avant | Top Solder Mask |
| `projet-B_Mask.gbs` | Masque de soudure arrière | Bottom Solder Mask |
| `projet-F_Silkscreen.gto` | Sérigraphie avant | Top Silkscreen |
| `projet-B_Silkscreen.gbo` | Sérigraphie arrière | Bottom Silkscreen |
| `projet-Edge_Cuts.gm1` | Contour du PCB | Board Outline |
| `projet-PTH.drl` | Perçages métallisés | Plated Holes |
| `projet-NPTH.drl` | Perçages non métallisés | Non-Plated Holes |
| `projet-job.gbrjob` | Fichier de job Gerber | Metadata |

## Instructions de commande

### 1. Préparation des fichiers

1. Créer une archive ZIP contenant tous les fichiers du dossier `gerbers/`:
   ```bash
   cd fabrication/gerbers/
   zip shield-pcb-gerbers.zip *.gtl *.gbl *.gts *.gbs *.gto *.gbo *.gm1 *.drl *.gbrjob
   ```

2. Vérifier que tous les fichiers sont inclus dans l'archive

### 2. Choix du fabricant

Fabricants recommandés:
- **JLCPCB** (Chine) - Économique, délai 5-10 jours
- **PCBWay** (Chine) - Qualité supérieure, prix modéré
- **OSH Park** (USA) - Haute qualité, bon pour prototypes
- **Eurocircuits** (Europe) - Fabrication locale européenne
- **PCB Solutions** (Canada) - Fabrication locale canadienne

### 3. Paramètres de commande

Lors de la commande sur le site du fabricant, utiliser ces paramètres:

#### JLCPCB
- **Base Material**: FR-4
- **Layers**: 2
- **Dimensions**: 210 × 140 mm (sera détecté automatiquement)
- **PCB Qty**: 5 (minimum économique)
- **PCB Thickness**: 1.6 mm
- **PCB Color**: Green (ou au choix)
- **Surface Finish**: HASL (standard) ou ENIG (meilleur pour soudage)
- **Copper Weight**: 1 oz
- **Gold Fingers**: No
- **Castellated Holes**: No
- **Remove Order Number**: Yes (optionnel, coût supplémentaire)

#### PCBWay / Autres fabricants
- Similaire à JLCPCB
- Télécharger le ZIP des fichiers Gerber
- Le système détectera automatiquement les paramètres
- Vérifier les dimensions et le nombre de couches

### 4. Vérification avant commande

Avant de valider la commande:
1. ✅ Vérifier l'aperçu Gerber sur le site du fabricant
2. ✅ Vérifier les dimensions du PCB
3. ✅ Vérifier le nombre de trous (PTH et NPTH)
4. ✅ Vérifier que les couches sont correctement détectées
5. ✅ Comparer le prix entre plusieurs quantités (5, 10, 20 pcs)

## Assemblage

### Composants requis

Voir le fichier `bom.csv` pour la liste complète des composants.

### Ordre d'assemblage recommandé

1. **Composants SMD** (si applicable): Souder en premier
2. **Composants bas**: Résistances, diodes
3. **Composants moyens**: Boutons, LED
4. **Composants hauts**: Potentiomètres, connecteurs
5. **Modules**: ESP32 (LilyGO), MPU-6050

### Outils nécessaires

- Fer à souder (température réglable, 350-400°C recommandé)
- Soudure 60/40 ou sans plomb (0.8mm de diamètre)
- Flux de soudure (optionnel mais recommandé)
- Pince à épiler
- Cutter ou pince coupante
- Multimètre
- Loupe ou microscope USB (optionnel)

### Procédure de soudage

#### Pour composants traversants (THT)
1. Insérer le composant dans le PCB
2. Plier légèrement les pattes pour maintenir en place
3. Retourner le PCB
4. Souder chaque patte:
   - Chauffer simultanément la patte et le pad (2-3 secondes)
   - Appliquer la soudure
   - Retirer la soudure puis le fer
5. Couper l'excédent de patte avec une pince coupante
6. Vérifier visuellement: soudure brillante, conique, sans pont

#### Pour modules (ESP32, MPU-6050)
1. **Option A - Headers soudés**:
   - Souder des headers mâles sur les modules
   - Souder des sockets femelles sur le PCB
   - Enficher les modules (amovibles)

2. **Option B - Soudage direct**:
   - Souder directement les modules sur le PCB
   - Plus compact mais non amovible

**Recommandation**: Utiliser l'option A pour faciliter le dépannage

### Tests après assemblage

1. **Inspection visuelle**:
   - Vérifier toutes les soudures
   - Chercher les ponts de soudure
   - Vérifier l'orientation des composants polarisés (LED, diodes)

2. **Test de continuité**:
   - Vérifier qu'il n'y a pas de court-circuit entre VCC et GND
   - Tester la continuité des pistes critiques

3. **Test fonctionnel**:
   - Connecter l'alimentation (5V via USB)
   - Vérifier la consommation de courant (devrait être < 100mA au repos)
   - Programmer l'ESP32 avec un firmware de test
   - Tester chaque composant individuellement

## Dépannage fabrication

### Problèmes courants

| Problème | Cause probable | Solution |
|----------|----------------|----------|
| PCB ne s'allume pas | Court-circuit VCC-GND | Vérifier au multimètre, chercher ponts de soudure |
| Composant ne fonctionne pas | Soudure froide ou manquante | Refaire les soudures suspectes |
| LED ne s'allume pas | Polarité inversée ou résistance manquante | Vérifier orientation LED, tester résistance |
| ESP32 ne se programme pas | Mauvaise connexion USB ou driver | Vérifier câble, installer drivers CH340/CP2102 |
| Valeurs potentiomètre erratiques | Mauvaise soudure ou interférence | Vérifier soudures, ajouter condensateurs de découplage |

### Modifications après fabrication

Si des modifications sont nécessaires:
1. Documenter la modification dans un fichier `MODIFICATIONS.md`
2. Utiliser des fils de reprise (jumper wires) si nécessaire
3. Mettre à jour les fichiers KiCad pour la prochaine révision
4. Incrémenter le numéro de révision

## Coûts estimés

### Fabrication PCB (estimation 2026)

| Fabricant | Quantité | Prix unitaire | Délai | Frais de port |
|-----------|----------|---------------|-------|---------------|
| JLCPCB | 5 pcs | ~5-8 USD | 5-10 jours | ~15-30 USD |
| PCBWay | 5 pcs | ~15-25 USD | 5-10 jours | ~20-35 USD |
| OSH Park | 3 pcs | ~20-30 USD | 10-14 jours | Inclus (USA) |

**Note**: Prix indicatifs pour PCB standard 2 couches. Frais de douane possibles pour expédition internationale.

### Composants (estimation)

- Composants passifs (R, LED, boutons): ~10-15 USD
- Potentiomètres (×3): ~5-10 USD
- Module LilyGO T-A7670E: ~30-50 USD
- Module MPU-6050: ~5-10 USD
- Connecteurs et headers: ~5-10 USD

**Total estimé par unité**: ~60-95 USD (PCB + composants)

## Contrôle qualité

### Checklist de réception PCB

Lors de la réception des PCB fabriqués:
- [ ] Vérifier les dimensions avec un pied à coulisse
- [ ] Vérifier l'absence de rayures ou défauts visuels
- [ ] Tester la continuité des pistes principales
- [ ] Vérifier qu'il n'y a pas de court-circuit VCC-GND
- [ ] Comparer avec les fichiers Gerber (aperçu en ligne)
- [ ] Vérifier tous les trous de perçage
- [ ] Tester l'épaisseur du PCB (devrait être 1.6mm)

### Checklist qualité assemblage

Après assemblage:
- [ ] Tous les composants sont correctement orientés
- [ ] Toutes les soudures sont propres et brillantes
- [ ] Pas de ponts de soudure visibles
- [ ] Pas de résidu de flux excessif
- [ ] Test de continuité réussi
- [ ] Test fonctionnel de base réussi
- [ ] Documentation des modifications éventuelles

## Révisions futures

### Pour la prochaine révision du PCB

Améliorations suggérées:
1. Ajouter des condensateurs de découplage (100nF) près de chaque IC
2. Ajouter un interrupteur d'alimentation
3. Ajouter des LEDs de statut (Power, TX, RX)
4. Prévoir des trous de montage (M3) aux quatre coins
5. Ajouter une zone pour identifier le PCB (nom, version, date)
6. Augmenter l'espacement entre composants pour faciliter le soudage manuel
7. Ajouter des points de test pour faciliter le débogage

### Documentation des révisions

Format pour numérotation: `v[Major].[Minor]`
- **Major**: Changement de fonctionnalité ou incompatibilité
- **Minor**: Corrections, améliorations mineures

Exemple:
- v1.0: Version initiale (cette version)
- v1.1: Correction erreurs mineures
- v2.0: Ajout de fonctionnalités majeures

## Support et ressources

### Fichiers de conception
- Fichiers KiCad source: `../kicad/`
- Schéma PDF: À générer depuis KiCad
- Layout PDF: À générer depuis KiCad

### Tutoriels recommandés
- Soudage de composants traversants: [YouTube - Guide complet]
- Lecture de schémas électroniques: [Electronics Tutorials]
- Dépannage de PCB: [Sparkfun PCB Basics]

### Contact
Pour questions sur la fabrication:
- Email: [votre-email]
- GitHub Issues: [lien-repo]/issues

---

**Document créé**: 2026-03-30  
**Révision PCB**: v1.0  
**Auteur**: [Votre nom]
