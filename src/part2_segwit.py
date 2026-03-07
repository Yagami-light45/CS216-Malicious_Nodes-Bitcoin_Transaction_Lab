# Import for connection

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration for RPC Connection

RPC_USER="varshith"
RPC_PASSWORD = "varshith@CS216"
RPC_HOST = "127.0.0.1"
RPC_PORT = 18443

# Response class for setup function
class setup_response:
    def __init__(self, success, message, data):
        self.success = success
        self.message = message
        self.data = data

# RPC Connection function
def rpc_connection():
    rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    return AuthServiceProxy(rpc_url)

# Setup function for wallets and addresses
def setup_wallet_addresses(rpc):
    wallet_name = "part-2"

    try:
        loaded_wallets = rpc.listwallets()

        if wallet_name not in loaded_wallets:
            try:
                rpc.loadwallet(wallet_name)
            except JSONRPCException:
                rpc.createwallet(wallet_name, False, False, "", False, False)

    except JSONRPCException as err:
        return setup_response(False, "Wallet setup failed", {"error": str(err)})

    try:
        wallet_rpc = AuthServiceProxy(
            f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}"
        )
    except JSONRPCException as err:
        return setup_response(False, "Wallet connection failed", {"error": str(err)})

    try:
        address_A = wallet_rpc.getnewaddress("address-a-part2", "p2sh-segwit")
        address_B = wallet_rpc.getnewaddress("address-b-part2", "p2sh-segwit")
        address_C = wallet_rpc.getnewaddress("address-c-part2", "p2sh-segwit")
    except JSONRPCException as err:
        return setup_response(False, "Address generation failed", {"error": str(err)})

    return setup_response(
        True,
        "Wallet ready and addresses generated",
        {
            "wallet": wallet_rpc,
            "address_A": address_A,
            "address_B": address_B,
            "address_C": address_C
        }
    )


def main():
    print(" CS 216: Bitcoin Transaction Lab - Part 2: P2SH-SegWit (P2SH-P2WPKH)")
    # Step-1 Connect RPC
    print("Connecting to Bitcoin Daemon")
    rpc = rpc_connection()
    # Connection Test
    blockchain_info = rpc.getblockchaininfo()
    print(f"Connected to Bitcoin network: {blockchain_info['chain']}")
    print(f"Current block height: {blockchain_info['blocks']}")

    # Step-2 Create wallet and setup 3 addresses A', B', C'
    setup_response=setup_wallet_addresses(rpc)
    if not setup_response.success:
        print(f"Failure while setup: {setup_response.message}")
        return
    else:
        print(setup_response.message)

    
    
if __name__=="__main__" :
    main()
