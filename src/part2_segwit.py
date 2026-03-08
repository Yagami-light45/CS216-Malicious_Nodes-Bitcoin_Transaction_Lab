# Import for connection

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json


# Configuration for RPC Connection

RPC_USER="varshith"
RPC_PASSWORD = "varshith@CS216"
RPC_HOST = "127.0.0.1"
RPC_PORT = 18443

# Helper function
def save_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=str)

 
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
    wallet_name = "lab"

    try:
        loaded_wallets = rpc.listwallets()

        if wallet_name not in loaded_wallets:
            try:
                rpc.loadwallet(wallet_name)
            except JSONRPCException:
                try:
                    rpc.createwallet(wallet_name, False, False, "", False, False)
                except JSONRPCException as create_err:
                    return setup_response(False, f"Cannot create wallet: {create_err}", {})

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
    return funding_response(True, "Funding successful", utxos)

# Response class for Transaction
class transaction_response:
    def __init__(self, success, message, data):
        self.success = success
        self.message = message
        self.data = data

# Creating transaction
def create_transaction(wallet_rpc, from_address, to_address, fee=0.0001, dir=1) -> transaction_response:
    try:
        utxos = wallet_rpc.listunspent(1, 9999999, [from_address])

        if not utxos:
            return transaction_response(False, "No UTXOs available for source address", {})

        utxo = max(utxos, key=lambda x: x["amount"])

        send_amount = round(float(utxo["amount"]) - fee, 8)

        inputs = [
            {
                "txid": utxo["txid"],
                "vout": utxo["vout"]
            }
        ]

        outputs = {
            to_address: send_amount
        }

        raw_tx = wallet_rpc.createrawtransaction(inputs, outputs)

        decoded_unsigned = wallet_rpc.decoderawtransaction(raw_tx)

        signed_tx = wallet_rpc.signrawtransactionwithwallet(raw_tx)

        if not signed_tx or not signed_tx.get("complete", False):
            return transaction_response(False, "Transaction signing failed", {})

        decoded_signed = wallet_rpc.decoderawtransaction(signed_tx["hex"])
        script_data = extract_script_data(decoded_signed)
        txid = wallet_rpc.sendrawtransaction(signed_tx["hex"])

        wallet_rpc.generatetoaddress(1, from_address)

        try:
            confirmed_tx = wallet_rpc.getrawtransaction(txid, True)
        except JSONRPCException:
            tx_details = wallet_rpc.gettransaction(txid)
            confirmed_tx = wallet_rpc.decoderawtransaction(tx_details["hex"])

        transaction_data = {
            "txid": txid,
            "from": from_address,
            "to": to_address,
            "amount": send_amount,
            "unsigned_tx": decoded_unsigned,
            "signed_tx": decoded_signed,
            "confirmed_tx": confirmed_tx,
            "script_analysis": script_data,
            "size": confirmed_tx.get("size", 0),
            "vsize": confirmed_tx.get("vsize", 0),
            "weight": confirmed_tx.get("weight", 0)
        }
        s=""
        if dir==1:
            s="A_B"
        else:
            s="B_C"
        save_to_file(transaction_data, f"part_2_transaction_{s}.json")
        return transaction_response(True, "Transaction successful", transaction_data)

    except JSONRPCException as err:
        return transaction_response(False, "RPC transaction error", {"error": str(err)})

# Extranction of decoded part
def extract_script_data(decoded_tx):
    vin = decoded_tx["vin"][0]

    script_sig = vin.get("scriptSig", {})
    witness = vin.get("txinwitness", [])

    vout = decoded_tx["vout"]

    script_pubkeys = []
    for out in vout:
        script_pubkeys.append(out["scriptPubKey"])

    script_data = {
        "scriptSig": script_sig,
        "witness": witness,
        "scriptPubKeys": script_pubkeys
    }

    return script_data

