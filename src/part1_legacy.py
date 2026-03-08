import json
import traceback
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

RPC_USER = "harshith"          
RPC_PASSWORD = "iitindore"  
RPC_HOST = "127.0.0.1"
RPC_PORT = 18443              

# connect to bitcoin daemon
def get_rpc_connection():       
    return AuthServiceProxy(f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}")

# fns for formatting
def print_separator(title):
    print(f"\n{'=' * 70}\n {title}\n{'=' * 70}")

def print_json(data, title=""):
    if title: print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))

# fn to save data to a json
def save_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Data saved to {filename}")

# Setup Wallet and Address Generation
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

# Funding to A
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
    
    unspent_A_list = wallet_rpc.listunspent(1, 9999999, [addr_A])
    
    if not unspent_A_list:
        print("Error: No confirmed UTXOs found for Address A.")
        return None
        
    utxo_A = unspent_A_list[0]
    print_json(utxo_A, "Selected UTXO from Address A")
    
    amount_in = float(utxo_A['amount'])
    amount_to_send = 2.0
    fee = 0.0001
    change_A = round(amount_in - amount_to_send - fee, 8)
    
    print(f"\nMath:\n  Input:  {amount_in} BTC\n  Send:   {amount_to_send} BTC\n  Fee:    {fee} BTC\n  Change: {change_A} BTC (Back to Address A)")
    # create tx
    inputs = [{"txid": utxo_A['txid'], "vout": utxo_A['vout']}]
    
    outputs = {
        addr_B: amount_to_send,
        addr_A: change_A
    }
    
    print("\nCreating raw transaction...")
    raw_tx_hex = wallet_rpc.createrawtransaction(inputs, outputs)
    decoded_tx = wallet_rpc.decoderawtransaction(raw_tx_hex)
    print_json(decoded_tx, "Decoded Unsigned Raw Transaction")

    print("\n--- Locking Script (scriptPubKey) Analysis ---")
    for vout in decoded_tx['vout']:
        spk = vout['scriptPubKey']
        print(f"Output {vout['n']}:\n  Value: {vout['value']} BTC\n  ASM: {spk.get('asm', 'N/A')}\n  Hex: {spk.get('hex', 'N/A')}\n")

    print("Signing transaction with wallet keys...")
    signed_tx = wallet_rpc.signrawtransactionwithwallet(raw_tx_hex)
    
    if not signed_tx['complete']:
        print("Error: Signing failed!")
        return None
        
    print("Signing successful!")

    # Broadcast to the Network
    print("\nBroadcasting transaction to Regtest network...")
    txid_AB = wallet_rpc.sendrawtransaction(signed_tx['hex'])
    print(f"Transaction ID (A -> B): {txid_AB}")
    
    print("\nMining 1 block to confirm the A -> B transaction...")
    miner_addr = wallet_rpc.getnewaddress()
    rpc.generatetoaddress(1, miner_addr)
    
    tx_info = wallet_rpc.gettransaction(txid_AB)
    print(f"Confirmations: {tx_info.get('confirmations', 0)}")
    
    #Save to JSON file
    save_to_file({
        "txid": txid_AB, "from": "Address A", "to": "Address B", "amount": amount_to_send,
        "decoded_transaction": wallet_rpc.decoderawtransaction(signed_tx['hex'])
    }, "transaction_A_to_B.json")

    return txid_AB

