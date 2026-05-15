import sys
import ctypes
import os
import time
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.rule import Rule
from rich.live import Live

console = Console()

# ----------------------------
# offsets (all confirmed from binary analysis)
# ----------------------------

CODE_OFFSET       = 0xA0   # 4 bytes XOR-encoded radio code
XOR_KEY           = 0x65656565

SW_OFFSET         = 0xA8   # 1 byte decimal SW version (e.g. 0x05 -> "0005")
DELPHI_PN_OFFSET  = 0xAD   # 8 bytes ASCII Delphi PN
DELPHI_PN_LEN     = 8

FW_OFFSET         = 0xB8   # firmware string: "DE2-DDM12.07.1300010613-"
FW_LEN            = 0x18

UNIT_ID_OFFSET    = 0xD7   # unit ID string: "VWZ4Z6N3599870"
UNIT_ID_LEN       = 14

REGION_OFFSET     = 0xF0   # e.g. "LOW NAR SDARS H03"
REGION_LEN        = 0x10

MIN_FILE_SIZE     = REGION_OFFSET + REGION_LEN

# optional — only present in Sirius-equipped units / full 4KB dumps
SIRIUS_SENTINEL   = 0x4F0  # sentinel bytes 0x55 precede ESN
SIRIUS_ESN_OFFSET = 0x4F8  # 12 bytes ASCII Sirius ESN
SIRIUS_ESN_LEN    = 12

PRESET_OFFSET     = 0x508  # 18 presets x 12 bytes each
PRESET_STRIDE     = 12
PRESET_COUNT      = 18
PRESET_DEFAULT    = "Preview"


# ----------------------------
# helpers
# ----------------------------

def read_ascii(f, offset, length):
    f.seek(offset)
    return f.read(length).decode("ascii", errors="ignore")


def clean(s):
    return s.replace("\x00", "").strip()


def get_file_size(f):
    pos = f.tell()
    f.seek(0, 2)
    size = f.tell()
    f.seek(pos)
    return size


# ----------------------------
# extractors
# ----------------------------

def extract_vw_pn(f):
    f.seek(0xC0)
    text = f.read(0x40).decode("ascii", errors="ignore")
    start = text.find("1K0035")
    if start == -1:
        return None
    return text[start:start + 10]


def extract_code(f):
    """4 bytes at 0xA0 XORed with key; every other hex digit = 4-digit code."""
    f.seek(CODE_OFFSET)
    raw = f.read(4)
    if len(raw) != 4:
        raise ValueError("Invalid EEPROM read at code offset")
    xored = int(raw.hex(), 16) ^ XOR_KEY
    return hex(xored)[2::2].zfill(4)


def extract_sw_version(f):
    """Single byte at 0xA8, zero-padded to 4 decimal digits."""
    f.seek(SW_OFFSET)
    return f"{f.read(1)[0]:04d}"


def extract_delphi_pn(f):
    """8 ASCII bytes at 0xAD, leading zeros stripped."""
    f.seek(DELPHI_PN_OFFSET)
    raw = f.read(DELPHI_PN_LEN).decode("ascii", errors="ignore").strip("\x00").strip()
    return raw.lstrip("0") or "0"


def extract_firmware(f):
    """
    Raw: 'DE2-DDM12.07.1300010613-'
    Formatted: 'DE2-DDM 12.07.13 0001 0613'
    Structure: model(7) + date(8) + build(4) + datecode(4) + '-'
    """
    f.seek(FW_OFFSET)
    raw = f.read(FW_LEN).decode("ascii", errors="ignore").replace("\x00", "").rstrip("-").strip()
    if len(raw) >= 23:
        return f"{raw[0:7]} {raw[7:15]} {raw[15:19]} {raw[19:23]}"
    return raw


def extract_unit_id(f):
    """14 bytes at 0xD7, e.g. 'VWZ4Z6N3599870'"""
    return clean(read_ascii(f, UNIT_ID_OFFSET, UNIT_ID_LEN))


def extract_region(f):
    return clean(read_ascii(f, REGION_OFFSET, REGION_LEN))


def extract_hw(f):
    region = extract_region(f)
    if "H" not in region:
        return None
    return "H" + region.split("H", 1)[1]


