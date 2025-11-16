# Fichier: API/paradex_api.py
import requests
import pandas as pd
import re

class ParadexAPI:
    """Classe pour gérer la connexion et le trading sur Paradex."""
    
    def __init__(self, api_config):
        """Initialise le trader."""
        print("[Paradex Trader] Initialisation...")
        self.api_key = api_config.get("key") # Adresse 0x...
        self.api_secret = api_config.get("secret") # Clé privée Paradex
        
        if not self.api_key or not self.api_secret:
            raise ValueError("Adresse (key) ou Secret non trouvée pour Paradex.")
        print("[Paradex Trader] Initialisation terminée.")

    def get_account_balance(self):
        """[TEST API] Récupère le solde du compte (Placeholder)."""
        print("[Paradex Trader] Appel de get_account_balance (non implémenté)...")
        if self.api_key and self.api_secret:
             return 123.45 # Renvoie un solde factice
        else:
            return None

    # def open_market_order(self, pair, is_buy, notional_usd, leverage):
    #    pass

# --- Fonctions de Scan (statiques) ---
def get_paradex_details_map():
    """[PARADEX - APPEL 1 - STATIQUE] Crée une carte : Symbole -> { Période, Levier }"""
    url = "https://api.prod.paradex.trade/v1/markets"
    headers = {"accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        markets_list = data.get('results', []) 
        details_map = {}
        if not markets_list: 
            print("Erreur Paradex (E1): 'results' vide dans /markets.")
            return None
        for market_data in markets_list: 
            pair_name = market_data.get('symbol')
            if market_data.get('asset_kind') == 'PERP':
                period = int(market_data.get('funding_period_hours', 1))
                if period == 0: period = 1
                imf_base_str = market_data.get('delta1_cross_margin_params', {}).get('imf_base', '1.0')
                try:
                    max_leverage = int(1 / float(imf_base_str))
                except (ValueError, ZeroDivisionError):
                    max_leverage = 1
                details_map[pair_name] = {'period': period, 'leverage': max_leverage}
        return details_map
    except Exception as e:
        print(f"Erreur Paradex (E1): {e}")
        return None

def get_paradex_funding_data():
    """[PARADEX - APPEL 2 - DYNAMIQUE] Récupère les taux."""
    try:
        print("-> Appel API Paradex...")
        details_map = get_paradex_details_map()
        if not details_map:
            print("Paradex: Échec de l'Étape 1 (Détails)")
            return []
        url = "https://api.prod.paradex.trade/v1/markets/summary"
        params = {"market": "ALL"}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status() 
        data = response.json()
        markets_list = data.get('results', [])
        funding_data = []
        for market_data in markets_list:
            pair_name = market_data.get('symbol', '')
            details = details_map.get(pair_name)
            if details:
                rate_for_period = float(market_data.get('funding_rate', 0))
                funding_period = details.get('period', 1)
                hourly_funding_rate = rate_for_period / funding_period
                funding_data.append({
                    "pair": pair_name, 
                    "rate_1h": hourly_funding_rate,
                    "platform": "Paradex",
                    "max_leverage": details.get('leverage')
                })
        print(f"Paradex: {len(funding_data)} paires trouvées.")
        return funding_data
    except Exception as e:
        print(f"Erreur dans get_paradex_data (E2): {e}")
        return []