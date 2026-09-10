import customtkinter as ctk
import os
import sys
import json
import re
import string
import webbrowser
import requests
import subprocess
import shutil
import ctypes
import datetime
from tkinter import filedialog, messagebox

try:
    import winreg  # Disponible uniquement sur Windows
except ImportError:
    winreg = None

ORANGE = "#ffaa00"
ROUGE = "#ff4444"

# Couleurs Cyberpunk
CYAN = "#00f3ff"
MAGENTA = "#ff00ff"
DARK_BG = "#0d0221"
GREEN = "#39ff14"

# Polices : Bahnschrift (fournie avec Windows) pour les titres/l'interface,
# Consolas (monospace) pour tout ce qui doit "avoir l'air d'un terminal"
FONT_TITRE_APP = ("Bahnschrift SemiBold", 20, "bold")
FONT_SOUS_TITRE = ("Bahnschrift", 11)
FONT_SECTION = ("Bahnschrift SemiBold", 16, "bold")

PLACEHOLDER_SOLUTION = "ÉCRIVEZ LA SOLUTION ICI..."

# ⚠️ À CONFIGURER : remplace par l'URL "raw" de ton bugs_data.json sur GitHub
# (sur GitHub : ouvre bugs_data.json > bouton "Raw" > copie l'URL)
URL_GITHUB_RAW = "https://raw.githubusercontent.com/Herumoru/Neural-Game-Fixer/main/bugs_data.json"


def chemin_base_donnees():
    """Retourne le chemin de bugs_data.json à côté du script OU de l'exécutable .exe,
    peu importe le dossier depuis lequel l'appli est lancée."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "bugs_data.json")


def chemin_icone():
    """Même logique que chemin_base_donnees(), pour trouver icon.ico à côté du script/exe."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "icon.ico")


CHEMIN_DB = chemin_base_donnees()
CHEMIN_ICONE = chemin_icone()


class GameFixerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Fenêtre principale
        self.title("⚡ NEURAL GAME FIXER ⚡")
        self.geometry("750x820")
        self.configure(fg_color=DARK_BG)

        try:
            self.iconbitmap(CHEMIN_ICONE)
        except Exception:
            pass  # Pas bloquant si l'icône est absente (ex: premier lancement sans le fichier)

        # FIX : évite un AttributeError si "Réparer" est cliqué avant tout scan
        self.jeu_detecte_actuel = None

        # Nom du jeu actuellement en cours de modification (None = mode ajout)
        self.jeu_en_edition = None

        # 0. Bandeau d'en-tête
        entete = ctk.CTkFrame(self, fg_color="#100228", corner_radius=0, height=64)
        entete.pack(fill="x", side="top")
        entete.pack_propagate(False)

        bloc_titre = ctk.CTkFrame(entete, fg_color="transparent")
        bloc_titre.pack(side="left", padx=20, pady=8)
        ctk.CTkLabel(bloc_titre, text="⚡ NEURAL GAME FIXER", font=FONT_TITRE_APP,
                    text_color=CYAN).pack(anchor="w")
        ctk.CTkLabel(bloc_titre, text="Détection & réparation · Steam · Epic · Battle.net",
                    font=FONT_SOUS_TITRE, text_color="#8a8aa0").pack(anchor="w")

        ctk.CTkFrame(self, fg_color=MAGENTA, height=2, corner_radius=0).pack(fill="x", side="top")

        # 1. Configuration des onglets
        self.tabs = ctk.CTkTabview(self,
                                   width=700,
                                   height=680,
                                   fg_color="#100228",
                                   segmented_button_fg_color="#0d0221",
                                   segmented_button_selected_color=CYAN,
                                   segmented_button_selected_hover_color="#00444d",
                                   border_width=2,
                                   border_color="#1e054d")
        self.tabs.pack(padx=20, pady=10)

        self.tab_scan = self.tabs.add("🔍 Scanner")
        self.tab_commu = self.tabs.add("🤝 Communauté")
        self.tab_diag = self.tabs.add("🩺 Diagnostic")

        # 2. Barre d'état flottante
        self.status_frame = ctk.CTkFrame(self, height=25, fg_color="transparent")
        self.status_frame.pack(side="bottom", fill="x", pady=5)

        self.lbl_status = ctk.CTkLabel(self.status_frame,
                                       text="● SYSTEM_READY",
                                       font=("Consolas", 10, "bold"),
                                       text_color="#00ff41")
        self.lbl_status.pack(side="left", padx=30)

        self.lbl_count = ctk.CTkLabel(self.status_frame,
                                      text="DB_ENTRIES: 0",
                                      font=("Consolas", 10),
                                      text_color="#666666")
        self.lbl_count.pack(side="right", padx=30)

        # 3. Lancement des interfaces
        self.setup_scan_tab()
        self.setup_community_tab()
        self.setup_diagnostic_tab()
        self.mettre_a_jour_compteur()
        self.rafraichir_liste_communaute()

    # ---------------------------------------------------------------
    # ONGLET SCANNER
    # ---------------------------------------------------------------

    def setup_scan_tab(self):
        """Onglet pour scanner et réparer"""
        ctk.CTkLabel(self.tab_scan, text="⚡ SYSTEM SCANNER ⚡", font=FONT_SECTION, text_color=CYAN).pack(pady=15)

        boutons_frame = ctk.CTkFrame(self.tab_scan, fg_color="transparent")
        boutons_frame.pack(pady=5)

        self.btn_scan = ctk.CTkButton(boutons_frame, text="LANCER L'ANALYSE", border_color=CYAN, border_width=2,
                                      fg_color="transparent", text_color=CYAN, hover_color="#062226",
                                      command=self.analyser_systeme)
        self.btn_scan.pack(side="left", padx=5)

        self.btn_auto_detect = ctk.CTkButton(boutons_frame, text="🔍 DÉTECTION RAPIDE", border_color=CYAN,
                                             border_width=2, fg_color="transparent", text_color=CYAN,
                                             hover_color="#062226", command=self.lancer_auto_detection)
        self.btn_auto_detect.pack(side="left", padx=5)

        self.progress_bar = ctk.CTkProgressBar(self.tab_scan, width=400, progress_color=CYAN, fg_color="#002226")
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        self.textbox = ctk.CTkTextbox(self.tab_scan, width=600, height=150, fg_color="black", text_color=GREEN,
                                      font=("Consolas", 12), border_color=CYAN, border_width=1)
        self.textbox.pack(pady=10)

        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.tab_scan,
            label_text="⚡ JEUX DÉTECTÉS",
            label_font=("Consolas", 13, "bold"),
            label_text_color=CYAN,
            label_fg_color="#0a0b10",
            fg_color="#0a0b10",
            corner_radius=10,
            border_width=1,
            border_color=CYAN,
            scrollbar_fg_color="#12131a",
            scrollbar_button_color="#ff0055",
            scrollbar_button_hover_color="#ff5599",
        )
        self.scrollable_frame.pack(pady=10, padx=15, fill="both", expand=True)

    def analyser_systeme(self):
        """Lance le scan complet, avec animation de la barre de progression"""
        self.textbox.delete("0.0", "end")
        self.textbox.insert("end", ">> INITIALISATION DU SCAN...\n")
        self.animer_barre(0)

    def animer_barre(self, valeur):
        if valeur <= 1.0:
            self.progress_bar.set(valeur)
            self.after(20, lambda: self.animer_barre(valeur + 0.02))
        else:
            self.executer_analyse_reelle()

    def executer_analyse_reelle(self):
        self.textbox.insert("end", ">> LECTURE DES BIBLIOTHÈQUES (STEAM + EPIC + BATTLE.NET)...\n")
        jeux_detectes = self.detecter_tous_les_jeux()

        if not jeux_detectes:
            self.textbox.insert("end", "[!] AUCUNE BIBLIOTHÈQUE / AUCUN JEU DÉTECTÉ.\n")
            return

        jeux_avec_infos = self.croiser_avec_base_de_donnees(jeux_detectes)
        nb_connus = sum(1 for j in jeux_avec_infos if j["infos"])
        self.textbox.insert("end", f">> {len(jeux_avec_infos)} JEU(X) DÉTECTÉ(S), {nb_connus} AVEC BUG CONNU.\n")
        self.afficher_jeux_detectes(jeux_avec_infos)

    def lancer_auto_detection(self):
        """Détection instantanée, sans animation (utilise la même logique que le scan complet)"""
        self.textbox.insert("end", "\n[ SYSTEM ] : Scan des launchers installés...\n")
        jeux_detectes = self.detecter_tous_les_jeux()
        jeux_avec_infos = self.croiser_avec_base_de_donnees(jeux_detectes)
        self.afficher_jeux_detectes(jeux_avec_infos)

    def afficher_jeux_detectes(self, jeux_avec_infos):
        """Peuple la liste déroulante avec, pour chaque jeu, son statut et un bouton d'action dédié.
        FIX : chaque jeu a maintenant son propre bouton (avant, seul le dernier jeu détecté
        était réparable via un bouton unique)."""
        for child in self.scrollable_frame.winfo_children():
            child.destroy()

        for jeu in jeux_avec_infos:
            nom, appid, infos = jeu["nom"], jeu["id"], jeu["infos"]
            plateforme = jeu.get("plateforme", "Steam")

            ligne = ctk.CTkFrame(self.scrollable_frame, fg_color="gray20")
            ligne.pack(pady=5, padx=5, fill="x")

            entete = ctk.CTkFrame(ligne, fg_color="transparent")
            entete.pack(fill="x")
            ctk.CTkLabel(entete, text=f"🎮 {nom[:30]}", font=("Consolas", 12, "bold")).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(entete, text=plateforme.upper(), font=("Consolas", 9, "bold"),
                        text_color="#888888").pack(side="left", padx=5)

            if infos:
                ctk.CTkLabel(entete, text="⚠ BUG CONNU", font=("Consolas", 10, "bold"), text_color=MAGENTA).pack(side="right", padx=10)
                ctk.CTkLabel(ligne, text=f"Symptôme : {infos.get('bug', 'N/A')}", font=("Consolas", 10),
                            text_color="#aaaaaa", wraplength=500, justify="left").pack(anchor="w", padx=15)
                ctk.CTkLabel(ligne, text=f"Solution : {infos.get('solution', 'N/A')}", font=("Consolas", 10),
                            text_color=GREEN, wraplength=500, justify="left").pack(anchor="w", padx=15, pady=(0, 5))
            else:
                ctk.CTkLabel(entete, text="Aucun bug connu", font=("Consolas", 10), text_color="#666666").pack(side="right", padx=10)

            boutons_action = ctk.CTkFrame(ligne, fg_color="transparent")
            boutons_action.pack(pady=(0, 8))

            if plateforme == "Steam" and appid:
                ctk.CTkButton(boutons_action, text="🔧 VÉRIFIER LES FICHIERS", width=190, fg_color=MAGENTA,
                             hover_color="#cc00cc",
                             command=lambda i=appid, n=nom: self.reparer_jeu_specifique(i, n)).pack(side="left", padx=3)
            elif plateforme == "Epic":
                ctk.CTkButton(boutons_action, text="🚀 OUVRIR EPIC LAUNCHER", width=190, fg_color=MAGENTA,
                             hover_color="#cc00cc",
                             command=lambda n=nom: self.ouvrir_epic_launcher(n)).pack(side="left", padx=3)
            else:
                ctk.CTkButton(boutons_action, text="ℹ️ COMMENT RÉPARER", width=190, fg_color="#444444",
                             hover_color="#5a5a5a",
                             command=lambda n=nom: self.afficher_instructions_manuelles(n)).pack(side="left", padx=3)

            ctk.CTkButton(boutons_action, text="🩺 ANALYSER LES CRASHS", width=190, fg_color="#1a1a3d",
                         border_color=CYAN, border_width=1, hover_color="#26264d",
                         command=lambda n=nom: self.analyser_crashs_jeu(n)).pack(side="left", padx=3)

    # ---------------------------------------------------------------
    # DÉTECTION STEAM (logique unifiée, avant dupliquée à deux endroits)
    # ---------------------------------------------------------------

    # ---------------------------------------------------------------
    # DIAGNOSTIC SYSTÈME (espace disque, RAM, pilote GPU, crashs)
    # ---------------------------------------------------------------

    def obtenir_espace_disque(self, lettre_disque):
        """Retourne (libre_go, total_go) pour un disque donné (ex: 'C:\\\\')."""
        try:
            total, _utilise, libre = shutil.disk_usage(lettre_disque)
            return round(libre / (1024 ** 3), 1), round(total / (1024 ** 3), 1)
        except OSError:
            return None, None

    def obtenir_ram(self):
        """RAM libre/totale via l'API Windows GlobalMemoryStatusEx (aucune dépendance
        externe). Retourne (None, None) si indisponible (ex: pas sous Windows)."""
        if not hasattr(ctypes, "windll"):
            return None, None

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        try:
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return round(stat.ullAvailPhys / (1024 ** 3), 1), round(stat.ullTotalPhys / (1024 ** 3), 1)
        except OSError:
            return None, None

    def obtenir_info_gpu(self):
        """⚠️ EXPÉRIMENTAL : liste les cartes graphiques et la date de leur pilote via
        PowerShell/WMI. Retourne une liste de (nom, date_lisible_ou_None)."""
        try:
            resultat = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-CimInstance Win32_VideoController | Select-Object Name,DriverDate | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10,
            )
            donnees = json.loads(resultat.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
            return []

        if isinstance(donnees, dict):
            donnees = [donnees]

        cartes = []
        for carte in donnees or []:
            nom = carte.get("Name") or "Carte graphique inconnue"
            date_lisible = None
            m = re.search(r"/Date\((\d+)", str(carte.get("DriverDate", "")))
            if m:
                try:
                    date_lisible = datetime.datetime.fromtimestamp(int(m.group(1)) / 1000)
                except (OSError, OverflowError, ValueError):
                    date_lisible = None
            cartes.append((nom, date_lisible))
        return cartes

    def lister_disques_a_verifier(self):
        """Le disque système + tous ceux qui hébergent une bibliothèque Steam détectée.
        FIX : dédoublonne en ignorant la casse — Windows ne fait pas la différence entre
        "C:\\" et "c:\\", mais une simple comparaison de texte si."""
        disques = []
        cles_vues = set()

        def ajouter(disque):
            cle = os.path.normcase(disque)
            if cle not in cles_vues:
                cles_vues.add(cle)
                disques.append(disque)

        ajouter(os.environ.get("SystemDrive", "C:") + "\\")
        for dossier in self.trouver_dossiers_steamapps():
            ajouter(os.path.splitdrive(dossier)[0] + "\\")

        return sorted(disques, key=str.lower)

    def ajouter_ligne_diagnostic(self, titre, statut, detail, couleur):
        """Affiche une ligne de résultat colorée (vert=OK, orange=attention, rouge=critique)."""
        ligne = ctk.CTkFrame(self.frame_diagnostic, fg_color="gray20")
        ligne.pack(pady=4, padx=5, fill="x")

        entete = ctk.CTkFrame(ligne, fg_color="transparent")
        entete.pack(fill="x")
        ctk.CTkLabel(entete, text=titre, font=("Consolas", 12, "bold")).pack(side="left", padx=10, pady=6)
        ctk.CTkLabel(entete, text=statut, font=("Consolas", 10, "bold"), text_color=couleur).pack(side="right", padx=10)

        if detail:
            ctk.CTkLabel(ligne, text=detail, font=("Consolas", 10), text_color="#aaaaaa",
                        wraplength=550, justify="left").pack(anchor="w", padx=15, pady=(0, 6))

    def lancer_diagnostic_systeme(self):
        """Vérifie l'espace disque, la RAM et l'âge du pilote GPU — les causes les plus
        courantes de plantages/ralentissements, tous jeux confondus."""
        for child in self.frame_diagnostic.winfo_children():
            child.destroy()

        # --- Espace disque ---
        for disque in self.lister_disques_a_verifier():
            libre, total = self.obtenir_espace_disque(disque)
            if libre is None:
                continue
            if libre < 10:
                statut, couleur = "CRITIQUE", ROUGE
            elif libre < 25:
                statut, couleur = "ATTENTION", ORANGE
            else:
                statut, couleur = "OK", GREEN
            self.ajouter_ligne_diagnostic(
                f"💾 Disque {disque}", statut, f"{libre} Go libres sur {total} Go", couleur,
            )

        # --- RAM ---
        libre_ram, total_ram = self.obtenir_ram()
        if total_ram is not None:
            if total_ram < 8:
                statut, couleur = "FAIBLE", ORANGE
                detail = f"{total_ram} Go au total ({libre_ram} Go libres) — 8 Go+ recommandés pour les jeux récents"
            else:
                statut, couleur = "OK", GREEN
                detail = f"{total_ram} Go au total, {libre_ram} Go libres actuellement"
            self.ajouter_ligne_diagnostic("🧠 Mémoire RAM", statut, detail, couleur)
        else:
            self.ajouter_ligne_diagnostic("🧠 Mémoire RAM", "N/A", "Impossible de lire la RAM sur ce système", "#666666")

        # --- GPU / pilote ---
        cartes = self.obtenir_info_gpu()
        if not cartes:
            self.ajouter_ligne_diagnostic("🖥 Carte graphique", "N/A",
                                          "Impossible de lire les infos GPU (nécessite PowerShell)", "#666666")
        else:
            for nom, date_pilote in cartes:
                if date_pilote is None:
                    self.ajouter_ligne_diagnostic(f"🖥 {nom}", "N/A", "Date du pilote inconnue", "#666666")
                    continue
                age_jours = (datetime.datetime.now() - date_pilote).days
                if age_jours > 365:
                    statut, couleur = "PILOTE ANCIEN", ORANGE
                else:
                    statut, couleur = "OK", GREEN
                self.ajouter_ligne_diagnostic(
                    f"🖥 {nom}", statut,
                    f"Pilote du {date_pilote.strftime('%d/%m/%Y')} ({age_jours} jours) — "
                    "un pilote très ancien est une cause fréquente de plantages/bugs graphiques",
                    couleur,
                )

    def setup_diagnostic_tab(self):
        """Onglet de diagnostic système général (indépendant d'un jeu précis)."""
        ctk.CTkLabel(self.tab_diag, text="🩺 DIAGNOSTIC SYSTÈME", font=FONT_SECTION, text_color=CYAN).pack(pady=15)
        ctk.CTkLabel(self.tab_diag,
                    text="Vérifie les causes les plus fréquentes de plantages/bugs, tous jeux confondus.",
                    font=FONT_SOUS_TITRE, text_color="#8a8aa0", wraplength=550).pack(pady=(0, 10))

        ctk.CTkButton(self.tab_diag, text="LANCER LE DIAGNOSTIC", border_color=CYAN, border_width=2,
                     fg_color="transparent", text_color=CYAN, hover_color="#062226",
                     command=self.lancer_diagnostic_systeme).pack(pady=5)

        self.frame_diagnostic = ctk.CTkScrollableFrame(
            self.tab_diag,
            label_text="RÉSULTATS",
            label_font=("Consolas", 12, "bold"),
            label_text_color=CYAN,
            label_fg_color="#0a0b10",
            fg_color="#0a0b10",
            corner_radius=10,
            border_width=1,
            border_color=CYAN,
        )
        self.frame_diagnostic.pack(pady=15, padx=15, fill="both", expand=True)

    def analyser_crashs_jeu(self, nom_jeu):
        """⚠️ EXPÉRIMENTAL : cherche des crashs récents ("Erreur d'application", Event ID
        1000) dans le Journal d'événements Windows mentionnant ce jeu. Ne nécessite pas
        de droits administrateur. Le format exact du texte peut varier selon la langue
        et la version de Windows — best effort, à valider en conditions réelles."""
        self.textbox.insert("end", f"\n[ DIAG ] : Recherche de crashs récents pour {nom_jeu}...\n")
        try:
            resultat = subprocess.run(
                ["wevtutil", "qe", "Application",
                 "/q:*[System[Provider[@Name='Application Error'] and (EventID=1000)]]",
                 "/c:150", "/rd:true", "/f:text"],
                capture_output=True, text=True, timeout=15,
            )
        except (OSError, subprocess.SubprocessError):
            self.textbox.insert("end", "[!] Impossible de lire le Journal d'événements Windows.\n")
            return

        sortie = resultat.stdout or ""
        blocs = [b for b in re.split(r"\n\s*\n", sortie) if b.strip()]
        trouvailles = [b for b in blocs if nom_jeu.lower() in b.lower()]

        if not trouvailles:
            self.textbox.insert(
                "end", f"[ OK ] : Aucun crash récent trouvé pour {nom_jeu} (150 dernières erreurs système passées en revue).\n"
            )
            return

        self.textbox.insert("end", f"[!] {len(trouvailles)} crash(s) récent(s) trouvé(s) mentionnant {nom_jeu} :\n")
        for bloc in trouvailles[:3]:
            premiere_ligne = bloc.strip().splitlines()[0]
            self.textbox.insert("end", f"    - {premiere_ligne}\n")
        self.textbox.insert(
            "end", "[ INFO ] : Détail complet dans l'Observateur d'événements Windows > Journaux Windows > Application.\n"
        )

    def trouver_chemin_steam(self):
        """Trouve le dossier d'installation de Steam via le registre Windows (méthode fiable,
        fonctionne quel que soit le disque ou le nom de dossier choisi à l'installation)."""
        if winreg is None:
            return None

        cles_a_essayer = (
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
        )
        for ruche, sous_cle, nom_valeur in cles_a_essayer:
            try:
                with winreg.OpenKey(ruche, sous_cle) as cle:
                    valeur, _ = winreg.QueryValueEx(cle, nom_valeur)
                    if valeur and os.path.exists(valeur):
                        return valeur
            except OSError:
                continue
        return None

    def trouver_dossiers_steamapps_via_config(self):
        """Lit la vraie configuration Steam (libraryfolders.vdf) pour lister TOUTES les
        bibliothèques déclarées, même sur un disque/dossier personnalisé.
        FIX : la bibliothèque principale peut être listée à la fois via le registre et via
        libraryfolders.vdf, parfois avec une casse ou des séparateurs différents (Windows
        étant insensible à la casse) — on normalise avant de comparer pour éviter les doublons."""
        chemin_steam = self.trouver_chemin_steam()
        if not chemin_steam:
            return []

        dossiers = []
        cles_vues = set()

        def ajouter(dossier):
            cle = os.path.normcase(os.path.normpath(dossier))
            if cle not in cles_vues:
                cles_vues.add(cle)
                dossiers.append(dossier)

        ajouter(os.path.join(chemin_steam, "steamapps"))

        fichier_vdf = os.path.join(chemin_steam, "steamapps", "libraryfolders.vdf")
        if os.path.exists(fichier_vdf):
            try:
                with open(fichier_vdf, "r", encoding="utf-8") as f:
                    contenu = f.read()
                for chemin_lib in re.findall(r'"path"\s+"([^"]+)"', contenu):
                    chemin_lib = chemin_lib.replace("\\\\", "\\")
                    ajouter(os.path.join(chemin_lib, "steamapps"))
            except OSError:
                pass

        return [d for d in dossiers if os.path.exists(d)]

    def trouver_dossiers_steamapps_par_balayage(self):
        """Méthode de secours : devine les emplacements en scannant chaque lettre de disque.
        Utilisée seulement si la lecture du registre/config Steam échoue."""
        dossiers = []
        for lettre in string.ascii_uppercase:
            base = f"{lettre}:\\"
            for sous_chemin in (
                os.path.join(base, "Program Files (x86)", "Steam", "steamapps"),
                os.path.join(base, "SteamLibrary", "steamapps"),
            ):
                if os.path.exists(sous_chemin):
                    dossiers.append(sous_chemin)
        return dossiers

    def trouver_dossiers_steamapps(self):
        """Retourne tous les dossiers 'steamapps' réels de Steam : d'abord via sa config
        (fiable), et seulement si ça échoue, via le balayage des disques (secours)."""
        dossiers = self.trouver_dossiers_steamapps_via_config()
        if dossiers:
            return dossiers
        return self.trouver_dossiers_steamapps_par_balayage()

    def detecter_tous_les_jeux_steam(self):
        """Lit les fichiers appmanifest*.acf pour lister tous les jeux réellement installés
        (plus fiable qu'un simple matching de noms de dossiers)."""
        jeux_trouves = []
        for steamapps in self.trouver_dossiers_steamapps():
            try:
                fichiers = os.listdir(steamapps)
            except (PermissionError, FileNotFoundError):
                continue
            for fichier in fichiers:
                if fichier.startswith("appmanifest") and fichier.endswith(".acf"):
                    chemin_complet = os.path.join(steamapps, fichier)
                    try:
                        with open(chemin_complet, "r", encoding="utf-8") as f:
                            contenu = f.read()
                        nom = re.search(r'"name"\s+"(.*?)"', contenu).group(1)
                        appid = re.search(r'"appid"\s+"(\d+)"', contenu).group(1)
                        jeux_trouves.append({"nom": nom, "id": appid, "plateforme": "Steam"})
                    except (AttributeError, OSError):
                        continue  # fichier .acf mal formé ou illisible
        return jeux_trouves

    def detecter_tous_les_jeux_epic(self):
        """Lit les manifestes (.item, au format JSON) d'Epic Games Launcher pour lister
        les jeux installés. Emplacement fixe, pas besoin de deviner un chemin."""
        dossier_manifests = os.path.join(
            os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
            "Epic", "EpicGamesLauncher", "Data", "Manifests",
        )
        jeux_trouves = []
        if not os.path.isdir(dossier_manifests):
            return jeux_trouves

        for fichier in os.listdir(dossier_manifests):
            if not fichier.endswith(".item"):
                continue
            chemin_complet = os.path.join(dossier_manifests, fichier)
            try:
                with open(chemin_complet, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                nom = manifest.get("DisplayName")
                if nom:
                    jeux_trouves.append({"nom": nom, "id": None, "plateforme": "Epic"})
            except (OSError, json.JSONDecodeError):
                continue  # fichier .item mal formé ou illisible
        return jeux_trouves

    # Dossiers trouvés dans product.db qui ne sont pas des jeux (le launcher lui-même, etc.)
    EXCLUS_BATTLENET = {"battle.net", "agent", "blizzard entertainment"}

    def detecter_tous_les_jeux_battlenet(self):
        """⚠️ EXPÉRIMENTAL : Battle.net n'a pas de format ouvert comme Steam/Epic. Ses jeux
        installés sont listés dans product.db, un fichier binaire (protobuf) sans schéma
        officiel. On extrait ici les chemins d'installation lisibles directement dans le
        fichier brut (comme la commande 'strings'), sans décoder le protobuf complet.
        Peut remonter du bruit ou rater des jeux selon la version de Battle.net."""
        chemin_db = os.path.join(
            os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
            "Battle.net", "Agent", "product.db",
        )
        jeux_trouves = []
        if not os.path.isfile(chemin_db):
            return jeux_trouves

        try:
            with open(chemin_db, "rb") as f:
                contenu_brut = f.read()
        except OSError:
            return jeux_trouves

        # Battle.net stocke ses chemins avec des slashs ("C:/Program Files/...") et non des
        # antislashs comme le reste de Windows. On cherche un chemin qui commence par une
        # lettre de disque, peu importe le séparateur utilisé.
        chemins_bruts = re.findall(rb"[A-Za-z]:[\\/][ -~]{2,}", contenu_brut)
        noms_vus = set()

        for chemin_bytes in chemins_bruts:
            chemin = chemin_bytes.decode("utf-8", errors="ignore")
            nom = os.path.basename(chemin.rstrip("/\\"))
            if not nom or len(nom) <= 2:
                continue
            if nom.lower() in self.EXCLUS_BATTLENET:
                continue
            if nom not in noms_vus:
                noms_vus.add(nom)
                jeux_trouves.append({"nom": nom, "id": None, "plateforme": "Battle.net"})

        return jeux_trouves

    def detecter_tous_les_jeux(self):
        """Combine la détection de tous les launchers supportés (Steam + Epic + Battle.net).
        FIX : dédoublonne par nom au cas où un même jeu remonterait deux fois (ex: chemin
        dupliqué dans product.db, bibliothèque Steam comptée deux fois)."""
        tous = (
            self.detecter_tous_les_jeux_steam()
            + self.detecter_tous_les_jeux_epic()
            + self.detecter_tous_les_jeux_battlenet()
        )

        cles_vues = set()
        resultat = []
        for jeu in tous:
            cle = jeu["nom"].strip().lower()
            if cle not in cles_vues:
                cles_vues.add(cle)
                resultat.append(jeu)
        return resultat

    def croiser_avec_base_de_donnees(self, jeux_detectes):
        """Associe à chaque jeu détecté sa fiche bug/solution si elle existe dans bugs_data.json."""
        data = self.charger_base_de_donnees()
        resultat = []
        for jeu in jeux_detectes:
            nom_reel = jeu["nom"].lower().strip()
            infos = None
            for nom_enregistre, fiche in data.items():
                cle = nom_enregistre.lower().strip()
                if cle in nom_reel or nom_reel in cle:
                    infos = fiche
                    break
            resultat.append({**jeu, "infos": infos})
        return resultat

    def reparer_jeu_specifique(self, steam_id, nom_jeu):
        """Lance la vérification d'intégrité Steam pour un jeu donné."""
        self.textbox.insert("end", f"\n[ FIX ] : Lancement du protocole pour {nom_jeu}...\n")
        if steam_id:
            webbrowser.open(f"steam://validate/{steam_id}")
            self.textbox.insert("end", "[ OK ] : Steam a ouvert la fenêtre de vérification.\n")
        else:
            self.textbox.insert("end", "[!] PAS D'ID STEAM TROUVÉ.\n")

    def ouvrir_epic_launcher(self, nom_jeu):
        """Epic ne propose pas d'équivalent à steam://validate/ : on ouvre le launcher
        et on indique la manip manuelle (Bibliothèque > ⋯ > Vérifier)."""
        self.textbox.insert("end", f"\n[ INFO ] : Ouverture d'Epic Games Launcher pour {nom_jeu}...\n")
        self.textbox.insert("end", "[ INFO ] : Dans Epic, clic sur les ⋯ du jeu > Vérifier.\n")
        webbrowser.open("com.epicgames.launcher://start")

    def afficher_instructions_manuelles(self, nom_jeu):
        """Pour les plateformes sans vérification automatisée fiable (Battle.net...) :
        on affiche la marche à suivre plutôt que de deviner une commande qui risquerait
        de ne pas fonctionner."""
        self.textbox.insert(
            "end",
            f"\n[ INFO ] : Pour {nom_jeu}, ouvre Battle.net > clique sur le jeu > "
            "roue crantée ⚙ > Analyse et réparation.\n",
        )



    # ---------------------------------------------------------------
    # ONGLET COMMUNAUTÉ
    # ---------------------------------------------------------------

    def setup_community_tab(self):
        """Interface de contribution + gestion (modifier/supprimer) de la base"""
        ctk.CTkLabel(self.tab_commu, text="--- AJOUTER / MODIFIER UN JEU ---",
                    font=FONT_SECTION, text_color=MAGENTA).pack(pady=(12, 8))

        style_champ = {"width": 400, "height": 36, "fg_color": "black", "border_color": "#301050"}

        self.ent_jeu = ctk.CTkEntry(self.tab_commu, placeholder_text="NOM DU DOSSIER (ex: Cyberpunk 2077)", **style_champ)
        self.ent_jeu.pack(pady=6)

        self.ent_id = ctk.CTkEntry(self.tab_commu, placeholder_text="ID STEAM DU JEU", **style_champ)
        self.ent_id.pack(pady=6)

        self.ent_bug = ctk.CTkEntry(self.tab_commu, placeholder_text="DESCRIPTION DU SYMPTÔME", **style_champ)
        self.ent_bug.pack(pady=6)

        self.txt_sol = ctk.CTkTextbox(self.tab_commu, width=400, height=70,
                                      fg_color="black", border_color="#301050", border_width=2)
        self.txt_sol.pack(pady=6)
        self.txt_sol.insert("0.0", PLACEHOLDER_SOLUTION)
        # FIX : le placeholder ne s'effaçait jamais et pouvait finir enregistré comme vraie solution
        self.txt_sol.bind("<FocusIn>", self._effacer_placeholder_solution)
        self.txt_sol.bind("<FocusOut>", self._restaurer_placeholder_solution)

        boutons_form = ctk.CTkFrame(self.tab_commu, fg_color="transparent")
        boutons_form.pack(pady=8)

        self.btn_save = ctk.CTkButton(boutons_form, text="VALIDER L'INJECTION",
                                      fg_color="transparent", border_color=MAGENTA, border_width=2,
                                      text_color=MAGENTA, hover_color="#2e002e",
                                      font=("Consolas", 14, "bold"),
                                      command=self.ajouter_bug_commu)
        self.btn_save.pack(side="left", padx=5)

        self.btn_annuler = ctk.CTkButton(boutons_form, text="✖ ANNULER", fg_color="#444444",
                                         hover_color="#5a5a5a", command=self.annuler_edition)
        # Caché tant qu'on n'édite pas une entrée existante

        # --- Partage manuel de la base (export/import JSON) ---
        boutons_partage = ctk.CTkFrame(self.tab_commu, fg_color="transparent")
        boutons_partage.pack(pady=(0, 8))

        ctk.CTkButton(boutons_partage, text="📤 EXPORTER LA BASE", fg_color="transparent",
                     border_color=CYAN, border_width=2, text_color=CYAN, hover_color="#062226",
                     command=self.exporter_base).pack(side="left", padx=5)

        ctk.CTkButton(boutons_partage, text="📥 IMPORTER UNE BASE", fg_color="transparent",
                     border_color=CYAN, border_width=2, text_color=CYAN, hover_color="#062226",
                     command=self.importer_base).pack(side="left", padx=5)

        ctk.CTkButton(boutons_partage, text="🔄 SYNC GITHUB", fg_color="transparent",
                     border_color=MAGENTA, border_width=2, text_color=MAGENTA, hover_color="#2e002e",
                     command=self.synchroniser_github).pack(side="left", padx=5)

        # --- Recherche + liste de la base actuelle ---
        self.ent_recherche = ctk.CTkEntry(self.tab_commu, placeholder_text="🔎 Rechercher un jeu dans la base...",
                                          width=400, height=32, fg_color="black", border_color=CYAN)
        self.ent_recherche.pack(pady=(10, 6))
        self.ent_recherche.bind("<KeyRelease>", lambda e: self.rafraichir_liste_communaute(self.ent_recherche.get()))

        self.scrollable_frame_commu = ctk.CTkScrollableFrame(
            self.tab_commu,
            label_text="📚 BASE ACTUELLE",
            label_font=("Consolas", 12, "bold"),
            label_text_color=CYAN,
            label_fg_color="#0a0b10",
            fg_color="#0a0b10",
            corner_radius=10,
            border_width=1,
            border_color=CYAN,
        )
        self.scrollable_frame_commu.pack(pady=(0, 10), padx=15, fill="both", expand=True)

    def _effacer_placeholder_solution(self, event=None):
        if self.txt_sol.get("0.0", "end").strip() == PLACEHOLDER_SOLUTION:
            self.txt_sol.delete("0.0", "end")

    def _restaurer_placeholder_solution(self, event=None):
        if not self.txt_sol.get("0.0", "end").strip():
            self.txt_sol.insert("0.0", PLACEHOLDER_SOLUTION)

    def ajouter_bug_commu(self):
        jeu = self.ent_jeu.get().strip()
        steam_id = self.ent_id.get().strip()
        bug = self.ent_bug.get().strip()
        sol = self.txt_sol.get("0.0", "end").strip()
        if sol == PLACEHOLDER_SOLUTION:
            sol = ""

        if not jeu:
            return  # On n'enregistre pas si le nom du jeu est vide

        try:
            data = self.charger_base_de_donnees()

            # Si on modifiait une entrée et que le nom a changé, on retire l'ancienne
            # clé pour ne pas laisser un doublon derrière soi
            if self.jeu_en_edition and self.jeu_en_edition != jeu:
                data.pop(self.jeu_en_edition, None)

            data[jeu] = {"id": steam_id, "bug": bug, "solution": sol}

            with open(CHEMIN_DB, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            message = "✅ MODIFIÉ" if self.jeu_en_edition else "✅ INJECTION RÉUSSIE"
            self.btn_save.configure(text=message, fg_color="green")
            self.after(2000, lambda: self.btn_save.configure(text="VALIDER L'INJECTION", fg_color=MAGENTA))

            self.annuler_edition()
            self.mettre_a_jour_compteur()
            self.rafraichir_liste_communaute(self.ent_recherche.get())

        except PermissionError:
            self.textbox.insert("end", "[!] ERREUR : Fermez le fichier bugs_data.json pour enregistrer.\n")

    def exporter_base(self):
        """Sauvegarde une copie de la base courante dans un fichier choisi par l'utilisateur,
        pour pouvoir la partager (mail, Discord, clé USB...)."""
        chemin = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichier JSON", "*.json")],
            initialfile="bugs_data_export.json",
            title="Exporter la base de bugs",
        )
        if not chemin:
            return  # L'utilisateur a annulé

        data = self.charger_base_de_donnees()
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        messagebox.showinfo("Export réussi", f"{len(data)} jeu(x) exporté(s) vers :\n{chemin}")

    def importer_base(self):
        """Fusionne une base externe (reçue d'un autre utilisateur) dans la base locale."""
        chemin = filedialog.askopenfilename(
            filetypes=[("Fichier JSON", "*.json")],
            title="Importer une base de bugs",
        )
        if not chemin:
            return

        try:
            with open(chemin, "r", encoding="utf-8") as f:
                base_externe = json.load(f)
        except (json.JSONDecodeError, OSError):
            messagebox.showerror("Erreur", "Ce fichier n'est pas une base de bugs valide.")
            return

        if not isinstance(base_externe, dict) or not base_externe:
            messagebox.showerror("Erreur", "Ce fichier ne contient aucune entrée valide.")
            return

        self._fusionner_base_externe(base_externe, source="le fichier importé")

    def synchroniser_github(self):
        """Récupère la base communautaire publiée sur GitHub et la fusionne avec la base locale."""
        if "TON-PSEUDO-GITHUB" in URL_GITHUB_RAW:
            messagebox.showwarning(
                "Configuration requise",
                "Renseigne d'abord l'URL de ton dépôt dans URL_GITHUB_RAW, en haut de main.py "
                "(sur GitHub : ouvre bugs_data.json > bouton \"Raw\" > copie l'URL).",
            )
            return

        try:
            reponse = requests.get(URL_GITHUB_RAW, timeout=10)
            reponse.raise_for_status()
            base_distante = reponse.json()
        except requests.RequestException:
            messagebox.showerror("Erreur réseau", "Impossible de contacter GitHub. Vérifie ta connexion.")
            return
        except ValueError:
            messagebox.showerror("Erreur", "Le fichier distant n'est pas un JSON valide.")
            return

        if not isinstance(base_distante, dict) or not base_distante:
            messagebox.showinfo("Synchronisation", "Aucune entrée trouvée sur le dépôt distant.")
            return

        self._fusionner_base_externe(base_distante, source="GitHub")

    def _fusionner_base_externe(self, base_externe, source="la source externe"):
        """Logique de fusion commune à l'import fichier et à la synchro GitHub."""
        data = self.charger_base_de_donnees()
        nouveaux = [nom for nom in base_externe if nom not in data]
        conflits = [nom for nom in base_externe if nom in data]

        reponse = messagebox.askyesnocancel(
            "Synchroniser la base",
            f"{len(nouveaux)} nouveau(x) jeu(x) depuis {source}.\n"
            f"{len(conflits)} jeu(x) déjà présent(s) dans ta base.\n\n"
            "Oui = écraser tes entrées en conflit avec celles reçues\n"
            "Non = garder tes entrées, ajouter seulement les nouveaux jeux\n"
            "Annuler = ne rien faire",
        )

        if reponse is None:
            return

        for nom, infos in base_externe.items():
            if nom in data and reponse is False:
                continue
            data[nom] = infos

        with open(CHEMIN_DB, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        self.mettre_a_jour_compteur()
        self.rafraichir_liste_communaute(self.ent_recherche.get())
        messagebox.showinfo("Terminé", "La base a été mise à jour.")

    def charger_jeu_pour_edition(self, nom):
        """Pré-remplit le formulaire avec une entrée existante pour la modifier."""
        data = self.charger_base_de_donnees()
        infos = data.get(nom)
        if not infos:
            return

        self.jeu_en_edition = nom

        self.ent_jeu.delete(0, "end")
        self.ent_jeu.insert(0, nom)

        self.ent_id.delete(0, "end")
        self.ent_id.insert(0, infos.get("id", ""))

        self.ent_bug.delete(0, "end")
        self.ent_bug.insert(0, infos.get("bug", ""))

        self.txt_sol.delete("0.0", "end")
        self.txt_sol.insert("0.0", infos.get("solution") or PLACEHOLDER_SOLUTION)

        self.btn_save.configure(text="METTRE À JOUR")
        self.btn_annuler.pack(side="left", padx=5)

    def annuler_edition(self):
        """Quitte le mode édition et vide le formulaire."""
        self.jeu_en_edition = None

        self.ent_jeu.delete(0, "end")
        self.ent_id.delete(0, "end")
        self.ent_bug.delete(0, "end")
        self.txt_sol.delete("0.0", "end")
        self.txt_sol.insert("0.0", PLACEHOLDER_SOLUTION)

        self.btn_save.configure(text="VALIDER L'INJECTION")
        self.btn_annuler.pack_forget()

    def supprimer_jeu(self, nom):
        """Retire définitivement une entrée de la base."""
        data = self.charger_base_de_donnees()
        data.pop(nom, None)

        with open(CHEMIN_DB, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        if self.jeu_en_edition == nom:
            self.annuler_edition()

        self.mettre_a_jour_compteur()
        self.rafraichir_liste_communaute(self.ent_recherche.get())

    def rafraichir_liste_communaute(self, filtre=""):
        """Affiche la liste des jeux de la base, filtrée par la recherche, avec actions par ligne."""
        for child in self.scrollable_frame_commu.winfo_children():
            child.destroy()

        data = self.charger_base_de_donnees()
        filtre = filtre.lower().strip()

        for nom in sorted(data.keys(), key=str.lower):
            if filtre and filtre not in nom.lower():
                continue

            ligne = ctk.CTkFrame(self.scrollable_frame_commu, fg_color="gray20")
            ligne.pack(pady=4, padx=5, fill="x")

            ctk.CTkLabel(ligne, text=nom, font=("Consolas", 11)).pack(side="left", padx=10, pady=6)

            ctk.CTkButton(ligne, text="🗑️", width=36, fg_color="#661111", hover_color="#8a1c1c",
                         command=lambda n=nom: self.supprimer_jeu(n)).pack(side="right", padx=(5, 10))
            ctk.CTkButton(ligne, text="✏️", width=36, fg_color="#301050", hover_color="#472170",
                         command=lambda n=nom: self.charger_jeu_pour_edition(n)).pack(side="right", padx=5)

    # ---------------------------------------------------------------
    # DIVERS
    # ---------------------------------------------------------------

    def charger_base_de_donnees(self):
        if os.path.exists(CHEMIN_DB):
            with open(CHEMIN_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def mettre_a_jour_compteur(self):
        """Compte les jeux dans le JSON et met à jour l'affichage."""
        data = self.charger_base_de_donnees()
        self.lbl_count.configure(text=f"BASE : {len(data)} JEU(X)")


if __name__ == "__main__":
    app = GameFixerApp()
    app.mainloop()
