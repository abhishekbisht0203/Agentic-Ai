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
    default: "ARC - AI Research Copilot",
    template: "%s | ARC - AI Research Copilot",
  },
  description:
    "ARC - AI Research Copilot. Intelligent research, analysis, and automation platform.",
  keywords: [
    "ARC",
    "AI Research Copilot",
    "research",
    "LLM",
    "RAG",
    "knowledge base",
    "document analysis",
  ],
  authors: [{ name: "ARC - AI Research Copilot" }],
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
