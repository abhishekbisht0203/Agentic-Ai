import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const metadata: Metadata = {
  title: {
    default: "ARC - AI Research Copilot",
    template: "%s | ARC - AI Research Copilot",
  },
  description:
    "ARC is an AI-powered research platform that helps you analyze documents, build knowledge bases, chat with AI, and automate research workflows.",
  keywords: [
    "ARC",
    "AI Research Copilot",
    "research",
    "LLM",
    "RAG",
    "knowledge base",
    "document analysis",
    "AI agents",
    "workflow automation",
  ],
  authors: [{ name: "ARC - AI Research Copilot" }],
  openGraph: {
    title: "ARC - AI Research Copilot",
    description:
      "Analyze documents, chat with AI, and automate research workflows.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href={API_BASE} />
        <link rel="dns-prefetch" href={API_BASE} />
      </head>
      <body className={`${inter.variable} font-sans antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
