// ═══════════════════════════════════════════════════════════════
// Test de diagnostic du modem SIM7600 - Commandes AT
// ═══════════════════════════════════════════════════════════════
// Ce sketch permet de tester le modem avec des commandes AT
// pour diagnostiquer les problèmes de connexion cellulaire

#define MODEM_TX    27
#define MODEM_RX    26
#define MODEM_PWRKEY 4

HardwareSerial SerialAT(1);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n=== DIAGNOSTIC MODEM SIM7600 ===\n");
  
  // ─── Séquence de power-on du modem ───
  pinMode(MODEM_PWRKEY, OUTPUT);
  digitalWrite(MODEM_PWRKEY, LOW);
  
  Serial.println("Allumage du modem SIM7600...");
  Serial.println("1. Impulsion PWRKEY (500ms)...");
  digitalWrite(MODEM_PWRKEY, HIGH);
  delay(500);
  digitalWrite(MODEM_PWRKEY, LOW);
  
  Serial.println("2. Attente initialisation modem (10s)...");
  delay(10000);  // Le SIM7600 met ~10s à démarrer
  
  // Initialiser la communication série avec le modem
  // Test avec différents baudrates
  Serial.println("3. Test des baudrates...");
  
  int baudrates[] = {115200, 9600, 19200, 38400, 57600};
  for (int i = 0; i < 5; i++) {
    Serial.print("   Essai ");
    Serial.print(baudrates[i]);
    Serial.print(" baud... ");
    
    SerialAT.begin(baudrates[i], SERIAL_8N1, MODEM_RX, MODEM_TX);
    delay(500);
    
    // Vider le buffer
    while (SerialAT.available()) SerialAT.read();
    
    SerialAT.println("AT");
    delay(1000);
    
    if (SerialAT.available()) {
      Serial.println("REPONSE DETECTEE !");
      while (SerialAT.available()) {
        Serial.write(SerialAT.read());
      }
      Serial.println("\n   --> Baudrate correct trouve !");
      break;
    } else {
      Serial.println("pas de reponse");
    }
  }
  
  // Réinitialiser à 115200
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
  delay(1000);
  
  Serial.println("\n4. Envoi de commandes AT au modem...\n");
  
  // Test 1 : Vérifier que le modem répond
  Serial.println("1. Test de communication (AT)");
  sendAT("AT");
  
  // Test 2 : Informations du modem
  Serial.println("\n2. Informations du modem (ATI)");
  sendAT("ATI");
  
  // Test 3 : Vérifier la carte SIM
  Serial.println("\n3. Carte SIM (AT+CPIN?)");
  sendAT("AT+CPIN?");
  
  // Test 4 : Opérateur réseau
  Serial.println("\n4. Opérateur réseau (AT+COPS?)");
  sendAT("AT+COPS?");
  
  // Test 5 : Qualité du signal
  Serial.println("\n5. Qualité du signal (AT+CSQ)");
  sendAT("AT+CSQ");
  
  // Test 6 : État de l'enregistrement réseau
  Serial.println("\n6. Enregistrement réseau (AT+CREG?)");
  sendAT("AT+CREG?");
  
  // Test 7 : Type de réseau (2G/3G/4G)
  Serial.println("\n7. Type de réseau (AT+CPSI?)");
  sendAT("AT+CPSI?");
  
  // Test 8 : Configuration APN
  Serial.println("\n8. Configuration APN (AT+CGDCONT?)");
  sendAT("AT+CGDCONT?");
  
  // Test 9 : État de connexion GPRS
  Serial.println("\n9. État GPRS (AT+CGATT?)");
  sendAT("AT+CGATT?");
  
  // Test 10 : Adresse IP (si connecté)
  Serial.println("\n10. Adresse IP (AT+CGPADDR=1)");
  sendAT("AT+CGPADDR=1");
  
  Serial.println("\n=== FIN DU DIAGNOSTIC ===");
  Serial.println("\nInterprétation des résultats :");
  Serial.println("- AT+CPIN : READY = SIM OK, sinon SIM absente/verrouillée");
  Serial.println("- AT+CSQ  : >10 = signal acceptable, <10 = signal faible");
  Serial.println("- AT+CREG : 0,1 ou 0,5 = enregistré sur le réseau");
  Serial.println("- AT+CGATT: 1 = attaché au GPRS");
  Serial.println("\nTapez des commandes AT dans le moniteur série (ex: AT+COPS?)");
}

void loop() {
  // Mode passthrough : transférer les données entre Serial et SerialAT
  while (Serial.available()) {
    SerialAT.write(Serial.read());
  }
  while (SerialAT.available()) {
    Serial.write(SerialAT.read());
  }
}

void sendAT(const char* cmd) {
  Serial.print(">> ");
  Serial.println(cmd);
  
  // Vider le buffer avant d'envoyer
  while (SerialAT.available()) SerialAT.read();
  
  SerialAT.println(cmd);
  delay(2000);  // Attendre 2s pour la réponse
  
  Serial.print("<< ");
  bool gotResponse = false;
  while (SerialAT.available()) {
    Serial.write(SerialAT.read());
    gotResponse = true;
  }
  
  if (!gotResponse) {
    Serial.print("[PAS DE REPONSE]");
  }
  
  Serial.println();
}
