#!/usr/bin/env python3
# ProKill v2 - gestionnaire de processus avancé
# Requis : pip install psutil
# Exe : pip install pyinstaller && pyinstaller --onefile --noconsole --name ProKill prokill.py
# Lancer en admin pour tuer les process protégés

import os
import sys
import time
import json
import threading
import webbrowser
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import psutil
except ImportError:
    print("psutil manquant. Installe-le avec :  pip install psutil")
    sys.exit(1)

REFRESH_MS = 3000
WATCHDOG_MS = 2000

# ---------- Identité de l'app (à modifier ici) ----------
APP_VERSION = "2.2.0"
AUTHOR = "Karkarofff"
AUTHOR_URL = "https://github.com/karkarofff"          # plus tard : ton site
# URL d'un petit fichier JSON que TU héberges (ton site, GitHub, peu importe).
# Contenu attendu :  {"version": "2.3.0", "url": "https://tonsite.fr/prokill"}
# Quand tu sors une nouvelle version : tu montes "version" dans ce fichier,
# et toutes les anciennes installations proposeront la MàJ au lancement.
UPDATE_URL = "https://raw.githubusercontent.com/karkarofff/prokill/main/version.json"


def resource_path(name):
    """Chemin d'une ressource, compatible PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


# ---------- Config persistante (%APPDATA%\ProKill\config.json) ----------
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                          "ProKill")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ---------- Lancement au démarrage de Windows ----------
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "ProKill"


def _startup_command():
    if getattr(sys, "frozen", False):        # exe PyInstaller
        return f'"{sys.executable}"'
    script = os.path.abspath(sys.argv[0])
    pyw = sys.executable.replace("python.exe", "pythonw.exe")
    return f'"{pyw}" "{script}"'


def is_startup_enabled():
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, RUN_NAME)
        return True
    except Exception:
        return False


def set_startup(enabled):
    """Ajoute/retire ProKill du démarrage (registre utilisateur, pas admin)."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0,
                            winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, RUN_NAME, 0, winreg.REG_SZ,
                                  _startup_command())
            else:
                try:
                    winreg.DeleteValue(k, RUN_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def setup_window(win):
    """Barre de titre sombre (Windows 10/11) + icône si dispo."""
    try:
        win.iconbitmap(resource_path("prokill.ico"))
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
            value = ctypes.c_int(1)
            # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE (19 sur vieux builds Win10)
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

# ---------- Palette ----------
BG      = "#1e1f24"
BG2     = "#26272e"
BG3     = "#2f3038"
FG      = "#e8e8ea"
FG_DIM  = "#9a9ba3"
ACCENT  = "#e05555"   # rouge kill
ACCENT2 = "#4f9cf0"   # bleu actions douces
GREEN   = "#4fbf78"


class Tooltip:
    """Info-bulle au survol d'un widget."""
    def __init__(self, widget, text, delay=450):
        self.widget, self.text, self.delay = widget, text, delay
        self.tip, self._job = None, None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _=None):
        self._job = self.widget.after(self.delay, self._show)

    def _show(self):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, justify="left", wraplength=340,
                 bg="#111216", fg=FG, relief="solid", borderwidth=1,
                 font=("Segoe UI", 9), padx=8, pady=6).pack()

    def _hide(self, _=None):
        if self._job:
            self.widget.after_cancel(self._job)
            self._job = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


