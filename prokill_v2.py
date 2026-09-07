#!/usr/bin/env python3
# ProKill v2.3 - advanced process manager / gestionnaire de processus avancé
# Requis / requires : pip install psutil
# Exe : pyinstaller --onefile --noconsole --icon prokill.ico --add-data "prokill.ico;." --name ProKill prokill_v2.py

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
    print("psutil manquant / missing. ->  pip install psutil")
    sys.exit(1)

REFRESH_MS = 3000
WATCHDOG_MS = 2000

# ---------- Identité de l'app (à modifier ici) ----------
APP_VERSION = "2.3.0"
AUTHOR = "Karkarofff"
AUTHOR_URL = "https://github.com/karkarofff"          # plus tard : ton site
# URL d'un petit fichier JSON que TU héberges (ton site, GitHub, peu importe).
# Contenu attendu :  {"version": "2.4.0", "url": "https://tonsite.fr/prokill"}
UPDATE_URL = "https://raw.githubusercontent.com/karkarofff/prokill/main/version.json"

# ---------- Palette ----------
BG      = "#1e1f24"
BG2     = "#26272e"
BG3     = "#2f3038"
FG      = "#e8e8ea"
FG_DIM  = "#9a9ba3"
ACCENT  = "#e05555"   # rouge kill
ACCENT2 = "#4f9cf0"   # bleu actions douces
GREEN   = "#4fbf78"

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


