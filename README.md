# ⚡ Neural Game Fixer

Application desktop (Python + CustomTkinter, thème cyberpunk) pour aider les joueurs à
résoudre les bugs de leurs jeux Steam.

## Fonctionnalités

- Détection automatique des jeux Steam (registre + `libraryfolders.vdf`), Epic Games Store et Battle.net installés
- Croisement avec une base de bugs connus et leurs solutions (`bugs_data.json`)
- Réparation via la vérification d'intégrité des fichiers Steam (`steam://validate`) ou instructions manuelles pour Epic/Battle.net
- Onglet communautaire : ajouter, rechercher, modifier ou supprimer une entrée de la base
- Export/import de la base au format JSON, et synchronisation directe depuis GitHub
- Icône et interface personnalisées (thème cyberpunk)

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Construire l'exécutable Windows (.exe)

```bash
build.bat
```

L'exécutable est généré dans `dist\NeuralGameFixer.exe`, accompagné de sa base de bugs et de son icône.

## Structure

- `main.py` — code de l'application
- `bugs_data.json` — base de données des bugs connus (jeu → id Steam, bug, solution)
- `build.bat` — script de génération de l'exécutable Windows
- `icon.ico` — icône de l'application et de l'exécutable