def extract_sirius_esn(f):
    """
    Sirius ESN at 0x4F8, 12 ASCII digits.
    Validated by 0x55 sentinel bytes at 0x4F0 and 0x4F6.
    Returns None if not present or invalid.
    """
    if get_file_size(f) < SIRIUS_ESN_OFFSET + SIRIUS_ESN_LEN:
        return None
    f.seek(SIRIUS_SENTINEL)
    sentinels = f.read(8)
    if sentinels[0] != 0x55 or sentinels[6] != 0x55:
        return None
    f.seek(SIRIUS_ESN_OFFSET)
    raw = f.read(SIRIUS_ESN_LEN).decode("ascii", errors="ignore").strip("\x00").strip()
    return raw if (raw and raw.isdigit()) else None


def extract_presets(f, has_sirius):
    """
    18 Sirius preset names at 0x508, 12 bytes each.
    Only valid on Sirius-equipped units — gated on has_sirius.
    Returns list of (slot, name) tuples, or None.
    """
    if not has_sirius:
        return None
    if get_file_size(f) < PRESET_OFFSET + PRESET_COUNT * PRESET_STRIDE:
        return None
    presets = []
    for i in range(PRESET_COUNT):
        f.seek(PRESET_OFFSET + i * PRESET_STRIDE)
        raw = f.read(PRESET_STRIDE).decode("ascii", errors="ignore").strip("\x00").strip()
        if raw and raw != PRESET_DEFAULT:
            presets.append((i + 1, raw))
    return presets if presets else None


# ----------------------------
# main extract
# ----------------------------

def extract(path, force=False):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    size = os.path.getsize(path)
    if size < MIN_FILE_SIZE:
        if force:
            console.print(f"[yellow]Warning:[/] file too small ({size} bytes), results may be incomplete or wrong")
        else:
            raise ValueError(f"File too small ({size} bytes), expected at least {MIN_FILE_SIZE} — use --force to try anyway")

    with open(path, "rb") as f:
        vw = extract_vw_pn(f)
        if not vw:
            if force:
                console.print("[yellow]Warning:[/] VW PN not found — results may be wrong")
                vw = "UNKNOWN"
            else:
                raise ValueError("VW PN not found — may not be an RCD310 Delphi dump — use --force to try anyway")
        esn = extract_sirius_esn(f)
        return {
            "vw_pn":      vw,
            "code":       extract_code(f),
            "sw":         extract_sw_version(f),
            "hw":         extract_hw(f),
            "delphi_pn":  extract_delphi_pn(f),
            "firmware":   extract_firmware(f),
            "unit_id":    extract_unit_id(f),
            "region":     extract_region(f),
            "sirius_esn": esn,
            "presets":    extract_presets(f, has_sirius=esn is not None),
        }


# ----------------------------
# display
# ----------------------------

