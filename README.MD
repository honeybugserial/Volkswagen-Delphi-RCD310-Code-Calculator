# RCD310 Delphi Code Calculator & EEPROM Dumper

**A powerful, user-friendly tool to extract radio codes and detailed information from Volkswagen RCD310 Delphi EEPROM dumps.**

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Rich](https://img.shields.io/badge/Rich-Terminal%20UI-brightgreen)

---

## ✨ Features

- **Accurate Radio Code Extraction** — Reads the 4-byte XOR-encoded code at `0xA0` (XOR key `0x65656565`) and formats it as a clean 4-digit code.
- **Rich Information Display** — Extracts and displays:
  - VW Part Number
  - Software Version
  - Hardware Revision
  - Delphi Part Number
  - Firmware details (nicely formatted)
  - Unit ID
  - Region string
  - Sirius ESN (if present)
  - User presets (Sirius-equipped units)
- **User-Friendly** — 
  - Drag & drop or file picker (no command line required)
  - `--force` mode for edge cases
  - Auto-resizes console window (Windows)
- **Robust Validation** — Checks file size, VW PN signature, and Sirius sentinel bytes.

---

## 📸 Preview

### Main Output

```
──────────────────────────────────────────────── RCD310 Delphi - RADVW24C32.BIN ────────────────────────────────────────────────


   VW Part Number         1K0035164D
   SW Version             0010
   HW Revision            H02
   Delphi PN              28305128
   Firmware               DE2-DDM 13.09.11 0001 0372
   Unit ID                VWZ4Z6L3200701
   Region                 LOW NAR      H02

────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
╭────────────────────────────────────────────────────────  Radio Code  ────────────────────────────────────────────────────────╮
│                                                                                                                              │
│                                                           0 6 7 9                                                            │
│                                                                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

## 🚀 Usage

### Option 1: Double-click (Recommended)

1. Download the latest release (`RCD310-CodeCalc.exe` for Windows).
2. Double-click the executable.
3. Select your EEPROM dump (`.bin` file) using the file dialog.
4. Enjoy the results.

### Option 2: Command Line

```bash
RCD310-CodeCalc.exe path/to/dump.bin
RCD310-CodeCalc.exe dump.bin --force
```

### Option 3: Run from source

```
python RCD310_CodeCalc-final.py [dump.bin] [--force]
```

## 📋 Requirements (for source)

- Python 3.8+
- Required packages:
```
pip install rich pygetwindow screeninfo
```

## 🛠️ Building from Source

```
pip install pyinstaller
pyinstaller --onefile --icon=vwRadio.ico --hidden-import rich._unicode_data.unicode17-0-0 RCD310_CodeCalc-final.py

## ⚠️ Disclaimer

- For educational and personal use only.
- This tool is not affiliated with Volkswagen, Delphi, McDonalds, or any automotive manufacturer.
- Always ensure you have legitimate access to the EEPROM dump.

## 📄 License

- Yes

## ❤️ Acknowledgments

- Bill Paxton
