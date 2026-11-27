# Änderungsprotokoll

*[🇬🇧 English version](CHANGELOG.en.md)*

`ha_audi_connect` beginnt bei 1.0.0. Die Versionen 2.x der früheren Integration `audiconnect` stehen auf der [Release-Seite des Upstreams](https://github.com/audiconnect/audi_connect_ha/releases).

## 1.0.0 – 2026-11-22

**Neu**
- **Karte:** Die Integration bringt eine eigene Dashboard-Karte (`audi-connect-card`) mit: Foto oder Symbol, Status, Ladeband, Fahrten, Fahrzeugdetails und eine einklappbare Klimatisierung. Ein Tipp auf den Titel öffnet die Integration, langes Drücken aktualisiert die Fahrzeugdaten.
- **Karte – Türen und Fenster:** Eine realistische Draufsicht auf das Auto im Dialog, mit einem Statussymbol je Tür und Fenster.
- **Karte – Editor:** Audi-Logo, Fahrten, Klimatisierung und Fahrzeugdetails lassen sich ein- und ausschalten. Die Sitz- und Zonentasten vorne und hinten sind getrennte Optionen (standardmäßig aus). „Letzte Fahrt“ und „Langzeit“ sind einzeln wählbar (`show_trip_last`, `show_trip_long`), und die Zeilen der Fahrzeugdetails lassen sich auswählen (`stats_rows`); angeboten wird nur, was das Auto meldet.
- **Karte – Anzeige:** Fehlgeschlagene Aktionen, der Tag des Ladeendes, Bedienung per Tastatur und Screenreader und ein unbekannter Schlosszustand statt „verriegelt“. Die letzte Fahrt zeigt, wann sie endete („vor 10 Std.“).
- **Fahrten:** Sensoren für die letzte Fahrt und die Langzeit-Summen, mit Zustandsklassen, damit die Summen Langzeitstatistiken behalten. Dazu der Zeitstempel-Sensor „Letzte Fahrt Ende“, der nur einen Wert liefert, wenn das Auto eine echte Zeit mit Zeitzone schickt.
- **Weitere Sensoren:** Öffnung der Fenster in Prozent, Warnungen, Parkbremse, Batteriepflege-Modus, Klimatisierungsmodus (auch als Auswahl), Ladeszenario, Sicherheitsstatus des Autos und das Ende der Online-Dienste.
- **Laden:** Die vom Auto gemeldeten Ladeziel-Grenzen, eine Auswahl für den Ladestrom des Profils, in dem das Auto steht, und der Schalter zum automatischen Entriegeln des Ladesteckers (experimentell). Langzeitstatistiken für Ladestand, Reichweite, Tankfüllung, Ladeleistung und Außentemperatur.
- **Bedienung:** Hupen-Taste (standardmäßig aus, getrennt vom stillen Blinken). Dienste zum Anlegen, Löschen und Ein-/Ausschalten von Klimatisierungs-Timern.
- **Übersetzungen:** Entitätsnamen auf Englisch und Deutsch, dazu vollständige Übersetzungen für fi, fr, nl, nb, pt und pt-BR. Entitäts-IDs entstehen aus den englischen Namen, in welcher Sprache Home Assistant auch läuft.
- **Fehlersuche:** Zwei Optionen, beide standardmäßig aus: Die Rohantworten des Autos ins Debug-Log schreiben (FIN, Positionen, Benutzer-ID, PINs und Tokens maskiert) und optional FIN und Position ungeschwärzt lassen. Anmelde- und Token-Routen werden nie geloggt.
- **Reparatur-Hinweise:** Meldet das Auto Online-Dienste als beendet oder endet einer innerhalb von 30 Tagen, erscheint unter **Reparaturen** ein Hinweis mit den Diensten und dem Datum. Er verschwindet von selbst.
- **Fehlermeldungen:** Die Meldungen bei fehlgeschlagenen Befehlen, Dienstaufrufen und der Anmeldung sind übersetzt (8 Sprachen).
- **Diagnose:** Sie listet alle Capability-IDs und die Supports-Flags des Autos, benennt die Routen für Klimatisierung, Laden, Aufwecken, Hupen und Timer und sagt, welche Fahrtwerte vorliegen. `probe_api` und lesende Proben bekannter Routen (BFF, GraphQL, `bs/`, Fahrten).

**Geändert**
- **Domain:** Die Integration heißt jetzt `ha_audi_connect` (vorher `audiconnect`), und das Verzeichnis `custom_components/ha_audi_connect`, damit sie sich nicht mit der Upstream-Integration überschneidet. Das ist eine neue Integration für Home Assistant: Eintrag entfernen, neu einrichten, Dienste `audiconnect.*` in Automationen auf `ha_audi_connect.*` umstellen. Verlauf und Entity-IDs bleiben erhalten, wenn der alte Eintrag vorher entfernt wird (siehe README).
- **Laden starten und stoppen:** Die Tasten bleiben, sind aber experimentell und standardmäßig deaktiviert: Audi nimmt den Befehl an, ein A6 e-tron führt ihn nicht aus.
- **Standlicht und Bremsstatus:** Beide zeigen schlicht An/Aus statt „Sicher/Unsicher“.
- **Aufwecken:** Die Taste ist standardmäßig aus. Ein Aufwecken, das das Auto nicht ausführt, ist eine Warnung und kein Fehler.
- **Optionen:** Das Abfrageintervall wird erklärt. Entitäten sind nach Nutzung einsortiert, Verbindungsdetails in der Diagnose, der Kilometerstand in der Hauptansicht. Der Fahrzeugtyp gehört zum Gerätemodell und ist kein Sensor mehr.
- **Sensoren nur bei Bedarf:** Konnektivität, Aktivität, AC-Strombegrenzung und ein weiterer Motor entstehen nur bei Autos, die sie melden. Die Händler- und Service-Sensoren erscheinen nur, wenn es etwas zu zeigen gibt.
- **Befehle:** Befehle ans Auto (Schalter, Tasten, Schloss, Klima, Zahlen, Auswahlen) laufen nacheinander statt gleichzeitig, weil Audi die Anfragen begrenzt.
- **Neuanmeldung:** Sie lehnt ein anderes myAudi-Konto ab als das, mit dem der Eintrag eingerichtet wurde.

**Korrigiert**
- **Diagnose:** Ein Fahrtende, das als echte Zeit ankommt, gilt als lesbar.
- **Anmeldung:** Ein rotierter Refresh-Token bleibt erhalten, wenn ein späterer Login- oder Aktualisierungsschritt scheitert. Nach einem Befehl, der schon aktualisiert hat, folgt keine zweite Cloud-Abfrage.
- **Eingaben:** Zahlen und Auswahlen zeigen den eben geschriebenen Wert, bis das Auto einen anderen meldet. Die Zieltemperatur eines stehenden Autos wird in 0,5-Grad-Schritten ins Auto geschrieben.
- **Werte:** Die Restladezeit ist unbekannt statt 0, solange ohne Schätzung geladen wird. Abfahrtstimer und Ladeziel-Grenzen werden so gelesen, wie der A6 sie meldet. Der Device-Tracker speichert die FIN nicht mehr als Attribut. Geheimnisse werden in Logs geschwärzt.
- **Karte:** Glas und Tagfahrlicht behalten ihre Farbe, unabhängig von der Primärfarbe des Themes. Der Fokus bleibt im geöffneten Dialog.

**Entfernt**
- Der Sensor für das Navigationsziel des Ladens, der doppelte Sensor für den Ziel-Ladestand und die lokalen Händler- und Servicedaten.
- Die Option „Cloud-Aktualisierung beim Start“: Wurde die erste Abfrage übersprungen, gab es keine Entitäten.
- Die ungenutzte alte Lader-Abfrage und der nicht erreichbare Schritt für den Geräte-Code.
