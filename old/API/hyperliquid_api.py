# Fichier: API/hyperliquid_api.py
import requests
import pandas as pd
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
import time

class HyperliquidAPI:
    """Classe pour gérer la connexion et le trading sur Hyperliquid."""
    
    def __init__(self, api_config):
        """Initialise le trader."""
        print("[HL Trader] Initialisation...")
        self.private_key = api_config.get("secret")
        if not self.private_key:
            raise ValueError("Clé privée (secret) non trouvée pour Hyperliquid.")
        try:
            self.account = Account.from_key(self.private_key)
            self.address = self.account.address
            print(f"[HL Trader] Connecté en tant que: {self.address}")
        except Exception as e:
            raise ValueError(f"Clé privée Hyperliquid invalide: {e}")
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.exchange = Exchange(self.account, constants.MAINNET_API_URL)
        print("[HL Trader] Initialisation terminée.")

    def get_account_balance(self):
        """Récupère le solde total (en USD) du compte."""
        try:
            user_state = self.info.user_state(self.address)
            if "marginSummary" in user_state:
                total_balance_usd = user_state["marginSummary"]["accountValue"]
                return float(total_balance_usd)
            else:
                return 0.0
        except Exception as e:
            print(f"[ERREUR HL Trader] Impossible de récupérer le solde: {e}")
            return None
    
    def open_market_order(self, pair, is_buy, notional_usd, leverage):
        """Ouvre un ordre MARKET sur Hyperliquid."""
        try:
            print(f"[HL Trader] Préparation de l'ordre: {'LONG' if is_buy else 'SHORT'} {pair}...")
            notional_usd = float(notional_usd)
            all_prices = self.info.all_mids()
            if pair not in all_prices:
                print(f"[ERREUR HL] Paire '{pair}' introuvable sur Hyperliquid.")
                return None
            current_price = float(all_prices[pair])
            print(f"[HL Trader] Prix actuel de {pair}: {current_price} USD")
            size_in_asset = notional_usd / current_price
            size_in_asset_rounded = round(size_in_asset, 6)
            if size_in_asset_rounded == 0.0:
                 print(f"[ERREUR HL] La taille de l'ordre est trop petite (0.0).")
                 return False
            print(f"[HL Trader] Définition du levier à {leverage}x pour {pair}...")
            try:
                leverage_response = self.exchange.update_leverage(int(leverage), pair) 
                print(f"[HL Trader] Réponse Levier: {leverage_response}")
            except Exception as e:
                print(f"[AVERTISSEMENT HL] Echec de la mise à jour du levier (peut-être déjà correct): {e}")
            print(f"[HL Trader] Envoi de l'ordre MARKET: {size_in_asset_rounded} {pair} (Notionnel: {notional_usd:.2f} USD)")
            order_response = self.exchange.market_open(
                pair, is_buy, size_in_asset_rounded, None 
            )
            print(f"[HL Trader] Réponse de l'ordre: {order_response}")
            if order_response["status"] == "ok":
                order_status = order_response["response"]["data"]["statuses"][0]
                if "filled" in order_status:
                    print(f"[SUCCÈS HL] Ordre {pair} rempli !")
                    return True
                else:
                    print(f"[ERREUR HL] L'ordre a été accepté mais non rempli: {order_status}")
                    return False
            else:
                error_message = order_response.get("response", "Réponse inconnue")
                print(f"[ÉCHEC HL] Échec de l'envoi de l'ordre: {error_message}")
                return False
        except Exception as e:
            print(f"[ERREUR HL Trader] Échec critique de open_market_order: {e}")
            return False

# --- Fonction de Scan (statique) ---
def get_hyperliquid_funding_data():
    """Récupère les données de Hyperliquid (Taux 1h + Levier)."""
    print("-> Appel API Hyperliquid...")
    url = "https://api.hyperliquid.xyz/info"
    payload = {"type": "metaAndAssetCtxs"}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status() 
        data = response.json()
        asset_metadata = data[0]['universe']
        asset_contexts = data[1]
        funding_data = []
        for i, asset_context in enumerate(asset_contexts):
            pair_name = asset_metadata[i].get('name')
            hourly_funding_rate = float(asset_context.get('funding', 0))
            max_leverage = int(asset_metadata[i].get('maxLeverage', 1))
            funding_data.append({
                "pair": pair_name, 
                "rate_1h": hourly_funding_rate, 
                "platform": "Hyperliquid",
                "max_leverage": max_leverage
            })
        print(f"Hyperliquid: {len(funding_data)} paires trouvées.")
        return funding_data
    except Exception as e:
        print(f"Erreur Hyperliquid: {e}")
        return []