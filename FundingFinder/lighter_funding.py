# Fichier: test_lighter_final.py
import requests
import pandas as pd
from datetime import datetime
import json

def get_lighter_details_map():
    """
    [LIGHTER - APPEL 1 - STATIQUE]
    Appelle /orderBookDetails pour créer une carte : Symbole -> Levier Max
    """
    print("Étape 1: Appel de /orderBookDetails (pour les leviers)...")
    url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails"
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Structure confirmée par ton debug
        markets_list = data.get('order_book_details', []) 
        
        details_map = {}
        if not markets_list: 
            print("Erreur Lighter (E1): 'order_book_details' vide ou structure inconnue.")
            return None

        for market_data in markets_list: 
            pair_name = market_data.get('symbol')
            
            # --- CORRECTION : Suppression du filtre 'market_id >= 1000' ---
            # Nous ne pouvons pas différencier PERP et SPOT ici,
            # donc nous récupérons TOUS les leviers.
            
            margin_fraction_str = market_data.get('min_initial_margin_fraction')
            if margin_fraction_str:
                try:
                    margin_fraction = float(margin_fraction_str)
                    if margin_fraction > 0:
                        max_leverage = int(10000 / margin_fraction)
                    else:
                        max_leverage = 1
                except (ValueError, ZeroDivisionError, TypeError):
                    max_leverage = 1
            else:
                max_leverage = 1
                
            details_map[pair_name] = max_leverage
        
        print(f"Étape 1: OK. Carte de {len(details_map)} leviers créée.")
        return details_map
        
    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP Étape 1: {http_err} - {http_err.response.text}")
        return None
    except Exception as err:
        print(f"Erreur Étape 1: {err}")
        return None

def get_lighter_rates(details_map):
    """
    [LIGHTER - APPEL 2 - DYNAMIQUE]
    Appelle /funding-rates et combine avec la carte des leviers.
    """
    print("Étape 2: Appel de /funding-rates (pour les taux)...")
    url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        data = response.json()
        all_rates_list = data.get('funding_rates', [])
        
        if not all_rates_list:
            print("Erreur Étape 2: 'funding_rates' est vide.")
            return None
            
        funding_data = []
        
        for item in all_rates_list:
            if item.get('exchange') == 'lighter':
                pair_name = item.get('symbol')
                
                # Utiliser la carte pour trouver le levier
                # Si la paire n'est pas dans la carte (ex: un SPOT), on met 1x
                max_leverage = details_map.get(pair_name, 1)
                
                # On ne garde que les paires qui sont dans la carte (implicitement PERP)
                if pair_name in details_map:
                    eight_hour_rate = float(item.get('rate', 0))
                    hourly_funding_rate = eight_hour_rate / 8
                    
                    funding_data.append({
                        "Paire": pair_name,
                        "Taux (8h API)": eight_hour_rate,
                        "Levier Max": max_leverage,
                        "Funding (1h) %": hourly_funding_rate * 100,
                        "Funding (8h) %": eight_hour_rate * 100
                    })
        
        print("Étape 2: OK. Taux et leviers combinés.")
        return pd.DataFrame(funding_data)

    except requests.exceptions.HTTPError as http_err:
        print(f"Erreur HTTP Étape 2: {http_err} - {http_err.response.text}")
        return None
    except Exception as err:
        print(f"Erreur Étape 2: {err}")
        return None

# --- Point d'entrée du script ---
if __name__ == "__main__":
    
    # Étape 1: Construire la carte
    details_map = get_lighter_details_map()
    
    if details_map:
        # Étape 2: Récupérer les taux et calculer
        df = get_lighter_rates(details_map)
        
        if df is not None and not df.empty:
            pd.set_option('display.max_rows', None)
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            
            print(f"\n--- Taux de Funding Lighter (Corrigés) --- (au {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            
            print("\nTOP Funding (Positif - bon pour short) :")
            print(df.sort_values(by="Funding (8h) %", ascending=False).head(10))
            
            print("\nTOP Funding (Négatif - bon pour long) :")
            print(df.sort_values(by="Funding (8h) %", ascending=True).head(10))
        else:
            print("Échec du calcul des taux.")