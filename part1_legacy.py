from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# 1. Setup RPC Connection
# Using the credentials from your bitcoin.conf file
rpc_user = "harshith"
rpc_password = "iitindore"
rpc_port = 18443

# We connect directly to "LabWallet" so we can use wallet commands
rpc_url = f"http://{rpc_user}:{rpc_password}@127.0.0.1:{rpc_port}/wallet/LabWallet"

try:
    rpc = AuthServiceProxy(rpc_url)
    info = rpc.getblockchaininfo()
    print(f"Successfully connected to {info['chain']} network! Blocks: {info['blocks']}")

    # 2. Generate Three Legacy Addresses (A, B, and C)
    # The "" is for the label, and "legacy" enforces the P2PKH format
    address_A = rpc.getnewaddress("", "legacy")
    address_B = rpc.getnewaddress("", "legacy")
    address_C = rpc.getnewaddress("", "legacy")

    print("\n--- Legacy Addresses Generated ---")
    print(f"Address A: {address_A}")
    print(f"Address B: {address_B}")
    print(f"Address C: {address_C}")

    # 3. Fund Address A
    # Sending 5 BTC from your mined balance to Address A
    print("\n--- Funding Address A ---")
    txid_fund_A = rpc.sendtoaddress(address_A, 5.0)
    print(f"Transaction ID (Funding A): {txid_fund_A}")

    # 4. Mine 1 block to confirm the transaction!
    # Without this, Address A's funds remain unconfirmed and cannot be spent.
    mining_address = rpc.getnewaddress()
    rpc.generatetoaddress(1, mining_address)
    print("Mined 1 block to confirm the transaction.")

except JSONRPCException as e:
    print(f"RPC Error: {e.error['message']}")
except Exception as e:
    print(f"Connection Error: Ensure bitcoind is running. Details: {e}")