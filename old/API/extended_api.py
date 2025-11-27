# Fichier: API/extended_api.py
import re
import asyncio
import pandas as pd

# --- Importations du SDK X10 (version STARKNET) ---
try:
    # CORRECTION : Utilisation des bons imports pour x10-python-trading-starknet
    from x10_starknet.models.config import MAINNET_CONFIG
    from x10_starknet.public_client import PublicClient
    from x10_starknet.trading_client import TradingClient
    from x10_starknet.models.account import StarkPerpetualAccount
    
    X10_SDK_AVAILABLE = True
except ImportError:
    print("ERREUR CRITIQUE: La bibliothèque 'x10-python-trading-starknet' est requise. Exécute : pip install x10-python-trading-starknet")
    X10_SDK_AVAILABLE = False
# --- Fin Importations SDK ---


# --- PARTIE 1 : Fonctions de Scan (Corrigé avec le SDK Public) ---

async def _async_get_funding_data():
    """Helper Asynchrone pour le scan public."""
    if not X10_SDK_AVAILABLE:
        return []
        
    print("-> Appel API Extended (X10 Starknet) SDK (/public/markets)...")
    client = None
    try:
        # 1. Utiliser le client public (pas besoin de clés)
        client = PublicClient(MAINNET_CONFIG)
        
        # 2. Récupérer le dictionnaire des marchés
        markets_dict = await client.get_markets()
        
        if not markets_dict:
            print("Erreur Extended (E1): 'markets' vide ou introuvable via SDK.")
            return []

        funding_data = []
        # 3. Itérer sur les marchés
        for pair_name_api, market_data in markets_dict.items():
            
            if market_data.status != 'ACTIVE':
                continue
                
            stats = market_data.market_stats
            config = market_data.trading_config
            
            hourly_funding_rate = stats.funding_rate
            max_leverage = config.max_leverage

            if hourly_funding_rate is not None and max_leverage is not None:
                try:
                    match = re.match(r"^[A-Z0-9]+", pair_name_api)
                    pair_name_std = match.group(0) if match else pair_name_api
                    
                    funding_data.append({
                        "pair": pair_name_std, 
                        "rate_1h": float(hourly_funding_rate),
                        "platform": "Extended",
                        "max_leverage": int(max_leverage)
                    })
                except Exception as e:
                    print(f"Skipping Extended pair {pair_name_api} due to invalid data: {e}")
                    
        print(f"Extended: {len(funding_data)} paires trouvées.")
        return funding_data
        
    except Exception as e:
        print(f"Erreur Extended (SDK Public): {e}")
        return []
    finally:
        if client:
            await client.close_session() # CORRECTION: La méthode peut s'appeler close_session

def get_extended_funding_data():
    """
    [EXTENDED - APPEL UNIQUE] (Corrigé avec SDK)
    Wrapper synchrone pour le scan de funding.
    """
    try:
        return asyncio.run(_async_get_funding_data())
    except Exception as e:
        print(f"Erreur Extended (asyncio run): {e}")
        return []

# --- PARTIE 2 : Classe de Trading (Corrigé avec SDK Privé) ---

class ExtendedAPI:
    """
    Classe pour gérer la connexion et le trading sur Extended (X10)
    en utilisant le SDK 'x10-python-trading-starknet'.
    """
    def __init__(self, api_config):
        print("[Extended Trader] Initialisation (SDK X10 Starknet)...")
        
        if not X10_SDK_AVAILABLE:
            raise ImportError("Bibliothèque 'x10-python-trading-starknet' non trouvée.")

        # Lit la configuration de config.json
        self.api_key = api_config.get("api_key")
        self.public_key = api_config.get("public_key")
        self.private_key = api_config.get("private_key")
        self.vault_id_str = api_config.get("vault_id")

        if not all([self.api_key, self.public_key, self.private_key, self.vault_id_str]):
            raise ValueError("Extended: api_key, public_key, private_key, ou vault_id manquant.")

        try:
            self.vault_id = int(self.vault_id_str)
        except ValueError:
             raise ValueError("Extended: vault_id n'est pas un nombre.")

        # 1. Initialiser le compte Stark
        self.stark_account = StarkPerpetualAccount(
            api_key=self.api_key,
            public_key=self.public_key,
            private_key=self.private_key,
            vault=self.vault_id,
        )
        
        # 2. Initialiser le client de trading
        self.trading_client = TradingClient(MAINNET_CONFIG, self.stark_account)
        
        print("[Extended Trader] Initialisation SDK terminée.")

    async def _async_get_account_balance(self):
        """[LOGIQUE ASYNC] Récupère le solde via le SDK."""
        try:
            # Récupère l'aperçu du compte
            account_overview = await self.trading_client.get_account_overview()
            
            # La structure est celle que vous avez mentionnée (balance, equity, etc.)
            if account_overview and account_overview.balance is not None:
                # On utilise 'equity' (Capitaux propres) comme solde total
                # car il inclut les PNL non réalisés.
                # Si vous préférez le solde "Wallet", utilisez account_overview.balance
                return float(account_overview.equity)
            else:
                print("[ERREUR Extended] Structure de réponse 'account' non valide via SDK.")
                return 0.0
        except Exception as e:
            print(f"[ERREUR Extended SDK] Impossible de récupérer le solde: {e}")
            return None
        finally:
            if self.trading_client:
                await self.trading_client.close_session()

    def get_account_balance(self):
        """
        [TEST API] Récupère le solde du compte (réel via SDK).
        Wrapper synchrone pour appeler la fonction async.
        """
        print("[Extended Trader] Appel de get_account_balance (réel SDK)...")
        try:
            return asyncio.run(self._async_get_account_balance())
        except Exception as e:
            print(f"Erreur Extended (asyncio.run get_balance): {e}")
            return None

    # def open_market_order(self, pair, is_buy, notional_usd, leverage):
    #    pass