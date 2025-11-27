# Fichier: main_app.py
import tkinter as tk
import ttkbootstrap as ttk 
from tkinter import font, messagebox
import requests
import pandas as pd
import re
import threading
import json
import os 
from datetime import datetime

# --- Imports depuis nos fichiers personnalisés ---
from bot_page import BotPage 
from dashboard_page import DashboardPage
from stats_page import StatsPage
from scanner_logic import find_funding_opportunities
from API import (
    get_hyperliquid_funding_data,
    get_paradex_funding_data,
    get_lighter_funding_data,
    get_extended_funding_data
)

CONFIG_FILE = "config.json"


# --- SECTION 1 : LA "PAGE" FUNDING (Inchangée) ---
class FundingPage(ttk.Frame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app_controller = app_controller 
        self.current_df = pd.DataFrame() 
        self.last_sort_col = "Score (1h)" 
        self.last_sort_reverse = True     
        
        top_frame = ttk.Frame(self, padding=(10, 10))
        top_frame.pack(fill='x')

        self.refresh_button = ttk.Button(
            top_frame, 
            text="🔄 Mettre à jour (Force)", 
            command=self.start_fetch_thread_forced,
            bootstyle="info"
        )
        self.refresh_button.pack(side='left', padx=(0, 20))

        self.var_hyperliquid = tk.BooleanVar(value=True)
        self.var_paradex = tk.BooleanVar(value=True)
        self.var_lighter = tk.BooleanVar(value=True)
        self.var_extended = tk.BooleanVar(value=True) 
        
        cb_hl = ttk.Checkbutton(
            top_frame, text="Hyperliquid", variable=self.var_hyperliquid,
            bootstyle="primary", command=self.start_fetch_thread_cached
        )
        cb_hl.pack(side='left', padx=5)
        cb_px = ttk.Checkbutton(
            top_frame, text="Paradex", variable=self.var_paradex,
            bootstyle="primary", command=self.start_fetch_thread_cached
        )
        cb_px.pack(side='left', padx=5)
        cb_lt = ttk.Checkbutton(
            top_frame, text="Lighter", variable=self.var_lighter,
            bootstyle="primary", command=self.start_fetch_thread_cached
        )
        cb_lt.pack(side='left', padx=5)
        
        cb_ex = ttk.Checkbutton(
            top_frame, text="Extended", variable=self.var_extended,
            bootstyle="primary", command=self.start_fetch_thread_cached
        )
        cb_ex.pack(side='left', padx=5)

        self.status_label = ttk.Label(
            top_frame, text="Prêt.", 
            font=('-family "Calibri" -size 10 -slant italic')
        )
        self.status_label.pack(side='right')

        tree_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        tree_frame.pack(fill='both', expand=True)
        
        self.columns = (
            'Paire', 'Score (1h)', 'Spread (1h)', 'Min Levier',
            'Long Sur', 'Levier Long', 'Taux Long (1h)', 
            'Short Sur', 'Levier Short', 'Taux Short (1h)'
        )
                   
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings', bootstyle="darkly")
        
        for col in self.columns:
            self.tree.heading(
                col, 
                text=col, 
                command=lambda c=col: self.sort_by_column(c)
            )
            self.tree.column(col, width=120, anchor='c') 

        self.tree.column('Paire', width=60, anchor='w')
        self.tree.column('Score (1h)', anchor='e', width=100)
        self.tree.column('Spread (1h)', anchor='e', width=120)
        self.tree.column('Min Levier', width=80)
        self.tree.column('Levier Long', width=80)
        self.tree.column('Levier Short', width=80)
        self.tree.column('Taux Long (1h)', anchor='e', width=120)
        self.tree.column('Taux Short (1h)', anchor='e', width=120)

        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)
        
        self.after(100, self.start_fetch_thread_cached)

    def start_fetch_thread_cached(self):
        self.start_fetch_thread(force_rescan=False)
        
    def start_fetch_thread_forced(self):
        self.start_fetch_thread(force_rescan=True)

    def start_fetch_thread(self, force_rescan=False):
        """Demande un scan au contrôleur central."""
        self.status_label.config(text="Chargement des données API...")
        self.refresh_button.config(state="disabled")
        filters = {
            "hl": self.var_hyperliquid.get(),
            "px": self.var_paradex.get(),
            "lt": self.var_lighter.get(),
            "ex": self.var_extended.get()
        }
        self.app_controller.start_global_scan(
            filters=filters,
            force=force_rescan,
            callback=self.on_data_received
        )

    def on_data_received(self, df, error_msg=None):
        """Reçoit les données et appelle update_table."""
        if not self.winfo_exists():
            print("Callback on_data_received annulé (page détruite).")
            return
            
        if error_msg:
            self.status_label.config(text=error_msg)
            self.current_df = pd.DataFrame() 
            self.update_table(self.current_df) 
            self.refresh_button.config(state="normal")
            return
            
        if df is not None:
            self.current_df = df.copy() 
            try:
                self.current_df = self.current_df.sort_values(
                    by=self.last_sort_col, 
                    ascending=(not self.last_sort_reverse)
                )
            except KeyError:
                self.last_sort_col = "Paire"
                self.last_sort_reverse = False
            self.update_table(self.current_df)
        else:
            self.status_label.config(text="Scan terminé, mais pas de données.")
            self.update_table(pd.DataFrame()) 
            
        self.refresh_button.config(state="normal")
        
    def sort_by_column(self, col):
        """Trie les données existantes lorsque l'en-tête est cliqué."""
        if not self.winfo_exists(): return
        if self.current_df.empty: return 

        if col == self.last_sort_col:
            self.last_sort_reverse = not self.last_sort_reverse
        else:
            self.last_sort_reverse = col in ['Paire', 'Long Sur', 'Short Sur'] 
            
        self.last_sort_col = col
        try:
            if col in ['Score (1h)', 'Spread (1h)', 'Min Levier', 'Levier Long', 'Levier Short', 'Taux Long (1h)', 'Taux Short (1h)']:
                sorted_df = self.current_df.sort_values(
                    by=col, 
                    ascending=(not self.last_sort_reverse)
                )
            else:
                sorted_df = self.current_df.sort_values(
                    by=col, 
                    ascending=self.last_sort_reverse
                )
            self.update_table(sorted_df)
        except Exception as e:
            print(f"Erreur de tri: {e}")

    def update_table(self, df):
        """Met à jour le tableau avec n'importe quel DataFrame."""
        if not self.winfo_exists():
            print("Callback update_table annulé (page détruite).")
            return
            
        for item in self.tree.get_children():
            self.tree.delete(item)

        if df is not None and not df.empty:
            for i, row in df.iterrows():
                values = [
                    row['Paire'],
                    f"{row['Score (1h)']:.2f}",
                    f"{row['Spread (1h)']:.4f}%",
                    f"{row['Min Levier']}x",
                    row['Long Sur'],
                    f"{row['Levier Long']}x",
                    f"{row['Taux Long (1h)']:.4f}%",
                    row['Short Sur'],
                    f"{row['Levier Short']}x",
                    f"{row['Taux Short (1h)']:.4f}%",
                ]
                self.tree.insert('', 'end', values=values)
            
            if self.app_controller.last_scan_time:
                last_scan_str = self.app_controller.last_scan_time.strftime('%H:%M:%S')
                self.status_label.config(text=f"Données mises à jour à {last_scan_str}")
        else:
            self.status_label.config(text="Aucune opportunité trouvée (vérifie tes filtres).")