# tx B -> C
def create_tx_B_to_C(rpc, wallet_rpc, addr_B, addr_C, txid_AB):
    print_separator("PART 4: TRANSACTION B -> C (1.0 BTC) & SCRIPT EXTRACTION")
    
    unspent_B_list = wallet_rpc.listunspent(1, 9999999, [addr_B])
    
    if not unspent_B_list:
        print("Error: No confirmed UTXOs found for Address B.")
        return None
        
    utxo_B = next((utxo for utxo in unspent_B_list if utxo['txid'] == txid_AB), unspent_B_list[0])
    
    amount_in = float(utxo_B['amount']) 
    amount_to_send = 1.0
    fee = 0.0001
    change_B = round(amount_in - amount_to_send - fee, 8)
    
    print(f"Math:\n  Input:  {amount_in} BTC\n  Send:   {amount_to_send} BTC to Address C\n  Fee:    {fee} BTC\n  Change: {change_B} BTC (Back to Address B)")
    
    # create transaction
    inputs = [{"txid": utxo_B['txid'], "vout": utxo_B['vout']}]
    outputs = {addr_C: amount_to_send, addr_B: change_B}
    
    raw_tx_BC = wallet_rpc.createrawtransaction(inputs, outputs)

    decoded_tx_BC = wallet_rpc.decoderawtransaction(raw_tx_BC)
    print_json(decoded_tx_BC, "Decoded Unsigned Raw Transaction")

    print("\n--- Locking Script (scriptPubKey) Analysis ---")
    for vout in decoded_tx_BC['vout']:
        spk = vout['scriptPubKey']
        print(f"Output {vout['n']}:\n  Value: {vout['value']} BTC\n  ASM: {spk.get('asm', 'N/A')}\n  Hex: {spk.get('hex', 'N/A')}\n")


    # Sign
    signed_tx = wallet_rpc.signrawtransactionwithwallet(raw_tx_BC)
    
    if not signed_tx['complete']:
        print("Error: Signing failed!")
        return None
        
    print("\nSigning B -> C transaction successful!")

    print_separator(" SCRIPT EXTRACTION")

    prev_tx_info = wallet_rpc.gettransaction(txid_AB)
    prev_tx_decoded = wallet_rpc.decoderawtransaction(prev_tx_info['hex'])
    
    vout_index = utxo_B['vout']
    script_pub_key = prev_tx_decoded['vout'][vout_index]['scriptPubKey']['hex']
    script_pub_key_asm = prev_tx_decoded['vout'][vout_index]['scriptPubKey'].get('asm', '')
    
    decoded_signed_BC = wallet_rpc.decoderawtransaction(signed_tx['hex'])
    script_sig = decoded_signed_BC['vin'][0]['scriptSig']['hex']
    script_sig_asm = decoded_signed_BC['vin'][0]['scriptSig'].get('asm', '')
    
    print(f"Locking Script (scriptPubKey) from Address B's UTXO:\n  ASM: {script_pub_key_asm}\n  Hex: {script_pub_key}\n")
    print(f"Unlocking Script (scriptSig) generated by Address B:\n  ASM: {script_sig_asm}\n  Hex: {script_sig}\n")
    
    print("Run this exact command in your terminal to debug the stack:")

    btcdeb_cmd = f"btcdeb '[{script_sig}]' '{script_pub_key}'"
    print(btcdeb_cmd)
    print("=" * 70)

    print("\nBroadcasting transaction to Regtest network...")
    txid_BC = wallet_rpc.sendrawtransaction(signed_tx['hex'])
    print(f"Transaction ID (B -> C): {txid_BC}")
    
    print("\nMining 1 block to confirm the B -> C transaction...")
    rpc.generatetoaddress(1, wallet_rpc.getnewaddress())
    
    # Save to JSON file
    save_to_file({
        "txid": txid_BC, "from": "Address B", "to": "Address C", "amount": amount_to_send,
        "btcdeb_command": btcdeb_cmd
    }, "transaction_B_to_C.json")

    return txid_BC

def main():
    print("=" * 70 + "\n CS 216: Bitcoin Transaction Lab - Part 1: Legacy (P2PKH)\n" + "=" * 70)
    try:
        print("\nConnecting to Bitcoin daemon...")
        rpc = get_rpc_connection()
        b_info = rpc.getblockchaininfo()
        print(f"Connected to Bitcoin network: {b_info['chain']}\nCurrent block height: {b_info['blocks']}")
        
        # Setup
        wallet_rpc, address_A, address_B, address_C = setup_wallet_and_addresses(rpc)
        
        # funding A
        txid_fund_A = fund_address_A(rpc, wallet_rpc, address_A)
        
        # Transaction A -> B
        if txid_fund_A:
             txid_AB = create_tx_A_to_B(rpc, wallet_rpc, address_A, address_B)
             
             # transaction B -> C
             if txid_AB:
                 txid_BC = create_tx_B_to_C(rpc, wallet_rpc, address_B, address_C, txid_AB)
                 
                 print_separator("SUMMARY - Part 1: Legacy (P2PKH) Transactions")
                 print(f"\nFiles Generated:\n  - transaction_A_to_B.json\n  - transaction_B_to_C.json")
                 print(f"\nFinal balances:")
                 
                 for label, addr in [("A", address_A), ("B", address_B), ("C", address_C)]:
                     try: bal = sum(u['amount'] for u in wallet_rpc.listunspent(0, 9999999, [addr]))
                     except: bal = 0
                     print(f"  Address {label}: {bal} BTC")
                 
                 print("\n" + "=" * 70 + "\n Part 1 Complete!\n" + "=" * 70)

    except JSONRPCException as e:
        print(f"\nRPC Error: {e}\nMake sure bitcoind is running in regtest mode with correct RPC credentials.")
    except Exception as e:
        print(f"\nError: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()