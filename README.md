# Funding Farming Bot v2.0

Application moderne de farming de funding avec stratégies delta-neutral automatiques.

## Nouveautés v2.0

- **Interface CustomTkinter** avec design Glassmorphism professionnel
- **Trading complet** sur 4 plateformes (Hyperliquid, Paradex, Lighter, Extended/X10)
- **Algorithme optimisé** avec calcul des frais et slippage réels
- **Architecture modulaire** avec séparation par plateforme
- **Monitoring temps réel** des positions et PnL
- **Gestion automatique** : Take Profit, Stop Loss, reversal detection

## Caractéristiques

### Plateformes Supportées

| Plateforme | Funding Data | Trading | Status |
|-----------|--------------|---------|--------|
| Hyperliquid | ✅ | ✅ | Complet |
| Paradex | ✅ | ✅ | Complet |
| Lighter | ✅ | ✅ | Complet |
| Extended (X10) | ✅ | ✅ | Complet |

### Fonctionnalités Principales

1. **Scanner de Fundings**
   - Scan multi-plateformes en temps réel
   - Calcul du spread net (après frais et slippage)
   - Filtrage par plateforme et paire
   - Top 25 meilleures opportunités

2. **Bot Delta Neutral**
   - Exécution automatique LONG + SHORT
   - Rollback automatique en cas d'échec
   - Configuration du stake et levier
   - Auto-management (TP/SL/reversal)

3. **Dashboard Portfolio**
   - Soldes en temps réel de toutes les plateformes
   - PnL total et par plateforme
   - Funding accumulé

4. **Statistiques Airdrops**
   - Tracking ROI par plateforme
   - Historique des performances

5. **Configuration API**
   - Interface simple pour toutes les clés API
   - Sauvegarde sécurisée
   - Validation automatique

## Installation

### Prérequis

- Python 3.9+
- pip

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Dépendances principales

- `customtkinter` : Interface moderne
- `hyperliquid-python-sdk` : SDK Hyperliquid
- `lighter` : SDK Lighter
- `x10-python-trading-starknet` : SDK Extended/X10
- `pandas` : Traitement de données
- `requests` : Appels HTTP

## Configuration

### 1. Configurer les clés API

Lancez l'application et allez dans l'onglet **Settings**.

#### Hyperliquid
- **Private Key** : Votre clé privée (0x...)

#### Paradex
- **Wallet Address** : Votre adresse (0x...)
- **JWT Token** : Token d'authentification

#### Lighter
- **API Private Key** : Clé privée API
- **Account Index** : Index du compte (0, 1, 2...)
- **API Key Index** : Index de la clé API (2 par défaut)

#### Extended (X10)
- **API Key** : Clé API
- **Public Key** : Clé publique
- **Private Key** : Clé privée
- **Vault ID** : ID du vault

### 2. Sauvegarder

Cliquez sur **Save Configuration**. Les clés sont stockées dans `config.json`.

## Utilisation

### Lancer l'application

```bash
python main.py
```

### Workflow typique

1. **Scanner** : Recherchez des opportunités
   - Sélectionnez les plateformes à scanner
   - Cliquez sur "Scan Opportunities"
   - Cliquez sur une opportunité pour la sélectionner

2. **Bot** : Exécutez une stratégie
   - L'opportunité sélectionnée s'affiche automatiquement
   - Configurez le stake size (ex: 100 USD)
   - Configurez le levier (ex: 5x)
   - (Optionnel) Configurez Take Profit et Stop Loss
   - Cliquez sur "Execute Strategy"

3. **Dashboard** : Suivez votre portfolio
   - Cliquez sur "Refresh Data" pour actualiser
   - Visualisez vos soldes par plateforme

## Architecture

```
BotFarmAirdrop/
├── main.py                  # Point d'entrée
├── config.json              # Configuration (généré)
├── requirements.txt         # Dépendances
│
├── src/
│   ├── core/                # Logique métier
│   │   ├── models.py        # Modèles de données
│   │   └── scanner.py       # Algorithme de scan
│   │
│   ├── platforms/           # Implémentations par plateforme
│   │   ├── base.py          # Classe abstraite
│   │   ├── hyperliquid/
│   │   ├── paradex/
│   │   ├── lighter/
│   │   └── extended/
│   │
│   ├── trading/             # Moteur de trading
│   │   ├── executor.py      # Exécuteur unifié
│   │   └── position_manager.py  # Gestion positions
│   │
│   ├── ui/                  # Interface utilisateur
│   │   ├── app.py           # Application principale
│   │   ├── theme.py         # Thème Glassmorphism
│   │   ├── components/      # Composants réutilisables
│   │   └── pages/           # Pages de l'app
│   │
│   └── config/              # Gestion configuration
│       └── manager.py
│
└── old/                     # Ancien code (archivé)
```

## Algorithme

### Calcul du Spread Net

```
Net Spread = Gross Spread - Frais - Slippage

Frais par plateforme (taker) :
- Hyperliquid : 0.03%
- Paradex : 0.05%
- Lighter : 0.05%
- Extended : 0.05%

Slippage estimé :
- Hyperliquid : 0.10%
- Paradex : 0.15%
- Lighter : 0.15%
- Extended : 0.20%

Coût total = (Entry Fee + Exit Fee + Slippage) / 24h * leverage
```

### Score d'Opportunité

```
Score (1h) = Spread (1h) % × Min Leverage × 100
```

Les opportunités sont classées par score décroissant.

## Sécurité

- Les clés API sont stockées localement dans `config.json`
- Un backup automatique (`config.json.bak`) est créé avant chaque sauvegarde
- Les clés privées sont masquées dans l'interface (show="*")
- Aucune donnée n'est envoyée vers des serveurs externes

## Dépannage

### CustomTkinter non installé

```bash
pip install customtkinter
```

### SDK manquants

Certains SDKs peuvent nécessiter des installations spécifiques :

```bash
# Hyperliquid
pip install hyperliquid-python-sdk eth-account

# Lighter (vérifier la documentation officielle)
pip install lighter

# X10 Starknet (vérifier la documentation officielle)
pip install x10-python-trading-starknet
```

### Erreur "Platform not available"

Vérifiez que vos clés API sont correctement configurées dans **Settings**.

### Les scans ne retournent rien

- Vérifiez votre connexion internet
- Vérifiez que les plateformes sont bien sélectionnées
- Vérifiez que vos clés API sont valides

## Développement

### Ajouter une nouvelle plateforme

1. Créer `src/platforms/nouvelle_plateforme/api.py`
2. Hériter de `BasePlatformAPI`
3. Implémenter toutes les méthodes abstraites
4. Enregistrer avec `PlatformFactory.register()`

### Modifier le thème

Éditez `src/ui/theme.py` pour ajuster les couleurs et styles.

## Licence

Projet personnel - Tous droits réservés

## Contact

Pour toute question ou suggestion, créez une issue sur GitHub.

---

**Version** : 2.0.0
**Date** : Novembre 2025
**Auteur** : Funding Farming Bot Team
