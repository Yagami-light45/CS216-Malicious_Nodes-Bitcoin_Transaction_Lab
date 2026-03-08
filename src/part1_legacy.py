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

#Funding to A
def fund_address_A(rpc, wallet_rpc, addr_A):
    print_separator("PART 2: FUNDING ADDRESS A")
    
    balance = wallet_rpc.getbalance()
    print(f"Starting wallet balance: {balance} BTC")
    
    if balance < 5.0:
        print("\nInsufficient balance. Mining 101 blocks to generate mature funds...")
        miner_addr = wallet_rpc.getnewaddress()
        rpc.generatetoaddress(101, miner_addr)
        balance = wallet_rpc.getbalance()
        print(f"New wallet balance: {balance} BTC")
        
    print(f"\nSending 5.0 BTC to Address A ({addr_A})...")
    txid_fund_A = wallet_rpc.sendtoaddress(addr_A, 5.0)
    print(f"Funding TXID: {txid_fund_A}")
    
    print("\nMining 1 block to confirm the transaction...")
    miner_addr = wallet_rpc.getnewaddress()
    rpc.generatetoaddress(1, miner_addr)

    tx_info = wallet_rpc.gettransaction(txid_fund_A)
    print(f"Confirmations: {tx_info.get('confirmations', 0)}")
    
    return txid_fund_A

def create_tx_A_to_B(rpc, wallet_rpc, addr_A, addr_B):
    print_separator("PART 3: TRANSACTION A -> B (2.0 BTC)")
    
    # listunspent(minconf, maxconf, [addresses])
    unspent_A_list = wallet_rpc.listunspent(1, 9999999, [addr_A])
    
    if not unspent_A_list:
        print("Error: No confirmed UTXOs found for Address A. Did you mine a block after funding?")
        return None
        
    utxo_A = unspent_A_list[0]
    print_json(utxo_A, "Selected UTXO from Address A")
    
    amount_in = float(utxo_A['amount'])
    amount_to_send = 2.0
    fee = 0.0001
    
    change_A = round(amount_in - amount_to_send - fee, 8)
    
    print(f"\nMath:\n  Input:  {amount_in} BTC\n  Send:   {amount_to_send} BTC\n  Fee:    {fee} BTC\n  Change: {change_A} BTC (Back to Address A)")
    #create tx
    inputs = [{"txid": utxo_A['txid'], "vout": utxo_A['vout']}]
    
    outputs = {
        addr_B: amount_to_send,
        addr_A: change_A
    }
    
    print("\nCreating raw transaction...")
    raw_tx_hex = wallet_rpc.createrawtransaction(inputs, outputs)
    
    decoded_tx = wallet_rpc.decoderawtransaction(raw_tx_hex)
    print_json(decoded_tx, "Decoded Unsigned Raw Transaction")

    #Sign the Transaction
    print("\nSigning transaction with wallet keys...")
    signed_tx = wallet_rpc.signrawtransactionwithwallet(raw_tx_hex)
    
    if not signed_tx['complete']:
        print("Error: Signing failed!")
        return None
        
    print("Signing successful!")

    #Broadcast to the Network
    print("\nBroadcasting transaction to Regtest network...")
    txid_AB = wallet_rpc.sendrawtransaction(signed_tx['hex'])
    print(f"Transaction ID (A -> B): {txid_AB}")
    
    print("\nMining 1 block to confirm the A -> B transaction...")
    miner_addr = wallet_rpc.getnewaddress()
    rpc.generatetoaddress(1, miner_addr)
    
    # Verify confirmation
    tx_info = wallet_rpc.gettransaction(txid_AB)
    print(f"Confirmations: {tx_info.get('confirmations', 0)}")
    
    return txid_AB

def main():
    print("=" * 70 + "\n CS 216: Bitcoin Transaction Lab - Part 1: Legacy (P2PKH)\n" + "=" * 70)
    try:
        print("\nConnecting to Bitcoin daemon...")
        rpc = get_rpc_connection()
        b_info = rpc.getblockchaininfo()
        print(f"Connected to Bitcoin network: {b_info['chain']}\nCurrent block height: {b_info['blocks']}")
        
        wallet_rpc, address_A, address_B, address_C = setup_wallet_and_addresses(rpc)
        
        txid_fund_A = fund_address_A(rpc, wallet_rpc, address_A)
        
        # Transaction A -> B
        if txid_fund_A:
             txid_AB = create_tx_A_to_B(rpc, wallet_rpc, address_A, address_B)
        
    except JSONRPCException as e:
        print(f"\nRPC Error: {e}\nMake sure bitcoind is running in regtest mode with correct RPC credentials.")
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()