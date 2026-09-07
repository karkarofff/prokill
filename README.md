<p align="center">
  <img src="prokill_logo.png" width="140" alt="ProKill logo">
</p>

<h1 align="center">ProKill</h1>

<p align="center">
  A process killer for Windows — more powerful and more precise than Task Manager.
</p>

<p align="center">
  🇫🇷 <a href="README.fr.md">Version française</a>
</p>

---

## What is it?

We've all been there: a game that crashed but is still running in the background, a launcher leaving five invisible sub-processes behind, a program that refuses to close. Windows Task Manager doesn't show everything, and its search only looks at the process name.

**ProKill** lists ALL the processes on your machine and lets you close them, gracefully or by force, with a proper search engine.

## Features

- **Smart filter**: searches the name, but also the **full exe path**, the PID and the user. Type `epic` and you'll find every Epic Games process, even the obscurely named ones like `EOSOverlayRenderer.exe`.
- **Kill (graceful)**: asks the process to close, and automatically escalates to a force kill if it doesn't respond within 3 seconds.
- **Force kill**: immediate termination (Delete key).
- **Kill the tree**: the process AND all its sub-processes at once.
- **Kill whole filter**: filter `epic`, one click, all of Epic is gone.
- **Watchlist**: a watched process gets re-killed automatically as soon as it reappears. The list is saved between sessions.
- **Run at Windows startup** (optional, one checkbox): combined with the watchlist, unwanted processes are eliminated from boot, without thinking about it.
- **Process details** (double-click): command line, network connections, open files, parent process.
- **Tree view** parent > children, column sorting, multi-select.
- **Open the exe's folder** to identify an unknown process.
- **Updates**: ProKill tells you at launch when a new version is available.
- **Bilingual interface** English / French: language auto-detected from Windows, 🌐 button to switch, choice remembered.
- Dark UI, built-in help (❔ button), tooltips on every button.

## Installation

### Regular users (recommended)

Download `ProKill.exe` from the [Releases](../../releases) page and run it. That's it, nothing to install.

> **SmartScreen note**: on first launch, Windows may show a warning (unsigned executable, which is normal for a small independent project). Click *More info* then *Run anyway*. The full source code is readable in this repository.

> **Tip**: run ProKill as administrator to be able to kill protected processes.

### From source

```
pip install psutil
python prokill_v2.py
```

### Build the exe yourself

```
pip install pyinstaller psutil
pyinstaller --onefile --noconsole --icon prokill.ico --add-data "prokill.ico;." --name ProKill prokill_v2.py
```

The executable is generated in `dist/`.

## Screenshots

<img width="1138" height="703" alt="ProKill interface" src="https://github.com/user-attachments/assets/192816af-66e1-43fb-b8d7-fdbc9f66f65d" />

## Requirements

- Windows 10 / 11
- Nothing else for the exe. Python 3.10+ and `psutil` for the source version.

## Warning

Killing a Windows system process (SYSTEM user) can make the machine unstable. ProKill gives you the power; try not to shoot the ambulance.

## License

MIT — do whatever you want with it, a mention is appreciated.

---

<p align="center">
  Developed by <a href="https://github.com/karkarofff">Karkarofff</a>
</p>
