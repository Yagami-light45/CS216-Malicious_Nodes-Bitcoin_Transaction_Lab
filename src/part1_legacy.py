from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import time

RPC_USER = "harshith"
RPC_PASS = "iitindore"
RPC_PORT = 18443
RPC_URL = f"http://{RPC_USER}:{RPC_PASS}@127.0.0.1:{RPC_PORT}/wallet/LabWallet"

def mine_block(rpc, miner_address, num_blocks=1):
    rpc.generatetoaddress(num_blocks, miner_address)
    print(f"    [+] Mined {num_blocks} block(s) to confirm transactions.")

def main():
    try:
        # Connect to the Bitcoin node
        rpc = AuthServiceProxy(RPC_URL)
        info = rpc.getblockchaininfo()
        print(f"Successfully connected to {info['chain']}! Current blocks: {info['blocks']}\n")

        # We need an address to receive the mining rewards
        miner_address = rpc.getnewaddress("", "legacy")

        print(" --- Step 1: Generating Legacy Addresses ---")
        addr_A = rpc.getnewaddress("Address_A", "legacy")
        addr_B = rpc.getnewaddress("Address_B", "legacy")
        addr_C = rpc.getnewaddress("Address_C", "legacy")
        
        print(f"    Address A: {addr_A}")
        print(f"    Address B: {addr_B}")
        print(f"    Address C: {addr_C}\n")

        print("--- Step 2: Funding Address A ---")
        txid_fund = rpc.sendtoaddress(addr_A, 5.0)
        print(f"    [+] Sent 5.0 BTC to A. TXID: {txid_fund}")
        mine_block(rpc, miner_address)

    except JSONRPCException as e:
        print(f"\n RPC Error: {e.error['message']}")
    except Exception as e:
        print(f"\n Unexpected Error: {e}")

if __name__ == "__main__":
    main()