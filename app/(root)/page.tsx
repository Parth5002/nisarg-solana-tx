"use client";

import { Button } from "@/components/ui/button";
import ConnectWallet from "@/components/wallet";
import { useUnifiedWallet } from "@jup-ag/wallet-adapter";
import {
    LAMPORTS_PER_SOL,
    PublicKey,
    Transaction,
    SystemProgram,
    TransactionInstruction,
    Connection,
} from "@solana/web3.js";

export default function HomePage() {
    const { connected, publicKey, sendTransaction } = useUnifiedWallet();

    async function handleClick() {
        console.log("Button clicked");

        try {
            if (!publicKey) {
                throw new Error("Wallet not connected");
            }

            const connection = new Connection("https://api.devnet.solana.com", "confirmed");

            const lamports = LAMPORTS_PER_SOL * 0.001; // 0.001 SOL

            const memoData = JSON.stringify({
                message: "Hello from " + publicKey.toBase58(),
                timestamp: new Date().toISOString(),
            });

            const transaction = new Transaction().add(
                // Transfer SOL to recipient wallet
                SystemProgram.transfer({
                    fromPubkey: publicKey,
                    toPubkey: new PublicKey("JLoZ8cWwv6hPYR1dshN61scNHwF9DAA257YtVjZfB3E"),
                    lamports: lamports,
                }),
                // Add memo instruction with transaction details
                new TransactionInstruction({
                    keys: [{ pubkey: publicKey, isSigner: true, isWritable: true }],
                    data: Buffer.from(memoData, "utf-8"),
                    programId: new PublicKey(
                        "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
                    ),
                })
            );


            const signature = await sendTransaction(transaction, connection);
            console.log("Transaction sent with signature:", signature);

            // Wait for confirmation
            const latestBlockhash = await connection.getLatestBlockhash();
            const confirmation = await connection.confirmTransaction({
                signature,
                blockhash: latestBlockhash.blockhash,
                lastValidBlockHeight: latestBlockhash.lastValidBlockHeight,
            });

            if (confirmation.value.err) {
                throw new Error("Transaction failed to confirm: " + confirmation.value.err.toString());
            }

            console.log("Transaction confirmed:", confirmation);

            return confirmation
        } catch (error) {
            console.error("Error:", error);
        }
    }

    return (
        <div className="w-full h-screen flex flex-col">
            <div className="p-4 flex w-full border-b">
                <div className="flex items-center w-full max-w-[90vw] mx-auto justify-between">
                    <h1 className="font-semibold">Name</h1>
                    <ConnectWallet />
                </div>
            </div>

            <div className="flex flex-col items-center justify-center h-full">
                {connected ? (
                    <Button
                        variant="outline"
                        onClick={handleClick}
                    >
                        Make A Transaction
                    </Button>
                ) : (
                    "connect your wallet to make a transaction"
                )}
            </div>
        </div>
    );
}
