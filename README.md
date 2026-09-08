# ⚡ Neural Game Fixer

Application desktop (Python + CustomTkinter, thème cyberpunk) pour aider les joueurs à
résoudre les bugs de leurs jeux Steam.

## Fonctionnalités

- Détection automatique des jeux Steam installés (lecture des fichiers `.acf`, tous disques confondus)
- Croisement avec une base de bugs connus et leurs solutions (`bugs_data.json`)
- Réparation via la vérification d'intégrité des fichiers Steam (`steam://validate`)
- Onglet communautaire pour ajouter un jeu, un bug et sa solution à la base

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Structure

- `main.py` — code de l'application
- `bugs_data.json` — base de données des bugs connus (jeu → id Steam, bug, solution)
