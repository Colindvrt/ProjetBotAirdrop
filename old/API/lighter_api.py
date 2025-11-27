# Fichier: API/lighter_api.py
import requests
import pandas as pd
import re
import asyncio
try:
    import lighter
except ImportError:
    print("ERREUR CRITIQUE: La bibliothèque 'lighter' est requise. Exécute : pip install lighter")
    lighter = None

class LighterAPI:
    """Classe pour gérer la connexion et le trading sur Lighter."""
    
    def __init__(self, api_config):
        """Initialise le trader avec les 3 clés de config."""
        print("[Lighter Trader] Initialisation...")
        self.base_url = "https://mainnet.zklighter.elliot.ai"
        
        self.api_private_key = api_config.get("key")
        self.account_index_str = api_config.get("account_index")
        self.api_key_index_str = api_config.get("api_key_index")
        
        if not self.api_private_key or not self.account_index_str or not self.api_key_index_str:
            raise ValueError("Lighter: Clé Privée API, Account Index, ou API Key Index manquant.")
            
        try:
            self.account_index = int(self.account_index_str)
            self.api_key_index = int(self.api_key_index_str)
        except ValueError:
             raise ValueError("Lighter: Account Index ou API Key Index n'est pas un nombre.")
        
        print(f"[Lighter Trader] Initialisation terminée pour Account {self.account_index} / Key {self.api_key_index}.")

    async def _async_get_account_balance(self):
        """[LOGIQUE ASYNC] Se connecte au SignerClient et récupère le solde."""
        if lighter is None:
            raise ImportError("Bibliothèque Lighter non trouvée.")
            
        client = None
        try:
            client = lighter.SignerClient(
                url=self.base_url,
                private_key=self.api_private_key,
                account_index=self.account_index,
                api_key_index=self.api_key_index
            )
            response, err = await client.get_account()
            if err is not None:
                raise Exception(f"Erreur de l'API Lighter: {err}")
            
            target_sub_account_id = f"{self.account_index}-{self.api_key_index}"
            
            if response.sub_accounts and target_sub_account_id in response.sub_accounts:
                sub_account = response.sub_accounts[target_sub_account_id]
                balance_str = sub_account.portfolio_value
                return float(balance_str)
            else:
                print(f"[AVERTISSEMENT Lighter] Sub-account {target_sub_account_id} non trouvé ou solde nul.")
                return 0.0
        except Exception as e:
            print(f"[ERREUR Lighter Async] Impossible de récupérer le solde: {e}")
            return None
        finally:
            if client:
                await client.close()

    def get_account_balance(self):
        """[TEST API] Wrapper synchrone pour appeler la fonction async."""
        print("[Lighter Trader] Appel de get_account_balance (réel)...")
        try:
            return asyncio.run(self._async_get_account_balance())
        except Exception as e:
            print(f"Erreur asyncio.run: {e}")
            return None
    
    # def open_market_order(self, pair, is_buy, notional_usd, leverage):
    #    pass

# --- Fonctions de Scan (statiques) ---
def get_lighter_details_map():
    """[LIGHTER - APPEL 1 - STATIQUE] Crée une carte : Symbole -> Levier Max"""
    print("-> Appel API Lighter (Détails /orderBookDetails)...")
    url = "https://mainnet.zklighter.elliot.ai/api/v1/orderBookDetails"
    headers = {"accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        markets_list = data.get('order_book_details', []) 
        details_map = {}
        if not markets_list: 
            print("Erreur Lighter (E1): 'order_book_details' vide ou structure inconnue.")
            return None
        for market_data in markets_list: 
            pair_name = market_data.get('symbol')
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
        print(f"Lighter (E1): Carte de {len(details_map)} leviers créée.")
        return details_map
    except Exception as e:
        print(f"Erreur Lighter (E1): {e}")
        return None
        
def get_lighter_funding_data():
    """[LIGHTER - APPEL 2 - DYNAMIQUE] Récupère les taux."""
    try:
        print("-> Appel API Lighter (Taux)...")
        details_map = get_lighter_details_map()
        if not details_map:
            print("Lighter: Échec de l'Étape 1 (Détails). Les leviers seront à 1x.")
            details_map = {} 
        url = "https://mainnet.zklighter.elliot.ai/api/v1/funding-rates"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status() 
        data = response.json()
        all_rates_list = data.get('funding_rates', [])
        funding_data = []
        for item in all_rates_list:
            if item.get('exchange') == 'lighter':
                pair_name = item.get('symbol')
                max_leverage = details_map.get(pair_name, 1) 
                if max_leverage > 1:
                    eight_hour_rate = float(item.get('rate', 0))
                    hourly_funding_rate = eight_hour_rate / 8
                    funding_data.append({
                        "pair": pair_name, 
                        "rate_1h": hourly_funding_rate, 
                        "platform": "Lighter",
                        "max_leverage": max_leverage
                    })
        print(f"Lighter: {len(funding_data)} paires trouvées.")
        return funding_data
    except Exception as e:
        print(f"Erreur Lighter (E2): {e}")
        return []