HELP_TEXT = """\
PROKILL - C'EST QUOI ?
ProKill liste TOUS les processus qui tournent sur ton PC et permet de les
fermer, y compris ceux que le Gestionnaire des tâches cache ou n'arrive
pas à fermer. Typiquement : un jeu qui a planté, un launcher qui laisse
traîner des sous-process en arrière-plan, un logiciel qui refuse de mourir.

LE FILTRE (barre du haut)
Tape n'importe quoi : un nom, un bout de chemin, un PID, un utilisateur.
Exemple : tape "epic" et tu verras TOUS les process dont le fichier .exe
se trouve dans un dossier Epic Games, même s'ils portent un nom obscur
comme EOSOverlayRenderer.exe. C'est la grande force de ProKill : on
cherche aussi dans le CHEMIN du programme, pas juste dans son nom.

LES BOUTONS
- Tuer (propre) : demande poliment au process de se fermer (comme quand
  tu cliques sur la croix). S'il ne répond pas sous 3 secondes, ProKill
  le tue de force automatiquement. À utiliser en premier.
- Tuer de FORCE : extermination immédiate, sans sommation. Pour les
  process complètement plantés. Raccourci : touche Suppr.
- Tuer l'ARBRE : tue le process sélectionné ET tous ses enfants
  (sous-process). Parfait pour les launchers qui lancent 4-5 process.
- Tuer tout le filtre : tue de force TOUT ce qui est affiché à l'écran.
  Tape "epic", clique, tout Epic dégage. Une confirmation est demandée.
- Surveiller : ajoute le process à la liste de surveillance. Si un
  process du même nom réapparaît, il est re-tué automatiquement toutes
  les 2 secondes. Pratique contre les programmes qui se relancent seuls.
  Clique sur "Surveillance (n)" pour voir/vider la liste.
- Ouvrir le dossier : ouvre l'explorateur à l'endroit exact où se trouve
  le fichier .exe du process. Utile pour identifier un inconnu.

LA LISTE
- Clic sur un en-tête de colonne : trie la liste.
- Double-clic sur un process : fenêtre de détails (ligne de commande,
  connexions réseau, fichiers ouverts, process parent).
- Clic droit : menu rapide avec les mêmes actions.
- Vue arbre : affiche les process hiérarchiquement (parent > enfants).
  Note : quand un filtre est actif, l'affichage repasse en liste à plat.
- Process système : décoche pour masquer les process de Windows et n'y
  voir que TES programmes.

BON À SAVOIR
- "Accès refusé" = le process est protégé. Relance ProKill en
  administrateur (clic droit > Exécuter en tant qu'administrateur).
- Tuer un process système de Windows peut faire planter le PC. Dans le
  doute, ne touche pas à ce qui tourne sous SYSTEM.
- Lancer au démarrage : coche cette case pour que ProKill se lance tout
  seul à l'ouverture de Windows. La liste de surveillance est
  sauvegardée : tes process surveillés sont re-tués dès le démarrage
  sans que tu aies à y penser.
- Mises à jour : ProKill vérifie au lancement si une nouvelle version
  est disponible et te prévient. Clic droit sur "développé par ..." en
  bas à droite pour vérifier manuellement.
"""


