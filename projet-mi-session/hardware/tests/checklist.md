## Checklist de validation — Prototype Breadboard

**Date de validation:** 23 mars 2026  
**Testé par:** Henri Tadja  
**Matériel:** ESP32-WROOM-32 + Breadboard + Composants

---

### Alimentation

- [x] **Alimentation 3.3 V mesurée aux pins VCC de chaque composant**
  - MPU6050 VCC: 3.3V ✅
  - Boutons pull-up: 3.3V ✅
  - LED anode (via résistance): ~2V ✅
  - Test effectué: Multimètre en mode tension DC

- [x] **Masse commune vérifiée** (multimètre en continuité)
  - GND ESP32 ↔ GND MPU6050: Continuité ✅
  - GND ESP32 ↔ GND Breadboard rail: Continuité ✅
  - Test effectué: Multimètre mode continuité (bip)

---

### LED

- [x] **Chaque LED s'allume avec la tension correcte** (≈ 2 V aux bornes)
  - LED1 (GPIO 25): Allumée avec commande HIGH
  - Tension mesurée aux bornes: ~2.1V (LED rouge)
  - Test effectué: Multimètre + commande digitalWrite

- [x] **Résistances de limitation vérifiées**
  - Résistance LED: 220Ω (nominale)
  - Valeur mesurée: ~218Ω ✅
  - Test effectué: Multimètre mode résistance

---

### MPU6050 (Accéléromètre/Gyroscope)

- [x] **MPU6050 répond aux commandes I2C** (scan I2C réussi)
  - Adresse détectée: 0x68
  - Logs série: `[MPU6050] Connexion etablie`
  - Test effectué: Scan I2C via code Arduino

- [x] **Connexions I2C vérifiées**
  - SDA (GPIO 21): Connecté au MPU6050 SDA ✅
  - SCL (GPIO 22): Connecté au MPU6050 SCL ✅
  - Pull-up internes activés (pas de résistances externes nécessaires)

---

### Boutons

- [x] **Chaque bouton produit bien 0 V / 3.3 V selon l'état**
  - BTN1 (GPIO 13): Relâché=3.3V (pull-up externe 10kΩ), Pressé=0V ✅
  - BTN2 (GPIO 14): Relâché=3.3V (pull-up externe 10kΩ), Pressé=0V ✅
  - BTN3 (GPIO 15): Relâché=3.3V (pull-up externe 10kΩ), Pressé=0V ✅
  - Test effectué: Multimètre + pression manuelle

- [x] **Résistances pull-up externes vérifiées**
  - Valeur nominale: 10kΩ (chacune)
  - Valeurs mesurées: ~9.8kΩ, ~10.1kΩ, ~9.9kΩ ✅
  - Connexions: Entre GPIO et 3.3V

---

### Potentiomètres

- [x] **Chaque potentiomètre produit une tension variable 0–3.3 V**
  - POT1 (GPIO 32): 0V (min) → 3.3V (max) ✅
  - POT2 (GPIO 33): 0V (min) → 3.3V (max) ✅
  - POT3 (GPIO 34): 0V (min) → 3.3V (max) ✅
  - Test effectué: Multimètre + rotation complète de chaque axe

- [x] **Valeur ADC cohérente** (0-4095 pour 12 bits)
  - POT1 pleine rotation: 0 → 4095 ✅
  - POT2 pleine rotation: 0 → 4095 ✅
  - POT3 pleine rotation: 0 → 4095 ✅
  - Test effectué: Logs série affichant valeurs ADC

---

### Câblage général

- [x] **Pas de court-circuit détecté**
  - Test effectué: Vérification visuelle + test continuité croisée
  
- [x] **Toutes les connexions sécurisées**
  - Fils bien insérés dans breadboard
  - Pas de fils desserrés
  - Test effectué: Vérification visuelle + test léger tirage

- [x] **Organisation du breadboard claire**
  - Rail alimentation 3.3V (rouge)
  - Rail GND (noir/bleu)
  - Composants espacés pour éviter interférences

---

### Schéma de câblage
```
ESP32-WROOM-32
├─ GPIO 13 ──[10kΩ]── 3.3V  (BTN1 pull-up)
│            └─[BTN1]─ GND
├─ GPIO 14 ──[10kΩ]── 3.3V  (BTN2 pull-up)
│            └─[BTN2]─ GND
├─ GPIO 15 ──[10kΩ]── 3.3V  (BTN3 pull-up)
│            └─[BTN3]─ GND
├─ GPIO 25 ──[220Ω]──[LED1]─ GND
├─ GPIO 32 ── POT1 curseur (0-3.3V)
├─ GPIO 33 ── POT2 curseur (0-3.3V)
├─ GPIO 34 ── POT3 curseur (0-3.3V)
├─ GPIO 21 (SDA) ── MPU6050 SDA
├─ GPIO 22 (SCL) ── MPU6050 SCL
├─ 3.3V ── MPU6050 VCC, Potentiomètres VCC, Pull-ups
└─ GND ── Masse commune
```

---

### Photos du montage

- [ ] Photo vue d'ensemble du breadboard
- [ ] Photo connexions ESP32
- [ ] Photo MPU6050
- [ ] Photo boutons avec résistances
- [ ] Photo LED avec résistance

*(À joindre dans le dossier `hardware/photos/` du projet)*

---

**✅ Prototype breadboard validé et opérationnel**

**Signature:** Henri Tadja  
**Date:** 23 mars 2026
