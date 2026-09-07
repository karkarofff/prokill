<p align="center">
  <img src="prokill_logo.png" width="140" alt="Logo ProKill">
</p>

<h1 align="center">ProKill</h1>

<p align="center">
  Un tueur de processus pour Windows, plus puissant et plus précis que le Gestionnaire des tâches.
</p>

<p align="center">
  🇬🇧 <a href="README.md">English version</a>
</p>

---

## C'est quoi ?

On a tous connu ça : un jeu qui a planté mais tourne encore en arrière-plan, un launcher qui laisse traîner cinq sous-processus invisibles, un logiciel qui refuse de se fermer. Le Gestionnaire des tâches de Windows ne montre pas tout, et sa recherche est limitée au nom du processus.

**ProKill** liste TOUS les processus de la machine et permet de les fermer, proprement ou de force, avec un vrai moteur de recherche.

## Fonctionnalités

- **Filtre intelligent** : cherche dans le nom, mais aussi dans le **chemin complet de l'exe**, le PID et l'utilisateur. Tapez `epic` et vous trouvez tous les processus d'Epic Games, même ceux au nom obscur comme `EOSOverlayRenderer.exe`.
- **Tuer (propre)** : demande au processus de se fermer, et escalade automatiquement en kill de force s'il ne répond pas sous 3 secondes.
- **Tuer de force** : extermination immédiate (touche Suppr).
- **Tuer l'arbre** : le processus ET tous ses sous-processus d'un coup.
- **Tuer tout le filtre** : filtrez `epic`, un clic, tout Epic dégage.
- **Surveillance** : un processus surveillé est re-tué automatiquement dès qu'il réapparaît. La liste est sauvegardée entre les sessions.
- **Lancement au démarrage de Windows** (optionnel, une case à cocher) : combiné à la surveillance, les processus indésirables sont éliminés dès le boot, sans y penser.
- **Détails d'un processus** (double-clic) : ligne de commande, connexions réseau, fichiers ouverts, processus parent.
- **Vue arbre** parent > enfants, tri par colonne, sélection multiple.
- **Ouvrir le dossier de l'exe** pour identifier un processus inconnu.
- **Mises à jour** : ProKill vous prévient au lancement quand une nouvelle version est disponible.
- **Interface bilingue** français / anglais : langue détectée automatiquement depuis Windows, bouton 🌐 pour basculer, choix mémorisé.
- Interface sombre, aide intégrée (bouton ❔), info-bulles sur chaque bouton.

## Installation

### Utilisateur (recommandé)

Téléchargez `ProKill.exe` depuis la page [Releases](../../releases) et lancez-le. C'est tout, rien à installer.

> **Note SmartScreen** : au premier lancement, Windows peut afficher un avertissement (exécutable non signé, c'est normal pour un petit projet indépendant). Cliquez sur *Informations complémentaires* puis *Exécuter quand même*. Le code source est entièrement lisible dans ce dépôt.

> **Astuce** : lancez ProKill en tant qu'administrateur pour pouvoir tuer les processus protégés.

### Depuis les sources

```
pip install psutil
python prokill_v2.py
```

### Compiler soi-même l'exe

```
pip install pyinstaller psutil
pyinstaller --onefile --noconsole --icon prokill.ico --add-data "prokill.ico;." --name ProKill prokill_v2.py
```

L'exécutable est généré dans `dist/`.

## Captures d'écran

<img width="1138" height="703" alt="Interface de ProKill" src="https://github.com/user-attachments/assets/192816af-66e1-43fb-b8d7-fdbc9f66f65d" />

## Prérequis

- Windows 10 / 11
- Rien d'autre pour l'exe. Python 3.10+ et `psutil` pour la version source.

## Avertissement

Tuer un processus système de Windows (utilisateur SYSTEM) peut rendre la machine instable. ProKill vous donne le pouvoir, à vous de ne pas tirer sur l'ambulance.

## Licence

MIT — faites-en ce que vous voulez, une mention est appréciée.

---

<p align="center">
  Développé par <a href="https://github.com/karkarofff">Karkarofff</a>
</p>
