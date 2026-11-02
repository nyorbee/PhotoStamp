"""
PhotoStamp - napis z miejscem (i nie tylko) wtopiony w zdjęcia, np. do cyfrowej ramki.
https://github.com/nyorbee/PhotoStamp   (licencja MIT)

Zakładka 1: każde zdjęcie dostaje własny napis (np. "Gdańsk / Polsat Plus Arena")
            w wybranym stylu: pudełko, matowe szkło, pastylka z pinezką, akcent, sam tekst z cieniem.
Zakładka 2: zapisuje współrzędne GPS do EXIF (aplikacje typu Fotoo zamieniają je na nazwę miejsca).

Wymaga: pip install -r requirements.txt   (pillow, piexif)
"""

import json
import os
import shutil
import sys
import threading
import tkinter as tk
import urllib.parse
import urllib.request
import webbrowser
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

import piexif
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageTk
from PIL import JpegImagePlugin, PngImagePlugin  # noqa: F401  (jawnie, żeby Nuitka je dołączyła)

APP_NAME = "PhotoStamp"
APP_VERSION = "1.2"          # podbijaj razem z --product-version w komendzie Nuitki
FACEBOOK_URL = "https://www.facebook.com/ajtiguy"
GITHUB_URL = "https://github.com/nyorbee/PhotoStamp"


