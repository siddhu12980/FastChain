# ASCII art and boxes
banner = """
███████╗ █████╗ ███████╗████████╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗
██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║
█████╗  ███████║███████╗   ██║   ██║     ███████║███████║██║██╔██╗ ██║
██╔══╝  ██╔══██║╚════██║   ██║   ██║     ██╔══██║██╔══██║██║██║╚██╗██║
██║     ██║  ██║███████║   ██║   ╚██████╗██║  ██║██║  ██║██║██║ ╚████║
╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
"""

status_box = """
┌──────────── NETWORK STATUS ────────────┐
│                                        │
│  🟢 Miners Online: [Loading]           │
│  📦 Pending Tx: [Loading]              │
│                                        │
└────────────────────────────────────────┘
"""

actions_box = """
┌─────────── QUICK ACTIONS ──────────┐
│                                    │
│  [/chain] 👁️  View Blockchain       │
│  [/transaction] 💸 Send Coins      │
│  [/balance] 💰 Check Balance       │
│  [/pending] 🕒 View Pending TX     │
│  [/ws/mineer] ⛏️  Connect as Miner  │
│                                    │
└────────────────────────────────────┘
"""


# async def lifespan(app:FastAPI):
#     print(banner)
#     print(status_box)
#     print(actions_box)
#     yield
#     print("Shutting down...")



def print_with_style():
    # ASCII art banner
    banner = """
    ███████╗ █████╗ ███████╗████████╗ ██████╗██╗  ██╗ █████╗ ██╗███╗   ██╗
    ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔════╝██║  ██║██╔══██╗██║████╗  ██║
    █████╗  ███████║███████╗   ██║   ██║     ███████║███████║██║██╔██╗ ██║
    ██╔══╝  ██╔══██║╚════██║   ██║   ██║     ██╔══██║██╔══██║██║██║╚██╗██║
    ██║     ██║  ██║███████║   ██║   ╚██████╗██║  ██║██║  ██║██║██║ ╚████║
    ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
    """
    print(banner)
    print("\n🚀 FastChain Server Starting...\n")
    print("┌──────────── SERVER INFO ────────────┐")
    print("│                                     │")
    print("│  🔗 Blockchain Initialized          │")
    print("│  📡 WebSocket Server Ready          │")
    print("│  ⚡ API Server Running              │")
    print("│                                     │")
    print("└─────────────────────────────────────┘\n")

    print(actions_box)