def print_results(info, filename):
    console.print()

    # header
    console.rule(f"[bold grey50]RCD310 Delphi - {os.path.basename(filename)}[/]")
    console.print()

    # info table
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(style="dim", width=18)
    table.add_column()

    table.add_row("VW Part Number",  f"[white]{info['vw_pn']}[/]")
    table.add_row("SW Version",      f"[white]{info['sw']}[/]")
    table.add_row("HW Revision",     f"[white]{info['hw'] or 'N/A'}[/]")
    table.add_row("Delphi PN",       f"[white]{info['delphi_pn']}[/]")
    table.add_row("Firmware",        f"[white]{info['firmware']}[/]")
    table.add_row("Unit ID",         f"[white]{info['unit_id']}[/]")
    table.add_row("Region",          f"[white]{info['region']}[/]")

    if info['sirius_esn']:
        table.add_row("Sirius ESN",  f"[white]{info['sirius_esn']}[/]")

    if info['presets']:
        names = "  ".join(name for _, name in info['presets'])
        table.add_row("Presets", f"[dim white]{names}[/]")

    console.print(table)

    # radio code panel — the main event
    spaced_code = " ".join(info['code'])
    code_text = Text(spaced_code, style="bold green", justify="center", end="")
    console.print(Rule(style="dim"))
    console.print(
        Panel(
            Align.center(code_text),
            title="[bold white] Radio Code [/]",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )
    console.print()


# ----------------------------
# file picker
# ----------------------------

def pick_file_gui():
    """
    Open a tkinter file-open dialog defaulting to the script directory,
    filtered to .bin files.  Returns the chosen path, or None if cancelled.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog

        script_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

        root = tk.Tk()
        root.withdraw()           # hide the blank Tk window
        root.attributes("-topmost", True)   # dialog appears on top

        path = filedialog.askopenfilename(
            title="Select RCD310 EEPROM dump",
            initialdir=script_dir,
            filetypes=[("Binary dump", "*.bin"), ("All files", "*.*")],
        )
        root.destroy()
        return path or None

    except Exception as e:
        console.print(f"[bold red]Could not open file picker:[/] {e}")
        return None


# --- Clear Console
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

# --- Set Console Title
def set_terminal_title(title: str):
    """Directly sets the console window title."""
    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW(title)

# --- Resize Console Window
def resize_console(w: int = 1500, h: int = 800, title: str = None) -> bool:
    try:
        import pygetwindow as gw
    except ImportError:
        return False

    try:
        from screeninfo import get_monitors
        monitors = get_monitors()
        primary = next((m for m in monitors if m.x == 0 and m.y == 0), monitors[0])
        screen_w = primary.width
        screen_h = primary.height
    except Exception:
        screen_w = 1920
        screen_h = 1080

    # Clamp to screen
    w = min(w, screen_w)
    h = min(h, screen_h)

    # Center position
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2

    # Find window by title or try common console titles
    #console_titles = ["testTitle", title]
    console_titles = title
    win = None

    if title:
        wins = gw.getWindowsWithTitle(title)
        if wins:
            win = wins[0]
    else:
        for t in console_titles:
            wins = gw.getWindowsWithTitle(t)
            if wins:
                win = wins[0]
                break

    if not win:
        return False

    try:
        win.resizeTo(w, h)
        win.moveTo(x, y)
        return True
    except Exception:
        return False


def print_header():
    console = Console()
    
    # New ASCII Art for "Delphi Dumper"
    header_text = r"""                                                        
█████▄  ▄█████ ████▄  ████▄ ▄██  ▄██▄    ▄█████  ▄▄▄  ▄▄▄▄  ▄▄▄▄▄ 
██▄▄██▄ ██     ██  ██  ▄▄██  ██ ██  ██   ██     ██▀██ ██▀██ ██▄▄  
██   ██ ▀█████ ████▀  ▄▄▄█▀  ██  ▀██▀    ▀█████ ▀███▀ ████▀ ██▄▄▄ 
                                                                  
▄█████  ▄▄▄  ▄▄     ▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄  ▄▄ ▄▄  ▄▄  ▄▄▄▄ ▄▄▄▄▄ ▄▄▄▄   
██     ██▀██ ██    ██▀▀▀ ██▄▄  ██▄█▄ ██ ███▄██ ██ ▄▄ ██▄▄  ██▄█▄  
▀█████ ██▀██ ██▄▄▄ ▀████ ██▄▄▄ ██ ██ ██ ██ ▀██ ▀███▀ ██▄▄▄ ██ ██  
    """
    
    # Technical tagline in brackets
    tagline = "[ A Delphi // 0xA0 XOR-65 Code Calculator Tool ]"

    colors = ["red", "orange3", "magenta"]
    i = 0

    try:
        with Live(auto_refresh=False) as live:
            while i < 20:
                current_color = colors[i % len(colors)]
                
                # Combine the ASCII and the Tagline into a single centered display
                content = Text.assemble(
                    (header_text, current_color),
                    ("\n", ""),
                    (f"{tagline.center(65)}", "bold white")
                )
                
                panel = Panel(
                    Align.center(content),
                    border_style=current_color, 
                    expand=True,
                    padding=(1, 1)
                )
                
                live.update(panel, refresh=True)
                i += 1
                time.sleep(0.07746) 
    except KeyboardInterrupt:
        console.print("\n[bold white]Strobe stopped by user.[/]")


def main():
    import argparse
    
    temp_title = "RCD310 Code Calcering"
    set_terminal_title(temp_title)
    
    clear_screen()
    resize_console(1200, 500, title=temp_title)
    time.sleep(0.05)
    print_header()
    
    parser = argparse.ArgumentParser(description="RCD310 Delphi EEPROM Info Extractor", add_help=True)
    parser.add_argument("dump", nargs="?", default=None, help="Path to EEPROM dump file (.bin) — omit to open a file picker")
    parser.add_argument("--force", action="store_true", help="Try to extract even if the file looks invalid")
    args = parser.parse_args()

    dump_path = args.dump

    if dump_path is None:
        console.print("[dim]No file specified — opening file picker…[/]")
        dump_path = pick_file_gui()
        if not dump_path:
            console.print("[bold red]No file selected. Exiting.[/]")
            sys.exit(1)

    try:
        info = extract(dump_path, force=args.force)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[bold red]Error:[/] {e}")
        sys.exit(1)

    print_results(info, dump_path)
    input("\nPress Enter to exit…")
    
if __name__ == "__main__":
    main()