def resource_path(name):
    """Plik dołączony do programu (photostamp.ico, created.png) - działa z .py i z exe Nuitki."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

# ---------- język interfejsu (EN / PL) ----------
# Klucze = teksty polskie (tak jak w kodzie); wartości = angielskie.
# Wewnętrzne nazwy stylów/pozycji/akcentów zostają po polsku (zapisana praca i szablony
# działają w obu językach) - tłumaczony jest tylko to, co widać na ekranie.
LANG = "en"

EN = {
    # pozycje / style / akcenty / czcionki
    "Lewy dolny róg": "Bottom left",
    "Środek dołu": "Bottom centre",
    "Prawy dolny róg": "Bottom right",
    "Lewy górny róg": "Top left",
    "Środek góry": "Top centre",
    "Prawy górny róg": "Top right",
    "Własna (przeciągnij myszką)": "Custom (drag with the mouse)",
    "Pudełko": "Box",
    "Matowe szkło": "Frosted glass",
    "Pastylka z pinezką": "Pill with pin",
    "Pastylka z pinezką na matowym szkle": "Pill with pin on frosted glass",
    "Półprzezroczyste z akcentem": "Translucent with accent",
    "Matowe szkło z akcentem": "Frosted glass with accent",
    "Sam tekst z cieniem": "Text with shadow only",
    "Czerwony – lokomotywa": "Red – locomotive",
    "Pomarańczowy – zachód słońca": "Orange – sunset",
    "Złoty – piasek": "Gold – sand",
    "Zielony – las": "Green – forest",
    "Turkusowy – morze": "Turquoise – sea",
    "Niebieski – niebo": "Blue – sky",
    "Fioletowy – lawenda": "Purple – lavender",
    "Różowy – kwiaty": "Pink – flowers",
    "Biały": "White",
    "Własny kolor…": "Custom colour…",
    "Własny ({col})": "Custom ({col})",
    "Automatycznie (jak 1. linia)": "Automatic (like line 1)",
    "Domyślna": "Default",
    # okno główne
    "{app} v{ver}  –  napis i lokalizacja na zdjęciach": "{app} v{ver}  –  captions and location on photos",
    "Zdjęcia (JPEG)": "Photos (JPEG)",
    "Dodaj pliki…": "Add files…",
    "Dodaj folder…": "Add folder…",
    "Usuń zaznaczone": "Remove selected",
    "Wyczyść": "Clear",
    "{n} plików": "{n} files",
    "Każde zdjęcie ma własny napis – to, co wpiszesz, zostaje tylko na wybranym zdjęciu. "
    "Nowe zdjęcie startuje z pustym tekstem i wyglądem/pozycją z poprzedniego.":
        "Every photo has its own caption – what you type stays on the selected photo only. "
        "A new photo starts with empty text and the look/position of the previous one.",
    "Dodaj zdjęcia, żeby zacząć.": "Add photos to get started.",
    "Język:": "Language:",
    # zakładka napisu
    "Napis na zdjęciu": "Caption on photo",
    "Podgląd – przeciągnij napis myszką; rozmiar: kółko myszy albo biały kwadracik w rogu":
        "Preview – drag the caption with the mouse; resize: mouse wheel or the white corner handle",
    "◀ Poprzednie": "◀ Previous",
    "Następne ▶": "Next ▶",
    "Dodaj zdjęcia, żeby zobaczyć podgląd": "Add photos to see a preview",
    "Szablony": "Templates",
    "Zapisz jako…": "Save as…",
    "Usuń": "Delete",
    "Tekst:": "Text:",
    "(\\n = nowa linia)": "(\\n = new line)",
    "Styl:": "Style:",
    "Pinezka przed napisem (w kolorze akcentu)": "Pin before the caption (accent colour)",
    "Kolor akcentu:": "Accent colour:",
    "(pasek przy stylu z akcentem, pinezka w pastylce)": "(bar in accent styles, pin in pills)",
    "Plik…": "File…",
    "Czcionka:": "Font:",
    "Rozmiar (% krótszego boku):": "Size (% of shorter side):",
    "Odstęp między liniami:": "Line spacing:",
    "Druga i dalsze linie:": "Second and further lines:",
    "Czcionka dalszych linii:": "Font of further lines:",
    "Automatycznie = cieńsza odmiana 1. linii": "Automatic = lighter weight of line 1",
    "Pozycja:": "Position:",
    "(albo złap napis myszką na podglądzie)": "(or grab the caption on the preview)",
    "Tekst": "Text",
    "Tło / cień": "Bg / shadow",
    "Kolory:": "Colours:",
    "Krycie tła / cienia (%):": "Background / shadow opacity (%):",
    "Rozmycie cienia:": "Shadow blur:",
    "Grubość cienia:": "Shadow spread:",
    "(suwaki cienia działają przy stylu „Sam tekst z cieniem”)": "(shadow sliders apply to “Text with shadow only”)",
    "Zaokrąglenie rogów:": "Corner rounding:",
    "Odstęp tekstu od krawędzi tła:": "Text padding inside background:",
    "Margines od brzegu zdjęcia (%):": "Margin from photo edge (%):",
    "Obrys tekstu (gdy tło przezroczyste)": "Text outline (for transparent background)",
    "Jakość JPEG:": "JPEG quality:",
    "Ten WYGLĄD na wszystkie (napisy i pozycje zostają)": "This LOOK on all photos (texts and positions stay)",
    "Napis + wygląd na wszystkie": "Caption + look on all",
    "Kopie do „z_napisem”": "Copies to “z_napisem”",
    "Nadpisz oryginały": "Overwrite originals",
    "  Dodaj napisy do zdjęć  ": "  Add captions to photos  ",
    "(bez napisu)": "(no caption)",
    "Rozmiar napisu: {v}%": "Caption size: {v}%",
    "Nie da się pokazać podglądu:\n{ex}": "Cannot show the preview:\n{ex}",
    "Wybierz kolor": "Choose colour",
    "Kolor akcentu": "Accent colour",
    # szablony
    "Błąd": "Error",
    "Nie udało się zapisać szablonów:\n{ex}": "Could not save templates:\n{ex}",
    "Zapisz szablon": "Save template",
    "Nazwa szablonu:": "Template name:",
    "Szablon istnieje": "Template exists",
    "Szablon „{name}” już istnieje. Nadpisać?": "Template “{name}” already exists. Overwrite?",
    "Zapisano szablon „{name}”.": "Template “{name}” saved.",
    "Usuń szablon": "Delete template",
    "Najpierw wybierz szablon z listy.": "Select a template from the list first.",
    "Usunąć szablon „{name}”?": "Delete template “{name}”?",
    "Usunięto szablon „{name}”.": "Template “{name}” deleted.",
    "Szablon „{name}” ustawiony na zdjęciu {photo}.": "Template “{name}” applied to {photo}.",
    # praca / wszystkie zdjęcia
    "Nie udało się zapisać pracy: {ex}": "Could not save your work: {ex}",
    "Ostatnia praca": "Previous work",
    "Wczytać ostatnią pracę?\n\n{n} zdjęć, w tym {t} z wpisanym napisem.":
        "Load your previous work?\n\n{n} photos, {t} of them with a caption.",
    "\n({n} plików już nie ma na dysku – zostaną pominięte.)":
        "\n({n} files no longer exist on disk – they will be skipped.)",
    "Wczytano pracę: {n} zdjęć, {t} z napisem.": "Work loaded: {n} photos, {t} with a caption.",
    "Wszystkie zdjęcia": "All photos",
    "Ustawić obecny napis i wygląd na wszystkich {n} zdjęciach?\nNapisy wpisane wcześniej w innych zdjęciach zostaną zastąpione.":
        "Apply the current caption and look to all {n} photos?\nCaptions typed earlier on other photos will be replaced.",
    "Ustawiono na wszystkich {n} zdjęciach.": "Applied to all {n} photos.",
    "Wygląd na wszystkie": "Look on all photos",
    "Ustawić obecny wygląd (styl, czcionkę, kolory, rozmiar) na wszystkich {n} zdjęciach?\n\nNapisy i pozycje każdego zdjęcia zostają bez zmian.":
        "Apply the current look (style, font, colours, size) to all {n} photos?\n\nEach photo keeps its own caption and position.",
    "Wygląd ustawiony na {n} zdjęciach z napisem – napisy i pozycje bez zmian.":
        "Look applied to {n} captioned photos – captions and positions unchanged.",
    # zapis zdjęć
    "Brak zdjęć": "No photos",
    "Dodaj najpierw zdjęcia.": "Add some photos first.",
    "Brak tekstu": "No text",
    "Żadne zdjęcie nie ma wpisanego napisu.": "None of the photos has a caption.",
    "Dodać napisy do {n} zdjęć?": "Add captions to {n} photos?",
    "\n{n} zdjęć bez napisu zostanie pominiętych.": "\n{n} photos without a caption will be skipped.",
    "\n\nOryginały zostaną nadpisane (kopie w „_oryginaly”).": "\n\nOriginals will be overwritten (backups in “_oryginaly”).",
    "Potwierdź": "Confirm",
    "Dodaję napisy… {n}/{total}": "Adding captions… {n}/{total}",
    "w oryginałach": "in the originals",
    "w podfolderach „z_napisem”": "in “z_napisem” subfolders",
    "Gotowe: {ok} zdjęć {where}, {err} błędów.": "Done: {ok} photos {where}, {err} errors.",
    "Część plików pominięta": "Some files were skipped",
    "Gotowe": "Done",
    "Dodano napis do {ok} zdjęć ({where}).": "Caption added to {ok} photos ({where}).",
    # zakładka GPS
    "Lokalizacja GPS w EXIF": "GPS location in EXIF",
    "Fotoo zamienia współrzędne na nazwę sam (tryb exact = adres, abbreviated = skrót). "
    "Własnego tekstu tak nie ustawisz – do tego służy zakładka „Napis na zdjęciu”.":
        "Frame apps such as Fotoo turn coordinates into a place name themselves (exact = address, "
        "abbreviated = short). You cannot set your own text this way – use the “Caption on photo” tab for that.",
    "Miejsce:": "Place:",
    "Islandia": "Iceland",
    "Szukaj": "Search",
    "Wynik:": "Result:",
    "Szerokość (lat):": "Latitude:",
    "Długość (lon):": "Longitude:",
    "(możesz też wpisać ręcznie)": "(you can also type them in)",
    "Zachowaj datę modyfikacji pliku": "Keep file modification date",
    "Kopia oryginałów do „_oryginaly”": "Back up originals to “_oryginaly”",
    "Zapisz GPS do zdjęć": "Write GPS to photos",
    "Szukam „{q}”…": "Searching for “{q}”…",
    "Błąd wyszukiwania: {err}": "Search error: {err}",
    "Nic nie znaleziono.": "Nothing found.",
    "Znaleziono {n} wyników. Sprawdź, czy pierwszy jest właściwy.": "Found {n} results. Check that the first one is right.",
    "Złe współrzędne": "Invalid coordinates",
    "Podaj poprawną szerokość (-90..90) i długość (-180..180).": "Enter a valid latitude (-90..90) and longitude (-180..180).",
    "Zapisać GPS {la}, {lo} do {n} zdjęć?": "Write GPS {la}, {lo} to {n} photos?",
    "Zapisuję GPS… {n}/{total}": "Writing GPS… {n}/{total}",
    "Gotowe: {ok} zapisanych, {err} błędów.": "Done: {ok} written, {err} errors.",
    "brak GPS": "no GPS",
}


def tr(s, **kw):
    """Tekst w bieżącym języku; kw wstawiane w {pola}."""
    t = EN.get(s, s) if LANG == "en" else s
    return t.format(**kw) if kw else t


class MappedCombo(ttk.Combobox):
    """Lista rozwijana, która POKAZUJE przetłumaczone nazwy, a w zmiennej trzyma wewnętrzne (polskie)."""

    def __init__(self, master, var, keys_fn, **kw):
        self.var, self.keys_fn = var, keys_fn
        self.disp = tk.StringVar()
        super().__init__(master, textvariable=self.disp, state="readonly", **kw)
        self.bind("<<ComboboxSelected>>", self._picked, add="+")
        var.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    def refresh(self):
        self.config(values=[tr(k) for k in self.keys_fn()])
        self.disp.set(tr(self.var.get()))

    def _picked(self, _e=None):
        i, keys = self.current(), self.keys_fn()
        if 0 <= i < len(keys) and self.var.get() != keys[i]:
            self.var.set(keys[i])


JPEG_EXT = (".jpg", ".jpeg", ".jpe")
SKIP_DIRS = {"_oryginaly", "z_napisem"}
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".exif_lokalizacja.json")
TEMPLATES_FILE = os.path.join(os.path.expanduser("~"), ".exif_lokalizacja_szablony.json")
WORK_FILE = os.path.join(os.path.expanduser("~"), ".exif_lokalizacja_praca.json")
NOT_IN_TEMPLATE = {"overwrite"}  # gdzie zapisywać - to nie część wyglądu

POSITIONS = {
    "Lewy dolny róg": ("left", "bottom"),
    "Środek dołu": ("center", "bottom"),
    "Prawy dolny róg": ("right", "bottom"),
    "Lewy górny róg": ("left", "top"),
    "Środek góry": ("center", "top"),
    "Prawy górny róg": ("right", "top"),
}
CUSTOM = "Własna (przeciągnij myszką)"
SNAP = 0.025  # przyciąganie do krawędzi i środka podczas przeciągania

STYLES = [
    "Pudełko",
    "Matowe szkło",
    "Pastylka z pinezką",
    "Pastylka z pinezką na matowym szkle",
    "Półprzezroczyste z akcentem",
    "Matowe szkło z akcentem",
    "Sam tekst z cieniem",
]
# wybranie stylu z listy ustawia dla niego sensowne tło (potem możesz to zmienić)
STYLE_PRESETS = {
    "Pudełko": {"bg": "#000000", "bg_opacity": 100, "radius_pct": 25, "pad_pct": 45},
    "Matowe szkło": {"bg": "#0f141e", "bg_opacity": 40, "radius_pct": 40, "pad_pct": 55},
    "Pastylka z pinezką": {"bg": "#000000", "bg_opacity": 55, "pad_pct": 50},
    "Pastylka z pinezką na matowym szkle": {"bg": "#0f141e", "bg_opacity": 40, "pad_pct": 50},
    "Półprzezroczyste z akcentem": {"bg": "#000000", "bg_opacity": 60, "radius_pct": 20, "pad_pct": 55},
    "Matowe szkło z akcentem": {"bg": "#0f141e", "bg_opacity": 40, "radius_pct": 20, "pad_pct": 55},
    "Sam tekst z cieniem": {"bg": "#000000", "bg_opacity": 80, "shadow_blur_pct": 18, "shadow_spread_pct": 6},
}
ACCENTS = {
    "Czerwony – lokomotywa": "#e62828",
    "Pomarańczowy – zachód słońca": "#ff7a1a",
    "Złoty – piasek": "#f2b632",
    "Zielony – las": "#3fae5a",
    "Turkusowy – morze": "#1fb5ad",
    "Niebieski – niebo": "#2f86eb",
    "Fioletowy – lawenda": "#8a5cf6",
    "Różowy – kwiaty": "#ff5fa2",
    "Biały": "#ffffff",
}
ACCENT_CUSTOM = "Własny kolor…"

DEFAULTS = {
    "style": "Pudełko",
    "accent": "#e62828",
    "sub_size_pct": 70,
    "sub_lighter": False,
    "shadow_blur_pct": 18,
    "shadow_spread_pct": 6,
    "show_pin": False,
    "sub_font": "Automatycznie (jak 1. linia)",
    "text": "Islandia",
    "font": "Segoe UI Semibold",
    "font_file": "",
    "size_pct": 4.0,
    "line_spacing_pct": 20,
    "position": "Lewy dolny róg",
    "pos_x": 0.0,
    "pos_y": 1.0,
    "fg": "#ffffff",
    "bg": "#000000",
    "bg_opacity": 100,
    "radius_pct": 25,
    "pad_pct": 45,
    "margin_pct": 3.0,
    "stroke": False,
    "quality": 95,
    "overwrite": False,
}


# ---------- czcionki ----------

def find_fonts():
    """Zwraca {nazwa: ścieżka} dla WSZYSTKICH czcionek zainstalowanych w systemie
    (nazwa = rodzina + odmiana, np. "Segoe UI Semibold", "Arial Bold")."""
    dirs = [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
        "/usr/share/fonts",
        "/Library/Fonts",
        "/System/Library/Fonts/Supplemental",
    ]
    found = {}
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for root, _dirs, names in os.walk(d):
            for n in names:
                if not n.lower().endswith((".ttf", ".otf", ".ttc")):
                    continue
                p = os.path.join(root, n)
                try:
                    fam, sty = ImageFont.truetype(p, 12).getname()
                except Exception:
                    continue
                if not fam:
                    continue
                name = fam if (not sty or sty.lower() in ("regular", "normal", "book", "roman")) else f"{fam} {sty}"
                found.setdefault(name, p)
    if found:
        return dict(sorted(found.items(), key=lambda kv: kv[0].lower()))
    return find_fonts_basic()


def find_fonts_basic():
    """Zapasowo: kilka popularnych czcionek po nazwach plików."""
    candidates = {
        "Segoe UI": "segoeui.ttf",
        "Segoe UI Semibold": "seguisb.ttf",
        "Segoe UI Bold": "segoeuib.ttf",
        "Segoe UI Light": "segoeuil.ttf",
        "Bahnschrift": "bahnschrift.ttf",
        "Arial": "arial.ttf",
        "Arial Bold": "arialbd.ttf",
        "Calibri": "calibri.ttf",
        "Georgia": "georgia.ttf",
        "Georgia Italic": "georgiai.ttf",
        "Trebuchet MS": "trebuc.ttf",
        "Verdana": "verdana.ttf",
        "DejaVu Sans": "DejaVuSans.ttf",
        "DejaVu Sans Bold": "DejaVuSans-Bold.ttf",
    }
    dirs = [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
        "/usr/share/fonts/truetype/dejavu",
        "/Library/Fonts",
        "/System/Library/Fonts/Supplemental",
    ]
    found = {}
    for name, fname in candidates.items():
        for d in dirs:
            p = os.path.join(d, fname)
            if d and os.path.isfile(p):
                found[name] = p
                break
    return found


FONTS = find_fonts()
# cieńsza odmiana czcionki dla drugiej i dalszych linii
LIGHTER = {
    "Segoe UI Semibold": "Segoe UI",
    "Segoe UI Bold": "Segoe UI",
    "Segoe UI": "Segoe UI Light",
    "Arial Bold": "Arial",
    "DejaVu Sans Bold": "DejaVu Sans",
}


SUB_AUTO = "Automatycznie (jak 1. linia)"


def lighter_name(name):
    """Cieńsza odmiana tej samej rodziny, np. 'Arial Bold' -> 'Arial'."""
    if LIGHTER.get(name) in FONTS:
        return LIGHTER[name]
    low = name.lower()
    for w in (" extrabold", " extra bold", " black", " heavy", " semibold", " semi bold",
              " demibold", " bold", " medium"):
        if w in low:
            i = low.index(w)
            cand = (name[:i] + name[i + len(w):]).strip()
            if cand in FONTS:
                return cand
            if (cand + " Regular") in FONTS:
                return cand + " Regular"
    return None


def load_font(o, size, sub=False):
    name = o.get("font")
    path = o.get("font_file") or FONTS.get(name)
    if sub:
        if o.get("sub_font") in FONTS:          # wybrana osobna czcionka dalszych linii
            path = FONTS[o["sub_font"]]
        elif o.get("sub_lighter") and not o.get("font_file") and lighter_name(name or ""):
            path = FONTS[lighter_name(name)]    # automatycznie: cieńsza odmiana
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    try:
        return ImageFont.load_default(size=size)  # Pillow 10.1+
    except TypeError:
        return ImageFont.load_default()


# ---------- napis na zdjęciu ----------

def render_label(img, o, return_box=False):
    """Rysuje napis z tłem na kopii obrazu (RGB). Rozmiary liczone względem
    krótszego boku, więc napis wygląda tak samo na każdej rozdzielczości.
    Pozycja własna: pos_x/pos_y od 0 do 1 (0 = lewo/góra, 1 = prawo/dół)."""
    o = {**DEFAULTS, **o}
    raw = str(o["text"]).replace("\\n", "\n").strip()
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if not lines:
        return (img.copy(), None) if return_box else img.copy()
    style = o["style"] if o["style"] in STYLES else STYLES[0]
    pill = style.startswith("Pastylka")
    glass = style in ("Matowe szkło", "Pastylka z pinezką na matowym szkle", "Matowe szkło z akcentem")
    accent_bar = style in ("Półprzezroczyste z akcentem", "Matowe szkło z akcentem")
    shadow = style == "Sam tekst z cieniem"
    if pill:
        lines = ["  ·  ".join(lines)]

    W, H = img.size
    short = min(W, H)
    size = max(8, int(short * float(o["size_pct"]) / 100))
    tf = load_font(o, size)
    sf = load_font(o, max(6, int(size * float(o["sub_size_pct"]) / 100)), sub=True)
    fonts = [tf] + [sf] * (len(lines) - 1)
    stroke = max(1, size // 18) if o["stroke"] else 0
    spacing = int(size * float(o["line_spacing_pct"]) / 100)

    hpos, vpos = POSITIONS.get(o["position"], (None, None))
    fx = min(1.0, max(0.0, float(o["pos_x"])))
    fy = min(1.0, max(0.0, float(o["pos_y"])))
    if hpos is None:  # własna pozycja
        align = "left" if fx < 1 / 3 else "right" if fx > 2 / 3 else "center"
    else:
        align = hpos

    # --- wymiary bloku tekstu: od góry wielkiej litery 1. linii do dołu ogonków ostatniej ---
    meas = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths = [meas.textlength(ln, font=f) + 2 * stroke for ln, f in zip(lines, fonts)]

    def cap(f):
        return -f.getbbox("H", anchor="ls")[1]

    def desc(f):
        return f.getbbox("gjpyą", anchor="ls")[3]

    baselines = [cap(tf) + stroke]
    for i in range(1, len(lines)):
        baselines.append(baselines[-1] + desc(fonts[i - 1]) + spacing + cap(fonts[i]))
    tw = int(max(widths))
    th = int(baselines[-1] + desc(fonts[-1]) + stroke)

    pad = 0 if shadow else int(size * float(o["pad_pct"]) / 100)
    padx = int(pad * 1.25) if pill else pad
    pin_on = pill or bool(o["show_pin"])
    icon_h = int(cap(tf) * 1.45) if pin_on else 0
    icon_w = int(icon_h * 0.72)
    icon_gap = int(size * 0.35) if pin_on else 0
    acc_w = max(2, int(short * 0.009)) if accent_bar else 0
    content_w = icon_w + icon_gap + tw
    bw = content_w + 2 * padx + acc_w
    bh = th + 2 * pad
    margin = int(short * float(o["margin_pct"]) / 100)

    if hpos is None:
        rx, ry = W - 2 * margin - bw, H - 2 * margin - bh
        x = margin + round(rx * fx) if rx > 0 else (W - bw) // 2
        y = margin + round(ry * fy) if ry > 0 else (H - bh) // 2
    else:
        x = {"left": margin, "center": (W - bw) // 2, "right": W - margin - bw}[hpos]
        y = margin if vpos == "top" else H - margin - bh

    x, y = int(x), int(y)
    fg = ImageColor.getrgb(o["fg"])[:3]
    bg = ImageColor.getrgb(o["bg"])[:3]
    accent = ImageColor.getrgb(o["accent"])[:3]
    alpha = round(255 * float(o["bg_opacity"]) / 100)
    radius = bh // 2 if pill else int(min(bw, bh) / 2 * float(o["radius_pct"]) / 100)
    base = img.convert("RGBA")

    def box_mask():
        m = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=radius, fill=255)
        return m

    # --- tło ---
    if glass:
        region = img.convert("RGB").crop((x, y, x + bw, y + bh))
        region = region.filter(ImageFilter.GaussianBlur(max(2, int(short * 0.02)))).convert("RGBA")
        region.alpha_composite(Image.new("RGBA", (bw, bh), bg + (alpha,)))
        base.paste(region, (x, y), box_mask())
        edge = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(edge).rounded_rectangle([x, y, x + bw - 1, y + bh - 1], radius=radius,
                                               outline=(255, 255, 255, 70), width=max(1, short // 600))
        base.alpha_composite(edge)
    elif not shadow and alpha > 0:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle([x, y, x + bw - 1, y + bh - 1], radius=radius,
                                                fill=bg + (alpha,))
        base.alpha_composite(layer)

    # --- pasek akcentu (po stronie wyrównania tekstu) ---
    acc_left = align != "right"
    if accent_bar:
        strip = Image.new("L", (bw, bh), 0)
        sx = 0 if acc_left else bw - acc_w
        ImageDraw.Draw(strip).rectangle([sx, 0, sx + acc_w - 1, bh], fill=255)
        strip = ImageChops.multiply(strip, box_mask())
        base.paste(Image.new("RGBA", (bw, bh), accent + (255,)), (x, y), strip)

    # --- pinezka w kolorze akcentu ---
    left = x + padx + (acc_w if acc_left else 0)
    pin = pin_pos = None
    if pin_on:
        pin = Image.new("RGBA", (icon_w + 2, icon_h + 2), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pin)
        r = icon_w / 2
        pd.ellipse([0, 0, 2 * r, 2 * r], fill=accent + (255,))
        pd.polygon([(r - r * 0.82, r * 1.45), (r + r * 0.82, r * 1.45), (r, icon_h)], fill=accent + (255,))
        hr = r * 0.42
        pd.ellipse([r - hr, r - hr, r + hr, r + hr], fill=(0, 0, 0, 0))
        if pill:   # w pastylce: na środku wysokości
            top = y + (bh - icon_h) // 2
        else:      # przy pierwszej linii: na środku wysokości wielkich liter
            top = int(y + pad + baselines[0] - cap(tf) / 2 - icon_h / 2)
        pin_pos = (int(left), top)
        left += icon_w + icon_gap

    # --- tekst ---
    def draw_text(dr, col_main, col_sub, with_stroke=True):
        for i, (ln, f) in enumerate(zip(lines, fonts)):
            w = widths[i]
            lx = left + {"left": 0, "center": (tw - w) / 2, "right": tw - w}[align if not pill else "left"]
            dr.text((lx + stroke, y + pad + baselines[i]), ln, font=f, anchor="ls",
                    fill=col_main if i == 0 else col_sub,
                    stroke_width=stroke if with_stroke else 0, stroke_fill=bg + (255,))

    if shadow and alpha > 0:
        # cień = litery pogrubione o "grubość", potem rozmyte o "rozmycie" (oba względem wielkości liter)
        spread = int(size * float(o["shadow_spread_pct"]) / 100)
        blur = size * float(o["shadow_blur_pct"]) / 100
        sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        for i, (ln, f) in enumerate(zip(lines, fonts)):
            w = widths[i]
            lx = left + {"left": 0, "center": (tw - w) / 2, "right": tw - w}[align]
            sd.text((lx + stroke, y + pad + baselines[i]), ln, font=f, anchor="ls", fill=bg + (255,),
                    stroke_width=spread, stroke_fill=bg + (255,))
        if pin is not None:  # cień pinezki: jej kształt pogrubiony o tę samą grubość
            m = pin.split()[3].point(lambda v: 255 if v else 0)
            ImageDraw.Draw(m).ellipse([icon_w / 2 - icon_w * 0.22, icon_w / 2 - icon_w * 0.22,
                                       icon_w / 2 + icon_w * 0.22, icon_w / 2 + icon_w * 0.22], fill=255)
            if spread > 0:
                m = ImageOps.expand(m, border=spread, fill=0).filter(ImageFilter.MaxFilter(2 * spread + 1))
            sh.paste(Image.new("RGBA", m.size, bg + (255,)), (pin_pos[0] - spread, pin_pos[1] - spread), m)
        if blur >= 0.5:
            sh = sh.filter(ImageFilter.GaussianBlur(blur))
        # krycie 50% = cień jak po rozmyciu, 100% = dwa razy mocniejszy (rozmyty cień nie blednie)
        k = float(o["bg_opacity"]) / 50
        r_, g_, b_, a_ = sh.split()
        sh = Image.merge("RGBA", (r_, g_, b_, a_.point(lambda v: min(255, int(v * k)))))
        base.alpha_composite(sh)
    if pin is not None:
        base.alpha_composite(pin, pin_pos)
    txt = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sub_alpha = 225 if o["sub_lighter"] else 255
    draw_text(ImageDraw.Draw(txt), fg + (255,), fg + (sub_alpha,))
    base.alpha_composite(txt)

    out = base.convert("RGB")
    return (out, (x, y, bw, bh)) if return_box else out


def clean_exif(exif_bytes):
    """Orientation=1 (obraz jest już obrócony), bez starej miniatury."""
    if not exif_bytes:
        return None
    try:
        ex = piexif.load(exif_bytes)
        ex["0th"][piexif.ImageIFD.Orientation] = 1
        ex["thumbnail"] = None
        ex["1st"] = {}
        try:
            return piexif.dump(ex)
        except Exception:
            ex["Exif"].pop(piexif.ExifIFD.MakerNote, None)
            return piexif.dump(ex)
    except Exception:
        return None


def burn_file(src, dst, o):
    st = os.stat(src)
    with Image.open(src) as im:
        exif_bytes = im.info.get("exif")
        icc = im.info.get("icc_profile")
        img = ImageOps.exif_transpose(im).convert("RGB")
    out = render_label(img, o)
    kw = {"quality": int(o["quality"]), "optimize": True}
    ex = clean_exif(exif_bytes)
    if ex:
        kw["exif"] = ex
    if icc:
        kw["icc_profile"] = icc
    tmp = dst + ".tmp"
    out.save(tmp, "JPEG", **kw)
    os.replace(tmp, dst)
    os.utime(dst, (st.st_atime, st.st_mtime))


# ---------- GPS ----------

def geocode(query):
    params = urllib.parse.urlencode(
        {"q": query, "format": "json", "limit": 6, "accept-language": LANG}
    )
    req = urllib.request.Request(
        "https://nominatim.openstreetmap.org/search?" + params,
        headers={"User-Agent": f"{APP_NAME}/{APP_VERSION} (+{GITHUB_URL})"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [(d["display_name"], float(d["lat"]), float(d["lon"])) for d in data]


def to_dms(value):
    total = round(abs(value) * 3600 * 10000)
    deg, rest = divmod(total, 3600 * 10000)
    m, s = divmod(rest, 60 * 10000)
    return ((deg, 1), (m, 1), (s, 10000))


def from_dms(dms, ref):
    deg, m, s = (a / b for a, b in dms)
    val = deg + m / 60 + s / 3600
    return -val if ref in (b"S", b"W", "S", "W") else val


def read_gps(path):
    gps = piexif.load(path).get("GPS") or {}
    try:
        return (
            from_dms(gps[piexif.GPSIFD.GPSLatitude], gps[piexif.GPSIFD.GPSLatitudeRef]),
            from_dms(gps[piexif.GPSIFD.GPSLongitude], gps[piexif.GPSIFD.GPSLongitudeRef]),
        )
    except KeyError:
        return None


def write_gps(path, lat, lon, keep_mtime=True, backup_dir=None):
    st = os.stat(path)
    if backup_dir:
        os.makedirs(backup_dir, exist_ok=True)
        dst = os.path.join(backup_dir, os.path.basename(path))
        if not os.path.exists(dst):
            shutil.copy2(path, dst)
    exif = piexif.load(path)
    exif["GPS"] = {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S",
        piexif.GPSIFD.GPSLatitude: to_dms(lat),
        piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W",
        piexif.GPSIFD.GPSLongitude: to_dms(lon),
    }
    try:
        exif_bytes = piexif.dump(exif)
    except Exception:
        exif["Exif"].pop(piexif.ExifIFD.MakerNote, None)
        exif.pop("thumbnail", None)
        exif["1st"] = {}
        exif_bytes = piexif.dump(exif)
    piexif.insert(exif_bytes, path)
    if keep_mtime:
        os.utime(path, (st.st_atime, st.st_mtime))


# ---------- GUI ----------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        global LANG
        LANG = self.load_lang()
        self._i18n = []          # (widżet, opcja, tekst PL) - odświeżane przy zmianie języka
        self._i18n_tabs = []     # (notebook, karta, tekst PL)
        self._mapped = []        # MappedCombo do odświeżenia
        self.title(tr("{app} v{ver}  –  napis i lokalizacja na zdjęciach", app=APP_NAME, ver=APP_VERSION))
        try:
            self.iconbitmap(default=resource_path("photostamp.ico"))  # default= także dla okienek dialogowych
        except tk.TclError:
            pass
        self.geometry("1200x880")
        self.minsize(1000, 700)
        self.files = []
        self.file_opts = {}      # ścieżka -> ustawienia napisu tego zdjęcia
        self._loading = False    # True podczas wczytywania ustawień do panelu
        self.cur = None          # indeks bieżącego (edytowanego) zdjęcia
        self.results = []
        self._preview_cache = {}
        self._preview_job = None
        self.cfg = dict(DEFAULTS)
        self.cfg.update(self.load_settings())

        pad = {"padx": 8, "pady": 4}

        # --- lista plików (wspólna) ---
        f_files = self.L(ttk.LabelFrame(self), "Zdjęcia (JPEG)")
        f_files.pack(fill="x", **pad)
        btns = ttk.Frame(f_files)
        btns.pack(fill="x")
        self.L(ttk.Button(btns, command=self.add_files), "Dodaj pliki…").pack(side="left", **pad)
        self.L(ttk.Button(btns, command=self.add_folder), "Dodaj folder…").pack(side="left", **pad)
        self.L(ttk.Button(btns, command=self.remove_selected), "Usuń zaznaczone").pack(side="left", **pad)
        self.L(ttk.Button(btns, command=self.clear_files), "Wyczyść").pack(side="left", **pad)
        try:
            img = Image.open(resource_path("created.png"))
            img.thumbnail((200, 44))
            self.badge_img = ImageTk.PhotoImage(img)  # trzymamy referencję, inaczej obrazek zniknie
            badge = tk.Label(btns, image=self.badge_img, cursor="hand2", bd=0)
            badge.pack(side="right", padx=(4, 8))
            badge.bind("<Button-1>", lambda _e: webbrowser.open(FACEBOOK_URL))
        except (OSError, tk.TclError):
            pass
        # przełącznik języka EN / PL (zapamiętywany)
        lf_lang = ttk.Frame(btns)
        lf_lang.pack(side="right", padx=(4, 8))
        self.lang_var = tk.StringVar(value=LANG)
        for code in ("pl", "en"):
            ttk.Radiobutton(lf_lang, text=code.upper(), value=code, variable=self.lang_var,
                            style="Toolbutton", command=self.switch_language).pack(side="right")
        self.L(ttk.Label(lf_lang), "Język:").pack(side="right", padx=(0, 4))
        self.count_lbl = ttk.Label(btns, text=tr("{n} plików", n=0))
        self.count_lbl.pack(side="right", **pad)
        lf = ttk.Frame(f_files)
        lf.pack(fill="x", padx=8, pady=(0, 8))
        # exportselection=False: inaczej klik w pole tekstowe kasuje zaznaczenie na liście
        self.listbox = tk.Listbox(lf, selectmode="browse", height=7, exportselection=False,
                                  activestyle="none")
        sb = ttk.Scrollbar(lf, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.L(ttk.Label(f_files, foreground="gray"),
               "Każde zdjęcie ma własny napis – to, co wpiszesz, zostaje tylko na wybranym zdjęciu. "
               "Nowe zdjęcie startuje z pustym tekstem i wyglądem/pozycją z poprzedniego."
               ).pack(anchor="w", padx=8, pady=(0, 6))

        self.status = tk.StringVar(value=tr("Dodaj zdjęcia, żeby zacząć."))
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w").pack(fill="x", side="bottom")

        nb = self.nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, **pad)
        self.build_text_tab(nb)
        self.build_gps_tab(nb)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(400, self.offer_restore)

    # ===== zakładka: napis =====
    def build_text_tab(self, nb):
        tab = ttk.Frame(nb)
        self.add_tab(nb, tab, "Napis na zdjęciu")
        # lewy panel przewijany kółkiem myszy - mieści się na każdym ekranie
        holder = ttk.Frame(tab)
        holder.pack(side="left", fill="y", padx=(8, 0), pady=8)
        canvas = tk.Canvas(holder, highlightthickness=0, bd=0, width=470)
        vsb = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="y")
        left = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=left, anchor="nw")
        left.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"),
                                                            width=left.winfo_reqwidth()))

        def on_wheel(e):
            if canvas.winfo_height() < left.winfo_reqheight():
                canvas.yview_scroll(int(-e.delta / 120) or (-1 if e.delta > 0 else 1), "units")
        holder.bind("<Enter>", lambda e: self.bind_all("<MouseWheel>", on_wheel))
        holder.bind("<Leave>", lambda e: self.unbind_all("<MouseWheel>"))
        self._left_canvas = canvas

        right = self.L(ttk.LabelFrame(tab), "Podgląd – przeciągnij napis myszką; rozmiar: kółko myszy albo biały kwadracik w rogu")
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        navf = ttk.Frame(right)
        navf.pack(side="bottom", fill="x", pady=4)
        self.L(ttk.Button(navf, command=lambda: self.step(-1)), "◀ Poprzednie").pack(side="left", padx=8)
        self.L(ttk.Button(navf, command=lambda: self.step(1)), "Następne ▶").pack(side="right", padx=8)
        self.nav_lbl = ttk.Label(navf, anchor="center")
        self.nav_lbl.pack(side="left", fill="x", expand=True)
        # stała ramka wyznacza miejsce na podgląd; etykieta z obrazkiem leży na środku
        # i nie wpływa na rozmiar ramki (inaczej podgląd potrafił zniknąć / skurczyć się)
        self.preview_area = tk.Frame(right, bg="#2b2b2b")
        self.preview_area.pack(fill="both", expand=True)
        self.preview_lbl = tk.Label(self.preview_area, bg="#2b2b2b", fg="#dddddd", cursor="fleur",
                                    bd=0, highlightthickness=0, padx=0, pady=0,
                                    text=tr("Dodaj zdjęcia, żeby zobaczyć podgląd"))
        self.preview_lbl.place(relx=0.5, rely=0.5, anchor="center")
        self.preview_area.bind("<Configure>", lambda e: self.schedule_preview())
        self._pv = None
        self._grab = None
        self._resize = None
        self.preview_lbl.bind("<MouseWheel>", self.on_preview_wheel)                     # Windows / macOS
        self.preview_lbl.bind("<Button-4>", lambda e: (setattr(e, "delta", 120), self.on_preview_wheel(e)))
        self.preview_lbl.bind("<Button-5>", lambda e: (setattr(e, "delta", -120), self.on_preview_wheel(e)))
        self.preview_lbl.bind("<Motion>", self.on_preview_motion)
        self.preview_lbl.bind("<ButtonPress-1>", self.drag_start)
        self.preview_lbl.bind("<B1-Motion>", self.drag_move)
        self.preview_lbl.bind("<ButtonRelease-1>", self.drag_end)

        c = self.cfg
        self.v = {
            "text": tk.StringVar(value=""),
            "style": tk.StringVar(value=c["style"] if c["style"] in STYLES else STYLES[0]),
            "accent": tk.StringVar(value=c["accent"]),
            "sub_size_pct": tk.IntVar(value=c["sub_size_pct"]),
            "sub_lighter": tk.BooleanVar(value=c["sub_lighter"]),
            "sub_font": tk.StringVar(value=c["sub_font"]),
            "shadow_blur_pct": tk.IntVar(value=c["shadow_blur_pct"]),
            "shadow_spread_pct": tk.IntVar(value=c["shadow_spread_pct"]),
            "show_pin": tk.BooleanVar(value=c["show_pin"]),
            "font": tk.StringVar(value=c["font"] if c["font"] in FONTS else next(iter(FONTS), tr("Domyślna"))),
            "size_pct": tk.DoubleVar(value=c["size_pct"]),
            "line_spacing_pct": tk.IntVar(value=c["line_spacing_pct"]),
            "position": tk.StringVar(value=c["position"]),
            "bg_opacity": tk.IntVar(value=c["bg_opacity"]),
            "radius_pct": tk.IntVar(value=c["radius_pct"]),
            "pad_pct": tk.IntVar(value=c["pad_pct"]),
            "margin_pct": tk.DoubleVar(value=c["margin_pct"]),
            "stroke": tk.BooleanVar(value=c["stroke"]),
            "quality": tk.IntVar(value=c["quality"]),
            "overwrite": tk.BooleanVar(value=c["overwrite"]),
        }
        self.font_file = c.get("font_file", "")
        self.fg, self.bg = c["fg"], c["bg"]
        self.pos_x, self.pos_y = float(c["pos_x"]), float(c["pos_y"])

        r = 0

        def row(label, widget):
            nonlocal r
            self.L(ttk.Label(left), label).grid(row=r, column=0, sticky="w", pady=4)
            widget.grid(row=r, column=1, sticky="we", pady=4, padx=(8, 0))
            r += 1

        # --- szablony ---
        self.templates = self.load_templates()
        tf = self.L(ttk.LabelFrame(left), "Szablony")
        tf.grid(row=r, column=0, columnspan=2, sticky="we", pady=(0, 8)); r += 1
        self.tpl_var = tk.StringVar()
        self.tpl_combo = ttk.Combobox(tf, textvariable=self.tpl_var, state="readonly", width=24)
        self.tpl_combo.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.tpl_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_template(self.tpl_var.get()))
        self.L(ttk.Button(tf, command=self.save_template), "Zapisz jako…").pack(side="left", padx=2)
        self.L(ttk.Button(tf, width=8, command=self.delete_template), "Usuń").pack(side="left", padx=(2, 4))
        self.refresh_template_list()

        row("Tekst:", ttk.Entry(left, textvariable=self.v["text"], width=30))
        self.L(ttk.Label(left, foreground="gray"), "(\\n = nowa linia)").grid(row=r, column=1, sticky="w"); r += 1

        self.style_combo = self.mapped(left, self.v["style"], lambda: STYLES)
        self.style_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_style_preset(), add="+")
        row("Styl:", self.style_combo)
        row("", self.L(ttk.Checkbutton(left, variable=self.v["show_pin"]),
                       "Pinezka przed napisem (w kolorze akcentu)"))

        acf = ttk.Frame(left)
        self.accent_name = tk.StringVar()
        self.accent_combo = ttk.Combobox(acf, textvariable=self.accent_name, state="readonly", width=26)
        self.accent_combo.pack(side="left", fill="x", expand=True)
        self.accent_combo.bind("<<ComboboxSelected>>", lambda e: self.pick_accent())
        self.accent_swatch = tk.Label(acf, width=3, relief="solid", bd=1)
        self.accent_swatch.pack(side="left", padx=(6, 0))
        row("Kolor akcentu:", acf)
        self.L(ttk.Label(left, foreground="gray"), "(pasek przy stylu z akcentem, pinezka w pastylce)").grid(
            row=r, column=1, sticky="w"); r += 1
        self.update_accent_widgets()

        ff = ttk.Frame(left)
        self.font_combo = ttk.Combobox(ff, textvariable=self.v["font"], values=list(FONTS) or [tr("Domyślna")],
                                       state="readonly", width=20)
        self.font_combo.pack(side="left")
        self.font_combo.bind("<<ComboboxSelected>>", lambda e: self.clear_font_file())
        self.L(ttk.Button(ff, width=8, command=self.pick_font_file), "Plik…").pack(side="left", padx=4)
        row("Czcionka:", ff)
        self.font_file_lbl = ttk.Label(left, text=os.path.basename(self.font_file), foreground="gray")
        self.font_file_lbl.grid(row=r, column=1, sticky="w"); r += 1

        row("Rozmiar (% krótszego boku):",
            ttk.Spinbox(left, from_=1, to=30, increment=0.5, textvariable=self.v["size_pct"], width=8))
        sf = ttk.Frame(left)
        ttk.Scale(sf, from_=-40, to=150, variable=self.v["line_spacing_pct"],
                  command=lambda _: (self.spacing_lbl.config(text=f"{self.v['line_spacing_pct'].get()}%"),
                                     self.schedule_preview())).pack(side="left", fill="x", expand=True)
        self.spacing_lbl = ttk.Label(sf, text=f"{c['line_spacing_pct']}%", width=5)
        self.spacing_lbl.pack(side="left", padx=4)
        row("Odstęp między liniami:", sf)
        ssf = ttk.Frame(left)
        ttk.Scale(ssf, from_=40, to=100, variable=self.v["sub_size_pct"],
                  command=lambda _: self.sub_lbl.config(text=f"{self.v['sub_size_pct'].get()}%")
                  ).pack(side="left", fill="x", expand=True)
        self.sub_lbl = ttk.Label(ssf, text=f"{c['sub_size_pct']}%", width=5)
        self.sub_lbl.pack(side="left", padx=4)
        row("Druga i dalsze linie:", ssf)
        row("Czcionka dalszych linii:", self.mapped(left, self.v["sub_font"], lambda: [SUB_AUTO] + list(FONTS)))
        row("", self.L(ttk.Checkbutton(left, variable=self.v["sub_lighter"]),
                       "Automatycznie = cieńsza odmiana 1. linii"))
        row("Pozycja:", self.mapped(left, self.v["position"], lambda: list(POSITIONS) + [CUSTOM]))
        self.L(ttk.Label(left, foreground="gray"), "(albo złap napis myszką na podglądzie)").grid(
            row=r, column=1, sticky="w"); r += 1

        cf = ttk.Frame(left)
        self.fg_btn = self.L(tk.Button(cf, width=8, command=lambda: self.pick_color("fg")), "Tekst")
        self.fg_btn.pack(side="left")
        self.bg_btn = self.L(tk.Button(cf, width=12, command=lambda: self.pick_color("bg")), "Tło / cień")
        self.bg_btn.pack(side="left", padx=4)
        row("Kolory:", cf)
        self.update_color_buttons()

        row("Krycie tła / cienia (%):", ttk.Scale(left, from_=0, to=100, variable=self.v["bg_opacity"],
                                         command=lambda _: self.schedule_preview()))
        row("Rozmycie cienia:", ttk.Scale(left, from_=0, to=60, variable=self.v["shadow_blur_pct"]))
        row("Grubość cienia:", ttk.Scale(left, from_=0, to=30, variable=self.v["shadow_spread_pct"]))
        self.L(ttk.Label(left, foreground="gray"),
               "(suwaki cienia działają przy stylu „Sam tekst z cieniem”)").grid(row=r, column=1, sticky="w"); r += 1
        row("Zaokrąglenie rogów:", ttk.Scale(left, from_=0, to=100, variable=self.v["radius_pct"],
                                             command=lambda _: self.schedule_preview()))
        row("Odstęp tekstu od krawędzi tła:", ttk.Scale(left, from_=0, to=150, variable=self.v["pad_pct"],
                                                         command=lambda _: self.schedule_preview()))
        row("Margines od brzegu zdjęcia (%):",
            ttk.Spinbox(left, from_=0, to=20, increment=0.5, textvariable=self.v["margin_pct"], width=8))
        row("", self.L(ttk.Checkbutton(left, variable=self.v["stroke"]), "Obrys tekstu (gdy tło przezroczyste)"))
        row("Jakość JPEG:", ttk.Spinbox(left, from_=70, to=100, textvariable=self.v["quality"], width=8))

        left.columnconfigure(1, weight=1)

        # kółko myszy nad listami rozwijanymi przewija panel zamiast zmieniać wybór
        def no_wheel(w):
            for ch in w.winfo_children():
                if ch.winfo_class() in ("TCombobox", "TSpinbox"):
                    ch.bind("<MouseWheel>", lambda e: (on_wheel(e), "break")[1])
                no_wheel(ch)
        no_wheel(left)

        # stały pasek akcji na dole okna - zawsze widoczny
        bar = ttk.Frame(self)
        bar.pack(side="bottom", fill="x", padx=8, pady=(0, 6), before=self.nb)
        self.L(ttk.Button(bar, command=self.apply_look_to_all),
               "Ten WYGLĄD na wszystkie (napisy i pozycje zostają)").pack(side="left")
        self.L(ttk.Button(bar, command=self.apply_to_all), "Napis + wygląd na wszystkie").pack(side="left", padx=6)
        self.L(ttk.Radiobutton(bar, variable=self.v["overwrite"], value=False),
               "Kopie do „z_napisem”").pack(side="left", padx=(16, 4))
        self.L(ttk.Radiobutton(bar, variable=self.v["overwrite"], value=True),
               "Nadpisz oryginały").pack(side="left", padx=4)
        self.burn_btn = self.L(ttk.Button(bar, command=self.burn_all), "  Dodaj napisy do zdjęć  ")
        self.burn_btn.pack(side="right", ipady=4)

        for key, var in self.v.items():
            if key != "overwrite":
                var.trace_add("write", lambda *_: self.changed())

    def opts(self):
        def num(var, default):
            try:
                return float(var.get())
            except (tk.TclError, ValueError):
                return default
        return {
            "text": self.v["text"].get(),
            "style": self.v["style"].get(),
            "accent": self.v["accent"].get(),
            "sub_size_pct": int(num(self.v["sub_size_pct"], 70)),
            "sub_lighter": bool(self.v["sub_lighter"].get()),
            "sub_font": self.v["sub_font"].get(),
            "shadow_blur_pct": int(num(self.v["shadow_blur_pct"], 18)),
            "shadow_spread_pct": int(num(self.v["shadow_spread_pct"], 6)),
            "show_pin": bool(self.v["show_pin"].get()),
            "font": self.v["font"].get(),
            "font_file": self.font_file,
            "size_pct": num(self.v["size_pct"], 4),
            "line_spacing_pct": int(num(self.v["line_spacing_pct"], 20)),
            "position": self.v["position"].get(),
            "pos_x": round(self.pos_x, 4),
            "pos_y": round(self.pos_y, 4),
            "fg": self.fg,
            "bg": self.bg,
            "bg_opacity": int(num(self.v["bg_opacity"], 100)),
            "radius_pct": int(num(self.v["radius_pct"], 25)),
            "pad_pct": int(num(self.v["pad_pct"], 45)),
            "margin_pct": num(self.v["margin_pct"], 3),
            "stroke": bool(self.v["stroke"].get()),
            "quality": int(num(self.v["quality"], 95)),
            "overwrite": bool(self.v["overwrite"].get()),
        }

    # ----- szablony -----
    def load_templates(self):
        try:
            with open(TEMPLATES_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def write_templates(self):
        try:
            with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2, sort_keys=True)
        except Exception as ex:
            messagebox.showerror(tr("Błąd"), tr("Nie udało się zapisać szablonów:\n{ex}", ex=ex))

    def refresh_template_list(self, select=None):
        names = sorted(self.templates, key=str.lower)
        self.tpl_combo.config(values=names)
        self.tpl_var.set(select if select in self.templates else "")

    def save_template(self):
        default = " ".join(self.v["text"].get().replace("\\n", " ").split())
        name = simpledialog.askstring(tr("Zapisz szablon"), tr("Nazwa szablonu:"), initialvalue=default, parent=self)
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.templates and not messagebox.askyesno(
            tr("Szablon istnieje"), tr("Szablon „{name}” już istnieje. Nadpisać?", name=name)
        ):
            return
        self.templates[name] = {k: v for k, v in self.opts().items() if k not in NOT_IN_TEMPLATE}
        self.write_templates()
        self.refresh_template_list(select=name)
        self.status.set(tr("Zapisano szablon „{name}”.", name=name))

    def delete_template(self):
        name = self.tpl_var.get()
        if not name:
            messagebox.showinfo(tr("Usuń szablon"), tr("Najpierw wybierz szablon z listy."))
            return
        if messagebox.askyesno(tr("Usuń szablon"), tr("Usunąć szablon „{name}”?", name=name)):
            self.templates.pop(name, None)
            self.write_templates()
            self.refresh_template_list()
            self.status.set(tr("Usunięto szablon „{name}”.", name=name))

    def apply_template(self, name):
        t = self.templates.get(name)
        if not t:
            return
        if self.cur is None and self.files:
            self.select_only(0)
        self.set_panel(t)
        self.changed()  # zapis do bieżącego zdjęcia
        if self.cur is not None:
            self.status.set(tr("Szablon „{name}” ustawiony na zdjęciu {photo}.", name=name,
                               photo=os.path.basename(self.files[self.cur])))

    def set_panel(self, t):
        """Wpisuje ustawienia do panelu BEZ zapisywania ich do zdjęć."""
        o = dict(DEFAULTS)
        o.update(t)
        self._loading = True
        try:
            for key, var in self.v.items():
                if key in o and key not in NOT_IN_TEMPLATE:
                    var.set(o[key])
            if o["font"] not in FONTS and FONTS:
                self.v["font"].set(next(iter(FONTS)))
            self.font_file = o.get("font_file", "")
            if self.font_file and not os.path.isfile(self.font_file):
                self.font_file = ""
            self.font_file_lbl.config(text=os.path.basename(self.font_file))
            self.fg, self.bg = o["fg"], o["bg"]
            self.pos_x, self.pos_y = float(o["pos_x"]), float(o["pos_y"])
            if o["style"] not in STYLES:
                self.v["style"].set(STYLES[0])
            self.update_color_buttons()
            self.update_accent_widgets()
            self.spacing_lbl.config(text=f"{int(float(o['line_spacing_pct']))}%")
            self.sub_lbl.config(text=f"{int(float(o['sub_size_pct']))}%")
        finally:
            self._loading = False
        self.schedule_preview()

    # ----- ustawienia per zdjęcie -----
    # Model: self.cur = indeks bieżącego zdjęcia. Panel zawsze pokazuje JEGO ustawienia,
    # a każda zmiana w panelu zapisuje się tylko do niego (self.file_opts[ścieżka]).
    # file_opts[p] is None = zdjęcie jeszcze nieruszone.

    def panel_opts(self):
        return {k: v for k, v in self.opts().items() if k not in NOT_IN_TEMPLATE}

    def file_label(self, path):
        o = self.file_opts.get(path) or {}
        txt = " ".join(str(o.get("text", "")).replace("\\n", " / ").split())
        return f"{os.path.basename(path)}    —    {txt if txt else tr('(bez napisu)')}"

    def refresh_rows(self, indices):
        top = self.listbox.yview()[0]
        for i in indices:
            self.listbox.delete(i)
            self.listbox.insert(i, self.file_label(self.files[i]))
        if self.cur is not None:
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(self.cur)
        self.listbox.yview_moveto(top)

    def changed(self):
        """Każda zmiana w panelu -> zapis TYLKO do bieżącego zdjęcia."""
        if self._loading:
            return
        if self.cur is not None and self.cur < len(self.files):
            p = self.files[self.cur]
            old_text = (self.file_opts.get(p) or {}).get("text", "")
            self.file_opts[p] = self.panel_opts()
            if self.file_opts[p]["text"] != old_text:
                self.refresh_rows([self.cur])
            self.schedule_autosave()
        self.schedule_preview()

    # ----- autozapis pracy (napisy i pozycje każdego zdjęcia) -----
    def schedule_autosave(self):
        if getattr(self, "_autosave_job", None):
            self.after_cancel(self._autosave_job)
        self._autosave_job = self.after(700, self.autosave)

    def autosave(self):
        self._autosave_job = None
        data = {"version": 1, "files": self.files,
                "opts": {p: o for p, o in self.file_opts.items() if o}}
        try:
            tmp = WORK_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, WORK_FILE)
        except Exception as ex:
            self.status.set(tr("Nie udało się zapisać pracy: {ex}", ex=ex))

    def on_close(self):
        if getattr(self, "_autosave_job", None):
            self.after_cancel(self._autosave_job)
        self.autosave()
        self.destroy()

    def offer_restore(self):
        """Przy starcie: jeśli jest zapisana praca, zaproponuj jej wczytanie."""
        try:
            with open(WORK_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        if isinstance(data, dict) and "opts" in data:
            files, opts = data.get("files") or list(data["opts"]), data["opts"]
        elif isinstance(data, dict):  # zrzut ze starej wersji: {ścieżka: ustawienia}
            files, opts = sorted(data), data
        else:
            return
        files = [p for p in files if isinstance(p, str)]
        if not files:
            return
        exist = [p for p in files if os.path.isfile(p)]
        with_text = sum(1 for p in exist if (opts.get(p) or {}).get("text", "").strip())
        msg = tr("Wczytać ostatnią pracę?\n\n{n} zdjęć, w tym {t} z wpisanym napisem.", n=len(exist), t=with_text)
        if len(exist) < len(files):
            msg += tr("\n({n} plików już nie ma na dysku – zostaną pominięte.)", n=len(files) - len(exist))
        if not messagebox.askyesno(tr("Ostatnia praca"), msg):
            return
        self._add(exist)
        for p in exist:
            if isinstance(opts.get(p), dict):
                self.file_opts[p] = {**{k: v for k, v in DEFAULTS.items() if k not in NOT_IN_TEMPLATE},
                                     **opts[p]}
        self.refresh_rows(range(len(self.files)))
        self.cur = None
        if self.files:
            self.select_only(0)
        self.status.set(tr("Wczytano pracę: {n} zdjęć, {t} z napisem.", n=len(exist), t=with_text))

    def select_only(self, i):
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(i)
        self.listbox.see(i)
        self.on_select()

    def step(self, d):
        if not self.files:
            return
        i = (self.cur if self.cur is not None else -1) + d
        self.select_only(max(0, min(len(self.files) - 1, i)))

    def apply_to_all(self):
        if not self.files:
            return
        if not messagebox.askyesno(
            tr("Wszystkie zdjęcia"),
            tr("Ustawić obecny napis i wygląd na wszystkich {n} zdjęciach?\n"
               "Napisy wpisane wcześniej w innych zdjęciach zostaną zastąpione.", n=len(self.files))):
            return
        o = self.panel_opts()
        for p in self.files:
            self.file_opts[p] = dict(o)
        self.refresh_rows(range(len(self.files)))
        self.schedule_autosave()
        self.status.set(tr("Ustawiono na wszystkich {n} zdjęciach.", n=len(self.files)))

    # ----- styl i akcent -----
    def apply_style_preset(self):
        """Wybranie stylu z listy ustawia dopasowane tło (krycie, kolor, zaokrąglenie)."""
        p = STYLE_PRESETS.get(self.v["style"].get(), {})
        self._loading = True
        try:
            for k, val in p.items():
                if k == "bg":
                    self.bg = val
                elif k in self.v:
                    self.v[k].set(val)
            self.update_color_buttons()
        finally:
            self._loading = False
        self.changed()

    def update_accent_widgets(self):
        col = self.v["accent"].get()
        try:
            ImageColor.getrgb(col)
        except ValueError:
            col = DEFAULTS["accent"]
        self.accent_combo.config(values=[tr(n) for n in ACCENTS] + [tr(ACCENT_CUSTOM)])
        name = next((tr(n) for n, c in ACCENTS.items() if c.lower() == col.lower()), tr("Własny ({col})", col=col))
        self.accent_name.set(name)
        self.accent_swatch.config(bg=col)

    def pick_accent(self):
        i, names = self.accent_combo.current(), list(ACCENTS)
        if i == len(names):  # ostatnia pozycja: własny kolor
            res = colorchooser.askcolor(color=self.v["accent"].get(), title=tr("Kolor akcentu"))
            if res and res[1]:
                self.v["accent"].set(res[1])
        elif 0 <= i < len(names):
            self.v["accent"].set(ACCENTS[names[i]])
        self.update_accent_widgets()

    def apply_look_to_all(self):
        if not self.files:
            return
        n = sum(1 for p in self.files if self.file_opts.get(p))
        if not messagebox.askyesno(
            tr("Wygląd na wszystkie"),
            tr("Ustawić obecny wygląd (styl, czcionkę, kolory, rozmiar) na wszystkich {n} zdjęciach?\n\n"
               "Napisy i pozycje każdego zdjęcia zostają bez zmian.", n=len(self.files))):
            return
        look = {k: v for k, v in self.panel_opts().items() if k not in ("text", "position", "pos_x", "pos_y")}
        for p in self.files:
            o = self.file_opts.get(p)
            if o:
                o.update(look)
        self.schedule_autosave()
        self.status.set(tr("Wygląd ustawiony na {n} zdjęciach z napisem – napisy i pozycje bez zmian.", n=n))

    def pick_color(self, which):
        cur = self.fg if which == "fg" else self.bg
        res = colorchooser.askcolor(color=cur, title=tr("Wybierz kolor"))
        if res and res[1]:
            setattr(self, which, res[1])
            self.update_color_buttons()
            self.changed()

    def update_color_buttons(self):
        for btn, col in ((self.fg_btn, self.fg), (self.bg_btn, self.bg)):
            r, g, b = ImageColor.getrgb(col)
            txt = "#000000" if (r * 299 + g * 587 + b * 114) / 1000 > 128 else "#ffffff"
            btn.config(bg=col, fg=txt, activebackground=col)

    def pick_font_file(self):
        p = filedialog.askopenfilename(filetypes=[("Czcionki", "*.ttf *.otf *.ttc")])
        if p:
            self.font_file = p
            self.font_file_lbl.config(text=os.path.basename(p))
            self.changed()

    def clear_font_file(self):
        self.font_file = ""
        self.font_file_lbl.config(text="")
        self.changed()

    def schedule_preview(self):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(150, self.update_preview)

    def preview_path(self):
        if self.cur is not None and self.cur < len(self.files):
            self.nav_lbl.config(text=f"{self.cur + 1} / {len(self.files)}")
            return self.files[self.cur]
        self.nav_lbl.config(text="")
        return None

    def update_preview(self):
        self._preview_job = None
        path = self.preview_path()
        if not path:
            self._pv = None
            self._tkimg = None
            self.preview_lbl.config(image="", text=tr("Dodaj zdjęcia, żeby zobaczyć podgląd"))
            return
        try:
            if self._preview_cache.get("path") != path:
                with Image.open(path) as im:
                    img = ImageOps.exif_transpose(im).convert("RGB")
                    img.thumbnail((1600, 1600))
                self._preview_cache = {"path": path, "base": img}
            # renderujemy od razu w rozmiarze podglądu - szybko, więc przeciąganie jest płynne
            aw, ah = self.preview_area.winfo_width(), self.preview_area.winfo_height()
            if aw < 50 or ah < 50:  # okno jeszcze się nie ułożyło - spróbuj za chwilę
                self._preview_job = self.after(100, self.update_preview)
                return
            w, h = aw - 8, ah - 8
            if self._preview_cache.get("size") != (w, h):
                img = self._preview_cache["base"].copy()
                img.thumbnail((w, h))
                self._preview_cache.update(size=(w, h), scaled=img)
            # podgląd = dokładnie to, co jest w panelu (panel zawsze pokazuje bieżące zdjęcie)
            o = dict(DEFAULTS)
            o.update(self.opts())
            out, box = render_label(self._preview_cache["scaled"], o, return_box=True)
            self._pv = (out.size, box)
            if box:  # uchwyt do zmiany rozmiaru - tylko na podglądzie, nie trafia do pliku
                hx, hy, k = box[0] + box[2], box[1] + box[3], self.HANDLE
                ImageDraw.Draw(out).rectangle([hx - k, hy - k, hx + k, hy + k], fill=(255, 255, 255),
                                              outline=(30, 30, 30), width=2)
            self._tkimg = ImageTk.PhotoImage(out)
            self.preview_lbl.config(image=self._tkimg, text="")
        except Exception as ex:
            self._pv = None
            self.preview_lbl.config(image="", text=tr("Nie da się pokazać podglądu:\n{ex}", ex=ex))

    # ----- przeciąganie napisu myszką -----
    def _img_offset(self, size):
        # współrzędne zdarzeń są względem etykiety, a ta ma dokładnie rozmiar obrazka
        iw, ih = size
        return ((self.preview_lbl.winfo_width() - iw) // 2,
                (self.preview_lbl.winfo_height() - ih) // 2)

    # ----- zmiana rozmiaru myszką: uchwyt w prawym dolnym rogu + kółko myszy -----
    HANDLE = 7  # połowa boku kwadracika uchwytu (px na podglądzie)

    def _on_handle(self, px, py):
        if not self._pv or not self._pv[1]:
            return False
        bx, by, bw, bh = self._pv[1]
        return abs(px - (bx + bw)) <= self.HANDLE + 4 and abs(py - (by + bh)) <= self.HANDLE + 4

    def _set_size(self, val):
        val = round(min(30.0, max(1.0, val)), 1)
        self.v["size_pct"].set(val)  # trace -> changed() -> zapis do zdjęcia
        if self._preview_job:
            self.after_cancel(self._preview_job)
            self._preview_job = None
        self.update_preview()

    def _cur_size(self):
        try:
            return float(self.v["size_pct"].get())
        except (tk.TclError, ValueError):
            return 4.0

    def on_preview_wheel(self, e):
        if self.cur is None:
            return
        step = 1.07 if e.delta > 0 else 1 / 1.07
        self._set_size(self._cur_size() * step)
        self.status.set(tr("Rozmiar napisu: {v}%", v=f"{self._cur_size():.1f}"))

    def on_preview_motion(self, e):
        if self._pv and self._resize is None and self._grab is None:
            ox, oy = self._img_offset(self._pv[0])
            want = "bottom_right_corner" if self._on_handle(e.x - ox, e.y - oy) else "fleur"
            if self.preview_lbl.cget("cursor") != want:
                self.preview_lbl.config(cursor=want)

    def drag_start(self, e):
        if not self._pv or not self._pv[1]:
            return
        size, (bx, by, bw, bh) = self._pv
        ox, oy = self._img_offset(size)
        px, py = e.x - ox, e.y - oy
        if self._on_handle(px, py):
            # ciągnięcie za uchwyt = zmiana rozmiaru względem lewego górnego rogu napisu
            d0 = max(8.0, ((px - bx) ** 2 + (py - by) ** 2) ** 0.5)
            self._resize = (self._cur_size(), bx, by, d0)
            return
        if bx <= px <= bx + bw and by <= py <= by + bh:
            self._grab = (px - bx, py - by)  # złapany napis - trzymamy za to samo miejsce
        else:
            self._grab = (bw / 2, bh / 2)    # klik obok - napis skacze środkiem pod kursor
        self.drag_move(e)

    def drag_move(self, e):
        if self._resize is not None and self._pv:
            s0, bx, by, d0 = self._resize
            ox, oy = self._img_offset(self._pv[0])
            px, py = e.x - ox, e.y - oy
            d = max(4.0, ((px - bx) ** 2 + (py - by) ** 2) ** 0.5)
            self._set_size(s0 * d / d0)
            self.status.set(tr("Rozmiar napisu: {v}%", v=f"{self._cur_size():.1f}"))
            return
        if self._grab is None or not self._pv or not self._pv[1]:
            return
        (iw, ih), (_, _, bw, bh) = self._pv
        ox, oy = self._img_offset((iw, ih))
        nx = e.x - ox - self._grab[0]
        ny = e.y - oy - self._grab[1]
        try:
            margin = int(min(iw, ih) * float(self.v["margin_pct"].get()) / 100)
        except (tk.TclError, ValueError):
            margin = 0
        rx, ry = iw - 2 * margin - bw, ih - 2 * margin - bh

        def frac(v, r):
            f = min(1.0, max(0.0, (v - margin) / r)) if r > 0 else 0.5
            for s in (0.0, 0.5, 1.0):
                if abs(f - s) < SNAP:
                    return s
            return f

        self.pos_x, self.pos_y = frac(nx, rx), frac(ny, ry)
        if self.v["position"].get() != CUSTOM:
            self.v["position"].set(CUSTOM)  # trace -> changed()
        else:
            self.changed()
        if self._preview_job:
            self.after_cancel(self._preview_job)
            self._preview_job = None
        self.update_preview()

    def drag_end(self, _e):
        self._grab = None
        self._resize = None

    def burn_all(self):
        if not self.files:
            messagebox.showwarning(tr("Brak zdjęć"), tr("Dodaj najpierw zdjęcia."))
            return
        panel = self.opts()
        overwrite = panel["overwrite"]
        jobs = []
        for p in self.files:
            o = dict(DEFAULTS)
            o.update(self.file_opts.get(p) or {"text": ""})
            if o["text"].replace("\\n", "").strip():
                jobs.append((p, o))
        skipped = len(self.files) - len(jobs)
        if not jobs:
            messagebox.showwarning(tr("Brak tekstu"), tr("Żadne zdjęcie nie ma wpisanego napisu."))
            return
        msg = tr("Dodać napisy do {n} zdjęć?", n=len(jobs))
        if skipped:
            msg += tr("\n{n} zdjęć bez napisu zostanie pominiętych.", n=skipped)
        if overwrite:
            msg += tr("\n\nOryginały zostaną nadpisane (kopie w „_oryginaly”).")
        if not messagebox.askyesno(tr("Potwierdź"), msg):
            return
        self.save_settings(panel)
        self.burn_btn.config(state="disabled")

        def work():
            ok, errors = 0, []
            for n, (src, o) in enumerate(jobs, 1):
                try:
                    folder, name = os.path.split(src)
                    if overwrite:
                        bdir = os.path.join(folder, "_oryginaly")
                        os.makedirs(bdir, exist_ok=True)
                        bpath = os.path.join(bdir, name)
                        if not os.path.exists(bpath):
                            shutil.copy2(src, bpath)
                        burn_file(bpath, src, o)  # zawsze z czystego oryginału
                    else:
                        odir = os.path.join(folder, "z_napisem")
                        os.makedirs(odir, exist_ok=True)
                        burn_file(src, os.path.join(odir, name), o)
                    ok += 1
                except Exception as ex:
                    errors.append(f"{os.path.basename(src)}: {ex}")
                self.after(0, self.status.set, tr("Dodaję napisy… {n}/{total}", n=n, total=len(jobs)))
            self.after(0, self._burn_done, ok, errors, overwrite)

        threading.Thread(target=work, daemon=True).start()

    def _burn_done(self, ok, errors, overwrite):
        self.burn_btn.config(state="normal")
        where = tr("w oryginałach") if overwrite else tr("w podfolderach „z_napisem”")
        self.status.set(tr("Gotowe: {ok} zdjęć {where}, {err} błędów.", ok=ok, where=where, err=len(errors)))
        if errors:
            messagebox.showwarning(tr("Część plików pominięta"), "\n".join(errors[:20]))
        else:
            messagebox.showinfo(tr("Gotowe"), tr("Dodano napis do {ok} zdjęć ({where}).", ok=ok, where=where))

    # ===== zakładka: GPS =====
    def build_gps_tab(self, nb):
        tab = ttk.Frame(nb)
        self.add_tab(nb, tab, "Lokalizacja GPS w EXIF")
        pad = {"padx": 8, "pady": 4}

        self.L(ttk.Label(tab, foreground="gray", wraplength=900, justify="left"),
               "Fotoo zamienia współrzędne na nazwę sam (tryb exact = adres, abbreviated = skrót). "
               "Własnego tekstu tak nie ustawisz – do tego służy zakładka „Napis na zdjęciu”."
               ).pack(fill="x", **pad)

        row1 = ttk.Frame(tab)
        row1.pack(fill="x")
        self.L(ttk.Label(row1), "Miejsce:").pack(side="left", **pad)
        self.query = tk.StringVar(value=tr("Islandia"))
        e = ttk.Entry(row1, textvariable=self.query)
        e.pack(side="left", fill="x", expand=True, **pad)
        e.bind("<Return>", lambda _: self.search())
        self.search_btn = self.L(ttk.Button(row1, command=self.search), "Szukaj")
        self.search_btn.pack(side="left", **pad)

        row2 = ttk.Frame(tab)
        row2.pack(fill="x")
        self.L(ttk.Label(row2), "Wynik:").pack(side="left", **pad)
        self.combo = ttk.Combobox(row2, state="readonly")
        self.combo.pack(side="left", fill="x", expand=True, **pad)
        self.combo.bind("<<ComboboxSelected>>", self.pick_result)

        row3 = ttk.Frame(tab)
        row3.pack(fill="x")
        self.L(ttk.Label(row3), "Szerokość (lat):").pack(side="left", **pad)
        self.lat = tk.StringVar()
        ttk.Entry(row3, textvariable=self.lat, width=14).pack(side="left", **pad)
        self.L(ttk.Label(row3), "Długość (lon):").pack(side="left", **pad)
        self.lon = tk.StringVar()
        ttk.Entry(row3, textvariable=self.lon, width=14).pack(side="left", **pad)
        self.L(ttk.Label(row3, foreground="gray"), "(możesz też wpisać ręcznie)").pack(side="left", **pad)

        row4 = ttk.Frame(tab)
        row4.pack(fill="x")
        self.keep_mtime = tk.BooleanVar(value=True)
        self.backup = tk.BooleanVar(value=True)
        self.L(ttk.Checkbutton(row4, variable=self.keep_mtime), "Zachowaj datę modyfikacji pliku").pack(side="left", **pad)
        self.L(ttk.Checkbutton(row4, variable=self.backup), "Kopia oryginałów do „_oryginaly”").pack(side="left", **pad)
        self.save_btn = self.L(ttk.Button(row4, command=self.save_gps), "Zapisz GPS do zdjęć")
        self.save_btn.pack(side="right", **pad)

    def search(self):
        q = self.query.get().strip()
        if not q:
            return
        self.search_btn.config(state="disabled")
        self.status.set(tr("Szukam „{q}”…", q=q))

        def work():
            try:
                self.after(0, self._search_done, geocode(q), None)
            except Exception as ex:
                self.after(0, self._search_done, [], ex)

        threading.Thread(target=work, daemon=True).start()

    def _search_done(self, res, err):
        self.search_btn.config(state="normal")
        if err:
            self.status.set(tr("Błąd wyszukiwania: {err}", err=err))
            return
        self.results = res
        if not res:
            self.combo.config(values=[])
            self.combo.set("")
            self.status.set(tr("Nic nie znaleziono."))
            return
        self.combo.config(values=[r[0] for r in res])
        self.combo.current(0)
        self.pick_result()
        self.status.set(tr("Znaleziono {n} wyników. Sprawdź, czy pierwszy jest właściwy.", n=len(res)))

    def pick_result(self, _=None):
        i = self.combo.current()
        if 0 <= i < len(self.results):
            _, la, lo = self.results[i]
            self.lat.set(f"{la:.6f}")
            self.lon.set(f"{lo:.6f}")

    def save_gps(self):
        if not self.files:
            messagebox.showwarning(tr("Brak zdjęć"), tr("Dodaj najpierw zdjęcia."))
            return
        try:
            la = float(self.lat.get().replace(",", "."))
            lo = float(self.lon.get().replace(",", "."))
            assert -90 <= la <= 90 and -180 <= lo <= 180
        except Exception:
            messagebox.showerror(tr("Złe współrzędne"), tr("Podaj poprawną szerokość (-90..90) i długość (-180..180)."))
            return
        if not messagebox.askyesno(tr("Potwierdź"), tr("Zapisać GPS {la}, {lo} do {n} zdjęć?",
                                                       la=f"{la:.5f}", lo=f"{lo:.5f}", n=len(self.files))):
            return
        self.save_btn.config(state="disabled")
        files = list(self.files)
        keep, backup = self.keep_mtime.get(), self.backup.get()

        def work():
            ok, errors = 0, []
            for n, p in enumerate(files, 1):
                try:
                    bdir = os.path.join(os.path.dirname(p), "_oryginaly") if backup else None
                    write_gps(p, la, lo, keep, bdir)
                    ok += 1
                except Exception as ex:
                    errors.append(f"{os.path.basename(p)}: {ex}")
                self.after(0, self.status.set, tr("Zapisuję GPS… {n}/{total}", n=n, total=len(files)))
            self.after(0, self._gps_done, ok, errors)

        threading.Thread(target=work, daemon=True).start()

    def _gps_done(self, ok, errors):
        self.save_btn.config(state="normal")
        self.status.set(tr("Gotowe: {ok} zapisanych, {err} błędów.", ok=ok, err=len(errors)))
        if errors:
            messagebox.showwarning(tr("Część plików pominięta"), "\n".join(errors[:20]))

    # ===== pliki =====
    def _add(self, paths):
        added = 0
        for p in paths:
            if p.lower().endswith(JPEG_EXT) and p not in self.files:
                self.files.append(p)
                self.file_opts[p] = None  # nieruszone
                self.listbox.insert("end", self.file_label(p))
                added += 1
        self.count_lbl.config(text=tr("{n} plików", n=len(self.files)))
        if added:
            self.schedule_autosave()
        if added and self.cur is None:
            self.select_only(len(self.files) - added)
        else:
            self.refresh_rows([])  # przywraca zaznaczenie bieżącego
            self.schedule_preview()

    def add_files(self):
        self._add(filedialog.askopenfilenames(filetypes=[("JPEG", "*.jpg *.jpeg *.jpe *.JPG *.JPEG")]))

    def add_folder(self):
        d = filedialog.askdirectory()
        if not d:
            return
        paths = []
        for root, dirs, names in os.walk(d):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            paths += [os.path.join(root, n) for n in sorted(names)]
        self._add(paths)

    def remove_selected(self):
        if self.cur is None:
            return
        i = self.cur
        self.listbox.delete(i)
        self.file_opts.pop(self.files[i], None)
        del self.files[i]
        self.cur = None
        self.count_lbl.config(text=tr("{n} plików", n=len(self.files)))
        self.schedule_autosave()
        if self.files:
            self.select_only(min(i, len(self.files) - 1))
        else:
            self.schedule_preview()

    def clear_files(self):
        self.listbox.delete(0, "end")
        self.files.clear()
        self.file_opts.clear()
        self.cur = None
        self.count_lbl.config(text=tr("{n} plików", n=0))
        self.schedule_autosave()
        self.schedule_preview()

    def on_select(self, _=None):
        sel = self.listbox.curselection()
        if not sel:
            # nigdy nie zostawiamy listy bez zaznaczenia - wracamy na bieżące
            if self.cur is not None:
                self.listbox.selection_set(self.cur)
            return
        i = sel[0]
        if i != self.cur:
            self.cur = i
            o = self.file_opts.get(self.files[i])
            if o is None:
                # nieruszone zdjęcie: pusty tekst, wygląd i pozycja z poprzedniego
                o = self.panel_opts()
                o["text"] = ""
            self.set_panel(o)
            self.tpl_var.set("")
        self.schedule_preview()
        path = self.files[i]
        try:
            gps = read_gps(path)
            self.status.set(f"{os.path.basename(path)}: " +
                            (f"GPS {gps[0]:.5f}, {gps[1]:.5f}" if gps else tr("brak GPS")))
        except Exception:
            self.status.set(os.path.basename(path))

    # ===== ustawienia =====
    def load_settings(self):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                return {k: v for k, v in json.load(f).items() if k in DEFAULTS}
        except Exception:
            return {}

    def save_settings(self, o):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({**o, "lang": LANG}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ===== język =====
    def load_lang(self):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                lang = json.load(f).get("lang", "en")
            return lang if lang in ("en", "pl") else "en"
        except Exception:
            return "en"   # pierwszy start: po angielsku

    def save_lang(self):
        try:
            try:
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            data["lang"] = LANG
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def L(self, w, pl, opt="text"):
        """Ustawia przetłumaczony tekst widżetu i zapamiętuje go do zmiany języka na żywo."""
        self._i18n.append((w, opt, pl))
        w.config(**{opt: tr(pl)})
        return w

    def add_tab(self, nb, tab, pl):
        nb.add(tab, text=tr(pl))
        self._i18n_tabs.append((nb, tab, pl))

    def mapped(self, master, var, keys_fn, **kw):
        cb = MappedCombo(master, var, keys_fn, **kw)
        self._mapped.append(cb)
        return cb

    def switch_language(self):
        global LANG
        new = self.lang_var.get()
        if new == LANG:
            return
        LANG = new
        self.save_lang()
        for w, opt, pl in self._i18n:
            try:
                w.config(**{opt: tr(pl)})
            except tk.TclError:
                pass
        for nb, tab, pl in self._i18n_tabs:
            nb.tab(tab, text=tr(pl))
        for cb in self._mapped:
            cb.refresh()
        self.title(tr("{app} v{ver}  –  napis i lokalizacja na zdjęciach", app=APP_NAME, ver=APP_VERSION))
        self.update_accent_widgets()
        self.count_lbl.config(text=tr("{n} plików", n=len(self.files)))
        self.refresh_rows(range(len(self.files)))
        self.status.set("")
        self.schedule_preview()


if __name__ == "__main__":
    if not hasattr(ImageDraw.ImageDraw, "rounded_rectangle"):
        r = tk.Tk(); r.withdraw()
        messagebox.showerror("Pillow", "Pillow is too old / Za stary Pillow:\n\npip install -U pillow")
        sys.exit(1)
    App().mainloop()
