# Rick's Boekhoud Programma

Een boekhoudprogramma voor thuis (particulier gebruik), in het blauw/matrixgroen design van de ontwerprenders in `ontwerp/`.

## Wat kan het?

- **Bankbestand inladen** — CAMT.053 (XML), CSV (NL-banken) en MT940 (.sta)
- **Loonstrookjes (PDF) inladen** — waarden worden uit de PDF gelezen en kun je controleren; ook handmatig invullen
- **Transacties overzicht** — filteren op jaar/categorie/type, per regel de categorie en vast/variabel aanpassen
- **Kosteninzicht** — alle kostenposten met grafieken: per categorie, vast vs. variabel, gemiddelde vaste lasten p/m
- **IB-aangifte uitwerking** — Box I (loon, loonheffing, hypotheekrenteaftrek, eigenwoningforfait) en Box III (banktegoeden), klaar in januari; CSV/Excel-export
- **Rapporten** — transacties per jaar naar CSV exporteren
- **Lokaal en versleuteld** — alles staat in één versleuteld bestand op je eigen pc (AES-256 via Fernet, wachtwoord → PBKDF2 300k iteraties). Niets gaat naar het internet.

## Windows exe bouwen

De bouw loopt automatisch via GitHub Actions (workflow `Bouw Windows exe`):

1. Ga in GitHub naar **Actions → Bouw Windows exe**
2. Wacht tot de run groen is (paar minuten)
3. Open de run en download het artefact **Rick-s-Boekhoud-Programma-exe**
4. Plaats de exe waar je wilt en start hem — er opent een venster van 1280×720

> Soms waarschuwen Windows/SmartScreen bij onbekende exe's — normaal bij zelfgebouwde programma's: klik "Toch uitvoeren".

## Zelf draaien (voor ontwikkelaars)

```bash
pip install -r requirements.txt
python app/main.py            # natief venster
python app/main.py -no-native # in de browser
python -m pytest tests        # unit tests
```

## Belangrijke kanttekening

De IB-uitwerking is **indicatief** — geen belastingadvies. Gebruik de cijfers als voorbereiding voor je officiële aangifte en controleer ze in Mijn Belastingdienst.

## Back-up

Via **Instellingen → Back-up downloaden** haal je het versleutelde databestand op. Bewaar hem veilig; zonder je hoofdwachtwoord is de back-up leesbaar voor niemand.