class ProKill(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ProKill")
        self.geometry("1150x680")
        self.minsize(860, 480)
        self.configure(bg=BG)

        self._all_procs = []
        self._sort_col = "mem"
        self._sort_desc = True
        self._auto_refresh = tk.BooleanVar(value=True)
        self._show_system = tk.BooleanVar(value=True)
        self._tree_mode = tk.BooleanVar(value=False)
        self._watchlist = set()      # substrings surveillés (lowercase)
        self._watch_lock = threading.Lock()
        cfg = load_config()
        self._watchlist = set(cfg.get("watchlist", []))
        self._startup_var = tk.BooleanVar(value=is_startup_enabled())

        self._style()
        self._build_ui()
        self._update_watch_btn()
        setup_window(self)
        self.refresh(full=True)
        self.after(REFRESH_MS, self._tick)
        self.after(WATCHDOG_MS, self._watchdog_tick)

    # ---------- Style ----------
    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=FG, fieldbackground=BG2,
                    font=("Segoe UI", 10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG)
        s.configure("Dim.TLabel", foreground=FG_DIM)
        s.configure("TCheckbutton", background=BG, foreground=FG,
                    indicatorbackground=BG2, indicatorforeground="#ffffff")
        s.map("TCheckbutton",
              background=[("active", BG)],
              foreground=[("active", FG)],
              indicatorbackground=[("selected", ACCENT2),
                                   ("pressed", ACCENT2),
                                   ("active", BG3)])
        s.configure("TEntry", foreground=FG, fieldbackground=BG2,
                    insertcolor=FG, bordercolor=BG3,
                    lightcolor=BG3, darkcolor=BG3, padding=4)
        s.map("TEntry",
              fieldbackground=[("focus", BG2), ("!focus", BG2)],
              foreground=[("focus", FG), ("!focus", FG)])
        s.configure("Vertical.TScrollbar", background=BG3, troughcolor=BG,
                    bordercolor=BG, arrowcolor=FG_DIM,
                    lightcolor=BG3, darkcolor=BG3)
        s.map("Vertical.TScrollbar", background=[("active", "#3a3b45")])
        s.configure("Horizontal.TScrollbar", background=BG3, troughcolor=BG,
                    bordercolor=BG, arrowcolor=FG_DIM,
                    lightcolor=BG3, darkcolor=BG3)
        s.configure("Treeview", background=BG2, fieldbackground=BG2,
                    foreground=FG, rowheight=26, bordercolor=BG,
                    lightcolor=BG, darkcolor=BG)
        s.configure("Treeview.Heading", background=BG3, foreground=FG,
                    relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview.Heading", background=[("active", "#3a3b45")])
        s.map("Treeview", background=[("selected", "#44464f")],
              foreground=[("selected", "#ffffff")])
        for name, bg, fg in (("Kill.TButton", ACCENT, "#ffffff"),
                             ("Soft.TButton", BG3, FG),
                             ("Blue.TButton", ACCENT2, "#ffffff"),
                             ("Green.TButton", GREEN, "#ffffff")):
            s.configure(name, background=bg, foreground=fg, bordercolor=bg,
                        focusthickness=0, padding=(10, 6))
            s.map(name, background=[("active", bg), ("pressed", bg)])

    # ---------- UI ----------
    def _build_ui(self):
        top = ttk.Frame(self, padding=(8, 8, 8, 4))
        top.pack(fill="x")

        ttk.Label(top, text="🔎").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        entry = ttk.Entry(top, textvariable=self.search_var, width=42)
        entry.pack(side="left", padx=6)
        entry.focus()
        Tooltip(entry, "Filtre la liste. Cherche dans le NOM, le CHEMIN de "
                       "l'exe, le PID et l'utilisateur.\nExemple : tape "
                       "\"epic\" pour trouver tous les process d'Epic Games, "
                       "même ceux au nom bizarre.")

        b = ttk.Button(top, text="✕", width=3, style="Soft.TButton",
                       command=lambda: self.search_var.set(""))
        b.pack(side="left")
        Tooltip(b, "Efface le filtre.")

        cb = ttk.Checkbutton(top, text="Auto-refresh", variable=self._auto_refresh)
        cb.pack(side="left", padx=(14, 4))
        Tooltip(cb, "Rafraîchit la liste automatiquement toutes les 3 secondes.")

        cb2 = ttk.Checkbutton(top, text="Process système", variable=self._show_system,
                              command=self._apply_filter)
        cb2.pack(side="left", padx=4)
        Tooltip(cb2, "Affiche ou masque les process de Windows (SYSTEM, "
                     "services...).\nDécoche pour ne voir que TES programmes.")

        cb3 = ttk.Checkbutton(top, text="Vue arbre", variable=self._tree_mode,
                              command=self._apply_filter)
        cb3.pack(side="left", padx=4)
        Tooltip(cb3, "Affiche les process en hiérarchie parent > enfants.\n"
                     "(Repasse en liste à plat quand un filtre est actif.)")

        cb4 = ttk.Checkbutton(top, text="Lancer au démarrage",
                              variable=self._startup_var,
                              command=self._toggle_startup)
        cb4.pack(side="left", padx=4)
        Tooltip(cb4, "Lance ProKill automatiquement à l'ouverture de Windows.\n"
                     "Indispensable si tu utilises la surveillance : la liste "
                     "des process surveillés est sauvegardée et reprise à "
                     "chaque lancement.")

        hb = ttk.Button(top, text="❔ Aide", style="Blue.TButton", command=self.show_help)
        hb.pack(side="right")
        Tooltip(hb, "Explique le but de l'application et le rôle de chaque bouton.")

        rb = ttk.Button(top, text="⟳ Rafraîchir", style="Soft.TButton",
                        command=lambda: self.refresh(full=True))
        rb.pack(side="right", padx=6)
        Tooltip(rb, "Recharge la liste des process immédiatement.")

        # Tableau
        cols = ("pid", "name", "user", "cpu", "mem", "path")
        self.tree = ttk.Treeview(self, columns=cols, show="tree headings",
                                 selectmode="extended")
        headers = {"pid": ("PID", 70), "name": ("Nom", 190),
                   "user": ("Utilisateur", 130), "cpu": ("CPU %", 65),
                   "mem": ("RAM (Mo)", 85), "path": ("Chemin de l'exe", 470)}
        self.tree.column("#0", width=24, stretch=False)
        for c, (txt, w) in headers.items():
            self.tree.heading(c, text=txt, command=lambda col=c: self._sort_by(col))
            self.tree.column(c, width=w, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=(2, 4))
        self.tree.tag_configure("watched", foreground="#f0b64f")

        sb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")

        # Boutons
        bottom = ttk.Frame(self, padding=(8, 4))
        bottom.pack(fill="x")

        b1 = ttk.Button(bottom, text="Tuer (propre)", style="Soft.TButton",
                        command=lambda: self.kill_selected(force=False))
        b1.pack(side="left")
        Tooltip(b1, "Demande au process de se fermer proprement (comme la "
                    "croix de la fenêtre).\nS'il ne répond pas sous 3 s, il "
                    "est tué de force automatiquement.")

        b2 = ttk.Button(bottom, text="☠ Tuer de FORCE", style="Kill.TButton",
                        command=lambda: self.kill_selected(force=True))
        b2.pack(side="left", padx=6)
        Tooltip(b2, "Tue immédiatement le process, sans sommation.\nPour les "
                    "programmes plantés. Raccourci : touche Suppr.")

        b3 = ttk.Button(bottom, text="Tuer l'ARBRE", style="Kill.TButton",
                        command=self.kill_tree_selected)
        b3.pack(side="left")
        Tooltip(b3, "Tue le process sélectionné ET tous ses sous-process "
                    "(enfants).\nParfait pour les launchers qui lancent "
                    "plusieurs process.")

        b4 = ttk.Button(bottom, text="Tuer tout le filtre", style="Kill.TButton",
                        command=self.kill_all_filtered)
        b4.pack(side="left", padx=6)
        Tooltip(b4, "Tue de force TOUS les process actuellement affichés.\n"
                    "Exemple : filtre \"epic\" puis ce bouton = tout Epic "
                    "est fermé. Confirmation demandée.")

        b5 = ttk.Button(bottom, text="👁 Surveiller", style="Green.TButton",
                        command=self.watch_selected)
        b5.pack(side="left")
        Tooltip(b5, "Ajoute le process à la surveillance : s'il réapparaît, "
                    "il sera RE-TUÉ automatiquement.\nUtile contre les "
                    "programmes qui se relancent tout seuls.")

        self.watch_btn = ttk.Button(bottom, text="Surveillance (0)",
                                    style="Soft.TButton", command=self.show_watchlist)
        self.watch_btn.pack(side="left", padx=6)
        Tooltip(self.watch_btn, "Affiche et gère la liste des process surveillés.")

        b6 = ttk.Button(bottom, text="📁 Ouvrir le dossier", style="Soft.TButton",
                        command=self.open_folder)
        b6.pack(side="right")
        Tooltip(b6, "Ouvre l'explorateur à l'emplacement du fichier .exe du "
                    "process sélectionné.\nPratique pour identifier un "
                    "process inconnu.")

        self.status = tk.StringVar(value="Prêt")
        statusbar = ttk.Frame(self)
        statusbar.pack(fill="x")
        ttk.Label(statusbar, textvariable=self.status, style="Dim.TLabel",
                  padding=(10, 3)).pack(side="left")
        credit = ttk.Label(statusbar,
                           text=f"ProKill v{APP_VERSION} — développé par {AUTHOR}",
                           style="Dim.TLabel", padding=(10, 3), cursor="hand2")
        credit.pack(side="right")
        credit.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))
        Tooltip(credit, f"Clique pour ouvrir la page de {AUTHOR}.\n"
                        "Clic droit : vérifier les mises à jour.")
        credit.bind("<Button-3>",
                    lambda e: self.check_updates(silent=False))
        # vérification silencieuse au démarrage (ne dérange que si MàJ dispo)
        self.after(1500, lambda: self.check_updates(silent=True))

        # Menu clic droit
        self.menu = tk.Menu(self, tearoff=0, bg=BG3, fg=FG,
                            activebackground="#44464f", activeforeground="#fff")
        self.menu.add_command(label="Tuer (propre)",
                              command=lambda: self.kill_selected(force=False))
        self.menu.add_command(label="Tuer de force",
                              command=lambda: self.kill_selected(force=True))
        self.menu.add_command(label="Tuer l'arbre complet",
                              command=self.kill_tree_selected)
        self.menu.add_separator()
        self.menu.add_command(label="Surveiller ce process", command=self.watch_selected)
        self.menu.add_command(label="Filtrer sur ce nom", command=self._filter_on_name)
        self.menu.add_command(label="Détails", command=self.show_details)
        self.menu.add_command(label="Ouvrir le dossier de l'exe", command=self.open_folder)
        self.tree.bind("<Button-3>", self._popup)
        self.tree.bind("<Delete>", lambda e: self.kill_selected(force=True))
        self.tree.bind("<Double-1>", lambda e: self.show_details())

    def _popup(self, event):
        iid = self.tree.identify_row(event.y)
        if iid and iid not in self.tree.selection():
            self.tree.selection_set(iid)
        if self.tree.selection():
            self.menu.tk_popup(event.x_root, event.y_root)

    # ---------- Données ----------
    def refresh(self, full=False):
        def worker():
            procs = []
            for p in psutil.process_iter(
                    ["pid", "ppid", "name", "username", "exe", "memory_info"]):
                try:
                    info = p.info
                    procs.append({
                        "pid": info["pid"],
                        "ppid": info["ppid"],
                        "name": info["name"] or "?",
                        "user": (info["username"] or "").split("\\")[-1],
                        "cpu": p.cpu_percent(interval=None),
                        "mem": (info["memory_info"].rss // (1024 * 1024)
                                if info["memory_info"] else 0),
                        "path": info["exe"] or "",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            self._all_procs = procs
            self.after(0, self._apply_filter)
        threading.Thread(target=worker, daemon=True).start()

    def _tick(self):
        if self._auto_refresh.get():
            self.refresh()
        self.after(REFRESH_MS, self._tick)

    def _visible_procs(self):
        q = self.search_var.get().lower().strip()
        show_sys = self._show_system.get()
        rows = []
        for p in self._all_procs:
            if not show_sys and p["user"].upper() in (
                    "SYSTEM", "SERVICE LOCAL", "SERVICE RÉSEAU",
                    "LOCAL SERVICE", "NETWORK SERVICE", ""):
                continue
            if q:
                hay = f'{p["pid"]} {p["name"]} {p["path"]} {p["user"]}'.lower()
                if q not in hay:
                    continue
            rows.append(p)
        return rows, q

    def _row_tags(self, p):
        name = p["name"].lower()
        with self._watch_lock:
            return ("watched",) if any(w in name or w in p["path"].lower()
                                       for w in self._watchlist) else ()

    def _apply_filter(self):
        rows, q = self._visible_procs()
        sel_pids = {int(self.tree.item(i, "values")[0])
                    for i in self.tree.selection()} if self.tree.selection() else set()
        self.tree.delete(*self.tree.get_children())

        if self._tree_mode.get() and not q:
            by_pid = {p["pid"]: p for p in rows}
            iids = {}
            def insert(p):
                if p["pid"] in iids:
                    return iids[p["pid"]]
                parent_iid = ""
                pp = by_pid.get(p["ppid"])
                if pp and pp["pid"] != p["pid"]:
                    parent_iid = insert(pp)
                iid = self.tree.insert(parent_iid, "end", values=(
                    p["pid"], p["name"], p["user"], f'{p["cpu"]:.0f}',
                    p["mem"], p["path"]), open=True, tags=self._row_tags(p))
                iids[p["pid"]] = iid
                return iid
            for p in rows:
                insert(p)
        else:
            rows.sort(key=lambda r: (r[self._sort_col]
                                     if not isinstance(r[self._sort_col], str)
                                     else r[self._sort_col].lower()),
                      reverse=self._sort_desc)
            for p in rows:
                iid = self.tree.insert("", "end", values=(
                    p["pid"], p["name"], p["user"], f'{p["cpu"]:.0f}',
                    p["mem"], p["path"]), tags=self._row_tags(p))
                if p["pid"] in sel_pids:
                    self.tree.selection_add(iid)

        self.status.set(f'{len(rows)} process affichés / '
                        f'{len(self._all_procs)} au total'
                        + ("   |   ⚠ filtre actif : vue à plat"
                           if self._tree_mode.get() and q else ""))

    def _sort_by(self, col):
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col, self._sort_desc = col, True
        self._apply_filter()

    def _filter_on_name(self):
        sel = self.tree.selection()
        if sel:
            name = self.tree.item(sel[0], "values")[1]
            self.search_var.set(os.path.splitext(name)[0].rstrip("0123456789"))

    # ---------- Kill ----------
    def _selected_pids(self):
        return [int(self.tree.item(i, "values")[0]) for i in self.tree.selection()]

    def _kill_pid(self, pid, force):
        try:
            p = psutil.Process(pid)
            name = p.name()
            if force:
                p.kill()
            else:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except psutil.TimeoutExpired:
                    p.kill()
            return name, None
        except psutil.NoSuchProcess:
            return str(pid), None
        except psutil.AccessDenied:
            return str(pid), "accès refusé (relance ProKill en admin)"
        except Exception as e:
            return str(pid), str(e)

    def kill_selected(self, force):
        pids = self._selected_pids()
        if not pids:
            return
        errs = []
        for pid in pids:
            name, err = self._kill_pid(pid, force)
            if err:
                errs.append(f"{name} ({pid}) : {err}")
        self._after_kill(errs, len(pids))

    def kill_tree_selected(self):
        pids = self._selected_pids()
        if not pids:
            return
        errs, count = [], 0
        for pid in pids:
            try:
                parent = psutil.Process(pid)
                targets = parent.children(recursive=True) + [parent]
            except psutil.NoSuchProcess:
                continue
            for p in targets:
                count += 1
                _, err = self._kill_pid(p.pid, force=True)
                if err:
                    errs.append(f"{p.pid} : {err}")
        self._after_kill(errs, count)

    def kill_all_filtered(self):
        rows, _ = self._visible_procs()
        if not rows:
            return
        if not messagebox.askyesno(
                "Confirmation",
                f"Tuer de force les {len(rows)} process actuellement affichés ?"):
            return
        errs = []
        for p in rows:
            _, err = self._kill_pid(p["pid"], force=True)
            if err:
                errs.append(f'{p["name"]} ({p["pid"]}) : {err}')
        self._after_kill(errs, len(rows))

    def _after_kill(self, errs, total):
        time.sleep(0.3)
        self.refresh(full=True)
        if errs:
            messagebox.showwarning(
                "Résultat", f"{total - len(errs)}/{total} tués.\n\nÉchecs :\n"
                + "\n".join(errs[:15]))
        else:
            self.status.set(f"{total} process tué(s)")

    # ---------- Surveillance ----------
    def _save_watchlist(self):
        with self._watch_lock:
            wl = sorted(self._watchlist)
        cfg = load_config()
        cfg["watchlist"] = wl
        save_config(cfg)

    def _toggle_startup(self):
        want = self._startup_var.get()
        if not set_startup(want):
            self._startup_var.set(is_startup_enabled())
            messagebox.showwarning(
                "Démarrage",
                "Impossible de modifier le démarrage automatique.")
        else:
            self.status.set("Lancement au démarrage : "
                            + ("activé" if want else "désactivé"))

    def watch_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        added = []
        for i in sel:
            name = self.tree.item(i, "values")[1].lower()
            with self._watch_lock:
                if name not in self._watchlist:
                    self._watchlist.add(name)
                    added.append(name)
        self._update_watch_btn()
        if added:
            self._save_watchlist()
            # premier kill immédiat
            self.kill_selected(force=True)
            self.status.set("Surveillance : " + ", ".join(added)
                            + " (re-kill auto si réapparition)")

    def _update_watch_btn(self):
        with self._watch_lock:
            n = len(self._watchlist)
        self.watch_btn.configure(text=f"Surveillance ({n})")

    def _watchdog_tick(self):
        with self._watch_lock:
            watch = set(self._watchlist)
        if watch:
            def worker():
                killed = []
                for p in psutil.process_iter(["pid", "name", "exe"]):
                    try:
                        name = (p.info["name"] or "").lower()
                        path = (p.info["exe"] or "").lower()
                        if any(w in name or (w in path and path) for w in watch):
                            p.kill()
                            killed.append(name)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                if killed:
                    self.after(0, lambda: self.status.set(
                        f"Watchdog : re-tué {', '.join(sorted(set(killed)))}"))
            threading.Thread(target=worker, daemon=True).start()
        self.after(WATCHDOG_MS, self._watchdog_tick)

    def show_watchlist(self):
        win = tk.Toplevel(self)
        win.title("Process surveillés")
        win.configure(bg=BG)
        win.geometry("420x320")
        setup_window(win)
        ttk.Label(win, text="Ces process sont re-tués automatiquement dès "
                            "qu'ils réapparaissent :", wraplength=390,
                  padding=8).pack(anchor="w")
        lb = tk.Listbox(win, bg=BG2, fg=FG, selectbackground="#44464f",
                        highlightthickness=0, relief="flat")
        lb.pack(fill="both", expand=True, padx=8, pady=4)
        with self._watch_lock:
            for w in sorted(self._watchlist):
                lb.insert("end", w)
        fr = ttk.Frame(win, padding=8)
        fr.pack(fill="x")
        def remove():
            sel = lb.curselection()
            if sel:
                val = lb.get(sel[0])
                with self._watch_lock:
                    self._watchlist.discard(val)
                lb.delete(sel[0])
                self._update_watch_btn()
                self._save_watchlist()
        def clear():
            with self._watch_lock:
                self._watchlist.clear()
            lb.delete(0, "end")
            self._update_watch_btn()
            self._save_watchlist()
        ttk.Button(fr, text="Retirer la sélection", style="Soft.TButton",
                   command=remove).pack(side="left")
        ttk.Button(fr, text="Tout vider", style="Kill.TButton",
                   command=clear).pack(side="right")

    # ---------- Détails / divers ----------
    def show_details(self):
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(self.tree.item(sel[0], "values")[0])
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                lines = [f"PID : {p.pid}",
                         f"Nom : {p.name()}",
                         f"Statut : {p.status()}",
                         f"Démarré : {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(p.create_time()))}",
                         f"Exe : {p.exe() if self._safe(p.exe) else '(accès refusé)'}",
                         f"Dossier de travail : {self._safe(p.cwd) or '(accès refusé)'}",
                         f"Parent : {self._parent_str(p)}",
                         "",
                         "Ligne de commande :",
                         "  " + " ".join(self._safe(p.cmdline) or ["(accès refusé)"]),
                         ""]
                conns = self._safe(p.net_connections) if hasattr(p, "net_connections") \
                    else self._safe(p.connections)
                lines.append("Connexions réseau :")
                if conns:
                    for c in conns[:25]:
                        l = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
                        r = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
                        lines.append(f"  {c.status:<12} {l}  ->  {r}")
                else:
                    lines.append("  (aucune ou accès refusé)")
                lines.append("")
                files = self._safe(p.open_files)
                lines.append("Fichiers ouverts :")
                if files:
                    for f in files[:40]:
                        lines.append(f"  {f.path}")
                else:
                    lines.append("  (aucun ou accès refusé)")
        except psutil.NoSuchProcess:
            messagebox.showinfo("Info", "Ce process n'existe plus.")
            return

        win = tk.Toplevel(self)
        win.title(f"Détails - PID {pid}")
        win.configure(bg=BG)
        win.geometry("760x560")
        setup_window(win)
        txt = tk.Text(win, bg=BG2, fg=FG, insertbackground=FG, relief="flat",
                      font=("Consolas", 10), wrap="none", padx=10, pady=10)
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        txt.insert("1.0", "\n".join(lines))
        txt.configure(state="disabled")

    @staticmethod
    def _safe(fn):
        try:
            return fn()
        except (psutil.AccessDenied, psutil.NoSuchProcess, OSError):
            return None

    def _parent_str(self, p):
        try:
            pp = p.parent()
            return f"{pp.name()} (PID {pp.pid})" if pp else "(aucun)"
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "(inconnu)"

    def check_updates(self, silent=True):
        """Compare APP_VERSION au fichier version.json hébergé (UPDATE_URL)."""
        def worker():
            try:
                req = urllib.request.Request(
                    UPDATE_URL, headers={"User-Agent": f"ProKill/{APP_VERSION}"})
                with urllib.request.urlopen(req, timeout=6) as r:
                    data = json.load(r)
                latest = str(data.get("version") or "").lstrip("vV")
                url = data.get("url") or AUTHOR_URL
                if not latest:
                    raise ValueError("pas de version")
                def as_tuple(v):
                    return tuple(int(x) for x in v.split(".") if x.isdigit())
                if as_tuple(latest) > as_tuple(APP_VERSION):
                    def ask():
                        if messagebox.askyesno(
                                "Mise à jour disponible",
                                f"Une nouvelle version de ProKill est dispo !\n\n"
                                f"Ta version : {APP_VERSION}\n"
                                f"Dernière version : {latest}\n\n"
                                "Ouvrir la page de téléchargement ?"):
                            webbrowser.open(url)
                    self.after(0, ask)
                elif not silent:
                    self.after(0, lambda: messagebox.showinfo(
                        "Mise à jour",
                        f"Tu as déjà la dernière version ({APP_VERSION})."))
            except Exception:
                if not silent:
                    self.after(0, lambda: messagebox.showinfo(
                        "Mise à jour",
                        "Impossible de vérifier les mises à jour\n"
                        "(pas de connexion ou fichier de version introuvable)."))
        threading.Thread(target=worker, daemon=True).start()

    def open_folder(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.tree.item(sel[0], "values")[5]
        if path and os.path.exists(path):
            os.startfile(os.path.dirname(path))
        else:
            messagebox.showinfo("Info", "Chemin inconnu pour ce process.")

    def show_help(self):
        win = tk.Toplevel(self)
        win.title("ProKill - Comment ça marche")
        win.configure(bg=BG)
        win.geometry("720x600")
        setup_window(win)
        txt = tk.Text(win, bg=BG2, fg=FG, relief="flat", wrap="word",
                      font=("Segoe UI", 10), padx=14, pady=12)
        sb = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=8)
        txt.pack(fill="both", expand=True, padx=(8, 0), pady=8)
        txt.insert("1.0", HELP_TEXT)
        txt.configure(state="disabled")


if __name__ == "__main__":
    ProKill().mainloop()