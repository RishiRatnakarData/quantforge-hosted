"""Small, versioned discovery directory. Not a live exchange listing or index membership file.

No market prices, returns, recommendations, or licensed holdings are stored here.
The directory is deliberately curated for personal navigation; arbitrary tickers remain searchable
in live mode even if not listed here.
"""

from __future__ import annotations

# Format: SYMBOL|FULL NAME. Groups are broad browsing categories, not classifications
# sourced from an index provider. Recheck listings before relying on an entry.
GROUPS: dict[str, str] = {
    "Technology": """
AAPL|Apple
MSFT|Microsoft
NVDA|NVIDIA
AVGO|Broadcom
ORCL|Oracle
CRM|Salesforce
ADBE|Adobe
AMD|Advanced Micro Devices
INTC|Intel
QCOM|Qualcomm
TXN|Texas Instruments
AMAT|Applied Materials
LRCX|Lam Research
KLAC|KLA Corporation
MU|Micron Technology
ADI|Analog Devices
MRVL|Marvell Technology
SNPS|Synopsys
CDNS|Cadence Design Systems
PANW|Palo Alto Networks
CRWD|CrowdStrike
FTNT|Fortinet
NOW|ServiceNow
INTU|Intuit
IBM|IBM
ACN|Accenture
PLTR|Palantir Technologies
DELL|Dell Technologies
HPQ|HP Inc.
HPE|Hewlett Packard Enterprise
ANET|Arista Networks
NET|Cloudflare
DDOG|Datadog
SNOW|Snowflake
MDB|MongoDB
SHOP|Shopify
UBER|Uber Technologies
TSM|Taiwan Semiconductor Manufacturing
ASML|ASML Holding
ARM|Arm Holdings
SAP|SAP
""",
    "Communication": """
GOOGL|Alphabet (Google), Class A
GOOG|Alphabet (Google), Class C
META|Meta Platforms (Facebook)
NFLX|Netflix
DIS|Walt Disney
CMCSA|Comcast
T|AT&T
VZ|Verizon
TMUS|T-Mobile US
SPOT|Spotify
PINS|Pinterest
SNAP|Snap
RDDT|Reddit
EA|Electronic Arts
TTWO|Take-Two Interactive
RBLX|Roblox
""",
    "Consumer": """
AMZN|Amazon
TSLA|Tesla
WMT|Walmart
COST|Costco
HD|Home Depot
LOW|Lowe's
TGT|Target
MCD|McDonald's
SBUX|Starbucks
NKE|Nike
LULU|Lululemon Athletica
CMG|Chipotle Mexican Grill
YUM|Yum! Brands
DPZ|Domino's Pizza
KO|Coca-Cola
PEP|PepsiCo
PG|Procter & Gamble
CL|Colgate-Palmolive
KMB|Kimberly-Clark
EL|Estée Lauder
KR|Kroger
DG|Dollar General
DLTR|Dollar Tree
ABNB|Airbnb
BKNG|Booking Holdings
MAR|Marriott International
HLT|Hilton Worldwide
F|Ford Motor
GM|General Motors
RIVN|Rivian Automotive
NIO|NIO
BABA|Alibaba Group
PDD|PDD Holdings
MELI|MercadoLibre
""",
    "Finance": """
BRK.B|Berkshire Hathaway Class B
JPM|JPMorgan Chase
BAC|Bank of America
WFC|Wells Fargo
C|Citigroup
GS|Goldman Sachs
MS|Morgan Stanley
BLK|BlackRock
SCHW|Charles Schwab
V|Visa
MA|Mastercard
AXP|American Express
PYPL|PayPal
COF|Capital One
USB|U.S. Bancorp
PNC|PNC Financial Services
TFC|Truist Financial
BK|Bank of New York Mellon
STT|State Street
CME|CME Group
ICE|Intercontinental Exchange
SPGI|S&P Global
MCO|Moody's
MSCI|MSCI
CB|Chubb
PGR|Progressive
TRV|Travelers
AIG|American International Group
MET|MetLife
PRU|Prudential Financial
COIN|Coinbase
HOOD|Robinhood Markets
SOFI|SoFi Technologies
""",
    "Healthcare": """
LLY|Eli Lilly
JNJ|Johnson & Johnson
UNH|UnitedHealth Group
ABBV|AbbVie
MRK|Merck & Co.
PFE|Pfizer
AMGN|Amgen
GILD|Gilead Sciences
BMY|Bristol Myers Squibb
REGN|Regeneron Pharmaceuticals
VRTX|Vertex Pharmaceuticals
ISRG|Intuitive Surgical
TMO|Thermo Fisher Scientific
DHR|Danaher
ABT|Abbott Laboratories
MDT|Medtronic
SYK|Stryker
BSX|Boston Scientific
CVS|CVS Health
CI|The Cigna Group
HCA|HCA Healthcare
ZTS|Zoetis
NVO|Novo Nordisk
AZN|AstraZeneca
NVS|Novartis
""",
    "Industrials": """
CAT|Caterpillar
DE|Deere & Company
GE|GE Aerospace
HON|Honeywell
RTX|RTX Corporation
LMT|Lockheed Martin
NOC|Northrop Grumman
GD|General Dynamics
BA|Boeing
UPS|United Parcel Service
FDX|FedEx
UNP|Union Pacific
CSX|CSX Corporation
NSC|Norfolk Southern
WM|Waste Management
RSG|Republic Services
ETN|Eaton
EMR|Emerson Electric
PH|Parker-Hannifin
ITW|Illinois Tool Works
MMM|3M
PCAR|PACCAR
DAL|Delta Air Lines
UAL|United Airlines
AAL|American Airlines
UBER|Uber Technologies
""",
    "Energy & materials": """
XOM|Exxon Mobil
CVX|Chevron
COP|ConocoPhillips
EOG|EOG Resources
SLB|SLB
HAL|Halliburton
OXY|Occidental Petroleum
VLO|Valero Energy
MPC|Marathon Petroleum
PSX|Phillips 66
KMI|Kinder Morgan
WMB|Williams Companies
NEE|NextEra Energy
DUK|Duke Energy
SO|Southern Company
D|Dominion Energy
AEP|American Electric Power
EXC|Exelon
CEG|Constellation Energy
NEM|Newmont
FCX|Freeport-McMoRan
NUE|Nucor
LIN|Linde
APD|Air Products and Chemicals
SHW|Sherwin-Williams
DOW|Dow
""",
    "Real estate": """
AMT|American Tower
PLD|Prologis
EQIX|Equinix
WELL|Welltower
O|Realty Income
SPG|Simon Property Group
PSA|Public Storage
DLR|Digital Realty Trust
VICI|VICI Properties
AVB|AvalonBay Communities
EQR|Equity Residential
CBRE|CBRE Group
""",
    "Index & ETFs": """
VOO|Vanguard S&P 500 ETF
SPY|SPDR S&P 500 ETF Trust
IVV|iShares Core S&P 500 ETF
VTI|Vanguard Total Stock Market ETF
SCHB|Schwab U.S. Broad Market ETF
ITOT|iShares Core S&P Total U.S. Stock Market ETF
QQQ|Invesco QQQ Trust
QQQM|Invesco NASDAQ 100 ETF
DIA|SPDR Dow Jones Industrial Average ETF
IWM|iShares Russell 2000 ETF
VT|Vanguard Total World Stock ETF
VXUS|Vanguard Total International Stock ETF
VEA|Vanguard FTSE Developed Markets ETF
VWO|Vanguard FTSE Emerging Markets ETF
EFA|iShares MSCI EAFE ETF
EEM|iShares MSCI Emerging Markets ETF
BND|Vanguard Total Bond Market ETF
AGG|iShares Core U.S. Aggregate Bond ETF
TLT|iShares 20+ Year Treasury Bond ETF
IEF|iShares 7-10 Year Treasury Bond ETF
SGOV|iShares 0-3 Month Treasury Bond ETF
SHY|iShares 1-3 Year Treasury Bond ETF
LQD|iShares iBoxx Investment Grade Corporate Bond ETF
HYG|iShares iBoxx High Yield Corporate Bond ETF
GLD|SPDR Gold Shares
IAU|iShares Gold Trust
SCHD|Schwab U.S. Dividend Equity ETF
VIG|Vanguard Dividend Appreciation ETF
VYM|Vanguard High Dividend Yield ETF
XLK|Technology Select Sector SPDR Fund
XLF|Financial Select Sector SPDR Fund
XLV|Health Care Select Sector SPDR Fund
XLE|Energy Select Sector SPDR Fund
XLI|Industrial Select Sector SPDR Fund
XLY|Consumer Discretionary Select Sector SPDR Fund
XLP|Consumer Staples Select Sector SPDR Fund
VNQ|Vanguard Real Estate ETF
SOXX|iShares Semiconductor ETF
SMH|VanEck Semiconductor ETF
ARKK|ARK Innovation ETF
""",
    "Crypto": """
BTC/USD|Bitcoin
ETH/USD|Ethereum
SOL/USD|Solana
LTC/USD|Litecoin
AVAX/USD|Avalanche
DOGE/USD|Dogecoin
LINK/USD|Chainlink
""",
}


def _build_catalog() -> tuple[dict[str, str], ...]:
    result = []
    seen = set()
    for category, content in GROUPS.items():
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            symbol, name = line.split("|", 1)
            if symbol in seen:
                continue
            seen.add(symbol)
            kind = "crypto" if category == "Crypto" else "etf" if category == "Index & ETFs" else "stock"
            result.append({"symbol": symbol, "name": name, "category": category, "asset_class": kind})
    return tuple(result)


CATALOG = _build_catalog()
BY_SYMBOL = {asset["symbol"]: asset for asset in CATALOG}
ETF_CATALOG_SYMBOLS = frozenset(entry["symbol"] for entry in CATALOG if entry["asset_class"] == "etf")


def display_name(symbol: str) -> str:
    """Fall back to ticker for assets not in the curated offline directory."""
    record = BY_SYMBOL.get(symbol.strip().upper())
    return record["name"] if record else symbol.strip().upper()


def directory_data() -> dict:
    """Small read-only catalog response; prices and listing status are not implied."""
    return {
        "entries": list(CATALOG),
        "categories": list(GROUPS),
        "total": len(CATALOG),
        "complete_market_listing": False,
        "note": "Curated navigation list, not exchange listings or index constituents.",
    }
