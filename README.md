<h1 align="center">Audi Connect</h1>

<p align="center">
  Home-Assistant-Integration für Audi Connect (myAudi) – Fahrzeugstatus, Fernsteuerung und Klimatisierung, komplett über die Oberfläche einrichtbar.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://www.home-assistant.io/"><img src="https://img.shields.io/badge/Home%20Assistant-Custom%20Integration-18BCF2.svg?logo=home-assistant&logoColor=white" alt="Home Assistant"></a>
  <a href="https://github.com/bertel2020/HA-audi_connect/releases"><img src="https://img.shields.io/github/v/release/bertel2020/HA-audi_connect?sort=semver&include_prereleases" alt="Release"></a>
  <a href="https://github.com/bertel2020/HA-audi_connect/actions/workflows/validate.yml"><img src="https://github.com/bertel2020/HA-audi_connect/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/bertel2020/HA-audi_connect" alt="Lizenz"></a>
</p>

<p align="center">
  <a href="https://buymeacoffee.com/bertel2020"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00?logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a>
  <a href="https://ko-fi.com/bertel2020"><img src="https://img.shields.io/badge/Ko--fi-support-FF5E5B?logo=ko-fi&logoColor=white" alt="Ko-fi"></a>
  <a href="https://paypal.me/RobertoMartins"><img src="https://img.shields.io/badge/PayPal-donate-00457C?logo=paypal&logoColor=white" alt="PayPal"></a>
</p>

<p align="center"><em><a href="README.en.md">🇬🇧 English version</a></em></p>

