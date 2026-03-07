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

    except JSONRPCException as e:
        print(f"\n RPC Error: {e.error['message']}")
    except Exception as e:
        print(f"\n Unexpected Error: {e}")

if __name__ == "__main__":
    main()