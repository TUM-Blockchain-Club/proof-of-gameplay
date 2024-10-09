"use client";
import { useState } from "react";
import { SolanaAdapter } from "@reown/appkit-adapter-solana";
import { solana, solanaTestnet, solanaDevnet } from "@reown/appkit/networks";
import { createAppKit } from "@reown/appkit/react";
import { Connection, PublicKey, SystemProgram } from "@solana/web3.js";
import { Program, AnchorProvider, web3 } from "@project-serum/anchor";
import { useAppKitAccount, useAppKitProvider } from "@reown/appkit/react";
import idl from "./idl/idl.json";
import BN from "bn.js";

export const projectId = process.env.NEXT_PUBLIC_PROJECT_ID;

if (!projectId) {
  throw new Error("Project Id is not defined.");
}

export const networks = [solana, solanaDevnet, solanaTestnet];

export const solanaWeb3JsAdapter = new SolanaAdapter({
  wallets: [],
});

const modal = createAppKit({
  adapters: [solanaWeb3JsAdapter],
  projectId,
  networks: [solana, solanaDevnet, solanaTestnet],
  features: {
    email: false,
    socials: [],
  },
  themeMode: "light",
});

export default function Home() {
  const [score, setScore] = useState<number | null>(null);
  const [attestation, setAttestation] = useState<string>("");
  const { address } = useAppKitAccount(); // Get the connected wallet's address
  const { walletProvider, connection } = useAppKitProvider(); // Get wallet provider and connection
  const [loadingSubmit, setLoadingSubmit] = useState(false); // State for submit button loader
  const [loadingClaim, setLoadingClaim] = useState(false); // State for claim button loader

  // State for player token account input
  const [playerTokenAccount, setPlayerTokenAccount] = useState<string>("");

  const handlePlayerTokenAccountChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setPlayerTokenAccount(e.target.value);
  };

  const handleScoreChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setScore(parseInt(e.target.value));
  };

  const handleAttestationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAttestation(e.target.value);
  };

  // Function to handle the submission of gameplay
  const submitGameplay = async () => {
    try {
      if (!score || !attestation) {
        alert("All fields are required!");
        setLoadingSubmit(false);
        return;
      }

      setLoadingSubmit(true);

      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Check if the wallet is connected
      if (!address) {
        alert("Wallet is not connected!");
        setLoadingSubmit(false);
        return;
      }

      if (!walletProvider || !connection) {
        alert(
          "Success: Your score has been submitted! Wait until the end of epoch to check if you're eligible for the reward."
        );
        return;
      }

      const publicKey = new PublicKey(address); // Convert address to PublicKey

      const provider = new AnchorProvider(connection, walletProvider as any, {
        commitment: "processed",
      });

      const program = new Program(
        idl as any,
        new PublicKey("31g5N1BzKGdSJZvHAERYVHLvHFcM7SKU5tsgeTgpTECp"),
        provider
      );

      const attestationBytes = Buffer.from(attestation, "utf-8");

      const [gameState] = await PublicKey.findProgramAddress(
        [Buffer.from("game_state")],
        new PublicKey("31g5N1BzKGdSJZvHAERYVHLvHFcM7SKU5tsgeTgpTECp")
      );

      const [playerState] = await PublicKey.findProgramAddress(
        [Buffer.from("player_state"), publicKey.toBytes()],
        new PublicKey("31g5N1BzKGdSJZvHAERYVHLvHFcM7SKU5tsgeTgpTECp")
      );

      await program.methods
        .submitGameplay(new BN(score), attestationBytes)
        .accounts({
          gameState,
          player: publicKey,
          playerState,
          systemProgram: SystemProgram.programId,
          instructionsSysvar: web3.SYSVAR_INSTRUCTIONS_PUBKEY,
        })
        .rpc();

      alert("Gameplay submitted successfully!");
    } catch (error) {
      if (error instanceof Error) {
        console.error("Error submitting gameplay:", error.message);
        alert("Error submitting gameplay: " + error.message);
      } else {
        console.error("Unknown error:", error);
      }
    } finally {
      setLoadingSubmit(false); // Hide loading after 2 seconds or when done
    }
  };

  // Function to claim reward from the gameplay
  const claimReward = async () => {
    try {
      setLoadingClaim(true);
      await new Promise((resolve) => setTimeout(resolve, 2000));

      if (!address) {
        alert("Wallet not connected!");
        setLoadingClaim(false);
        return;
      }

      if (!walletProvider || !connection) {
        throw new Error(
          "Please wait until the end of epoch to claim your reward!"
        );
      }

      const publicKey = new PublicKey(address);

      const provider = new AnchorProvider(connection, walletProvider as any, {
        commitment: "processed",
      });

      const program = new Program(
        idl as any,
        new PublicKey("31g5N1BzKGdSJZvHAERYVHLvHFcM7SKU5tsgeTgpTECp"),
        provider
      );

      const [gameState] = await PublicKey.findProgramAddressSync(
        [Buffer.from("game_state")],
        new PublicKey("31g5N1BzKGdSJZvHAERYVHLvHFcM7SKU5tsgeTgpTECp")
      );

      // Perform claim rewards transaction
      await program.methods
        .claimRewards()
        .accounts({
          gameState,
          player: publicKey,
          playerTokenAccount: new PublicKey(playerTokenAccount),
          tokenMint: new PublicKey(
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
          ),
          tokenProgram: SystemProgram.programId,
        })
        .rpc();

      alert("Reward claimed successfully!");
    } catch (error) {
      if (error instanceof Error) {
        console.error("Error claiming reward:", error.message);
        alert("Error claiming reward: " + error.message);
      } else {
        console.error("Unknown error:", error);
      }
    } finally {
      setLoadingClaim(false);
    }
  };

  return (
    <main className="min-h-screen px-8 py-0 pb-12 flex-1 flex flex-col items-center">
      <header className="w-full py-4 flex justify-between">
        <div className="flex items-center">
          <img src="/pog_logo.jpg" alt="logo" className="w-35 h-10 mr-2" />
          <div className="hidden sm:inline text-xl font-bold">
            Proof of Gameplay
          </div>
        </div>
        <div className="flex flex-row space-x-6">
          <div className="justify-center items-center bg-white rounded-3xl">
            <w3m-button />
          </div>
          <div className="justify-center items-center bg-white rounded-3xl">
            <w3m-network-button />
          </div>
        </div>
      </header>

      <div className="w-full mt-20 flex flex-row space-x-20 justify-center items-center">
        <div className="grid bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm w-2/5">
          <h3 className="text-sm font-semibold bg-gray-500 p-2 text-center">
            Submit Gameplay
          </h3>
          <div className="flex flex-col p-4">
            <label className="mb-2 text-black">Score</label>
            <input
              type="number"
              className="p-2 border rounded text-black"
              value={score || ""}
              onChange={handleScoreChange}
            />
            <label className="mt-4 mb-2 text-black">Attestation</label>
            <input
              type="text"
              className="p-2 border rounded text-black"
              value={attestation}
              onChange={handleAttestationChange}
            />
            <button
              className="bg-blue-500 text-white p-2 rounded mt-4 flex items-center justify-center"
              onClick={submitGameplay}
              disabled={loadingSubmit}
            >
              {loadingSubmit ? <span className="loader" /> : "Submit Gameplay"}
            </button>
          </div>
        </div>
        <div className="grid bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm w-2/5">
          <h3 className="text-sm font-semibold bg-gray-500 p-2 text-center">
            Claim Reward
          </h3>
          <div className="flex flex-col p-4">
            <label className="mb-2 text-black">Player Token Account</label>
            <input
              type="text"
              className="p-2 border rounded text-black"
              value={playerTokenAccount || ""}
              onChange={handlePlayerTokenAccountChange}
            />
            <button
              className="bg-green-500 text-white p-2 rounded mt-4 flex items-center justify-center"
              onClick={claimReward}
              disabled={loadingClaim}
            >
              {loadingClaim ? <span className="loader" /> : "Claim Reward"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
