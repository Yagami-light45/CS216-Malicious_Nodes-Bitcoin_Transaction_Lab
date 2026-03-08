import json
import traceback
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

RPC_USER = "harshith"          
RPC_PASSWORD = "iitindore"  
RPC_HOST = "127.0.0.1"
RPC_PORT = 18443              
#connect to bitcoin daemon
def get_rpc_connection():       
    return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

#fns for formatting
def print_separator(title):
    print(f"\n{'=' * 70}\n {title}\n{'=' * 70}")

def print_json(data, title=""):
    if title: print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))

#fn to save data to a json
def save_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Data saved to {filename}")


#Setup Wallet and Address Generation

def setup_wallet_and_addresses(rpc):
    print_separator("PART 1: SETUP - Wallet and Address Generation")
    wallet_name = "lab"
    
    try:
        if wallet_name not in rpc.listwallets():
            try:
                rpc.loadwallet(wallet_name)
                print(f"Loaded existing wallet: {wallet_name}")
            except JSONRPCException:
                rpc.createwallet(wallet_name, False, False, "", False, False)
                print(f"Created new wallet: {wallet_name}")
        else:
            print(f"Wallet already loaded: {wallet_name}")
    except JSONRPCException as e:
        print(f"Wallet operation error: {e}")
        try:
            rpc.createwallet(wallet_name, False, False, "", False, True)
            print(f"Created new wallet: {wallet_name}")
        except: pass
    
    wallet_rpc = AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}")
    
    addr_A = wallet_rpc.getnewaddress("Address_A", "legacy")
    addr_B = wallet_rpc.getnewaddress("Address_B", "legacy")
    addr_C = wallet_rpc.getnewaddress("Address_C", "legacy")
    
    print(f"\nGenerated Legacy (P2PKH) Addresses:\n  Address A: {addr_A}\n  Address B: {addr_B}\n  Address C: {addr_C}\n\nAddress Validation:")
    for name, addr in [("A", addr_A), ("B", addr_B), ("C", addr_C)]:
        print(f"  Address {name}: Type={wallet_rpc.getaddressinfo(addr).get('desc', 'unknown')}")
        
    return wallet_rpc, addr_A, addr_B, addr_C

def main():
    print("=" * 70 + "\n CS 216: Bitcoin Transaction Lab - Part 1: Legacy (P2PKH)\n" + "=" * 70)
    try:
        print("\nConnecting to Bitcoin daemon...")
        rpc = get_rpc_connection()
        b_info = rpc.getblockchaininfo()
        print(f"Connected to Bitcoin network: {b_info['chain']}\nCurrent block height: {b_info['blocks']}")
        
        wallet_rpc, address_A, address_B, address_C = setup_wallet_and_addresses(rpc)
        
    except JSONRPCException as e:
        print(f"\nRPC Error: {e}\nMake sure bitcoind is running in regtest mode with correct RPC credentials.")
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()