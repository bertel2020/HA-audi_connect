# Audi Connect – Benutzerhandbuch

*[🇬🇧 English version](user-guide.en.md)*

Dieses Handbuch beschreibt, was die Integration nach der Einrichtung bietet: Bedienelemente, Laden, Klimatisierung, Service-Aktionen, Diagnose und Reparatur-Hinweise. Installation, Einrichtung und Optionen stehen in der [README](../README.md), die Dashboard-Karte ebenfalls. Hintergründe zu Funktionsstatus und API stehen in den [API-Hinweisen](api-notes.md).

## Bedienelemente

Die Geräteseite jedes Fahrzeugs bietet die Aktionen direkt an, die häufigen brauchen also keinen Service-Aufruf mehr. Was verfügbar ist, hängt davon ab, was das Fahrzeug meldet, und bei Schloss und Motor davon, dass eine S-PIN eingerichtet ist. Die Entities sind auf der Geräteseite gruppiert; die vollständige Liste der Sensoren und Binärsensoren (Reichweite, Kilometerstand, Laden, Türen und Fenster, Fahrten, Serviceintervalle, Datenaktualität und mehr) richtet sich danach, was das Auto meldet.

| Bedienelement                  | Typ     | Ersetzt                                               |
| ------------------------------ | ------- | ----------------------------------------------------- |
| `Door lock`                    | Lock    | `execute_vehicle_action` mit `lock` / `unlock`        |
| `Climatisation`                | Climate | `start_climate_control` / `stop_climatisation`        |
| `Preheater`                    | Switch  | `execute_vehicle_action` mit `start_/stop_preheater`  |
| `Global charge target`         | Number  | `set_target_soc`                                      |
| `Current location target`      | Number  | `set_location_charge_target` (ohne `profile_id`)      |
| `<Profil> charge target`       | Number  | `set_location_charge_target` mit `profile_id`         |
| `Start engine` / `Stop engine` | Button  | `start_engine` / `stop_engine`                        |
| `Flash lights`                 | Button  | –, neu                                                |
| `Charge mode`                  | Select  | `set_charge_mode`                                     |
| `Start/Stop charging (experimental)` | Button | `execute_vehicle_action` mit `start_/stop_charger`; siehe unten |
| Ladestrom des Standortprofils  | Select  | –, neu; nur wenn das Auto die Einstellung meldet      |
| `Refresh vehicle data`         | Button  | `refresh_vehicle_data`                                |
| `Wake vehicle`                 | Button  | –, neu; braucht eine gemeldete Wecken-Fähigkeit       |
| `Honk and flash`               | Button  | –, neu; standardmäßig deaktiviert                     |
| `Climatisation ON/OFF`         | Switch  | –, Auth0-Fahrzeuge                                    |
| `Window heating`, `Climatisation at unlock`, Sitzzonen | Switch | –, die im Auto gespeicherten Klima-Einstellungen |
| `Climatisation mode`           | Select  | `start_climate_control` mit `climatisation_mode`      |
| `Start/Stop window heating (experimental)` | Button | `execute_vehicle_action` mit `start_/stop_window_heating` |
| `Release plug after charging (experimental)` | Switch | –                                         |

### Ladeziele

Es gibt drei Arten, weil das Auto drei Stellen für die Zahl hat:

- **Global charge target** schreibt `charging/settings`. Es bestimmt nicht, wo eine Ladung an einem Standort endet (Upstream #722), ist also das am wenigsten nützliche der drei und bleibt nur, weil es eine echte, eigene Einstellung ist.
- **Current location charge target** schreibt das Profil, in dem das Auto gerade steht, von der Integration aus `vehiclePositionedInProfileID` ermittelt. Nutze es in Automationen, die gelten sollen, wo auch immer das Auto steht.
- **Eine Zahl pro Standortprofil**, benannt nach dem Profil („Home charge target“, „Work charge target“). Sie werden aus dem gelesen, was das Auto meldet; ein im Auto hinzugefügtes oder entferntes Profil erscheint oder verschwindet also nach dem nächsten Refresh. Ein im Auto gelöschtes Profil macht sein Bedienelement nicht verfügbar, statt ein veraltetes Ziel zu zeigen.

`sensor.<fahrzeug>_active_charging_profile_name` zeigt, welches Profil gilt, sodass ein Dashboard den maßgeblichen Standort neben den Reglern anzeigen kann. Die Profil-Bedienelemente hängen an der Profil-ID, nicht am Namen: Wer einen Standort in der myAudi-App umbenennt, benennt das Bedienelement um, ohne Automationen zu brechen, die darauf verweisen.

Die Service-Aktionen weiter unten funktionieren weiterhin und bleiben der Weg zu den parametrisierten Befehlen: `start_climate_control` (Temperatur, Sitz- und Scheibenheizung, Klimamodus) und `start_auxiliary_heating` (Dauer) nehmen Einstellungen, die das Fahrzeug nicht zurückmeldet, und haben deshalb kein Bedienelement auf der Seite.

### Laden starten und stoppen

Die Tasten `Start charging (experimental)` und `Stop charging (experimental)` gibt es, aber sie sind doppelt abgesichert: Sie erscheinen nur mit der Option _Enable experimental vehicle controls_, nur bei Autos, die eine Lade-Fähigkeit melden, und sind in der Entity-Registry standardmäßig deaktiviert. Das Auto meldet kein eigenes Merkmal für „Laden fernstarten“, die Integration kann also nicht erkennen, ob es den Befehl ausführt. Beides ist auch über `execute_vehicle_action` erreichbar (`start_charger`, `stop_charger`, `start_timed_charger`).

Prüfe die Wirkung an deinem Auto, bevor du dich in einer Automation darauf verlässt. An einem A6 e-tron wird der Befehl von der API angenommen, aber das Auto führt ihn nicht aus: Stoppen, zweimal aus ruhigem Zustand gesendet, ließ das Auto weiter mit 6,5 kW laden. Starten ist unbewiesen. Es schien einmal zu funktionieren, aber das Auto hatte damals ein Ziel weit über dem Ladestand und hätte ohnehin geladen; später mit dem Ziel unter dem Ladestand wurde der Befehl angenommen und es passierte nichts. Zeitgesteuertes Laden läuft über denselben Befehl und ist deshalb ebenfalls unsicher.

Zuverlässiger ist `Target state of charge`: Ein Wert über dem aktuellen Ladestand startet eine Ladung, ein Wert darunter stoppt sie. Das war bei allen Tests in jede Richtung der Hebel, der sich konsistent verhalten hat. Die Abfahrtstimer des Autos sind der andere verlässliche Weg und werden hier gemeldet, aber noch nicht geschrieben.

Zahlen- und Auswahlfelder (Ladeziele, `Charge mode`, `Climatisation mode`) zeigen nach dem Schreiben den gesendeten Wert, bis das Auto einen anderen meldet, höchstens aber 20 Minuten lang. Das Auto bestätigt solche Werte oft erst nach Minuten; ohne diese Annahme würde das Bedienelement sofort auf den alten Wert zurückspringen.

Nach einem Befehl fragt die Integration die Cloud einmal ab. Hat der Befehl selbst schon eine Abfrage ausgelöst, folgt keine zweite.

### Blinken und Hupen

`Flash` lässt die Fahrzeugbeleuchtung zehn Sekunden blinken. Das Auto muss eine Position gemeldet haben, weil die API eine verlangt; das Bedienelement lehnt ab, statt eine Anfrage zu senden, die abgelehnt würde.

`Honk and flash` lässt zusätzlich die Hupe ertönen. Es ist ein eigener Button und in der Entity-Registry standardmäßig deaktiviert, weil er laut ist. Beide nutzen denselben Endpunkt, aber `Flash` sendet nur den Blink-Modus und kann die Hupe deshalb nie auslösen.

## Klimatisierung

Die Climate-Entity schaltet die Klimatisierung ein und aus und setzt die Zieltemperatur. Das Auto meldet, ob die Klimatisierung läuft und in welchem Modus (Heizen, Kühlen, Lüften), die Entity zeigt also das Fahrzeug und nicht, was Home Assistant zuletzt angefordert hat.

Zwei Dinge macht sie bewusst nicht. Sie hat keine Ist-Temperatur, weil das Auto die Außentemperatur meldet und nicht die im Innenraum, und die Außentemperatur als Ist-Temperatur einer Climate-Entity anzuzeigen würde falsch darstellen, was gemessen wird. Und sie bietet weder Sitz- oder Scheibenheizung noch Klimatisierung beim Entsperren oder den Komfort-/Eco-Modus an: Das Fahrzeug meldet das nie zurück, ein Bedienelement würde also nur zeigen, was du zuletzt eingestellt hast. Dafür die Service-Aktion `start_climate_control` verwenden.

Die Zieltemperatur kommt vom Auto, das sie in seinen Klima-Einstellungen meldet. Home Assistant hält nur als Rückfall einen Wert vor, für ein Fahrzeug, das keinen meldet, und für den Moment zwischen Änderungswunsch und Bestätigung durch das Auto. Das Auto speichert halbe Grad, und das Bedienelement geht ebenfalls in halben Graden. Bei ausgeschalteter Klimatisierung wird ein neues Ziel in die Einstellungen des Autos geschrieben, ohne sie zu starten; das Auto kann mehrere Minuten brauchen, bis es den neuen Wert meldet, und bis dahin zeigt das Bedienelement den Wert, den das Auto noch hält.

Die übrigen vom Auto gemeldeten Klima-Einstellungen (Scheibenheizung, Klimatisierung beim Entsperren und die vorhandenen Sitzzonen) erscheinen als Schalter unter „Konfiguration“. Sie werden über den Einstellungs-Endpunkt des Autos geschrieben, ohne die Klimatisierung zu starten, was die myAudi-App nicht anbietet: Dort lässt sich ein beheizter Sitz nur aktivieren, während die Klimaanlage gestartet wird.

Jeder Schalter sendet das ganze Einstellungsobjekt mit einem geänderten Feld zurück, weil der Endpunkt ersetzt statt zusammenzuführen. Eine Sitz-Änderung kann deshalb die Zieltemperatur nicht löschen.

`start_auxiliary_heating` (Dauer) bleibt aus demselben Grund nur als Service-Aktion verfügbar.

Bei Auth0-Fahrzeugen startet und stoppt der Schalter **Climatisation ON/OFF** die Klimatisierung mit den im Auto gespeicherten Einstellungen und folgt dem vom Auto gemeldeten Zustand. Die Option _Quick start climate using car-stored settings_ lässt die Climate-Entity dasselbe tun, statt die in Home Assistant angezeigte Temperatur zu senden. Die Auswahl `Climatisation mode` (Komfort oder Eco) erscheint, wenn das Auto einen Modus meldet.

Welche dieser Schalter es gibt, entscheidet das Auto: Antwortet es auf eine Einstellung ausdrücklich mit „nicht unterstützt“ (zum Beispiel `supportsWindowHeatingEnabled: false` beim A6 e-tron), legt die Integration den Schalter nicht an. Fehlt eine Antwort, bleibt er erhalten. Was dein Auto meldet, steht im Diagnose-Download der Integration unter `capability_inventory`: `capability_ids` (alle Fähigkeiten) und `supports_flags` (die Antworten für Klimatisierung und Ladeprofile). Die Flags werden beim Start der Integration einmal gelesen; nach einem Neuladen stehen sie in der Diagnose.

Klima-Timer im Auto melden Sensoren (Anzahl aktiver Timer, nächster Timer in Ortszeit). Angelegt, geschaltet und gelöscht werden sie mit den Timer-Service-Aktionen weiter unten.

## Service-Aktionen

### Audi Connect: Refresh Vehicle Data

`audiconnect.refresh_vehicle_data`

Normale Updates holen Daten vom Audi-Connect-Cloud-Dienst und sprechen nicht direkt mit dem Fahrzeug. _Diese_ Service-Aktion löst eine Aktualisierungsanfrage beim Fahrzeug selbst aus. Werden die Daten erfolgreich abgerufen, aktualisiert sich Home Assistant automatisch. Die Service-Aktion braucht als Parameter das Fahrzeug (Gerät).

#### Parameter

- **`device_id`**: Das Audi-Fahrzeug (Gerät), auf das die Aktion angewendet wird.

> [!CAUTION]
> **Diese Service-Aktion zählt gegen dein tägliches API-Limit.** Häufiges Ausführen kann das Limit aufbrauchen. Sparsam nutzen und die verbleibenden API-Aufrufe über den Diagnosesensor **„API Requests Remaining“** oder **Einstellungen → System → Reparaturen & Systeminformationen** im Blick behalten.

> [!NOTE]
> Der Diagnosesensor **„API Requests Remaining“** stellt nach einem Neustart von Home Assistant seinen letzten bekannten Wert wieder her. Sein Attribut `last_observed` hält fest, wann Audi zuletzt einen `Vcf-Remaining-Calls`-Wert geliefert hat. Ist `value_restored` `true`, stammt der angezeigte Wert aus der vorherigen Laufzeit von Home Assistant und gibt das aktuell verbleibende Kontingent womöglich nicht mehr wieder.

### Audi Connect: Refresh Cloud Data

`audiconnect.refresh_cloud_data`

_Diese_ Service-Aktion löst eine Aktualisierungsanfrage bei der Cloud aus.

- Funktion: Aktualisiert die Daten aller Fahrzeuge aus der Online-Quelle, wie beim Start der Integration oder in den geplanten Aktualisierungsintervallen.
- Verhalten: Erzwingt keine Aktualisierung auf Fahrzeugseite. Haben Fahrzeuge zuletzt nichts gemeldet, können die abgerufenen Daten veraltet sein.
- Hinweis: Die Service-Aktion bildet die aktive Abfrage ohne Zeitplan nach und gibt mehr Kontrolle über den Zeitpunkt der Aktualisierung.
- **WICHTIG:** Diese Service-Aktion hat keine eingebaute Nutzungsgrenze. Übermäßige Nutzung kann zu einer vorübergehenden Sperrung deines Kontos führen.

#### Parameter

- `keine`

### Audi Connect: Execute Vehicle Action

`audiconnect.execute_vehicle_action`

Mit dieser Service-Aktion führst du Aktionen an deinem Audi aus, angegeben durch das Fahrzeug und die gewünschte Aktion.

#### Parameter

- **`device_id`**: Das Audi-Fahrzeug (Gerät), auf das die Aktion angewendet wird.
- **`action`**: Die auszuführende Aktion. Verfügbar sind:
  - **`lock`**: Fahrzeug verriegeln.
  - **`unlock`**: Fahrzeug entriegeln.
  - **`start_climatisation`**: Klimatisierung starten. (Veraltet) -- Deprecated
  - **`stop_climatisation`**: Klimatisierung stoppen.
  - **`start_charger`**: Laden starten.
  - **`start_timed_charger`**: Laden mit Timer starten.
  - **`stop_charger`**: Laden stoppen.
  - **`start_preheater`**: Standheizung starten. (Veraltet) -- Deprecated
  - **`stop_preheater`**: Standheizung stoppen.
  - **`start_window_heating`**: Scheibenheizung starten.
  - **`stop_window_heating`**: Scheibenheizung stoppen.

#### Anwendungsbeispiel

So verriegelst du ein Fahrzeug:

```yaml
service: audiconnect.execute_vehicle_action
data:
  device_id: 034986de941a1f824b3f06c0a1d9333f
  action: "lock"
```

#### Hinweise

- Einige Service-Aktionen brauchen die in der Einrichtung hinterlegte S-PIN.
- Nach einer erfolgreichen Aktion wartet die Integration die eingestellte **Cloud Refresh Delay** ab und führt dann eine Cloud-Abfrage durch. Ist **Refresh Vehicle Data After Action** aktiv, wird vor der Verzögerung zusätzlich ein Fahrzeug-Refresh gesendet.

### Audi Connect: Start Climate Control

`audiconnect.start_climate_control`

Mit dieser Service-Aktion startest du die Klimatisierung mit Optionen für Temperatur, Scheibenheizung und automatische Sitzheizung.

#### Parameter

- **`device_id`**: Das Audi-Fahrzeug (Gerät), auf das die Aktion angewendet wird.
- **`temp_f`** (_optional_): Gewünschte Temperatur in Fahrenheit. Standard ist `70`.
- **`temp_c`** (_optional_): Gewünschte Temperatur in Celsius. Standard ist `21`.
- **`glass_heating`** (_optional_): Scheibenheizung ein (`True`) oder aus (`False`). Standard ist `False`.
- **`seat_fl`** (_optional_): Sitzheizung vorne links ein (`True`) oder aus (`False`). Standard ist `False`.
- **`seat_fr`** (_optional_): Sitzheizung vorne rechts ein (`True`) oder aus (`False`). Standard ist `False`.
- **`seat_rl`** (_optional_): Sitzheizung hinten links ein (`True`) oder aus (`False`). Standard ist `False`.
- **`seat_rr`** (_optional_): Sitzheizung hinten rechts ein (`True`) oder aus (`False`). Standard ist `False`.
- **`climatisation_at_unlock`** (_optional_): Klimatisierung läuft weiter, wenn das Fahrzeug entriegelt wird.
- **`climatisation_mode`** (_optional_): `comfort` (Standard) oder `economy`.

#### Anwendungsbeispiel

So startest du die Klimatisierung mit 72 °F, Scheibenheizung und beiden vorderen Sitzheizungen:

```yaml
service: audiconnect.start_climate_control
data:
  device_id: 034986de941a1f824b3f06c0a1d9333f
  temp_f: 72
  glass_heating: True
  seat_fl: True
  seat_fr: True
```

#### Hinweise

- `temp_f` und `temp_c` schließen sich aus. Werden beide angegeben, hat `temp_f` Vorrang.
- Ohne `temp_f` und `temp_c` gelten 70 °F beziehungsweise 21 °C.
- Nach einer erfolgreichen Aktion wartet die Integration die eingestellte **Cloud Refresh Delay** ab und führt dann eine Cloud-Abfrage durch. Ist **Refresh Vehicle Data After Action** aktiv, wird vor der Verzögerung zusätzlich ein Fahrzeug-Refresh gesendet.

### Audi Connect: Start Auxiliary Heating

`audiconnect.start_auxiliary_heating`

Mit dieser Service-Aktion startest du die Standheizung, optional mit Dauer.

#### Parameter

- **`device_id`**: Das Audi-Fahrzeug (Gerät), auf das die Aktion angewendet wird.
- **`duration`** (_optional_): Minuten, die die Standheizung läuft, bevor sie sich ausschaltet. Ohne Angabe sind es `20` Minuten.

#### Anwendungsbeispiel

So startest du die Standheizung für 40 Minuten:

```yaml
service: audiconnect.start_auxiliary_heating
data:
  device_id: 034986de941a1f824b3f06c0a1d9333f
  duration: 40
```

#### Hinweise

- Braucht die in der Einrichtung hinterlegte S-PIN.
- Nach einer erfolgreichen Aktion wartet die Integration die eingestellte **Cloud Refresh Delay** ab und führt dann eine Cloud-Abfrage durch. Ist **Refresh Vehicle Data After Action** aktiv, wird vor der Verzögerung zusätzlich ein Fahrzeug-Refresh gesendet.

### Audi Connect: Set Target State of Charge

`audiconnect.set_target_soc`

Setzt das globale Ladeziel (20-100 %, in 5er-Schritten). Was dieser Wert bestimmt und was nicht, steht unter [Ladeziele](#ladeziele).

- **`device_id`**: Das Audi-Fahrzeug.
- **`target_soc`**: Ladeziel in Prozent.

### Audi Connect: Set Location Charge Target

`audiconnect.set_location_charge_target`

Setzt das Ladeziel eines Standortprofils (20-100 %, in 5er-Schritten). Diese dauerhafte Einstellung bestimmt, wo eine Ladung an diesem Standort endet.

- **`device_id`**: Das Audi-Fahrzeug.
- **`profile_id`** (_optional_): Das zu ändernde Profil. Leer lassen, um das Profil zu ändern, in dem das Auto gerade steht.
- **`target_soc`**: Ladeziel für diesen Standort.

### Audi Connect: Set Charge Mode

`audiconnect.set_charge_mode`

Setzt die Ladebetriebsart als Vorgabe. Eine laufende Ladung wird weder gestartet noch gestoppt.

- **`device_id`**: Das Audi-Fahrzeug.
- **`charge_mode`**: `manual` lädt, sobald angesteckt; `timer` lädt nur zu den geplanten Zeiten des Autos.

### Audi Connect: Start Engine / Stop Engine

`audiconnect.start_engine`, `audiconnect.stop_engine`

Startet oder stoppt den Motor aus der Ferne. Starten braucht die S-PIN. Es gelten die Fähigkeitsregeln unter **Funktionsstatus und API-Kompatibilität** in den [API-Hinweisen](api-notes.md).

- **`device_id`**: Das Audi-Fahrzeug.

### Audi Connect: Klima-Timer

`audiconnect.create_climatisation_timer`, `audiconnect.set_climatisation_timer_enabled`, `audiconnect.delete_climatisation_timer`

Verwaltet die Klima-Timer des Autos. Zeiten gelten in der Ortszeit des Autos. Die Timer-Nummer steht in den Attributen der Klima-Timer-Sensoren.

- **`device_id`**: Das Audi-Fahrzeug.
- Anlegen: **`time`** (zum Beispiel `07:30`), **`days`** (ein Timer nimmt genau einen Tag), **`repeat`** (jede Woche, Standard an), **`enabled`** (Standard an).
- Schalten: **`timer_id`**, **`enabled`**.
- Löschen: **`timer_id`**.

### Diagnose

Die folgenden Service-Aktionen dienen der Fehlersuche. Nutze sie nur, wenn du fehlenden Daten nachgehst, denn sie zählen gegen das API-Limit.

- `audiconnect.probe_api` sendet eine reine Leseanfrage (selectivestatus-`jobs`, einen `path` unterhalb der Fahrzeug-URL oder eine feste `graphql`-Abfrage) und gibt die geschwärzte Antwort zurück.
- `audiconnect.probe_api_paths` prüft acht bekannte Lese-Endpunkte (`extended` fügt vier experimentelle hinzu). Das Ergebnis erscheint im nächsten Export unter **Diagnose herunterladen**. Ein erneuter Lauf mit anderem Modus innerhalb von 15 Minuten wird abgelehnt.
- `audiconnect.test_climatisation_write` ist experimentell. Es schreibt eine Klima-Einstellung mit einer wählbaren Variante des Anfragekörpers (`app_dto` ist der Standard; `app_full` sendet alle zwölf Felder der App-Anfrage) und **ändert die im Auto gespeicherte Einstellung**.

Wer sehen will, was Audi wirklich schickt, schaltet in den **Optionen** `Log raw API responses (debug)` ein, aktiviert unter **Einstellungen ➤ Geräte & Dienste ➤ Audi Connect** die **Debug-Protokollierung**, löst **Fahrzeugdaten aktualisieren** aus und liest das Log (Zeilen `Raw API response from …`). Danach beides wieder ausschalten. Maskiert werden FIN, Koordinaten, Benutzer-ID, PINs und Tokens; mit `Also log VIN and position unredacted` bleiben FIN, Position und Benutzer-ID stehen. Anmelde- und Token-Antworten kommen nie ins Log, anders als beim Schalter `DEBUG_VERBOSE` im Code, der auch Tokens ausgibt.

Die Diagnosesensoren `Vehicle data freshness`, `Vehicle data age`, `Cloud last successful poll` und `API Requests Remaining` zeigen, wie aktuell die Daten sind. Für ausführliche Logs `custom_components.audiconnect: debug` unter `logger:` in der `configuration.yaml` setzen.

### Reparatur-Hinweise

Nach jeder erfolgreichen Abfrage prüft die Integration die Enddaten der Online-Dienste, die das Auto meldet. Ist einer beendet, oder endet einer innerhalb von 30 Tagen, erscheint unter **Einstellungen ➤ System ➤ Reparaturen** ein Hinweis mit den betroffenen Diensten und dem Datum (je Auto höchstens einer, „beendet“ geht vor „endet bald“). Der Hinweis verschwindet von selbst, sobald die Daten wieder weit entfernt sind, und mit dem Eintrag, wenn du die Integration entfernst. Daten und Bedienung, die von einem beendeten Dienst abhängen, können ausfallen; verlängern lässt er sich in der myAudi-App oder beim Audi-Händler. Die FIN steht weder im Hinweis noch in seiner Kennung.