> [!IMPORTANT]
> **Anmeldestatus.** Audis alte Geräte- und Refresh-Anmeldewege sind in betroffenen Regionen gesperrt. Die Integration nutzt dort den interaktiven myAudi-Auth0/PKCE-Ablauf. Bestehende Einträge, die mit `invalid assertion headers` fehlschlagen, fordern eine erneute Anmeldung an. Hintergrund: [#903](https://github.com/audiconnect/audi_connect_ha/issues/903).

Wegen API-Änderungen ist **derzeit nicht der gesamte Funktionsumfang verfügbar**. Fehlt dir etwas, eröffne bitte ein [Issue](https://github.com/bertel2020/HA-audi_connect/issues/new/choose).

> [!CAUTION]
> Übermäßige Nutzung einzelner Funktionen kann dazu führen, dass dein Audi-Connect-Konto vorübergehend oder dauerhaft gesperrt wird. Nutze die Integration verantwortungsvoll und auf eigenes Risiko.

Die Komponente `audiconnect` bindet den Audi-Connect-Cloud-Dienst an Home Assistant an. Sie liefert Anwesenheitserkennung, Sensoren wie Reichweite, Kilometerstand und Tankfüllstand und bietet Fahrzeugaktionen wie Ver- und Entriegeln oder die Standheizung.

Dies ist ein Fork von [audiconnect/audi_connect_ha](https://github.com/audiconnect/audi_connect_ha). **Hinweis:** Einzelne Funktionen, etwa die Positionsaktualisierung per GPS, benötigen besondere Berechtigungen von Audi.

Dank für die erste Erkundung der API geht an die Leute aus dem ioBroker-VW-Connect-Forum, die herausgefunden haben, wie die API und das PIN-Hashing funktionieren. Teile des Codes basieren lose auf dem Python-Paket [AudiAPI](https://github.com/davidgiga1993/AudiAPI) von davidgiga1993. Der Dank für die ursprüngliche Integration gilt @arjenvrh.

## Installation

### Über HACS (empfohlen)

[![HACS-Repository in My Home Assistant öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bertel2020&repository=HA-audi_connect&category=integration)
[![Audi Connect zu My Home Assistant hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=audiconnect)

1. Über den ersten Button das Audi-Connect-Repository in HACS öffnen.
2. **Audi Connect** herunterladen und Home Assistant neu starten.
3. Über den zweiten Button die Integration hinzufügen. Alternativ in Home
   Assistant **Einstellungen → Geräte & Dienste → Integration hinzufügen →
   Audi Connect** öffnen.

Falls der erste Button nicht funktioniert, in HACS unter **Integrationen →
Benutzerdefinierte Repositories** `https://github.com/bertel2020/HA-audi_connect`
als Kategorie **Integration** eintragen.

### Manuell

Das Verzeichnis `custom_components/audiconnect` nach
`/config/custom_components/audiconnect` kopieren und Home Assistant neu
starten. Danach die Integration hinzufügen (siehe **Einrichtung**).

## Einrichtung

Die Einrichtung erfolgt über die Home-Assistant-Oberfläche.

Unter **Einstellungen ➤ Geräte & Dienste ➤ Integrationen** auf **➕ Integration hinzufügen** klicken und nach „Audi Connect“ suchen.

In Auth0-Regionen zeigt Home Assistant einen Audi-Anmeldelink. Öffne ihn in einem privaten Browserfenster und melde dich an. Audi leitet dann auf die registrierte Adresse `http://localhost:8080/myaudi-callback` weiter; eine Seite „Verbindung nicht möglich“ ist erwartet, weil kein lokaler Server nötig ist. Kopiere die vollständige URL aus der Adressleiste und füge sie in das Formular von Home Assistant ein. Home Assistant prüft den OAuth-State und tauscht den einmaligen Code per PKCE ein.

Region, S-PIN und API-Level lassen sich später über **Neu konfigurieren** am Integrationseintrag ändern. Lehnt Audi die gespeicherte Anmeldung ab, startet Home Assistant die erneute Anmeldung.

### Konfigurationsvariablen

| Name            | Typ      | Standard | Beschreibung                                                                                                                                                                                                                              |
| --------------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Username`      | `string` | –        | Benutzername deines Audi-Connect-Kontos. Nur in Regionen mit Passwort-Anmeldung.                                                                                                                                                          |
| `Password`      | `string` | –        | Passwort deines Audi-Connect-Kontos. Nur in Regionen mit Passwort-Anmeldung.                                                                                                                                                              |
| `S-PIN`         | `string` | –        | S-PIN deines Audi-Connect-Kontos für bestimmte Service-Aktionen.<br>(**Optional**)                                                                                                                                                        |
| `Region`        | `string` | `DE`     | Region, in der dein Audi-Connect-Konto registriert ist:<br>• `DE` – Europa<br>• `US` – USA<br>• `CA` – Kanada<br>• `CN` – China                                                                                                           |
| `Scan Interval` | `int`    | `15`     | Abstand (in Minuten), in dem der Status von Audi Connect abgerufen wird.<br>Minimum sind 15 Minuten.<br>\* _Später über das Menü KONFIGURIEREN änderbar._                                                                                 |
| `API Level`     | `int`    | `0`      | Bestimmt die API-Struktur für Service-Aufrufe:<br>• `0` – _Typischerweise_ Verbrenner (altes Format)<br>• `1` – _Typischerweise_ e-tron (Elektrofahrzeuge, neues Format)<br>\* _Später über das Menü KONFIGURIEREN änderbar._            |

## Optionen

Die Optionen findest du unter **Einstellungen ➤ Geräte & Dienste ➤ Integrationen ➤ Audi Connect ➤ Konfigurieren**:

| Name                                | Typ    | Standard | Beschreibung                                                                                                                                                                                                                                                                                                                       |
| ----------------------------------- | ------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Cloud Update at Startup`           | `bool` | `True`   | Schaltet die erste Cloud-Abfrage beim Start der Integration ein oder aus. Nützlich bei der Entwicklung oder bei häufigen Neustarts von Home Assistant.                                                                                                                                                                             |
| `Refresh Vehicle Data After Action` | `bool` | `False`  | Schickt nach jeder Service-Aktion (z. B. Klima, Verriegelung) einen Fahrzeug-Refresh. Das ist meist nicht nötig, weil sich das Fahrzeug nach einem Befehl selbst in der Cloud meldet. Jeder Fahrzeug-Refresh zählt gegen das API-Limit. Für mehr Reaktionsgeschwindigkeit lieber die Cloud-Refresh-Verzögerung erhöhen.            |
| `Cloud Refresh Delay`               | `int`  | `5`      | Sekunden, die nach einer Service-Aktion bis zur Cloud-Abfrage gewartet wird. Eine längere Verzögerung gibt dem Fahrzeug mehr Zeit, seinen neuen Zustand zu melden.                                                                                                                                                                  |
| `Scan Interval`                     | `int`  | `15`     | Abfrageintervall in Minuten (mindestens 15).                                                                                                                                                                                                                                                                                       |
| `Excluded VINs`                     | `str`  | –        | Kommagetrennte FIN-Liste (VIN) von Fahrzeugen, die von Einrichtung und Updates ausgenommen werden.                                                                                                                                                                                                                                 |
| `Quick start climate using car-stored settings` | `bool` | `False` | Beim Einschalten der Climate-Entity wird eine CARIAD-Startanfrage ohne Parameter gesendet, die die im Auto gespeicherten Einstellungen nutzt. Die in Home Assistant angezeigte Temperatur wird nicht übertragen. Optionaler Umweg für neuere Fahrzeuge. |
| `Enable experimental vehicle controls` | `bool` | `False` | Zeigt die Buttons zum Starten/Stoppen der Scheibenheizung und den Schalter zur Freigabe des Ladesteckers. Das tatsächliche Verhalten prüfen; HTTP 200 ist kein Beweis, dass das Fahrzeug gehandelt hat. |
| `Edit dealer and local service details` | `bool` | `False` | Öffnet ein Formular für Händler-, Servicetermin- und Garantiedaten, die in Home Assistant bleiben. Es werden keine Audi-API-Anfragen gesendet. |

_Hinweis: Die Integration lädt nach einem Klick auf `Senden` automatisch neu, ein Neustart von Home Assistant wird trotzdem empfohlen._

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
| `Refresh vehicle data`         | Button  | `refresh_vehicle_data`                                |
| `Wake vehicle`                 | Button  | –, neu; braucht eine gemeldete Wecken-Fähigkeit       |
| `Honk and flash`               | Button  | –, neu; standardmäßig deaktiviert                     |
| `Climatisation ON/OFF`         | Switch  | –, Auth0-Fahrzeuge                                    |
| `Window heating`, `Climatisation at unlock`, Sitzzonen | Switch | –, die im Auto gespeicherten Klima-Einstellungen |
| `Climatisation mode`           | Select  | `start_climate_control` mit `climatisation_mode`      |
| `Start/Stop window heating (experimental)` | Button | `execute_vehicle_action` mit `start_/stop_window_heating` |
| `Release plug after charging (experimental)` | Switch | –                                         |

### Funktionsstatus und API-Kompatibilität

Nicht alle Audi-Fahrzeuge und -Regionen bieten dieselben Funktionen. Die Integration unterscheidet zwischen einer von der Audi-API akzeptierten Anfrage und dem Fahrzeug, das die Aktion tatsächlich ausführt. Prüfe das Fahrzeug und den danach gemeldeten Zustand, bevor du dich in Automationen auf Fernbefehle verlässt.

| Status                                    | Bedienelement oder Fähigkeit                                             | Hinweise                                                                                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Standard, abhängig von Fähigkeiten        | Ver-/Entriegeln und Lichthupe                                            | Brauchen die jeweilige Fahrzeugberechtigung; den tatsächlichen Fahrzeugzustand prüfen                                                              |
| Standard bei unterstützten Auth0-Fahrzeugen | Schalter **Climatisation ON/OFF**                                      | Nutzt die im Auto gespeicherten Klima-Einstellungen und liest den vom Auto gemeldeten Zustand; ersetzt nicht die Klima-Temperatur-Entity           |
| Veraltet / modellabhängig                 | **Preheater** und die ursprüngliche **Climatisation**-Climate-Entity     | Aus Kompatibilitätsgründen behalten; ältere Routen können bei neueren Auth0-Konten fehlen oder abgelehnt werden                                    |
| Experimentell, per Opt-in                 | Buttons Scheibenheizung starten/stoppen und Schalter zur Steckerfreigabe | Standardmäßig aus; unter Konfigurieren als _experimentelle Fahrzeugsteuerung_ aktivierbar, wenn eine gemeldete Fähigkeit die Aktion erlaubt |
| Abhängig von Fähigkeiten                  | Buttons **Wake vehicle** und **Honk and flash**                          | Wecken braucht eine gemeldete Wecken-Fähigkeit; Hupen und Blinken ist in der Entity-Registry standardmäßig deaktiviert                     |
| Nur als Service                           | Laden starten, zeitgesteuert starten und stoppen                         | Über `execute_vehicle_action` verfügbar; es gibt dafür keine Entity (siehe unten)                                                         |
| Modellabhängig                            | Lademodus und Ziel-Ladestand ändern                                      | Audi kann eine HTTP-Anfrage annehmen, die Einstellung aber ablehnen oder nicht anwenden                                                            |

_Veraltet_ bezeichnet eine ältere Schnittstelle, keine angekündigte Entfernung. Die Integration behält vorhandene Unique-IDs und Service-Aufrufe, soweit möglich. Verfügbarkeit und Funktionsumfang müssen pro Fahrzeug geprüft werden, nicht aus einem einzelnen erfolgreichen Befehl oder einer Fähigkeitenliste abgeleitet. Eine unvollständige Cloud-Antwort kann eine Entity **nicht verfügbar** machen, statt sie zu entfernen.

**Ver-/Entriegeln:** Beide Richtungen nutzen einen Refresh nach dem Befehl und setzen das Attribut `last_command_status`: `request_failed`, `accepted_unconfirmed`, `confirmed_by_readback` oder `already_reported_in_requested_state`. Eine Bestätigung des Audi-Gateways oder ein verzögerter Cloud-Zustand ist keine bestätigte Türaktion am Fahrzeug, und keine Richtung wiederholt den Befehl blind.

**Motor aus der Ferne:** Ältere Verbrenner ohne Fähigkeitenliste (nicht Auth0) behalten den bisherigen Motor-Button als Rückfall. Ausdrücklich verweigerte Fähigkeiten, eingeschränkte Unterstützung, bekannte Hybrid-/Elektrotypen und Q8-Modellsperren gelten weiter. Auth0-Fahrzeuge brauchen eine ausdrücklich gemeldete Berechtigung.

**Ladeeinstellungen:** Bei Auth0-Fahrzeugen verweigert eine Änderung des globalen Ziel-Ladestands das Senden eines möglicherweise zerstörenden `charging/settings`-PUT, wenn Audi unbekannte Einstellungen zurückgibt. Bekannte schreibbare Einstellungen bleiben erhalten; Zeitstempel-Metadaten werden ausgelassen. Weitere schreibbare Schlüssel brauchen fahrzeugspezifische Belege.

**Q8-Klima:** Beim getesteten Audi Q8 PHEV funktioniert Klima EIN/AUS über den separaten modernen Auth0/CARIAD-Befehlsweg mit den im Auto gespeicherten Einstellungen. Eine Temperatur an die alte Klima-Schnittstelle zu übergeben hat bei diesem Fahrzeug nicht funktioniert. Das belegt keine Unterstützung für andere Audi-Typen oder Regionen. Ein künftiges Fähigkeitenmodell sollte gemeldete Funktionen mit Fahrzeugtyp, API-Generation und geprüftem modellspezifischem Verhalten kombinieren, ohne anzunehmen, dass ein Modellname eine Berechtigung gewährt oder eine fehlende Fähigkeit ein endgültiger Gegenbeweis ist.

**Wecken / schlafendes Fahrzeug:** Der Button `Wake vehicle` (sichtbar, wenn das Auto eine Wecken-Fähigkeit meldet) nutzt die Auth0/CARIAD-Route `vehiclewakeuptrigger`; eine HTTP-Antwort 2xx/204 ist **kein Beweis**, dass das Fahrzeug wirklich aufgewacht ist. Erste Q8-Beobachtungen deuten darauf hin, dass eine Wecken-Anfrage verzögerte Werte schlafender Fahrzeuge und des Ladestatus wiederherstellen kann, das ist aber nicht als allgemeine Lösung belegt. Ein geparktes Fahrzeug zu wecken kann außerdem Energie aus der 12-V- und/oder Traktionsbatterie kosten. Deshalb darf die automatische Abfrage das Fahrzeug **nie** in jedem Zyklus wecken, und die aktuelle Integration tut das nicht. Künftig sollten passiver Cloud-Refresh und aktives Wecken getrennt bleiben, ausdrückliche Nutzerabsicht oder geprüfte Lade-/Sitzungswechsel als mögliche Auslöser dienen, pro Fahrzeug Abkühlzeiten und Anfrage-/Energiebudgets gelten und die Aktualität nach einem begrenzten, verzögerten Rücklesen bestätigt werden, bevor Wecken oder Ladestatus als aktuell dargestellt werden. Das bleibt experimentell, bis Messungen zu Statusverbesserung, tatsächlicher Weckreaktion und Auswirkung auf die Batterie des geparkten Fahrzeugs vorliegen.

`Refresh vehicle data` nutzt eine andere Route (`vehiclewakeup`) und wartet bis zu 100 Sekunden auf die Antwort des Autos. Antwortet das Auto nicht rechtzeitig, steht eine Warnung im Log, kein Fehler: Es kann schlafen oder außer Reichweite sein.

Optionale lokale Händler-/Service-Angaben werden, falls eingerichtet, in den Home-Assistant-Optionen gehalten; sie werden **nicht** aus Audis Cloud abgerufen und dürfen nicht mit Service-Daten des Herstellers verwechselt werden.

### Ladeziele

Es gibt drei Arten, weil das Auto drei Stellen für die Zahl hat:

- **Global charge target** schreibt `charging/settings`. Es bestimmt nicht, wo eine Ladung an einem Standort endet (Upstream #722), ist also das am wenigsten nützliche der drei und bleibt nur, weil es eine echte, eigene Einstellung ist.
- **Current location charge target** schreibt das Profil, in dem das Auto gerade steht, von der Integration aus `vehiclePositionedInProfileID` ermittelt. Nutze es in Automationen, die gelten sollen, wo auch immer das Auto steht.
- **Eine Zahl pro Standortprofil**, benannt nach dem Profil („Home charge target“, „Work charge target“). Sie werden aus dem gelesen, was das Auto meldet; ein im Auto hinzugefügtes oder entferntes Profil erscheint oder verschwindet also nach dem nächsten Refresh. Ein im Auto gelöschtes Profil macht sein Bedienelement nicht verfügbar, statt ein veraltetes Ziel zu zeigen.

`sensor.<fahrzeug>_active_charging_profile_name` zeigt, welches Profil gilt, sodass ein Dashboard den maßgeblichen Standort neben den Reglern anzeigen kann. Die Profil-Bedienelemente hängen an der Profil-ID, nicht am Namen: Wer einen Standort in der myAudi-App umbenennt, benennt das Bedienelement um, ohne Automationen zu brechen, die darauf verweisen.

Die Service-Aktionen weiter unten funktionieren weiterhin und bleiben der Weg zu den parametrisierten Befehlen: `start_climate_control` (Temperatur, Sitz- und Scheibenheizung, Klimamodus) und `start_auxiliary_heating` (Dauer) nehmen Einstellungen, die das Fahrzeug nicht zurückmeldet, und haben deshalb kein Bedienelement auf der Seite.

### Laden starten und stoppen

Beides gibt es nicht als Entity, weil beides nicht durchgängig bestätigt ist. Beides bleibt über `execute_vehicle_action` erreichbar (`start_charger`, `stop_charger`, `start_timed_charger`); das Auto kann es ablehnen, oder es hat keine physische Wirkung.

Stoppen wird von der API angenommen und vom Auto bestätigt, und die Ladung läuft weiter. Zweimal aus ruhigem Zustand an einem Live-Fahrzeug gesendet, das beide Male weiter 6,5 kW zog.

Starten ist unbewiesen. Es schien einmal zu funktionieren, aber das Auto hatte damals ein Ziel weit über dem Ladestand und hätte ohnehin geladen; später mit dem Ziel unter dem Ladestand wiederholt, wurde der Befehl angenommen und es passierte nichts. Es gibt keinen Beleg, der „der Button hat die Ladung gestartet“ von „das Auto hätte ohnehin geladen“ trennt.

Zeitgesteuertes Laden ist aus demselben Grund ebenfalls nicht verfügbar: Es läuft über denselben Befehl wie Starten und Stoppen.

Nutze stattdessen `Target state of charge`. Ein Wert über dem aktuellen Ladestand startet eine Ladung, ein Wert darunter stoppt sie; das war bei allen Tests in jede Richtung der Hebel, der sich konsistent verhalten hat. Die Abfahrtstimer des Autos sind der andere verlässliche Weg und werden hier gemeldet, aber noch nicht geschrieben.

## Klimatisierung

Die Climate-Entity schaltet die Klimatisierung ein und aus und setzt die Zieltemperatur. Das Auto meldet, ob die Klimatisierung läuft und in welchem Modus (Heizen, Kühlen, Lüften), die Entity zeigt also das Fahrzeug und nicht, was Home Assistant zuletzt angefordert hat.

Zwei Dinge macht sie bewusst nicht. Sie hat keine Ist-Temperatur, weil das Auto die Außentemperatur meldet und nicht die im Innenraum, und die Außentemperatur als Ist-Temperatur einer Climate-Entity anzuzeigen würde falsch darstellen, was gemessen wird. Und sie bietet weder Sitz- oder Scheibenheizung noch Klimatisierung beim Entsperren oder den Komfort-/Eco-Modus an: Das Fahrzeug meldet das nie zurück, ein Bedienelement würde also nur zeigen, was du zuletzt eingestellt hast. Dafür die Service-Aktion `start_climate_control` verwenden.

Die Zieltemperatur kommt vom Auto, das sie in seinen Klima-Einstellungen meldet. Home Assistant hält nur als Rückfall einen Wert vor, für ein Fahrzeug, das keinen meldet, und für den Moment zwischen Änderungswunsch und Bestätigung durch das Auto. Das Auto speichert halbe Grad, und das Bedienelement geht ebenfalls in halben Graden. Bei ausgeschalteter Klimatisierung wird ein neues Ziel in die Einstellungen des Autos geschrieben, ohne sie zu starten; das Auto kann mehrere Minuten brauchen, bis es den neuen Wert meldet, und bis dahin zeigt das Bedienelement den Wert, den das Auto noch hält.

Die übrigen vom Auto gemeldeten Klima-Einstellungen (Scheibenheizung, Klimatisierung beim Entsperren und die vorhandenen Sitzzonen) erscheinen als Schalter unter „Konfiguration“. Sie werden über den Einstellungs-Endpunkt des Autos geschrieben, ohne die Klimatisierung zu starten, was die myAudi-App nicht anbietet: Dort lässt sich ein beheizter Sitz nur aktivieren, während die Klimaanlage gestartet wird.

Jeder Schalter sendet das ganze Einstellungsobjekt mit einem geänderten Feld zurück, weil der Endpunkt ersetzt statt zusammenzuführen. Eine Sitz-Änderung kann deshalb die Zieltemperatur nicht löschen.

`start_auxiliary_heating` (Dauer) bleibt aus demselben Grund nur als Service-Aktion verfügbar.

Bei Auth0-Fahrzeugen startet und stoppt der Schalter **Climatisation ON/OFF** die Klimatisierung mit den im Auto gespeicherten Einstellungen und folgt dem vom Auto gemeldeten Zustand. Die Option _Quick start climate using car-stored settings_ lässt die Climate-Entity dasselbe tun, statt die in Home Assistant angezeigte Temperatur zu senden. Die Auswahl `Climatisation mode` (Komfort oder Eco) erscheint, wenn das Auto einen Modus meldet.

Klima-Timer im Auto melden Sensoren (Anzahl aktiver Timer, nächster Timer in Ortszeit). Angelegt, geschaltet und gelöscht werden sie mit den Timer-Service-Aktionen weiter unten.

## Warum eine Entity manchmal verschwindet

Entities werden beim Einrichten der Integration angelegt, und bisher fragte diese Entscheidung, ob der Wert in der gerade gehaltenen Abfrage vorhanden war. Eine unvollständige oder ratenbegrenzte Abfrage hat deshalb Bedienelemente entfernt: Bei einem Fahrzeug nahm ein `429 Too Many Requests` sechzehn Entities mit, darunter einen Parkpositions-Sensor für ein Auto, das offensichtlich eine Parkposition hat. Sie kamen erst nach einem Neuladen zurück.

Das Auto meldet getrennt von jeder einzelnen Abfrage, was es kann, und die Integration fragt jetzt diese Liste, wo sich eine Fähigkeit eindeutig auf eine Entity abbilden lässt. Ein fehlender Wert macht die Entity nicht verfügbar, statt sie zu löschen.

Fahrzeuge, die keine Fähigkeitenliste melden, sind nicht betroffen und behalten das bisherige Verhalten.

### Blinken und Hupen

`Flash` lässt die Fahrzeugbeleuchtung zehn Sekunden blinken. Das Auto muss eine Position gemeldet haben, weil die API eine verlangt; das Bedienelement lehnt ab, statt eine Anfrage zu senden, die abgelehnt würde.

`Honk and flash` lässt zusätzlich die Hupe ertönen. Es ist ein eigener Button und in der Entity-Registry standardmäßig deaktiviert, weil er laut ist. Beide nutzen denselben Endpunkt, aber `Flash` sendet nur den Blink-Modus und kann die Hupe deshalb nie auslösen.

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

Setzt das globale Ladeziel (20-100 %, in 5er-Schritten). Was dieser Wert bestimmt und was nicht, steht unter **Ladeziele**.

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

Startet oder stoppt den Motor aus der Ferne. Starten braucht die S-PIN. Es gelten die Fähigkeitsregeln unter **Funktionsstatus und API-Kompatibilität**.

- **`device_id`**: Das Audi-Fahrzeug.

### Audi Connect: Klima-Timer

`audiconnect.create_climatisation_timer`, `audiconnect.set_climatisation_timer_enabled`, `audiconnect.delete_climatisation_timer`

Verwaltet die Klima-Timer des Autos. Zeiten gelten in der Ortszeit des Autos. Die Timer-Nummer steht in den Attributen der Klima-Timer-Sensoren.

- **`device_id`**: Das Audi-Fahrzeug.
- Anlegen: **`time`** (zum Beispiel `07:30`), **`days`** (ein Timer nimmt genau einen Tag), **`repeat`** (jede Woche, Standard an), **`enabled`** (Standard an).
- Schalten: **`timer_id`**, **`enabled`**.
- Löschen: **`timer_id`**.

### Audi Connect: Set Local Dealer

`audiconnect.set_local_dealer`

Speichert Händler-, Servicetermin- und Garantiedaten in Home Assistant. Es werden keine Audi-API-Anfragen gesendet. Nicht angegebene Felder behalten ihren Wert, leerer Text entfernt ein Feld, und `clear` entfernt den ganzen lokalen Eintrag des Fahrzeugs. Dieselben Daten lassen sich unter **Konfigurieren** bearbeiten.

### Diagnose

Die folgenden Service-Aktionen dienen der Fehlersuche. Nutze sie nur, wenn du fehlenden Daten nachgehst, denn sie zählen gegen das API-Limit.

- `audiconnect.probe_api` sendet eine reine Leseanfrage (selectivestatus-`jobs`, einen `path` unterhalb der Fahrzeug-URL oder eine feste `graphql`-Abfrage) und gibt die geschwärzte Antwort zurück.
- `audiconnect.probe_api_paths` prüft acht bekannte Lese-Endpunkte (`extended` fügt vier experimentelle hinzu). Das Ergebnis erscheint im nächsten Export unter **Diagnose herunterladen**. Ein erneuter Lauf mit anderem Modus innerhalb von 15 Minuten wird abgelehnt.
- `audiconnect.test_climatisation_write` ist experimentell. Es schreibt eine Klima-Einstellung mit einer wählbaren Variante des Anfragekörpers (`app_dto` ist der Standard; `app_full` sendet alle zwölf Felder der App-Anfrage) und **ändert die im Auto gespeicherte Einstellung**.

Die Diagnosesensoren `Vehicle data freshness`, `Vehicle data age`, `Cloud last successful poll` und `API Requests Remaining` zeigen, wie aktuell die Daten sind. Für ausführliche Logs `custom_components.audiconnect: debug` unter `logger:` in der `configuration.yaml` setzen.

## Dashboard-Karte

Die Integration bringt ihre eigene Dashboard-Karte `audi-connect-card` mit. Es gibt nichts zu installieren und kein YAML zu schreiben: Sie wird nach der Einrichtung der Integration automatisch geladen.

1. Ein Dashboard öffnen, **Bearbeiten** und **Karte hinzufügen** wählen.
2. **Audi Connect** auswählen.
3. Im Karten-Editor dein Fahrzeug wählen. Ein Foto ist optional: eines hochladen oder ein Bild aus dem Ordner `www` wählen (es wird als `/local/...` ausgeliefert).

Was sie zeigt:

- Titel oder Foto antippen öffnet die Integration; gedrückt halten aktualisiert die Fahrzeugdaten.
- Position, Kilometerstand und wie alt die Daten sind, dann eine Reihe von Status-Symbolen für Schloss, Türen, Fenster, Stecker, Licht und Warnungen. Ein Tipp auf Türen oder Fenster öffnet eine Draufsicht mit allen Türen und Fenstern; die Schloss-Taste im Pop-up verriegelt oder entriegelt nach einer Bestätigung.
- Der Ladestand als Balken, mit dem Ladeziel als Markierung (und einem Regler zum Ändern). Beim Laden ist der Balken animiert, und ein Band zeigt Leistung, gewonnene Reichweite pro Stunde und wann die Ladung fertig ist. Ein angesteckt wartendes Auto, ein erreichtes Ladeziel oder ein Ladefehler erscheint als kurzer Hinweis unter dem Balken.
- Letzte Fahrt und Langzeitfahrt, jeweils eingeklappt, bis du sie öffnest.
- Elektrische Reichweite, Tage bis zur nächsten Inspektion und wie lange das Auto geparkt ist.
- Klimatisierung mit Modus, Temperatur, Sitzheizung, Start und Stopp.

Entities werden über das Gerät des Fahrzeugs und den Übersetzungsschlüssel jeder Entity gefunden, wie auch immer du sie benannt hast. Teile, die das Auto nicht hat, werden weggelassen.

Die Karte gibt es auf Englisch und Deutsch, und sie folgt der Sprache von Home Assistant. Erscheint sie nicht in der Kartenliste, den Browser einmal neu laden, damit das Frontend sie lädt.

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## Haftungsausschluss

Dies ist eine unabhängige, community-entwickelte Integration. Sie steht in keiner Verbindung zu Audi, dem Volkswagen-Konzern oder CARIAD und wird von diesen weder unterstützt noch empfohlen. Die API wurde per Reverse Engineering ermittelt und kann sich jederzeit ändern oder ausfallen. Die Integration kann Befehle an ein echtes Fahrzeug senden. Sie wird **„wie besehen“, ohne jegliche Gewährleistung** bereitgestellt (siehe [LICENSE](LICENSE)) – die Nutzung erfolgt auf eigenes Risiko.

„Audi“, „myAudi“ sowie alle sonstigen in diesem Repository genannten Produkt- und Firmennamen sind Marken oder eingetragene Marken ihrer jeweiligen Inhaber. Ihre Nennung dient ausschließlich der Beschreibung, mit welchem Dienst diese Integration arbeitet. „Home Assistant“ ist eine Marke der Open Home Foundation.

## Copyright & Lizenz

Copyright © 2019 Arjen van Rhijn (@arjenvrh), Änderungen © 2026 bertel2020. Lizenziert unter der [MIT-Lizenz](LICENSE).
