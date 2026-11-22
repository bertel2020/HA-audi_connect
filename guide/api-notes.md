# Audi Connect – API-Hinweise

*[🇬🇧 English version](api-notes.en.md)*

Hintergrund zu dem, was die Audi-API und die Fahrzeuge tatsächlich tun: welche Funktionen belegt sind, welche nur angenommen werden und warum Entities gelegentlich verschwinden. Für die tägliche Bedienung reicht das [Benutzerhandbuch](user-guide.md).

## Funktionsstatus und API-Kompatibilität

Nicht alle Audi-Fahrzeuge und -Regionen bieten dieselben Funktionen. Die Integration unterscheidet zwischen einer von der Audi-API akzeptierten Anfrage und dem Fahrzeug, das die Aktion tatsächlich ausführt. Prüfe das Fahrzeug und den danach gemeldeten Zustand, bevor du dich in Automationen auf Fernbefehle verlässt.

| Status                                    | Bedienelement oder Fähigkeit                                             | Hinweise                                                                                                                                           |
| ----------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Standard, abhängig von Fähigkeiten        | Ver-/Entriegeln und Lichthupe                                            | Brauchen die jeweilige Fahrzeugberechtigung; den tatsächlichen Fahrzeugzustand prüfen                                                              |
| Standard bei unterstützten Auth0-Fahrzeugen | Schalter **Climatisation ON/OFF**                                      | Nutzt die im Auto gespeicherten Klima-Einstellungen und liest den vom Auto gemeldeten Zustand; ersetzt nicht die Klima-Temperatur-Entity           |
| Veraltet / modellabhängig                 | **Preheater** und die ursprüngliche **Climatisation**-Climate-Entity     | Aus Kompatibilitätsgründen behalten; ältere Routen können bei neueren Auth0-Konten fehlen oder abgelehnt werden                                    |
| Experimentell, per Opt-in                 | Buttons Scheibenheizung und **Laden starten/stoppen**, Schalter zur Steckerfreigabe | Standardmäßig aus; unter Konfigurieren als _experimentelle Fahrzeugsteuerung_ aktivierbar. Laden starten/stoppen nimmt Audi an, ein A6 e-tron führt es nicht aus |
| Abhängig von Fähigkeiten                  | Buttons **Wake vehicle** und **Honk and flash**                          | Wecken braucht eine gemeldete Wecken-Fähigkeit; Wecken sowie Hupen und Blinken sind in der Entity-Registry standardmäßig deaktiviert        |
| Modellabhängig                            | Lademodus und Ziel-Ladestand ändern                                      | Audi kann eine HTTP-Anfrage annehmen, die Einstellung aber ablehnen oder nicht anwenden                                                            |

_Veraltet_ bezeichnet eine ältere Schnittstelle, keine angekündigte Entfernung. Die Integration behält vorhandene Unique-IDs und Service-Aufrufe, soweit möglich. Verfügbarkeit und Funktionsumfang müssen pro Fahrzeug geprüft werden, nicht aus einem einzelnen erfolgreichen Befehl oder einer Fähigkeitenliste abgeleitet. Eine unvollständige Cloud-Antwort kann eine Entity **nicht verfügbar** machen, statt sie zu entfernen.

**Ver-/Entriegeln:** Beide Richtungen nutzen einen Refresh nach dem Befehl und setzen das Attribut `last_command_status`: `request_failed`, `accepted_unconfirmed`, `confirmed_by_readback` oder `already_reported_in_requested_state`. Eine Bestätigung des Audi-Gateways oder ein verzögerter Cloud-Zustand ist keine bestätigte Türaktion am Fahrzeug, und keine Richtung wiederholt den Befehl blind.

**Motor aus der Ferne:** Ältere Verbrenner ohne Fähigkeitenliste (nicht Auth0) behalten den bisherigen Motor-Button als Rückfall. Ausdrücklich verweigerte Fähigkeiten, eingeschränkte Unterstützung, bekannte Hybrid-/Elektrotypen und Q8-Modellsperren gelten weiter. Auth0-Fahrzeuge brauchen eine ausdrücklich gemeldete Berechtigung.

