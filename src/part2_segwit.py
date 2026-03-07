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

def main():
    print(" CS 216: Bitcoin Transaction Lab - Part 2: P2SH-SegWit (P2SH-P2WPKH)")
    # Step-1
    # Connect RPC
    print("Connecting to Bitcoin Daemon")
    rpc = rpc_connection()
    # Connection Test
    blockchain_info = rpc.getblockchaininfo()
    print(f"Connected to Bitcoin network: {blockchain_info['chain']}")
    print(f"Current block height: {blockchain_info['blocks']}")

if __name__=="__main__" :
    main()
