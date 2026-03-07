# Import for connection

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Configuration for RPC Connection

RPC_USER="varshith"
RPC_PASSWORD = "varshith@CS216"
RPC_HOST = "127.0.0.1"
RPC_PORT = 18443


 
# RPC Connection function
def rpc_connection():
    rpc_url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    return AuthServiceProxy(rpc_url)


# Response class for setup function
class setup_response:
    def __init__(self, success, message, data):
        self.success = success
        self.message = message
        self.data = data


# Setup function for wallets and addresses
def setup_wallet_addresses(rpc)-> setup_response:
    print("Setting up wallet and addresses")
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

# Response class for funding function
class funding_response:
    def __init__(self, success, message, data):
        self.success=success
        self.message=message
        self.data=data
        
        
# Funding function for address A
def fund_wallet(wallet_rpc, address_A)-> funding_response:
    print("Funding wallet address A")
    try:
        block_hashes = wallet_rpc.generatetoaddress(101, address_A)
        print(f"Mined {len(block_hashes)} blocks")

        balance = wallet_rpc.getbalance()
        print(f"Wallet balance: {balance} BTC")

        utxos = wallet_rpc.listunspent(1, 9999999, [address_A])
        print(f"\nUTXOs available for Address A': {len(utxos)}")
        if utxos:
            print(f"  Sample UTXO - txid: {utxos[0]['txid'][:16]}..., amount: {utxos[0]['amount']} BTC")
    except JSONRPCException as err:
        print(f"Error while funding address A: {err}")
        return funding_response(False,"RPC request error", {})
    return funding_response(True, "Funding succesful",utxos)

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

    # Step-3 Fund the first address for transactions
    fund_response=fund_wallet(setup_response.data["wallet"], setup_response.data["address_A"])
    if not fund_response.success:
        print(f"Funding error: {fund_response.message}")
    else:
        print(fund_response.message)
    
    # Step-4 
    
if __name__=="__main__" :
    main()
