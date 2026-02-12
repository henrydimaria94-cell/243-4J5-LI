// Contrôle de LEDs via commandes série
// Pour LilyGO A7670E - Exercice 7.6
// Commandes acceptées: "vert", "bleu", "off"

// Définition des pins pour les LEDs
#define LED_VERTE 27  // Pin GPIO pour LED verte
#define LED_BLEUE 12  // Pin GPIO pour LED bleue

String commandeRecue = "";  // Buffer pour stocker la commande

void setup() {
  // Initialiser la communication série
  Serial.begin(115200);
  delay(1000);

  // Configurer les pins des LEDs en sortie
  pinMode(LED_VERTE, OUTPUT);
  pinMode(LED_BLEUE, OUTPUT);

  // Éteindre toutes les LEDs au démarrage
  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_BLEUE, LOW);

  Serial.println("========================================");
  Serial.println("Contrôle de LEDs via Port Série");
  Serial.println("========================================");
  Serial.println("Commandes disponibles:");
  Serial.println("  - vert  : Allume LED verte (GPIO 27), éteint LED bleue");
  Serial.println("  - bleu  : Allume LED bleue (GPIO 12), éteint LED verte");
  Serial.println("  - off   : Éteint toutes les LEDs");
  Serial.println("========================================");
  Serial.println("En attente de commandes...");
}

void loop() {
  // Vérifier si des données sont disponibles sur le port série
  if (Serial.available() > 0) {
    // Lire la commande jusqu'au caractère de fin de ligne
    commandeRecue = Serial.readStringUntil('\n');

    // Nettoyer la commande (enlever espaces et retours chariot)
    commandeRecue.trim();
    commandeRecue.toLowerCase();  // Convertir en minuscules

    // Afficher la commande reçue
    Serial.print("Commande reçue: '");
    Serial.print(commandeRecue);
    Serial.println("'");

    // Traiter la commande
    if (commandeRecue == "vert" || commandeRecue == "verte") {
      // Allumer LED verte, éteindre LED bleue
      digitalWrite(LED_VERTE, HIGH);
      digitalWrite(LED_BLEUE, LOW);
      Serial.println("-> LED VERTE allumée (GPIO 27), LED BLEUE éteinte");

    } else if (commandeRecue == "bleu" || commandeRecue == "bleue") {
      // Allumer LED bleue, éteindre LED verte
      digitalWrite(LED_VERTE, LOW);
      digitalWrite(LED_BLEUE, HIGH);
      Serial.println("-> LED BLEUE allumée (GPIO 12), LED VERTE éteinte");

    } else if (commandeRecue == "off" || commandeRecue == "eteindre") {
      // Éteindre toutes les LEDs
      digitalWrite(LED_VERTE, LOW);
      digitalWrite(LED_BLEUE, LOW);
      Serial.println("-> Toutes les LEDs éteintes");

    } else {
      // Commande non reconnue
      Serial.println("-> Commande non reconnue!");
      Serial.println("   Utilisez: vert, bleu, ou off");
    }

    // Vider le buffer
    commandeRecue = "";
  }

  // Petite pause pour éviter de surcharger le processeur
  delay(10);
}
