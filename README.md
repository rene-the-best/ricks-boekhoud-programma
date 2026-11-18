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

## Zelf draaien met Python (ook Python 3.15)

De interface is gebouwd met **Tkinter**, dat bij Python zelf zit — er zijn dus geen pakketten meer die een compiler (Microsoft C++ Build Tools) nodig hebben. Alleen dit:

```bash
pip install -r requirements.txt   # cryptography + pdfminer.six, beide kant-en-klare pakketten
python app/main.py
python -m pytest tests            # unit tests
```

Werkt op Python 3.10 t/m 3.15 (en daarbuiten). Geen C++ Build Tools nodig.

## Belangrijke kanttekening

De IB-uitwerking is **indicatief** — geen belastingadvies. Gebruik de cijfers als voorbereiding voor je officiële aangifte en controleer ze in Mijn Belastingdienst.

## Werkomgeving Rick (installeringsnotities)

> Voor toekomstige sessies: dit is de werkomgeving van de gebruiker — houd hier rekening mee.

- **Python**: 3.15 (64-bit) op Windows 10/11
- **Starten via**: `py -m pip install -r requirements.txt` en daarna `py app\main.py` (gebruik `py`, niet `python`)
- **UI**: Tkinter (stdio-bibliotheek) — géén NiceGUI/pyyaml gebruiken, die kunnen op zijn Python-versie compileren
- **PDF**: pdfminer.six (pure Python) — géén pdfplumber
- **Code-downloads**: zip pakt uit met een geneste map (map-in-map); de projectmap met `requirements.txt` ligt één niveau dieper
- **Exe**: wordt gebouwd via GitHub Actions; downloaden via *Actions → run → Artifacts* (ingelogd op GitHub vereist)
- **Data-map op Windows**: `%APPDATA%\RicksBoekhoudProgramma\` (versleuteld `data.enc`)

## Back-up

Via **Instellingen → Back-up downloaden** haal je het versleutelde databestand op. Bewaar hem veilig; zonder je hoofdwachtwoord is de back-up leesbaar voor niemand.