# --- SECTION 2 : LA "PAGE" PARAMÈTRES (FORTEMENT MODIFIÉE) ---
class SettingsPage(ttk.Frame):
    def __init__(self, parent, app_controller=None): 
        super().__init__(parent)
        
        # --- STRUCTURE DE DONNÉES MISE À JOUR ---
        self.api_keys = {
            "hyperliquid": {
                "secret": tk.StringVar() 
            },
            "paradex": {
                "key": tk.StringVar(),    
                "secret": tk.StringVar()  
            },
            "lighter": {
                "key": tk.StringVar(),         
                "account_index": tk.StringVar(),
                "api_key_index": tk.StringVar(value="2") 
            },
            # --- MODIFIÉ : Structure pour Extended/X10 ---
            "extended": {
                "api_key": tk.StringVar(),
                "public_key": tk.StringVar(),
                "private_key": tk.StringVar(),
                "vault_id": tk.StringVar()
            }
            # --- FIN MODIFICATION ---
        }
        
        self.create_hyperliquid_frame()
        self.create_paradex_frame()
        self.create_lighter_frame()
        # --- MODIFIÉ : Appelle la nouvelle fonction ---
        self.create_extended_frame()
        
        save_button = ttk.Button(
            self, text="Enregistrer les Clés", 
            command=self.save_config, bootstyle="success"
        )
        save_button.pack(pady=20, padx=20)
        self.save_status_label = ttk.Label(self, text="")
        self.save_status_label.pack(pady=5)
        
        self.load_config()

    def create_platform_frame(self, platform_name, key_vars):
        """(N'est plus utilisé par Extended, mais gardé pour Paradex)"""
        frame = ttk.Labelframe(self, text=f" {platform_name} ", padding=(10, 5))
        frame.pack(fill="x", padx=20, pady=10)
        key_label = ttk.Label(frame, text="Clé API (Key):")
        key_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        key_entry = ttk.Entry(frame, textvariable=key_vars["key"], width=60)
        key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        secret_label = ttk.Label(frame, text="Clé Secrète (Secret):")
        secret_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        secret_entry = ttk.Entry(frame, textvariable=key_vars["secret"], width=60, show="*")
        secret_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        frame.columnconfigure(1, weight=1)

    def create_hyperliquid_frame(self):
        vars = self.api_keys["hyperliquid"]
        frame = ttk.Labelframe(self, text=" Hyperliquid ", padding=(10, 5))
        frame.pack(fill="x", padx=20, pady=10)
        secret_label = ttk.Label(frame, text="Clé Privée Portefeuille Bot (Secret):")
        secret_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        secret_entry = ttk.Entry(frame, textvariable=vars["secret"], width=60, show="*")
        secret_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        frame.columnconfigure(1, weight=1)

    def create_paradex_frame(self):
        vars = self.api_keys["paradex"]
        frame = ttk.Labelframe(self, text=" Paradex ", padding=(10, 5))
        frame.pack(fill="x", padx=20, pady=10)
        key_label = ttk.Label(frame, text="Adresse Portefeuille (0x...):")
        key_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        key_entry = ttk.Entry(frame, textvariable=vars["key"], width=60)
        key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        secret_label = ttk.Label(frame, text="Clé Privée Paradex (Secret):")
        secret_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        secret_entry = ttk.Entry(frame, textvariable=vars["secret"], width=60, show="*")
        secret_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")
        frame.columnconfigure(1, weight=1)

    def create_lighter_frame(self):
        vars = self.api_keys["lighter"]
        frame = ttk.Labelframe(self, text=" Lighter (Sub-Account) ", padding=(10, 5))
        frame.pack(fill="x", padx=20, pady=10)
        key_label = ttk.Label(frame, text="Clé Privée API (Key/Secret):")
        key_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        key_entry = ttk.Entry(frame, textvariable=vars["key"], width=60, show="*")
        key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        acc_idx_label = ttk.Label(frame, text="Account Index (Compte Principal):")
        acc_idx_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        acc_idx_entry = ttk.Entry(frame, textvariable=vars["account_index"], width=10)
        acc_idx_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        api_idx_label = ttk.Label(frame, text="API Key Index (Sub-Account):")
        api_idx_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        api_idx_entry = ttk.Entry(frame, textvariable=vars["api_key_index"], width=10)
        api_idx_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        frame.columnconfigure(1, weight=1)

    # --- NOUVELLE FONCTION : Cadre pour Extended/X10 ---
    def create_extended_frame(self):
        """Cadre spécifique pour Extended (basé sur le code x10)."""
        vars = self.api_keys["extended"]
        frame = ttk.Labelframe(self, text=" Extended (x10) ", padding=(10, 5))
        frame.pack(fill="x", padx=20, pady=10)
        
        # Clé API
        key_label = ttk.Label(frame, text="Clé API (api_key):")
        key_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        key_entry = ttk.Entry(frame, textvariable=vars["api_key"], width=60)
        key_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        
        # Clé Publique
        pub_label = ttk.Label(frame, text="Clé Publique (public_key):")
        pub_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        pub_entry = ttk.Entry(frame, textvariable=vars["public_key"], width=60)
        pub_entry.grid(row=1, column=1, padx=5, pady=5, sticky="we")

        # Clé Privée
        priv_label = ttk.Label(frame, text="Clé Privée (private_key):")
        priv_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        priv_entry = ttk.Entry(frame, textvariable=vars["private_key"], width=60, show="*")
        priv_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")
        
        # Vault ID
        vault_label = ttk.Label(frame, text="Vault ID (vault_id):")
        vault_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        vault_entry = ttk.Entry(frame, textvariable=vars["vault_id"], width=60)
        vault_entry.grid(row=3, column=1, padx=5, pady=5, sticky="we")
        
        frame.columnconfigure(1, weight=1)
    # --- FIN NOUVELLE FONCTION ---

    def load_config(self):
        """Charge les clés depuis config.json (mis à jour)."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                
                if "hyperliquid" in config_data:
                    self.api_keys["hyperliquid"]["secret"].set(config_data["hyperliquid"].get("secret", ""))
                if "paradex" in config_data:
                    self.api_keys["paradex"]["key"].set(config_data["paradex"].get("key", ""))
                    self.api_keys["paradex"]["secret"].set(config_data["paradex"].get("secret", ""))
                if "lighter" in config_data:
                    self.api_keys["lighter"]["key"].set(config_data["lighter"].get("key", ""))
                    self.api_keys["lighter"]["account_index"].set(config_data["lighter"].get("account_index", ""))
                    self.api_keys["lighter"]["api_key_index"].set(config_data["lighter"].get("api_key_index", "2"))
                # --- MODIFIÉ : Charge les 4 clés Extended ---
                if "extended" in config_data:
                    self.api_keys["extended"]["api_key"].set(config_data["extended"].get("api_key", ""))
                    self.api_keys["extended"]["public_key"].set(config_data["extended"].get("public_key", ""))
                    self.api_keys["extended"]["private_key"].set(config_data["extended"].get("private_key", ""))
                    self.api_keys["extended"]["vault_id"].set(config_data["extended"].get("vault_id", ""))
                # --- FIN MODIFICATION ---
                    
                self.save_status_label.config(text="Clés chargées.", bootstyle="info")
        except Exception as e:
            self.save_status_label.config(text=f"Erreur chargement: {e}", bootstyle="danger")

    def save_config(self):
        """Sauvegarde les clés actuelles dans config.json (mis à jour)."""
        try:
            config_data = {
                "hyperliquid": {
                    "secret": self.api_keys["hyperliquid"]["secret"].get()
                },
                "paradex": {
                    "key": self.api_keys["paradex"]["key"].get(),
                    "secret": self.api_keys["paradex"]["secret"].get()
                },
                "lighter": {
                    "key": self.api_keys["lighter"]["key"].get(),
                    "account_index": self.api_keys["lighter"]["account_index"].get(),
                    "api_key_index": self.api_keys["lighter"]["api_key_index"].get()
                },
                # --- MODIFIÉ : Sauvegarde les 4 clés Extended ---
                "extended": {
                    "api_key": self.api_keys["extended"]["api_key"].get(),
                    "public_key": self.api_keys["extended"]["public_key"].get(),
                    "private_key": self.api_keys["extended"]["private_key"].get(),
                    "vault_id": self.api_keys["extended"]["vault_id"].get()
                }
                # --- FIN MODIFICATION ---
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            self.save_status_label.config(text="Clés enregistrées avec succès !", bootstyle="success")
        except Exception as e:
            self.save_status_label.config(text=f"Erreur sauvegarde: {e}", bootstyle="danger")


# --- SECTION 3 : L'APPLICATION GRAPHIQUE PRINCIPALE (GUI) ---
# (Corrigée pour la logique .grid() / .tkraise())

class FundingScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Airdrop Farmer Bot")
        self.root.geometry("1400x700") 
        self.current_page = None
        
        self.cached_opportunities = None 
        self.last_scan_time = None       
        self.scan_lock = threading.Lock()  
        
        self.create_side_menu()
        
        # --- NOUVELLE LOGIQUE DE CRÉATION DE PAGES ---
        self.main_content_frame = ttk.Frame(self.root)
        self.main_content_frame.pack(side='right', fill='both', expand=True)
        
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        self.pages = {}
        for PageClass in (FundingPage, BotPage, DashboardPage, StatsPage, SettingsPage):
            page = PageClass(self.main_content_frame, self)
            self.pages[PageClass] = page
            page.grid(row=0, column=0, sticky="nsew")
        
        self.funding_page = self.pages[FundingPage]
        self.show_page(FundingPage) 
        # --- FIN DE LA NOUVELLE LOGIQUE ---

    def create_side_menu(self):
        menu_frame = ttk.Frame(self.root, width=200, bootstyle="secondary")
        menu_frame.pack(side='left', fill='y')
        menu_label = ttk.Label(menu_frame, text="Menu Principal", 
            font=('-family "Calibri" -size 16 -weight bold'), bootstyle="inverse-secondary")
        menu_label.pack(pady=20, padx=10)

        funding_button = ttk.Button(menu_frame, text="📈 Funding Scanner", 
            command=self.show_funding_page, bootstyle="success")
        funding_button.pack(fill='x', padx=10, pady=5)
        bot_button = ttk.Button(menu_frame, text="🤖 Delta Neutral Bot", 
            command=self.show_bot_page, bootstyle="light-outline")
        bot_button.pack(fill='x', padx=10, pady=5)
        dashboard_button = ttk.Button(menu_frame, text="📊 Dashboard", 
            command=self.show_dashboard_page, bootstyle="light-outline")
        dashboard_button.pack(fill='x', padx=10, pady=5)
        stats_button = ttk.Button(menu_frame, text="💸 Airdrop Stats", 
            command=self.show_stats_page, bootstyle="light-outline")
        stats_button.pack(fill='x', padx=10, pady=5)
        settings_button = ttk.Button(menu_frame, text="⚙️ Paramètres", 
            command=self.show_settings_page, bootstyle="light-outline")
        settings_button.pack(fill='x', padx=10, pady=5, side='bottom')

    # --- FONCTION DE NAVIGATION CORRIGÉE ---
    def show_page(self, PageClass):
        """Ramène la page demandée au premier plan."""
        if PageClass in self.pages:
            page = self.pages[PageClass]
            page.tkraise()
            self.current_page = page
            return page
        else:
            print(f"Erreur: Page {PageClass} non trouvée.")
            return None

    def show_funding_page(self):
        self.funding_page = self.show_page(FundingPage)

    def show_bot_page(self):
        self.show_page(BotPage) 

    def show_settings_page(self):
        self.show_page(SettingsPage)

    def show_dashboard_page(self):
        self.show_page(DashboardPage)
        
    def show_stats_page(self):
        self.show_page(StatsPage)

    # --- Fonction de Scan Centralisée ---
    def start_global_scan(self, filters, force=False, callback=None):
        if not force and self.cached_opportunities is not None:
            now = datetime.now()
            if self.last_scan_time and (now - self.last_scan_time).total_seconds() < 1800: # 30 min
                print("Chargement depuis le cache (< 30 min)")
                if callback:
                    filtered_df = self.filter_cached_data(filters)
                    self.safe_callback(callback, filtered_df, None)
                return

        if not self.scan_lock.acquire(blocking=False):
            print("Scan déjà en cours. Annulation.")
            if callback:
                self.safe_callback(callback, None, "Scan déjà en cours...")
            return

        print("Démarrage du thread de scan global...")
        threading.Thread(
            target=self._scan_thread, 
            args=(filters, callback), 
            daemon=True
        ).start()

    def _scan_thread(self, filters, callback):
        all_data = []
        try:
            all_data_hl = get_hyperliquid_funding_data()
            all_data_px = get_paradex_funding_data()
            all_data_lt = get_lighter_funding_data()
            all_data_ex = get_extended_funding_data()
            
            all_data = all_data_hl + all_data_px + all_data_lt + all_data_ex
            
            df = find_funding_opportunities(all_data)
            
            self.cached_opportunities = df
            self.last_scan_time = datetime.now()
            print("Cache global mis à jour.")
            
            filtered_df = self.filter_cached_data(filters)
            
            if callback:
                self.safe_callback(callback, filtered_df, None) 
                
        except Exception as e:
            print(f"Erreur critique dans _scan_thread: {e}")
            if callback:
                self.safe_callback(callback, None, f"Erreur: {e}") 
        finally:
            self.scan_lock.release() 
            print("Scan terminé. Verrou libéré.")
            
    def safe_callback(self, callback, df, error_msg):
        """Fonction wrapper pour s'assurer que le widget de callback existe."""
        if callback and hasattr(callback, '__self__') and callback.__self__.winfo_exists():
            callback(df, error_msg)
        else:
            print(f"Callback annulé car la page a été détruite.")

    def filter_cached_data(self, filters):
        """Filtre le DataFrame du cache selon les cases cochées."""
        if self.cached_opportunities is None:
            return pd.DataFrame()
            
        df = self.cached_opportunities.copy()
        
        platforms_to_keep = set()
        if filters.get("hl"): platforms_to_keep.add("Hyperliquid")
        if filters.get("px"): platforms_to_keep.add("Paradex")
        if filters.get("lt"): platforms_to_keep.add("Lighter")
        if filters.get("ex"): platforms_to_keep.add("Extended")
        
        df = df[
            (df['Long Sur'].isin(platforms_to_keep)) & 
            (df['Short Sur'].isin(platforms_to_keep))
        ]
        return df


# --- SECTION 4 : POINT D'ENTRÉE PRINCIPAL ---

if __name__ == "__main__":
    # Assure-toi d'avoir installé : pip install ttkbootstrap pandas requests eth-account hyperliquid-python-sdk lighter
    root = ttk.Window(themename="cyborg")
    app = FundingScannerApp(root)
    root.mainloop()