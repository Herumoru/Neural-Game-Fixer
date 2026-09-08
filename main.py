import customtkinter as ctk
import os
import json
import re
import string
import webbrowser

# Couleurs Cyberpunk
CYAN = "#00f3ff"
MAGENTA = "#ff00ff"
DARK_BG = "#0d0221"
GREEN = "#39ff14"

PLACEHOLDER_SOLUTION = "ÉCRIVEZ LA SOLUTION ICI..."


class GameFixerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Fenêtre principale
        self.title("⚡ NEURAL GAME FIXER ⚡")
        self.geometry("750x750")
        self.configure(fg_color=DARK_BG)

        # FIX : évite un AttributeError si "Réparer" est cliqué avant tout scan
        self.jeu_detecte_actuel = None

        # 1. Configuration des onglets
        self.tabs = ctk.CTkTabview(self,
                                   width=700,
                                   height=640,
                                   fg_color="#100228",
                                   segmented_button_fg_color="#0d0221",
                                   segmented_button_selected_color=CYAN,
                                   segmented_button_selected_hover_color="#00444d",
                                   border_width=2,
                                   border_color="#1e054d")
        self.tabs.pack(padx=20, pady=10)

        self.tab_scan = self.tabs.add("🔍 Scanner")
        self.tab_commu = self.tabs.add("🤝 Communauté")

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
        self.mettre_a_jour_compteur()

    # ---------------------------------------------------------------
    # ONGLET SCANNER
    # ---------------------------------------------------------------

    def setup_scan_tab(self):
        """Onglet pour scanner et réparer"""
        ctk.CTkLabel(self.tab_scan, text="⚡ SYSTEM SCANNER ⚡", font=("Consolas", 24, "bold"), text_color=CYAN).pack(pady=15)

        boutons_frame = ctk.CTkFrame(self.tab_scan, fg_color="transparent")
        boutons_frame.pack(pady=5)

        self.btn_scan = ctk.CTkButton(boutons_frame, text="LANCER L'ANALYSE", border_color=CYAN, border_width=2,
                                      fg_color="transparent", text_color=CYAN, command=self.analyser_systeme)
        self.btn_scan.pack(side="left", padx=5)

        self.btn_auto_detect = ctk.CTkButton(boutons_frame, text="🔍 DÉTECTION RAPIDE", border_color=CYAN,
                                             border_width=2, fg_color="transparent", text_color=CYAN,
                                             command=self.lancer_auto_detection)
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
        self.textbox.insert("end", ">> LECTURE DES BIBLIOTHÈQUES STEAM...\n")
        jeux_detectes = self.detecter_tous_les_jeux_steam()

        if not jeux_detectes:
            self.textbox.insert("end", "[!] AUCUNE BIBLIOTHÈQUE / AUCUN JEU DÉTECTÉ.\n")
            return

        jeux_avec_infos = self.croiser_avec_base_de_donnees(jeux_detectes)
        nb_connus = sum(1 for j in jeux_avec_infos if j["infos"])
        self.textbox.insert("end", f">> {len(jeux_avec_infos)} JEU(X) DÉTECTÉ(S), {nb_connus} AVEC BUG CONNU.\n")
        self.afficher_jeux_detectes(jeux_avec_infos)

    def lancer_auto_detection(self):
        """Détection instantanée, sans animation (utilise la même logique que le scan complet)"""
        self.textbox.insert("end", "\n[ SYSTEM ] : Scan des unités de stockage...\n")
        jeux_detectes = self.detecter_tous_les_jeux_steam()
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

            ligne = ctk.CTkFrame(self.scrollable_frame, fg_color="gray20")
            ligne.pack(pady=5, padx=5, fill="x")

            entete = ctk.CTkFrame(ligne, fg_color="transparent")
            entete.pack(fill="x")
            ctk.CTkLabel(entete, text=f"🎮 {nom[:30]}", font=("Consolas", 12, "bold")).pack(side="left", padx=10, pady=5)

            if infos:
                ctk.CTkLabel(entete, text="⚠ BUG CONNU", font=("Consolas", 10, "bold"), text_color=MAGENTA).pack(side="right", padx=10)
                ctk.CTkLabel(ligne, text=f"Symptôme : {infos.get('bug', 'N/A')}", font=("Consolas", 10),
                            text_color="#aaaaaa", wraplength=500, justify="left").pack(anchor="w", padx=15)
                ctk.CTkLabel(ligne, text=f"Solution : {infos.get('solution', 'N/A')}", font=("Consolas", 10),
                            text_color=GREEN, wraplength=500, justify="left").pack(anchor="w", padx=15, pady=(0, 5))
            else:
                ctk.CTkLabel(entete, text="Aucun bug connu", font=("Consolas", 10), text_color="#666666").pack(side="right", padx=10)

            ctk.CTkButton(ligne, text="🔧 VÉRIFIER LES FICHIERS", width=190, fg_color=MAGENTA,
                         command=lambda i=appid, n=nom: self.reparer_jeu_specifique(i, n)).pack(pady=(0, 8))

    # ---------------------------------------------------------------
    # DÉTECTION STEAM (logique unifiée, avant dupliquée à deux endroits)
    # ---------------------------------------------------------------

    def trouver_dossiers_steamapps(self):
        """Retourne tous les dossiers 'steamapps' existants, tous disques (A à Z) confondus."""
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
                        jeux_trouves.append({"nom": nom, "id": appid})
                    except (AttributeError, OSError):
                        continue  # fichier .acf mal formé ou illisible
        return jeux_trouves

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

    # ---------------------------------------------------------------
    # ONGLET COMMUNAUTÉ
    # ---------------------------------------------------------------

    def setup_community_tab(self):
        """Interface de contribution stylisée"""
        ctk.CTkLabel(self.tab_commu, text="--- AJOUTER UN JEU À LA BASE ---",
                    font=("Consolas", 16, "bold"), text_color=MAGENTA).pack(pady=20)

        style_champ = {"width": 400, "height": 40, "fg_color": "black", "border_color": "#301050"}

        self.ent_jeu = ctk.CTkEntry(self.tab_commu, placeholder_text="NOM DU DOSSIER (ex: Cyberpunk 2077)", **style_champ)
        self.ent_jeu.pack(pady=10)

        self.ent_id = ctk.CTkEntry(self.tab_commu, placeholder_text="ID STEAM DU JEU", **style_champ)
        self.ent_id.pack(pady=10)

        self.ent_bug = ctk.CTkEntry(self.tab_commu, placeholder_text="DESCRIPTION DU SYMPTÔME", **style_champ)
        self.ent_bug.pack(pady=10)

        self.txt_sol = ctk.CTkTextbox(self.tab_commu, width=400, height=100,
                                      fg_color="black", border_color="#301050", border_width=2)
        self.txt_sol.pack(pady=10)
        self.txt_sol.insert("0.0", PLACEHOLDER_SOLUTION)
        # FIX : le placeholder ne s'effaçait jamais et pouvait finir enregistré comme vraie solution
        self.txt_sol.bind("<FocusIn>", self._effacer_placeholder_solution)
        self.txt_sol.bind("<FocusOut>", self._restaurer_placeholder_solution)

        self.btn_save = ctk.CTkButton(self.tab_commu, text="VALIDER L'INJECTION",
                                      fg_color="transparent", border_color=MAGENTA, border_width=2,
                                      text_color=MAGENTA, hover_color="#2e002e",
                                      font=("Consolas", 14, "bold"),
                                      command=self.ajouter_bug_commu)
        self.btn_save.pack(pady=20)

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
            data[jeu] = {"id": steam_id, "bug": bug, "solution": sol}

            with open("bugs_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.btn_save.configure(text="✅ INJECTION RÉUSSIE", fg_color="green")
            self.after(2000, lambda: self.btn_save.configure(text="VALIDER L'INJECTION", fg_color=MAGENTA))
            self.mettre_a_jour_compteur()

        except PermissionError:
            self.textbox.insert("end", "[!] ERREUR : Fermez le fichier bugs_data.json pour enregistrer.\n")

    # ---------------------------------------------------------------
    # DIVERS
    # ---------------------------------------------------------------

    def charger_base_de_donnees(self):
        if os.path.exists("bugs_data.json"):
            with open("bugs_data.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def mettre_a_jour_compteur(self):
        """Compte les jeux dans le JSON et met à jour l'affichage."""
        data = self.charger_base_de_donnees()
        self.lbl_count.configure(text=f"BASE : {len(data)} JEU(X)")


if __name__ == "__main__":
    app = GameFixerApp()
    app.mainloop()
