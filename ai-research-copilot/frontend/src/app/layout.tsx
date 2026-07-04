import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: {
    default: "AI Research Copilot",
    template: "%s | AI Research Copilot",
  },
  description:
    "Enterprise Agentic AI Research Platform - Chat, Analyze, Research, Automate",
  keywords: [
    "AI",
    "research",
    "copilot",
    "LLM",
    "RAG",
    "knowledge base",
    "document analysis",
  ],
  authors: [{ name: "AI Research Copilot" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
