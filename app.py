from flask import Flask, jsonify, request
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.instruction import Instruction
import json
from solders.signature import Signature
import firebase_admin
from firebase_admin import credentials, firestore
import qrcode


app = Flask(__name__)
solana_client = Client("https://api.devnet.solana.com")

cred = credentials.Certificate("firebaseKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# ✅ Store to Firebase
def store_signature(signature, sender_wallet):
    print(f"📝 Storing signature to Firestore: {signature}")
    doc_ref = db.collection("auth_logs").document(signature)
    doc_ref.set({
        "signature": signature,
        "sender_wallet": sender_wallet,
        "authenticated": True
    })

    
    
    def generate_qr(signature):
        url = f"http://127.0.0.1:5000/authenticate/{signature}"
        qr = qrcode.make(url)
        qr.save("auth_qr.png")



@app.route("/")
def hello():
    return "Welcome to Solana + Flask!"


@app.route("/call-contract", methods=['GET', 'POST'])
def call_contract():
    try:
        program_pubkey = Pubkey.from_string("JLoZ8cWwv6hPYR1dshN61scNHwF9DAA257YtVjZfB3E")

        # Get account info
        info = solana_client.get_account_info(program_pubkey)
        account_data = {}
        if info.value:
            account = info.value
            account_data = {
                "lamports": account.lamports,
                "owner": str(account.owner),
                "executable": account.executable,
                "rent_epoch": account.rent_epoch,
                "data": account.data.decode("utf-8", errors="ignore")
            }
        else:
            account_data = {"status": "account not found"}

        # Get latest transaction
        txs = solana_client.get_signatures_for_address(program_pubkey, limit=1)
        if txs.value:
            latest_sig = str(txs.value[0].signature)
            sig_obj = Signature.from_string(latest_sig)

            tx_detail = solana_client.get_transaction(sig_obj, encoding="jsonParsed")
            parsed_tx = json.loads(tx_detail.value.to_json())
            sender = parsed_tx["transaction"]["message"]["accountKeys"][0]

            account_data["latest_transaction_signature"] = latest_sig
            account_data["sender_wallet"] = sender
            store_signature(latest_sig, {
                "pubkey": sender,
                "signer": True,
                "source": "transaction",
                "writable": True
            })

        else:
            account_data["latest_transaction_signature"] = None
            account_data["sender_wallet"] = None

        return jsonify(account_data)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/authenticate/<signature>", methods=["GET","POST"])
def authenticate_user(signature):
    print("🔎 Looking for signature:", signature)  # <--- ADD THIS
    try:
        doc_ref = db.collection("auth_logs").document(signature)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return jsonify({
                "authenticated": True,
                "wallet": data.get("sender_wallet")
            })
        else:
            return jsonify({
                "authenticated": False,
                "message": "Signature not found"
            })
    except Exception as e:
        return jsonify({"error": str(e)})



@app.route("/log-transaction", methods=['GET', 'POST'])
def log_transaction():
    data = request.json
    print("🔔 Received transaction log:", data)
    return jsonify({"status": "received"})


if __name__ == "__main__":
    app.run(debug=True)
