# Fichier: bot_page.py
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import font
from datetime import datetime
import threading
import json
import os
import asyncio

# Importe les fonctions de scan
try:
    from scanner_logic import (
        find_funding_opportunities 
    )
except ImportError:
    print("ERREUR: Le fichier scanner_logic.py est manquant.")
    
# --- IMPORTS CORRIGÉS ---
try:
    CONFIG_FILE = "config.json"
    
    def load_api_keys():
        """Charge les clés depuis config.json."""
        if not os.path.exists(CONFIG_FILE):
            print("[ERREUR MOTEUR] Fichier config.json introuvable.")
            return None
        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
            return config_data
        except Exception as e:
            print(f"[ERREUR MOTEUR] Erreur de lecture config.json: {e}")
            return None

    from API import (
        HyperliquidAPI,
        ParadexAPI,
        LighterAPI,
        ExtendedAPI
    )
except ImportError:
    print("ERREUR: Un ou plusieurs fichiers API sont manquants ou le paquet API n'est pas chargé.")
    def load_api_keys(): return None
    class HyperliquidAPI:
        def __init__(self, cfg): pass
        def get_account_balance(self): return -1.0
        def open_market_order(self, p, ib, notional_usd, l): return False 
    class ParadexAPI:
        def __init__(self, cfg): pass
        def get_account_balance(self): return 123.45
    class LighterAPI:
        def __init__(self, cfg): pass
        def get_account_balance(self): return 456.78
    class ExtendedAPI:
        def __init__(self, cfg): pass
        def get_account_balance(self): return 789.01
# --- FIN DES CORRECTIONS ---
    
try:
    import pandas as pd
except ImportError:
    print("ERREUR: La bibliothèque 'pandas' est requise. Installez-la avec : pip install pandas")
    pd = None

