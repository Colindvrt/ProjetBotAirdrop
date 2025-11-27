# Fichier: dashboard_page.py
import tkinter as tk
import ttkbootstrap as ttk
from tkinter import font

class DashboardPage(ttk.Frame):
    def __init__(self, parent, app_controller):
        super().__init__(parent)
        self.app_controller = app_controller

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(main_frame, text="Dashboard Global", 
                                font=('-family "Calibri" -size 24 -weight bold'))
        title_label.pack(pady=(0, 20), anchor="w")

        kpi_frame = ttk.Frame(main_frame)
        kpi_frame.pack(fill="x", pady=10)
        kpi_frame.columnconfigure(0, weight=1)
        kpi_frame.columnconfigure(1, weight=1)
        
        total_value_frame = ttk.Labelframe(kpi_frame, text=" Valeur Totale du Portfolio ", padding=20)
        total_value_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        total_value_label = ttk.Label(
            total_value_frame, text="$ 1,250.75", 
            font=('-family "Calibri" -size 28 -weight bold'), bootstyle="primary"
        )
        total_value_label.pack()

        pnl_frame = ttk.Labelframe(kpi_frame, text=" PNL Total (Non Réalisé) ", padding=20)
        pnl_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        pnl_label = ttk.Label(
            pnl_frame, text="+ $ 250.75", 
            font=('-family "Calibri" -size 28 -weight bold'), bootstyle="success"
        )
        pnl_label.pack()

        graph_frame = ttk.Frame(main_frame)
        graph_frame.pack(fill="both", expand=True, pady=20)
        graph_frame.columnconfigure(0, weight=2) 
        graph_frame.columnconfigure(1, weight=1) 

        chart_frame = ttk.Labelframe(graph_frame, text=" Évolution du Portfolio (Design) ", padding=10)
        chart_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        chart_canvas = tk.Canvas(chart_frame, bg="#2a2a2a", height=300, relief="flat", highlightthickness=0)
        chart_canvas.pack(fill="both", expand=True)
        
        # --- CORRECTION : Remplacement de -italic par -slant italic ---
        chart_canvas.create_text(
            150, 150, 
            text="[Placeholder pour le graphique PNL]", 
            fill="#6c757d", 
            font=('-family "Calibri" -size 14 -slant italic')
        )
        # --- FIN CORRECTION ---

        alloc_frame = ttk.Labelframe(graph_frame, text=" Allocation (Design) ", padding=20)
        alloc_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ttk.Label(alloc_frame, text="Hyperliquid: $ 510.20 (40.8%)").pack(anchor="w", pady=(0, 2))
        ttk.Progressbar(alloc_frame, value=40.8, bootstyle="info").pack(fill="x", pady=(0, 10))
        ttk.Label(alloc_frame, text="Paradex: $ 400.05 (32.0%)").pack(anchor="w", pady=(0, 2))
        ttk.Progressbar(alloc_frame, value=32.0, bootstyle="success").pack(fill="x", pady=(0, 10))
        ttk.Label(alloc_frame, text="Lighter: $ 240.50 (19.2%)").pack(anchor="w", pady=(0, 2))
        ttk.Progressbar(alloc_frame, value=19.2, bootstyle="warning").pack(fill="x", pady=(0, 10))
        ttk.Label(alloc_frame, text="Extended: $ 100.00 (8.0%)").pack(anchor="w", pady=(0, 2))
        ttk.Progressbar(alloc_frame, value=8.0, bootstyle="danger").pack(fill="x", pady=(0, 10))