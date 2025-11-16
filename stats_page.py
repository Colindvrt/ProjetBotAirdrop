# Fichier: stats_page.py
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import font

class StatsPage(ttk.Frame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app_controller = app_controller

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        main_frame.rowconfigure(1, weight=1) 
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1) 

        title_label = ttk.Label(main_frame, text="Analyse ROI Airdrop", 
                                font=('-family "Calibri" -size 24 -weight bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # --- Cadre 1: Formulaire de Saisie ---
        form_frame = ttk.Labelframe(main_frame, text=" Entrer un Airdrop (Design) ", padding=20)
        form_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        
        form_frame.columnconfigure(1, weight=1) 

        # --- MODIFIÉ : Ajout de "Extended" ---
        ttk.Label(form_frame, text="Airdrop:").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        airdrop_combo = ttk.Combobox(
            form_frame, 
            values=["Paradex", "Lighter", "Hyperliquid", "Extended", "Autre"],
            state="readonly"
        )
        airdrop_combo.current(0)
        airdrop_combo.grid(row=0, column=1, sticky="we", padx=5, pady=10)
        # --- FIN MODIFICATION ---

        ttk.Label(form_frame, text="Tokens Reçus:").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        ttk.Entry(form_frame).grid(row=1, column=1, sticky="we", padx=5, pady=10)
        
        ttk.Label(form_frame, text="Prix du Token ($):").grid(row=2, column=0, sticky="w", padx=5, pady=10)
        ttk.Entry(form_frame).grid(row=2, column=1, sticky="we", padx=5, pady=10)
        
        save_button = ttk.Button(form_frame, text="Ajouter aux Stats", bootstyle="success")
        save_button.grid(row=3, column=0, columnspan=2, sticky="we", padx=5, pady=20)

        # --- Cadre 2: Tableau des Stats ---
        stats_frame = ttk.Labelframe(main_frame, text=" Résultats (Design) ", padding=20)
        stats_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        stats_frame.rowconfigure(0, weight=1)
        stats_frame.columnconfigure(0, weight=1)

        columns = ("Airdrop", "Valeur ($)", "Volume Fait", "Frais Payés", "ROI (Val/Frais)")
        stats_tree = ttk.Treeview(stats_frame, columns=columns, show="headings", bootstyle="darkly")
        stats_tree.grid(row=0, column=0, sticky="nsew")

        for col in columns:
            stats_tree.heading(col, text=col)
            stats_tree.column(col, width=100, anchor="c")
            
        stats_tree.column("Airdrop", anchor="w")
        stats_tree.column("ROI (Val/Frais)", anchor="e")

        # --- MODIFIÉ : Ajout de "Extended" ---
        stats_tree.insert("", "end", values=("Paradex", "$ 1,200.00", "$ 1,500,000", "$ 350.00", "3.4x"))
        stats_tree.insert("", "end", values=("Hyperliquid", "$ 850.50", "$ 2,100,000", "$ 525.00", "1.6x"))
        stats_tree.insert("", "end", values=("Lighter", "En attente...", "$ 800,000", "$ 120.00", "N/A"))
        stats_tree.insert("", "end", values=("Extended", "En attente...", "$ 0", "$ 0.00", "N/A"))
        # --- FIN MODIFICATION ---

        scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=stats_tree.yview)
        stats_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")