class BotPage(ttk.Frame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app_controller = app_controller 
        
        self.mode_var = tk.StringVar(value="Manuel")
        self.stake_var = tk.StringVar(value="1000")
        self.leverage_var = tk.IntVar(value=10) 
        
        self.selected_opportunity = tk.StringVar()
        self.opportunities_df = None
        
        self.create_controls_frame()
        self.create_log_frame()
        
        self.after(100, self.load_cached_data)

    def create_controls_frame(self):
        """Crée le panneau de contrôle à gauche."""
        controls_frame = ttk.Frame(self, padding=20)
        controls_frame.pack(side="left", fill="y", padx=10, pady=10)

        title_label = ttk.Label(controls_frame, text="Bot Delta Neutral", 
                                font=('-family "Calibri" -size 18 -weight bold'))
        title_label.pack(pady=(0, 20), anchor="w")

        self.scan_button = ttk.Button(
            controls_frame, 
            text="1. Rafraîchir les Opportunités", 
            command=self.run_scanner_thread,
            bootstyle="info"
        )
        self.scan_button.pack(fill="x", pady=5)

        test_buttons_frame = ttk.Frame(controls_frame)
        test_buttons_frame.pack(fill="x", pady=(0, 10))

        self.test_api_hl = ttk.Button(
            test_buttons_frame, text="Test HL", 
            command=lambda: self.run_api_test_thread("hyperliquid"),
            bootstyle="light-outline"
        )
        self.test_api_hl.pack(side="left", fill="x", expand=True, padx=(0, 2))

        self.test_api_px = ttk.Button(
            test_buttons_frame, text="Test Paradex", 
            command=lambda: self.run_api_test_thread("paradex"),
            bootstyle="light-outline"
        )
        self.test_api_px.pack(side="left", fill="x", expand=True, padx=2)

        self.test_api_lt = ttk.Button(
            test_buttons_frame, text="Test Lighter", 
            command=lambda: self.run_api_test_thread("lighter"),
            bootstyle="light-outline"
        )
        self.test_api_lt.pack(side="left", fill="x", expand=True, padx=2)

        self.test_api_ex = ttk.Button(
            test_buttons_frame, text="Test Extended", 
            command=lambda: self.run_api_test_thread("extended"),
            bootstyle="light-outline"
        )
        self.test_api_ex.pack(side="left", fill="x", expand=True, padx=(2, 0))

        mode_label = ttk.Label(controls_frame, text="Mode de Sélection :")
        mode_label.pack(anchor="w", pady=(10, 5))
        
        mode_frame = ttk.Frame(controls_frame)
        mode_frame.pack(fill="x")
        manual_rb = ttk.Radiobutton(
            mode_frame, text="Manuel", variable=self.mode_var,
            value="Manuel", command=self.toggle_manual_pair_entry,
            bootstyle="info-toolbutton-outline"
        )
        manual_rb.pack(side="left", fill="x", expand=True, padx=(0, 5))
        auto_rb = ttk.Radiobutton(
            mode_frame, text="Auto", variable=self.mode_var,
            value="Auto", command=self.toggle_manual_pair_entry,
            bootstyle="info-toolbutton-outline"
        )
        auto_rb.pack(side="left", fill="x", expand=True, padx=(5, 0))

        settings_frame = ttk.Frame(controls_frame)
        settings_frame.pack(fill="x", pady=20)
        
        self.pair_label = ttk.Label(settings_frame, text="Opportunité (Manuel):")
        self.pair_label.grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.opportunities_combo = ttk.Combobox(
            settings_frame, textvariable=self.selected_opportunity,
            state="readonly", width=40
        )
        self.opportunities_combo.grid(row=0, column=1, sticky="w", padx=5, pady=10)
        self.opportunities_combo['values'] = ["Veuillez lancer un scan..."]
        
        stake_label = ttk.Label(settings_frame, text="Taille Position (USD):")
        stake_label.grid(row=1, column=0, sticky="w", padx=5, pady=10)
        stake_entry = ttk.Entry(settings_frame, textvariable=self.stake_var, width=15)
        stake_entry.grid(row=1, column=1, sticky="w", padx=5, pady=10)

        leverage_label = ttk.Label(settings_frame, text="Mon Levier Cible (1-20x):")
        leverage_label.grid(row=2, column=0, sticky="w", padx=5, pady=10)
        leverage_spinbox = ttk.Spinbox(
            settings_frame, from_=1, to=20, 
            textvariable=self.leverage_var, width=13
        )
        leverage_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=10)
        
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill="x", pady=20)
        
        self.start_button = ttk.Button(
            buttons_frame, text="Démarrer le Bot", command=self.start_bot_thread,
            bootstyle="success", state="disabled"
        )
        self.start_button.pack(side="left", fill="x", expand=True, padx=5)
        self.stop_button = ttk.Button(
            buttons_frame, text="Arrêter le Bot", command=self.stop_bot,
            bootstyle="danger", state="disabled"
        )
        self.stop_button.pack(side="right", fill="x", expand=True, padx=5)
        
        status_frame = ttk.Labelframe(controls_frame, text=" Statut de la Position ", padding=15)
        status_frame.pack(fill="x", pady=20)
        
        ttk.Label(status_frame, text="Position:").grid(row=0, column=0, sticky="w", padx=5)
        self.status_position_label = ttk.Label(status_frame, text="Aucune", bootstyle="secondary")
        self.status_position_label.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="Frais (Ouv+Ferm):").grid(row=1, column=0, sticky="w", padx=5)
        self.status_fees_label = ttk.Label(status_frame, text="N/A", bootstyle="secondary")
        self.status_fees_label.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(status_frame, text="Funding Accumulé:").grid(row=2, column=0, sticky="w", padx=5)
        self.status_funding_label = ttk.Label(status_frame, text="N/A", bootstyle="secondary")
        self.status_funding_label.grid(row=2, column=1, sticky="w", padx=5)
        
        ttk.Label(status_frame, text="PNL Total:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.status_pnl_label = ttk.Label(status_frame, text="N/A", bootstyle="secondary")
        self.status_pnl_label.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    def create_log_frame(self):
        """Crée la console de log à droite."""
        log_frame = ttk.Frame(self, padding=10)
        log_frame.pack(side="right", fill="both", expand=True)
        log_label = ttk.Label(log_frame, text="Logs du Bot :")
        log_label.pack(anchor="w", pady=5)
        self.log_text = tk.Text(
            log_frame, height=10, wrap="word",
            bg="#2a2a2a", fg="#cccccc", relief="flat",
            font=('-family "Consolas" -size 10')
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)
        self.add_log("Bienvenue sur le Bot Delta Neutral.")
        
    def load_cached_data(self):
        """Charge les données depuis le cache du contrôleur."""
        self.add_log("Vérification du cache de funding...")
        if self.app_controller.cached_opportunities is not None and not self.app_controller.cached_opportunities.empty:
            self.add_log(f"Données trouvées dans le cache (Scan à {self.app_controller.last_scan_time.strftime('%H:%M:%S')}).")
            self.populate_opportunities(self.app_controller.cached_opportunities, None)
        else:
            self.add_log("Cache vide. Cliquez sur 'Rafraîchir les Opportunités'.")

    def run_scanner_thread(self):
        """Lance le scan des opportunités dans un thread."""
        self.add_log("Scan forcé... Appel des APIs (HL, PX, LT, EX)...")
        self.start_button.config(state="disabled")
        self.scan_button.config(state="disabled")
        
        filters = {
            'hl': self.app_controller.funding_page.var_hyperliquid.get(),
            'px': self.app_controller.funding_page.var_paradex.get(),
            'lt': self.app_controller.funding_page.var_lighter.get(),
            'ex': self.app_controller.funding_page.var_extended.get()
        }
        
        self.app_controller.start_global_scan(
            filters=filters,
            force=True,
            callback=self.populate_opportunities
        )

    def populate_opportunities(self, df, error_msg=None):
        """[GUI] Remplit le menu déroulant (Combobox) avec les résultats."""
        if not self.winfo_exists(): return
            
        if error_msg:
            self.add_log(f"[ERREUR SCAN] {error_msg}")
            self.scan_button.config(state="normal")
            return
        if not isinstance(df, (pd.DataFrame, type(None))):
            df = None
        if df is None or df.empty:
            self.add_log("Scan terminé. Aucune opportunité trouvée.")
            self.opportunities_combo['values'] = ["Aucune opportunité trouvée"]
            self.selected_opportunity.set("Aucune opportunité trouvée")
            self.scan_button.config(state="normal")
            return

        self.add_log(f"Scan terminé. {len(df)} opportunités trouvées.")
        self.opportunities_df = df
        opportunity_list = []
        for index, row in df.iterrows():
            label = (
                f"Score {row['Score (1h)']:.2f} | {row['Paire']} (Levier Min: {row['Min Levier']}x) "
                f"| Spread: {row['Spread (1h)']:.4f}%"
            )
            opportunity_list.append(label)
        self.opportunities_combo['values'] = opportunity_list
        self.selected_opportunity.set(opportunity_list[0])
        self.toggle_manual_pair_entry()
        self.start_button.config(state="normal")
        self.stop_button.config(state="normal")
        self.scan_button.config(state="normal")

    def toggle_manual_pair_entry(self, *args):
        """Active/Désactive le menu déroulant si on est en mode Manuel."""
        if self.mode_var.get() == "Auto":
            self.opportunities_combo.config(state="disabled")
            self.pair_label.config(state="disabled")
            self.add_log("Mode Auto : le bot choisira le TOP 1 spread.")
        else:
            self.opportunities_combo.config(state="normal")
            self.pair_label.config(state="normal")
            self.add_log("Mode Manuel : choisissez une opportunité dans la liste.")

    def add_log(self, message):
        """Ajoute un message à la console de log."""
        if not self.winfo_exists(): return
        try:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_message = f"[{timestamp}] {message}\n"
            self.log_text.config(state="normal")
            self.log_text.insert("end", log_message)
            self.log_text.config(state="disabled")
            self.log_text.see("end")
        except tk.TclError:
            pass

    # --- CORRIGÉ : Fonctions de test remises ---
    def run_api_test_thread(self, platform):
        """Lance le test de connexion API pour la plateforme choisie."""
        self.add_log(f"Test de connexion {platform.capitalize()}...")
        
        buttons = {
            "hyperliquid": self.test_api_hl,
            "paradex": self.test_api_px,
            "lighter": self.test_api_lt,
            "extended": self.test_api_ex
        }
        buttons[platform].config(state="disabled")
            
        threading.Thread(target=self.test_api_connection, args=(platform,), daemon=True).start()

    def test_api_connection(self, platform):
        """[THREAD] Charge les clés et tente de se connecter."""
        trader_object = None
        balance = None
        try:
            api_config = load_api_keys()
            if not api_config or platform not in api_config:
                self.after_safe(self.add_log, f"[ERREUR] Clés {platform.capitalize()} non trouvées dans config.json.")
                return

            platform_config = api_config[platform]
            
            if platform == "hyperliquid":
                trader_object = HyperliquidAPI(platform_config)
                balance = trader_object.get_account_balance()
            elif platform == "paradex":
                trader_object = ParadexAPI(platform_config)
                balance = trader_object.get_account_balance() 
            elif platform == "lighter":
                trader_object = LighterAPI(platform_config)
                balance = trader_object.get_account_balance()
            elif platform == "extended":
                trader_object = ExtendedAPI(platform_config)
                balance = trader_object.get_account_balance() 
            
            if balance is not None:
                self.after_safe(self.add_log, f"[SUCCÈS] Connexion {platform.capitalize()} OK.")
                if hasattr(trader_object, 'address'):
                    self.after_safe(self.add_log, f"Adresse: {trader_object.address}")
                self.after_safe(self.add_log, f"Solde total du compte: {balance:.2f} USD")
            else:
                self.after_safe(self.add_log, f"[ERREUR] {platform.capitalize()}: Clés valides, mais impossible de récupérer le solde.")
                
        except ValueError as ve:
             self.after_safe(self.add_log, f"[ERREUR CLÉ {platform.capitalize()}] {ve}")
        except Exception as e:
            self.after_safe(self.add_log, f"[ERREUR INCONNUE {platform.capitalize()}] {e}")
        finally:
            buttons = {
                "hyperliquid": self.test_api_hl,
                "paradex": self.test_api_px,
                "lighter": self.test_api_lt,
                "extended": self.test_api_ex
            }
            if platform in buttons:
                self.after_safe(buttons[platform].config, state="normal")
    # --- FIN CORRECTION ---
    
    def start_bot_thread(self):
        """[GUI] Lance le bot dans un thread pour ne pas geler l'interface."""
        self.add_log("Démarrage du thread du bot...")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal") 
        threading.Thread(target=self.start_bot_logic, daemon=True).start()

    def start_bot_logic(self):
        """[THREAD] C'est la fonction principale du bot."""
        mode = self.mode_var.get()
        notional_size = self.stake_var.get()
        leverage_target_user = self.leverage_var.get()
        
        self.after_safe(self.add_log, "--- DÉMARRAGE DU BOT ---")
        self.after_safe(self.add_log, f"Mode: {mode}")
        self.after_safe(self.add_log, f"Taille Position Cible: {notional_size} USD")
        self.after_safe(self.add_log, f"Mon Levier Cible: {leverage_target_user}x")
        
        try:
            if self.opportunities_df is None or self.opportunities_df.empty:
                self.after_safe(self.add_log, "[ERREUR] Veuillez d'abord lancer un scan.")
                self.after_safe(self.start_button.config, state="normal")
                return

            opportunity_data = None
            if mode == "Manuel":
                selected_label = self.selected_opportunity.get()
                if "Veuillez" in selected_label or "Aucune" in selected_label:
                    self.after_safe(self.add_log, "[ERREUR] Opportunité manuelle non valide.")
                    self.after_safe(self.start_button.config, state="normal")
                    return
                selected_index = self.opportunities_combo['values'].index(selected_label)
                opportunity_data = self.opportunities_df.iloc[selected_index]
            else: 
                df_auto = self.opportunities_df[
                    (self.opportunities_df['Min Levier'] >= leverage_target_user)
                ]
                if df_auto.empty:
                    self.after_safe(self.add_log, f"[ERREUR] Mode Auto: Aucune opportunité trouvée supportant un levier {leverage_target_user}x.")
                    self.after_safe(self.start_button.config, state="normal")
                    return
                opportunity_data = df_auto.iloc[0] 

            actual_leverage = int(min(leverage_target_user, opportunity_data['Min Levier']))

            self.after_safe(self.add_log, f"Cible Sélectionnée: {opportunity_data['Paire']}")
            self.after_safe(self.add_log, f"-> LONG {opportunity_data['Long Sur']} (Max: {opportunity_data['Levier Long']}x)")
            self.after_safe(self.add_log, f"-> SHORT {opportunity_data['Short Sur']} (Max: {opportunity_data['Levier Short']}x)")
            self.after_safe(self.add_log, f"-> Levier de trading réel: {actual_leverage}x")

            if opportunity_data['Levier Long'] > leverage_target_user or opportunity_data['Levier Short'] > leverage_target_user:
                 self.after_safe(self.add_log, f"[AVERTISSEMENT] L'opportunité choisie dépasse votre levier cible. Utilisation du levier max de la paire: {actual_leverage}x.")
            
            self.after_safe(self.add_log, "Chargement des clés API depuis config.json...")
            api_config = load_api_keys()
            if not api_config:
                self.after_safe(self.add_log, "[ERREUR] Impossible de charger config.json.")
                self.after_safe(self.start_button.config, state="normal")
                return

            if opportunity_data['Long Sur'] == "Hyperliquid":
                self.after_safe(self.add_log, "Initialisation du trader Hyperliquid (LONG)...")
                trader_hl = HyperliquidAPI(api_config["hyperliquid"])
                success = trader_hl.open_market_order(
                    pair=opportunity_data['Paire'], is_buy=True, 
                    notional_usd=notional_size, leverage=actual_leverage
                )
                if not success:
                    self.after_safe(self.add_log, "[ÉCHEC] L'ordre LONG sur Hyperliquid a échoué. Arrêt du bot.")
                    self.after_safe(self.stop_bot)
                    return
                
            elif opportunity_data['Short Sur'] == "Hyperliquid":
                self.after_safe(self.add_log, "Initialisation du trader Hyperliquid (SHORT)...")
                trader_hl = HyperliquidAPI(api_config["hyperliquid"])
                success = trader_hl.open_market_order(
                    pair=opportunity_data['Paire'], is_buy=False, 
                    notional_usd=notional_size, leverage=actual_leverage
                )
                if not success:
                    self.after_safe(self.add_log, "[ÉCHEC] L'ordre SHORT sur Hyperliquid a échoué. Arrêt du bot.")
                    self.after_safe(self.stop_bot)
                    return
            
            if "Paradex" in [opportunity_data['Long Sur'], opportunity_data['Short Sur']]:
                self.after_safe(self.add_log, "Partie Paradex non implémentée. Ordre non passé.")
            if "Lighter" in [opportunity_data['Long Sur'], opportunity_data['Short Sur']]:
                self.after_safe(self.add_log, "Partie Lighter non implémentée. Ordre non passé.")
            if "Extended" in [opportunity_data['Long Sur'], opportunity_data['Short Sur']]:
                self.after_safe(self.add_log, "Partie Extended non implémentée. Ordre non passé.")

            self.after_safe(self.add_log, "Bot démarré (simulation).")
            
        except Exception as e:
            self.after_safe(self.add_log, f"[ERREUR] Impossible de démarrer le bot: {e}")
        finally:
            pass

    def stop_bot(self):
        """Fonction appelée par le bouton Arrêter."""
        self.add_log("--- ARRÊT DU BOT (Simulation) ---")
        
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def after_safe(self, func, *args, **kwargs):
        """
        Appelle 'after' seulement si le widget existe encore,
        en utilisant une lambda pour passer les arguments-clés (kwargs).
        """
        if self.winfo_exists():
            self.after(0, lambda: func(*args, **kwargs))