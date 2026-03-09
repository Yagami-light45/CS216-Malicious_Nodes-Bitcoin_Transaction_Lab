# Import required libraries
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json

RPC_USER="varshith"
RPC_PASSWORD="varshith@CS216"
RPC_HOST="127.0.0.1"
RPC_PORT=18443


def save_to_file(data, filename):
    with open(filename,"w") as f:
        json.dump(data,f,indent=2,default=str)


def rpc_connection():
    rpc_url=f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}"
    return AuthServiceProxy(rpc_url)


def setup_wallet_addresses(rpc):

    wallet_name="lab"

    loaded_wallets=rpc.listwallets()

    if wallet_name not in loaded_wallets:
        try:
            rpc.loadwallet(wallet_name)
        except JSONRPCException:
            rpc.createwallet(wallet_name)

    wallet_rpc=AuthServiceProxy(
        f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/wallet/{wallet_name}"
    )

    address_A=wallet_rpc.getnewaddress("A-part2","p2sh-segwit")
    address_B=wallet_rpc.getnewaddress("B-part2","p2sh-segwit")
    address_C=wallet_rpc.getnewaddress("C-part2","p2sh-segwit")

    return wallet_rpc,address_A,address_B,address_C


def mine_blocks(wallet_rpc,num,address):

    blocks=wallet_rpc.generatetoaddress(num,address)

    return blocks


def select_utxo(wallet_rpc,address,required_amount):

    utxos=wallet_rpc.listunspent(1,9999999,[address])

    for utxo in utxos:
        if utxo["amount"]>=required_amount:
            return utxo

    return None


def create_and_send_raw_tx(wallet_rpc,from_address,to_address,send_amount):

    fee=0.0001

    utxo=select_utxo(wallet_rpc,from_address,send_amount+fee)

    if not utxo:
        raise Exception("No suitable UTXO found")

    txid_in=utxo["txid"]
    vout_in=utxo["vout"]
    input_amount=float(utxo["amount"])

    change_amount=round(input_amount-send_amount-fee,8)

    inputs=[{
        "txid":txid_in,
        "vout":vout_in
    }]

    outputs={
        to_address:send_amount,
        from_address:change_amount
    }

    raw_tx=wallet_rpc.createrawtransaction(inputs,outputs)

    decoded_unsigned=wallet_rpc.decoderawtransaction(raw_tx)

    signed_tx=wallet_rpc.signrawtransactionwithwallet(raw_tx)

    if not signed_tx["complete"]:
        raise Exception("Signing failed")

    signed_hex=signed_tx["hex"]

    decoded_signed=wallet_rpc.decoderawtransaction(signed_hex)

    txid=wallet_rpc.sendrawtransaction(signed_hex)

    confirmed_tx=wallet_rpc.getrawtransaction(txid,True)

    script_data=extract_script_data(decoded_signed)

    tx_data={
        "txid":txid,
        "from":from_address,
        "to":to_address,
        "amount":send_amount,
        "unsigned_tx":decoded_unsigned,
        "signed_tx":decoded_signed,
        "confirmed_tx":confirmed_tx,
        "script_analysis":script_data,
        "size":confirmed_tx.get("size",0),
        "vsize":confirmed_tx.get("vsize",0),
        "weight":confirmed_tx.get("weight",0)
    }

    return tx_data


def extract_script_data(decoded_tx):

    vin=decoded_tx["vin"][0]

    script_sig=vin.get("scriptSig",{})
    witness=vin.get("txinwitness",[])

    script_pubkeys=[]

    for vout in decoded_tx["vout"]:
        script_pubkeys.append(vout["scriptPubKey"])

    return {
        "scriptSig":script_sig,
        "witness":witness,
        "scriptPubKeys":script_pubkeys
    }


def generate_btcdeb_commands(wallet_rpc, tx1_data, tx2_data):

    print("\nGenerating btcdeb stack-trace command")

    witness = tx2_data["script_analysis"]["witness"]
    script_pubkey = tx1_data["script_analysis"]["scriptPubKeys"][0]["hex"]

    signature = witness[0]
    pubkey = witness[1]

    # convert P2PKH style script for debugger
    # OP_DUP OP_HASH160 <pubkeyhash> OP_EQUALVERIFY OP_CHECKSIG
    pubkey_hash = script_pubkey[6:-4]

    script = f"{pubkey_hash}"

    command = f"btcdeb '[{signature} {pubkey}]' '{script}'"

    print("\nRun this command for btcdeb stack trace:\n")
    print(command)

    btcdeb_data = {
        "signature": signature,
        "pubkey": pubkey,
        "script": script,
        "command": command
    }

    save_to_file(btcdeb_data, "btcdeb_commands_segwit.json")
    
def main():

    print("SegWit P2SH-P2WPKH Transactions")

    rpc=rpc_connection()

    info=rpc.getblockchaininfo()

    print("Connected to:",info["chain"])

    wallet_rpc,address_A,address_B,address_C=setup_wallet_addresses(rpc)

    print("Address A:",address_A)
    print("Address B:",address_B)
    print("Address C:",address_C)

    print("\nMining 101 blocks to A")

    mine_blocks(wallet_rpc,101,address_A)

    print("\nCreating Transaction A -> B (2 BTC)")

    tx1=create_and_send_raw_tx(
        wallet_rpc,
        address_A,
        address_B,
        2.0
    )

    save_to_file(tx1,"part_2_transaction_A_B.json")

    mine_blocks(wallet_rpc,1,address_A)

    print("TXID:",tx1["txid"])

    print("\nCreating Transaction B -> C (1 BTC)")

    tx2=create_and_send_raw_tx(
        wallet_rpc,
        address_B,
        address_C,
        1.0
    )

    save_to_file(tx2,"part_2_transaction_B_C.json")

    mine_blocks(wallet_rpc,1,address_A)

    print("TXID:",tx2["txid"])

    generate_btcdeb_commands(
        wallet_rpc,
        tx1,
        tx2
    )

    print("\nTransaction Sizes")

    print("A->B size:",tx1["size"])
    print("A->B vsize:",tx1["vsize"])
    print("A->B weight:",tx1["weight"])

    print("B->C size:",tx2["size"])
    print("B->C vsize:",tx2["vsize"])
    print("B->C weight:",tx2["weight"])


if __name__=="__main__":
    main()