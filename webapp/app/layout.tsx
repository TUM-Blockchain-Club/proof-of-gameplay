import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import WalletConnectionProvider from "./WalletConnectionProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Proof of Gameplay",
  description: "Submit and verify your gameplay on Solana",
  authors: [
    { name: "Lucas Aschenbach" },
    { name: "Gopi Mehta" },
    { name: "Luis Bahners" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* <WalletConnectionProvider> */}
      <body className={inter.className}>{children}</body>
      {/* </WalletConnectionProvider> */}
    </html>
  );
}