# Generate btcdeb commands
def generate_btcdeb_commands(tx1_data, tx2_data):
    print("BTCDEB VALIDATION COMMANDS")
    
    if not tx2_data:
        print("No transaction data available for btcdeb commands")
        return
    
    txid = tx2_data.get("txid", "")
    input_txid = tx1_data.get("txid", "") if tx1_data else ""
    
    script_analysis = tx2_data.get("script_analysis", {})
    script_sig = script_analysis.get("scriptSig", {})
    witness = script_analysis.get("witness", [])
    
    print("\nP2SH-SegWit Script Structure:")
    print("  1. scriptPubKey (P2SH): OP_HASH160 <scriptHash> OP_EQUAL")
    print("  2. scriptSig contains: redeemScript (OP_0 <pubKeyHash>)")
    print("  3. Witness data: <signature> <publicKey>")
    
    print(f"\nscriptSig ASM: {script_sig.get('asm', 'N/A')}")
    print(f"Witness items: {len(witness)}")
    for i, w in enumerate(witness):
        print(f"  [{i}]: {w[:40]}..." if len(w) > 40 else f"  [{i}]: {w}")
    
    print(f"\nbtcdeb command:")
    print(f"  btcdeb --tx={txid}:0 --txin={input_txid}")
    
    btcdeb_data = {
        "txid": txid,
        "input_txid": input_txid,
        "script_sig": script_sig,
        "witness": witness,
        "command": f"btcdeb --tx={txid}:0 --txin={input_txid}"
    }
    save_to_file(btcdeb_data, "btcdeb_commands_segwit.json")


def main():
    print("Part 2: P2SH-SegWit (P2SH-P2WPKH)")
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
        print("Exiting cause of error in execution")
        return
    else:
        print(setup_response.message)

    # Step-3 Fund the first address for transactions
    fund_response=fund_wallet(setup_response.data["wallet"], setup_response.data["address_A"])
    if not fund_response.success:
        print(f"Funding error: {fund_response.message}")
        print("Exiting cause of error in execution")
        return
    else:
        print(fund_response.message)
    
    # Step-4 Create Transaction from A' to B'
    transaction_1_response=create_transaction(setup_response.data["wallet"], setup_response.data["address_A"], setup_response.data["address_B"], dir=1)
    if not transaction_1_response.success:
        print(f"Error while creating transaction A to B: {transaction_1_response.message}")
        print("Exiting cause of error in execution")
        return
    else:
        print(transaction_1_response.message)
    
    # Step-5 Create Transaction from B' to C'
    transaction_2_response=create_transaction(setup_response.data["wallet"], setup_response.data["address_B"],setup_response.data["address_C"], dir=2)
    if not transaction_2_response.success:
        print(f"Error while creating transaction from B to C: {transaction_2_response.message}")
        print("Exiting cause of error")
        return
    else:
        print(transaction_2_response.message)
    
    generate_btcdeb_commands(transaction_1_response.data, transaction_2_response.data)
    
    print("\nSummary")

    print("\nAddresses:")
    print("A':", setup_response.data["address_A"])
    print("B':", setup_response.data["address_B"])
    print("C':", setup_response.data["address_C"])

    print("\nTransactions:")
    print("A' -> B':", transaction_1_response.data.get("txid", "N/A"))
    print("B' -> C':", transaction_2_response.data.get("txid", "N/A"))

    print("\nTransaction sizes:")
    print("A'->B' size:", transaction_1_response.data.get("size", "N/A"), "bytes")
    print("A'->B' vsize:", transaction_1_response.data.get("vsize", "N/A"), "vbytes")
    print("A'->B' weight:", transaction_1_response.data.get("weight", "N/A"), "WU")
    print("B'->C' size:", transaction_2_response.data.get("size", "N/A"), "bytes")
    print("B'->C' vsize:", transaction_2_response.data.get("vsize", "N/A"), "vbytes")
    print("B'->C' weight:", transaction_2_response.data.get("weight", "N/A"), "WU")

    print("\nFiles generated:")
    addr_A = setup_response.data["address_A"]
    addr_B = setup_response.data["address_B"]
    addr_C = setup_response.data["address_C"]
    print(f"  transaction_{addr_A[:6]}_{addr_B[:6]}.json")
    print(f"  transaction_{addr_B[:6]}_{addr_C[:6]}.json")
    print("  btcdeb_commands_segwit.json")

    print("\nFinal balances:")
    for label, addr in [("A'", setup_response.data["address_A"]), ("B'", setup_response.data["address_B"]), ("C'", setup_response.data["address_C"])]:
        utxos = setup_response.data["wallet"].listunspent(0, 9999999, [addr])
        total = sum(u["amount"] for u in utxos)
        print(label, ":", total, "BTC")
    
if __name__=="__main__" :
    main()