# ---------- Traductions ----------
LANGS = {
 "fr": {
  "ready": "Prêt",
  "autorefresh": "Auto-refresh",
  "tt_autorefresh": "Rafraîchit la liste automatiquement toutes les 3 secondes.",
  "sys_procs": "Process système",
  "tt_sys": "Affiche ou masque les process de Windows (SYSTEM, services...).\nDécoche pour ne voir que TES programmes.",
  "tree_view": "Vue arbre",
  "tt_tree": "Affiche les process en hiérarchie parent > enfants.\n(Repasse en liste à plat quand un filtre est actif.)",
  "startup": "Lancer au démarrage",
  "tt_startup": "Lance ProKill automatiquement à l'ouverture de Windows.\nIndispensable si tu utilises la surveillance : la liste des process surveillés est sauvegardée et reprise à chaque lancement.",
  "help_btn": "❔ Aide",
  "tt_help": "Explique le but de l'application et le rôle de chaque bouton.",
  "refresh_btn": "⟳ Rafraîchir",
  "tt_refresh": "Recharge la liste des process immédiatement.",
  "tt_lang": "Switch interface to English",
  "tt_search": "Filtre la liste. Cherche dans le NOM, le CHEMIN de l'exe, le PID et l'utilisateur.\nExemple : tape \"epic\" pour trouver tous les process d'Epic Games, même ceux au nom bizarre.",
  "tt_clear": "Efface le filtre.",
  "col_pid": "PID", "col_name": "Nom", "col_user": "Utilisateur",
  "col_cpu": "CPU %", "col_mem": "RAM (Mo)", "col_path": "Chemin de l'exe",
  "kill_soft": "Tuer (propre)",
  "tt_kill_soft": "Demande au process de se fermer proprement (comme la croix de la fenêtre).\nS'il ne répond pas sous 3 s, il est tué de force automatiquement.",
  "kill_force": "☠ Tuer de FORCE",
  "tt_kill_force": "Tue immédiatement le process, sans sommation.\nPour les programmes plantés. Raccourci : touche Suppr.",
  "kill_tree": "Tuer l'ARBRE",
  "tt_kill_tree": "Tue le process sélectionné ET tous ses sous-process (enfants).\nParfait pour les launchers qui lancent plusieurs process.",
  "kill_filter": "Tuer tout le filtre",
  "tt_kill_filter": "Tue de force TOUS les process actuellement affichés.\nExemple : filtre \"epic\" puis ce bouton = tout Epic est fermé. Confirmation demandée.",
  "watch": "👁 Surveiller",
  "tt_watch": "Ajoute le process à la surveillance : s'il réapparaît, il sera RE-TUÉ automatiquement.\nUtile contre les programmes qui se relancent tout seuls.",
  "watch_count": "Surveillance ({n})",
  "tt_watchlist": "Affiche et gère la liste des process surveillés.",
  "open_folder": "📁 Ouvrir le dossier",
  "tt_open_folder": "Ouvre l'explorateur à l'emplacement du fichier .exe du process sélectionné.\nPratique pour identifier un process inconnu.",
  "m_kill_soft": "Tuer (propre)", "m_kill_force": "Tuer de force",
  "m_kill_tree": "Tuer l'arbre complet", "m_watch": "Surveiller ce process",
  "m_filter_name": "Filtrer sur ce nom", "m_details": "Détails",
  "m_open_folder": "Ouvrir le dossier de l'exe",
  "credit": "ProKill v{v} — développé par {a}",
  "tt_credit": "Clique pour ouvrir la page de {a}.\nClic droit : vérifier les mises à jour.",
  "status_count": "{shown} process affichés / {total} au total",
  "status_flat": "   |   ⚠ filtre actif : vue à plat",
  "status_killed": "{n} process tué(s)",
  "status_watch": "Surveillance : {names} (re-kill auto si réapparition)",
  "status_watchdog": "Watchdog : re-tué {names}",
  "status_startup_on": "Lancement au démarrage : activé",
  "status_startup_off": "Lancement au démarrage : désactivé",
  "startup_fail_title": "Démarrage",
  "startup_fail": "Impossible de modifier le démarrage automatique.",
  "confirm_title": "Confirmation",
  "confirm_kill_filter": "Tuer de force les {n} process actuellement affichés ?",
  "result_title": "Résultat",
  "result_body": "{ok}/{total} tués.\n\nÉchecs :\n{errs}",
  "access_denied": "accès refusé (relance ProKill en admin)",
  "info_title": "Info",
  "path_unknown": "Chemin inconnu pour ce process.",
  "proc_gone": "Ce process n'existe plus.",
  "wl_title": "Process surveillés",
  "wl_desc": "Ces process sont re-tués automatiquement dès qu'ils réapparaissent :",
  "wl_remove": "Retirer la sélection", "wl_clear": "Tout vider",
  "d_title": "Détails - PID {pid}",
  "d_pid": "PID", "d_name": "Nom", "d_status": "Statut", "d_started": "Démarré",
  "d_exe": "Exe", "d_cwd": "Dossier de travail", "d_parent": "Parent",
  "d_cmdline": "Ligne de commande :", "d_conns": "Connexions réseau :",
  "d_files": "Fichiers ouverts :",
  "d_none_f": "  (aucune ou accès refusé)", "d_none_m": "  (aucun ou accès refusé)",
  "d_denied": "(accès refusé)", "d_no_parent": "(aucun)", "d_unknown": "(inconnu)",
  "upd_title": "Mise à jour",
  "upd_avail_title": "Mise à jour disponible",
  "upd_avail": "Une nouvelle version de ProKill est dispo !\n\nTa version : {cur}\nDernière version : {new}\n\nOuvrir la page de téléchargement ?",
  "upd_ok": "Tu as déjà la dernière version ({v}).",
  "upd_fail": "Impossible de vérifier les mises à jour\n(pas de connexion ou fichier de version introuvable).",
  "help_title": "ProKill - Comment ça marche",
  "help_text": """\
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
- Langue : le bouton 🌐 en haut à droite bascule entre français et
  anglais. Ton choix est mémorisé.
""",
 },
 "en": {
  "ready": "Ready",
  "autorefresh": "Auto-refresh",
  "tt_autorefresh": "Automatically refreshes the list every 3 seconds.",
  "sys_procs": "System processes",
  "tt_sys": "Show or hide Windows processes (SYSTEM, services...).\nUntick to only see YOUR programs.",
  "tree_view": "Tree view",
  "tt_tree": "Shows processes as a parent > children hierarchy.\n(Falls back to a flat list while a filter is active.)",
  "startup": "Run at startup",
  "tt_startup": "Starts ProKill automatically when Windows boots.\nEssential if you use watching: the watchlist is saved and resumed on every launch.",
  "help_btn": "❔ Help",
  "tt_help": "Explains what the app does and what every button is for.",
  "refresh_btn": "⟳ Refresh",
  "tt_refresh": "Reloads the process list immediately.",
  "tt_lang": "Basculer l'interface en français",
  "tt_search": "Filters the list. Searches the NAME, the exe PATH, the PID and the user.\nExample: type \"epic\" to find every Epic Games process, even oddly named ones.",
  "tt_clear": "Clears the filter.",
  "col_pid": "PID", "col_name": "Name", "col_user": "User",
  "col_cpu": "CPU %", "col_mem": "RAM (MB)", "col_path": "Exe path",
  "kill_soft": "Kill (graceful)",
  "tt_kill_soft": "Politely asks the process to close (like clicking the window's X).\nIf it doesn't respond within 3 s, it gets force-killed automatically.",
  "kill_force": "☠ FORCE kill",
  "tt_kill_force": "Kills the process immediately, no questions asked.\nFor completely frozen programs. Shortcut: Delete key.",
  "kill_tree": "Kill the TREE",
  "tt_kill_tree": "Kills the selected process AND all its children (sub-processes).\nPerfect for launchers that spawn several processes.",
  "kill_filter": "Kill whole filter",
  "tt_kill_filter": "Force-kills ALL currently displayed processes.\nExample: filter \"epic\" then this button = all of Epic is gone. Confirmation asked.",
  "watch": "👁 Watch",
  "tt_watch": "Adds the process to the watchlist: if it reappears, it gets RE-KILLED automatically.\nUseful against programs that restart on their own.",
  "watch_count": "Watchlist ({n})",
  "tt_watchlist": "Shows and manages the list of watched processes.",
  "open_folder": "📁 Open folder",
  "tt_open_folder": "Opens Explorer at the location of the selected process's .exe file.\nHandy to identify an unknown process.",
  "m_kill_soft": "Kill (graceful)", "m_kill_force": "Force kill",
  "m_kill_tree": "Kill whole tree", "m_watch": "Watch this process",
  "m_filter_name": "Filter on this name", "m_details": "Details",
  "m_open_folder": "Open exe folder",
  "credit": "ProKill v{v} — developed by {a}",
  "tt_credit": "Click to open {a}'s page.\nRight-click: check for updates.",
  "status_count": "{shown} processes shown / {total} total",
  "status_flat": "   |   ⚠ filter active: flat view",
  "status_killed": "{n} process(es) killed",
  "status_watch": "Watching: {names} (auto re-kill on reappearance)",
  "status_watchdog": "Watchdog: re-killed {names}",
  "status_startup_on": "Run at startup: enabled",
  "status_startup_off": "Run at startup: disabled",
  "startup_fail_title": "Startup",
  "startup_fail": "Could not change the startup setting.",
  "confirm_title": "Confirmation",
  "confirm_kill_filter": "Force-kill the {n} currently displayed processes?",
  "result_title": "Result",
  "result_body": "{ok}/{total} killed.\n\nFailures:\n{errs}",
  "access_denied": "access denied (run ProKill as admin)",
  "info_title": "Info",
  "path_unknown": "Unknown path for this process.",
  "proc_gone": "This process no longer exists.",
  "wl_title": "Watched processes",
  "wl_desc": "These processes are automatically re-killed as soon as they reappear:",
  "wl_remove": "Remove selected", "wl_clear": "Clear all",
  "d_title": "Details - PID {pid}",
  "d_pid": "PID", "d_name": "Name", "d_status": "Status", "d_started": "Started",
  "d_exe": "Exe", "d_cwd": "Working directory", "d_parent": "Parent",
  "d_cmdline": "Command line:", "d_conns": "Network connections:",
  "d_files": "Open files:",
  "d_none_f": "  (none or access denied)", "d_none_m": "  (none or access denied)",
  "d_denied": "(access denied)", "d_no_parent": "(none)", "d_unknown": "(unknown)",
  "upd_title": "Update",
  "upd_avail_title": "Update available",
  "upd_avail": "A new version of ProKill is available!\n\nYour version: {cur}\nLatest version: {new}\n\nOpen the download page?",
  "upd_ok": "You already have the latest version ({v}).",
  "upd_fail": "Could not check for updates\n(no connection or version file not found).",
  "help_title": "ProKill - How it works",
  "help_text": """\
PROKILL - WHAT IS IT?
ProKill lists ALL the processes running on your PC and lets you close
them, including the ones Task Manager hides or fails to close.
Typically: a game that crashed, a launcher leaving sub-processes running
in the background, a program that refuses to die.

THE FILTER (top bar)
Type anything: a name, part of a path, a PID, a user.
Example: type "epic" and you'll see EVERY process whose .exe file lives
in an Epic Games folder, even the ones with obscure names like
EOSOverlayRenderer.exe. That's ProKill's superpower: it also searches
the program's PATH, not just its name.

THE BUTTONS
- Kill (graceful): politely asks the process to close (like clicking
  the X). If it doesn't respond within 3 seconds, ProKill force-kills
  it automatically. Use this first.
- FORCE kill: immediate termination, no questions asked. For completely
  frozen programs. Shortcut: Delete key.
- Kill the TREE: kills the selected process AND all its children
  (sub-processes). Perfect for launchers that spawn 4-5 processes.
- Kill whole filter: force-kills EVERYTHING currently displayed.
  Type "epic", click, all of Epic is gone. A confirmation is asked.
- Watch: adds the process to the watchlist. If a process with the same
  name reappears, it gets re-killed automatically every 2 seconds.
  Handy against programs that restart on their own.
  Click "Watchlist (n)" to view/clear the list.
- Open folder: opens Explorer at the exact location of the process's
  .exe file. Useful to identify an unknown one.

THE LIST
- Click a column header: sorts the list.
- Double-click a process: details window (command line, network
  connections, open files, parent process).
- Right-click: quick menu with the same actions.
- Tree view: shows processes hierarchically (parent > children).
  Note: while a filter is active, the display falls back to a flat list.
- System processes: untick to hide Windows processes and only see YOUR
  programs.

GOOD TO KNOW
- "Access denied" = the process is protected. Restart ProKill as
  administrator (right-click > Run as administrator).
- Killing a Windows system process can crash the PC. When in doubt,
  don't touch anything running as SYSTEM.
- Run at startup: tick this box so ProKill launches by itself when
  Windows starts. The watchlist is saved: your watched processes get
  re-killed from boot without you having to think about it.
- Updates: ProKill checks at launch whether a new version is available
  and tells you. Right-click "developed by ..." at the bottom right to
  check manually.
- Language: the 🌐 button at the top right switches between French and
  English. Your choice is remembered.
""",
 },
}


