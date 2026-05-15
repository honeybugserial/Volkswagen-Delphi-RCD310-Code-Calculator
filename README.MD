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

![ScreenShot01](https://github.com/honeybugserial/Volkswagen-Delphi-RCD310-Code-Calculator/blob/main/ScreenShot.png)

---

## 📥 Downloads

**Latest Version**

[⬇️ Download RCD310-CodeCalc.exe (Windows)](https://archive.org/download/rcd-310-code-calc-final/RCD310_CodeCalc-final.exe)

*Direct download from Internet Archive. No registration required.*

---

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