**Ladeeinstellungen:** Bei Auth0-Fahrzeugen verweigert eine Änderung des globalen Ziel-Ladestands das Senden eines möglicherweise zerstörenden `charging/settings`-PUT, wenn Audi unbekannte Einstellungen zurückgibt. Bekannte schreibbare Einstellungen bleiben erhalten; Zeitstempel-Metadaten werden ausgelassen. Weitere schreibbare Schlüssel brauchen fahrzeugspezifische Belege.

**Q8-Klima:** Beim getesteten Audi Q8 PHEV funktioniert Klima EIN/AUS über den separaten modernen Auth0/CARIAD-Befehlsweg mit den im Auto gespeicherten Einstellungen. Eine Temperatur an die alte Klima-Schnittstelle zu übergeben hat bei diesem Fahrzeug nicht funktioniert. Das belegt keine Unterstützung für andere Audi-Typen oder Regionen. Ein künftiges Fähigkeitenmodell sollte gemeldete Funktionen mit Fahrzeugtyp, API-Generation und geprüftem modellspezifischem Verhalten kombinieren, ohne anzunehmen, dass ein Modellname eine Berechtigung gewährt oder eine fehlende Fähigkeit ein endgültiger Gegenbeweis ist.

**Wecken / schlafendes Fahrzeug:** Der Button `Wake vehicle` wird angelegt, wenn das Auto eine Wecken-Fähigkeit meldet. Er ist in der Entity-Registry standardmäßig deaktiviert und von Hand aktivierbar. Er nutzt die Auth0/CARIAD-Route `vehiclewakeuptrigger`. An einem A6 e-tron antwortet sie mit 204, und das Auto meldet danach einen frischen Zeitstempel. Das belegt eine Reaktion des Autos, aber nicht, dass jedes Auto und jede Region so antwortet; vor allem ersetzt eine 2xx-Antwort allein nie die Prüfung des danach gemeldeten Zustands. Ein Wecken, das das Auto nicht ausführt, gilt als Warnung und nicht als Fehler.

Ein geparktes Fahrzeug zu wecken kann Energie aus der 12-V- und/oder Traktionsbatterie kosten. Deshalb weckt die automatische Abfrage das Fahrzeug **nie** in jedem Zyklus, und das soll so bleiben: Passiver Cloud-Refresh und aktives Wecken bleiben getrennt, Auslöser ist ausdrückliche Nutzerabsicht, und die Aktualität wird nach einem begrenzten, verzögerten Rücklesen bestätigt, bevor Wecken oder Ladestatus als aktuell gelten. Messungen zur Auswirkung auf die Batterie des geparkten Fahrzeugs liegen nicht vor.

`Refresh vehicle data` nutzt eine andere Route (`vehiclewakeup`) und wartet bis zu 100 Sekunden auf die Antwort des Autos. Antwortet das Auto nicht rechtzeitig, steht eine Warnung im Log, kein Fehler: Es kann schlafen oder außer Reichweite sein.

## Warum eine Entity manchmal verschwindet

Entities werden beim Einrichten der Integration angelegt, und bisher fragte diese Entscheidung, ob der Wert in der gerade gehaltenen Abfrage vorhanden war. Eine unvollständige oder ratenbegrenzte Abfrage hat deshalb Bedienelemente entfernt: Bei einem Fahrzeug nahm ein `429 Too Many Requests` sechzehn Entities mit, darunter einen Parkpositions-Sensor für ein Auto, das offensichtlich eine Parkposition hat. Sie kamen erst nach einem Neuladen zurück.

Das Auto meldet getrennt von jeder einzelnen Abfrage, was es kann, und die Integration fragt jetzt diese Liste, wo sich eine Fähigkeit eindeutig auf eine Entity abbilden lässt. Ein fehlender Wert macht die Entity nicht verfügbar, statt sie zu löschen.

Fahrzeuge, die keine Fähigkeitenliste melden, sind nicht betroffen und behalten das bisherige Verhalten.