def detect_lang():
    cfg = load_config()
    if cfg.get("lang") in LANGS:
        return cfg["lang"]
    if sys.platform == "win32":
        try:
            import ctypes
            lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lid & 0x3FF == 0x0C:      # 0x0C = français
                return "fr"
        except Exception:
            pass
    else:
        try:
            import locale
            if (locale.getlocale()[0] or "").lower().startswith("fr"):
                return "fr"
        except Exception:
            pass
    return "en"


LANG = detect_lang()


def t(key, **kw):
    s = LANGS.get(LANG, {}).get(key) or LANGS["en"].get(key, key)
    return s.format(**kw) if kw else s


def set_lang(lang):
    global LANG
    LANG = lang
    cfg = load_config()
    cfg["lang"] = lang
    save_config(cfg)


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


def resource_path(name):
    """Chemin d'une ressource, compatible PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


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
            for attr in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass


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
        self._watchlist = set()      # substrings surveillés (lowercase)
        self._watch_lock = threading.Lock()
        cfg = load_config()
        self._watchlist = set(cfg.get("watchlist", []))

        self._style()
        self._build_ui()
        self._update_watch_btn()
        setup_window(self)
        self.refresh(full=True)
        self.after(REFRESH_MS, self._tick)
        self.after(WATCHDOG_MS, self._watchdog_tick)
        # vérification silencieuse au démarrage (ne dérange que si MàJ dispo)
        self.after(1500, lambda: self.check_updates(silent=True))

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
        Tooltip(entry, t("tt_search"))

        b = ttk.Button(top, text="✕", width=3, style="Soft.TButton",
                       command=lambda: self.search_var.set(""))
        b.pack(side="left")
        Tooltip(b, t("tt_clear"))

        self._auto_refresh = tk.BooleanVar(value=True)
        cb = ttk.Checkbutton(top, text=t("autorefresh"),
                             variable=self._auto_refresh)
        cb.pack(side="left", padx=(14, 4))
        Tooltip(cb, t("tt_autorefresh"))

        self._show_system = tk.BooleanVar(value=True)
        cb2 = ttk.Checkbutton(top, text=t("sys_procs"),
                              variable=self._show_system,
                              command=self._apply_filter)
        cb2.pack(side="left", padx=4)
        Tooltip(cb2, t("tt_sys"))

        self._tree_mode = tk.BooleanVar(value=False)
        cb3 = ttk.Checkbutton(top, text=t("tree_view"),
                              variable=self._tree_mode,
                              command=self._apply_filter)
        cb3.pack(side="left", padx=4)
        Tooltip(cb3, t("tt_tree"))

        self._startup_var = tk.BooleanVar(value=is_startup_enabled())
        cb4 = ttk.Checkbutton(top, text=t("startup"),
                              variable=self._startup_var,
                              command=self._toggle_startup)
        cb4.pack(side="left", padx=4)
        Tooltip(cb4, t("tt_startup"))

        hb = ttk.Button(top, text=t("help_btn"), style="Blue.TButton",
                        command=self.show_help)
        hb.pack(side="right")
        Tooltip(hb, t("tt_help"))

        lb = ttk.Button(top, text="🌐 EN" if LANG == "fr" else "🌐 FR",
                        style="Soft.TButton", command=self._switch_lang)
        lb.pack(side="right", padx=6)
        Tooltip(lb, t("tt_lang"))

        rb = ttk.Button(top, text=t("refresh_btn"), style="Soft.TButton",
                        command=lambda: self.refresh(full=True))
        rb.pack(side="right")
        Tooltip(rb, t("tt_refresh"))

        # Tableau
        cols = ("pid", "name", "user", "cpu", "mem", "path")
        self.tree = ttk.Treeview(self, columns=cols, show="tree headings",
                                 selectmode="extended")
        headers = {"pid": (t("col_pid"), 70), "name": (t("col_name"), 190),
                   "user": (t("col_user"), 130), "cpu": (t("col_cpu"), 65),
                   "mem": (t("col_mem"), 85), "path": (t("col_path"), 470)}
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

        b1 = ttk.Button(bottom, text=t("kill_soft"), style="Soft.TButton",
                        command=lambda: self.kill_selected(force=False))
        b1.pack(side="left")
        Tooltip(b1, t("tt_kill_soft"))

        b2 = ttk.Button(bottom, text=t("kill_force"), style="Kill.TButton",
                        command=lambda: self.kill_selected(force=True))
        b2.pack(side="left", padx=6)
        Tooltip(b2, t("tt_kill_force"))

        b3 = ttk.Button(bottom, text=t("kill_tree"), style="Kill.TButton",
                        command=self.kill_tree_selected)
        b3.pack(side="left")
        Tooltip(b3, t("tt_kill_tree"))

        b4 = ttk.Button(bottom, text=t("kill_filter"), style="Kill.TButton",
                        command=self.kill_all_filtered)
        b4.pack(side="left", padx=6)
        Tooltip(b4, t("tt_kill_filter"))

        b5 = ttk.Button(bottom, text=t("watch"), style="Green.TButton",
                        command=self.watch_selected)
        b5.pack(side="left")
        Tooltip(b5, t("tt_watch"))

        self.watch_btn = ttk.Button(bottom, text=t("watch_count", n=0),
                                    style="Soft.TButton",
                                    command=self.show_watchlist)
        self.watch_btn.pack(side="left", padx=6)
        Tooltip(self.watch_btn, t("tt_watchlist"))

        b6 = ttk.Button(bottom, text=t("open_folder"), style="Soft.TButton",
                        command=self.open_folder)
        b6.pack(side="right")
        Tooltip(b6, t("tt_open_folder"))

        self.status = tk.StringVar(value=t("ready"))
        statusbar = ttk.Frame(self)
        statusbar.pack(fill="x")
        ttk.Label(statusbar, textvariable=self.status, style="Dim.TLabel",
                  padding=(10, 3)).pack(side="left")
        credit = ttk.Label(statusbar,
                           text=t("credit", v=APP_VERSION, a=AUTHOR),
                           style="Dim.TLabel", padding=(10, 3), cursor="hand2")
        credit.pack(side="right")
        credit.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))
        Tooltip(credit, t("tt_credit", a=AUTHOR))
        credit.bind("<Button-3>",
                    lambda e: self.check_updates(silent=False))

        # Menu clic droit
        self.menu = tk.Menu(self, tearoff=0, bg=BG3, fg=FG,
                            activebackground="#44464f", activeforeground="#fff")
        self.menu.add_command(label=t("m_kill_soft"),
                              command=lambda: self.kill_selected(force=False))
        self.menu.add_command(label=t("m_kill_force"),
                              command=lambda: self.kill_selected(force=True))
        self.menu.add_command(label=t("m_kill_tree"),
                              command=self.kill_tree_selected)
        self.menu.add_separator()
        self.menu.add_command(label=t("m_watch"), command=self.watch_selected)
        self.menu.add_command(label=t("m_filter_name"),
                              command=self._filter_on_name)
        self.menu.add_command(label=t("m_details"), command=self.show_details)
        self.menu.add_command(label=t("m_open_folder"), command=self.open_folder)
        self.tree.bind("<Button-3>", self._popup)
        self.tree.bind("<Delete>", lambda e: self.kill_selected(force=True))
        self.tree.bind("<Double-1>", lambda e: self.show_details())

    def _switch_lang(self):
        set_lang("en" if LANG == "fr" else "fr")
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        self._update_watch_btn()
        self._apply_filter()

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

        self.status.set(t("status_count", shown=len(rows),
                          total=len(self._all_procs))
                        + (t("status_flat")
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
            return str(pid), t("access_denied")
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
        if not messagebox.askyesno(t("confirm_title"),
                                   t("confirm_kill_filter", n=len(rows))):
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
                t("result_title"),
                t("result_body", ok=total - len(errs), total=total,
                  errs="\n".join(errs[:15])))
        else:
            self.status.set(t("status_killed", n=total))

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
            messagebox.showwarning(t("startup_fail_title"), t("startup_fail"))
        else:
            self.status.set(t("status_startup_on") if want
                            else t("status_startup_off"))

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
            self.status.set(t("status_watch", names=", ".join(added)))

    def _update_watch_btn(self):
        with self._watch_lock:
            n = len(self._watchlist)
        self.watch_btn.configure(text=t("watch_count", n=n))

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
                        t("status_watchdog",
                          names=", ".join(sorted(set(killed))))))
            threading.Thread(target=worker, daemon=True).start()
        self.after(WATCHDOG_MS, self._watchdog_tick)

    def show_watchlist(self):
        win = tk.Toplevel(self)
        win.title(t("wl_title"))
        win.configure(bg=BG)
        win.geometry("420x320")
        setup_window(win)
        ttk.Label(win, text=t("wl_desc"), wraplength=390,
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
        ttk.Button(fr, text=t("wl_remove"), style="Soft.TButton",
                   command=remove).pack(side="left")
        ttk.Button(fr, text=t("wl_clear"), style="Kill.TButton",
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
                started = time.strftime("%d/%m/%Y %H:%M:%S",
                                        time.localtime(p.create_time()))
                lines = [f'{t("d_pid")} : {p.pid}',
                         f'{t("d_name")} : {p.name()}',
                         f'{t("d_status")} : {p.status()}',
                         f'{t("d_started")} : {started}',
                         f'{t("d_exe")} : {self._safe(p.exe) or t("d_denied")}',
                         f'{t("d_cwd")} : {self._safe(p.cwd) or t("d_denied")}',
                         f'{t("d_parent")} : {self._parent_str(p)}',
                         "",
                         t("d_cmdline"),
                         "  " + " ".join(self._safe(p.cmdline)
                                         or [t("d_denied")]),
                         ""]
                conns = self._safe(p.net_connections) \
                    if hasattr(p, "net_connections") \
                    else self._safe(p.connections)
                lines.append(t("d_conns"))
                if conns:
                    for c in conns[:25]:
                        l = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "?"
                        r = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
                        lines.append(f"  {c.status:<12} {l}  ->  {r}")
                else:
                    lines.append(t("d_none_f"))
                lines.append("")
                files = self._safe(p.open_files)
                lines.append(t("d_files"))
                if files:
                    for f in files[:40]:
                        lines.append(f"  {f.path}")
                else:
                    lines.append(t("d_none_m"))
        except psutil.NoSuchProcess:
            messagebox.showinfo(t("info_title"), t("proc_gone"))
            return

        win = tk.Toplevel(self)
        win.title(t("d_title", pid=pid))
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
            return f"{pp.name()} (PID {pp.pid})" if pp else t("d_no_parent")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return t("d_unknown")

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
                    raise ValueError("no version")
                def as_tuple(v):
                    return tuple(int(x) for x in v.split(".") if x.isdigit())
                if as_tuple(latest) > as_tuple(APP_VERSION):
                    def ask():
                        if messagebox.askyesno(
                                t("upd_avail_title"),
                                t("upd_avail", cur=APP_VERSION, new=latest)):
                            webbrowser.open(url)
                    self.after(0, ask)
                elif not silent:
                    self.after(0, lambda: messagebox.showinfo(
                        t("upd_title"), t("upd_ok", v=APP_VERSION)))
            except Exception:
                if not silent:
                    self.after(0, lambda: messagebox.showinfo(
                        t("upd_title"), t("upd_fail")))
        threading.Thread(target=worker, daemon=True).start()

    def open_folder(self):
        sel = self.tree.selection()
        if not sel:
            return
        path = self.tree.item(sel[0], "values")[5]
        if path and os.path.exists(path):
            os.startfile(os.path.dirname(path))
        else:
            messagebox.showinfo(t("info_title"), t("path_unknown"))

    def show_help(self):
        win = tk.Toplevel(self)
        win.title(t("help_title"))
        win.configure(bg=BG)
        win.geometry("720x600")
        setup_window(win)
        txt = tk.Text(win, bg=BG2, fg=FG, relief="flat", wrap="word",
                      font=("Segoe UI", 10), padx=14, pady=12)
        sb = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", pady=8)
        txt.pack(fill="both", expand=True, padx=(8, 0), pady=8)
        txt.insert("1.0", t("help_text"))
        txt.configure(state="disabled")


if __name__ == "__main__":
    ProKill().mainloop()