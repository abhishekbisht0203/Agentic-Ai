"use client";

import * as React from "react";
import Link from "next/link";
import {
  Brain,
  BookOpen,
  FileText,
  GitBranch,
  BarChart3,
  MessageSquare,
  ArrowRight,
  Zap,
  Shield,
  Globe,
  Search,
  Sparkles,
  Clock,
  Layers,
  CheckCircle2,
  Quote,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: MessageSquare,
    title: "ARC Chat",
    description:
      "Have intelligent conversations with your documents. ARC cites sources, supports multiple AI models (GPT-4o, Claude 3.5, Gemini), and streams responses in real-time.",
    benefit: "Find answers in seconds, not hours",
  },
  {
    icon: BookOpen,
    title: "Knowledge Base",
    description:
      "Upload documents and ARC automatically chunks, embeds, and indexes them for semantic search. Build a searchable knowledge repository for your team.",
    benefit: "Instantly search across thousands of documents",
  },
  {
    icon: Brain,
    title: "ARC Agents",
    description:
      "Deploy autonomous AI agents for complex tasks: literature review, competitive analysis, data extraction, and report generation. Agents plan and execute multi-step workflows.",
    benefit: "Automate hours of research into minutes",
  },
  {
    icon: GitBranch,
    title: "Workflow Builder",
    description:
      "Visually chain AI operations — document analysis, web research, data extraction, and report generation — into automated research pipelines with branching logic.",
    benefit: "Build repeatable research automations",
  },
  {
    icon: FileText,
    title: "Document Center",
    description:
      "Upload PDFs, DOCX, Markdown, and more. ARC extracts text, applies intelligent chunking strategies (recursive, semantic, parent-child), and indexes for RAG-powered retrieval.",
    benefit: "Process 100+ pages in seconds",
  },
  {
    icon: BarChart3,
    title: "Analytics & Reports",
    description:
      "Track usage metrics, visualize trends, and generate PDF/CSV reports. Monitor token consumption, document processing volume, and agent activity across your team.",
    benefit: "Data-driven insights into your research",
  },
];

const testimonials = [
  {
    quote:
      "ARC turned our 6-person research team into a 20-person operation. We analyze 3x more papers in half the time.",
    author: "Dr. Sarah Chen",
    role: "Lead Researcher, BioMed Analytics",
    rating: 5,
  },
  {
    quote:
      "The workflow builder alone saves us 15 hours per week. We automated our entire competitive intelligence pipeline.",
    author: "Marcus Williams",
    role: "VP Strategy, TechVentures Inc.",
    rating: 5,
  },
  {
    quote:
      "We evaluated 8 AI research platforms. ARC was the only one that could actually handle our 10,000-document corpus.",
    author: "Priya Patel",
    role: "Director of Research, LegalGrid",
    rating: 5,
  },
];

const useCases = [
  {
    icon: Search,
    title: "Academic Research",
    description:
      "Literature reviews, paper analysis, citation tracking, and synthesis across thousands of sources.",
  },
  {
    icon: BarChart3,
    title: "Market Intelligence",
    description:
      "Competitor monitoring, trend analysis, report generation, and data extraction from earnings calls and filings.",
  },
  {
    icon: Layers,
    title: "Legal & Compliance",
    description:
      "Contract analysis, regulatory research, case law search, and due diligence document review.",
  },
  {
    icon: Sparkles,
    title: "Product Development",
    description:
      "User research synthesis, technical documentation analysis, and competitive feature comparison.",
  },
];

const howItWorks = [
  {
    step: 1,
    title: "Upload your documents",
    description:
      "Drag-and-drop PDFs, Word docs, or Markdown files. ARC automatically processes and indexes them.",
  },
  {
    step: 2,
    title: "Chat and analyze",
    description:
      "Ask questions, request summaries, or get insights. ARC searches your documents and responds with citations.",
  },
  {
    step: 3,
    title: "Build and automate",
    description:
      "Create knowledge bases, deploy AI agents, and design workflows to automate repetitive research tasks.",
  },
];

function formatStat(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K+`;
  return String(n);
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => (
        <svg
          key={i}
          className={`h-4 w-4 ${i < rating ? "text-amber-400" : "text-muted"}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  );
}

export default function LandingPage() {
  const [liveStats, setLiveStats] = React.useState<Record<string, number> | null>(null);
  const [statsLoading, setStatsLoading] = React.useState(true);

  React.useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    fetch(`${apiBase}/stats/public`)
      .then((r) => r.json())
      .then((data) => setLiveStats(data))
      .catch(() => setLiveStats(null))
      .finally(() => setStatsLoading(false));
  }, []);

  const stats = [
    {
      label: "Documents Processed",
      value: liveStats ? formatStat(liveStats.documents) : null,
    },
    {
      label: "Queries Answered",
      value: liveStats ? formatStat(liveStats.queries) : null,
    },
    {
      label: "Uptime",
      value: liveStats ? `${liveStats.uptime}%` : null,
    },
    {
      label: "Enterprise Users",
      value: liveStats ? formatStat(liveStats.users) : null,
    },
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Brain className="h-4 w-4" />
            </div>
            <span className="text-lg font-bold">ARC</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="#features"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </Link>
            <Link
              href="#use-cases"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Use Cases
            </Link>
            <Link
              href="/pricing"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Pricing
            </Link>
            <Link
              href="/docs"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Docs
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            <Button variant="ghost" asChild>
              <Link href="/login">Log in</Link>
            </Button>
            <Button asChild>
              <Link href="/register">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="py-24 md:py-32">
          <div className="container mx-auto px-4 text-center">
            <div className="mx-auto max-w-4xl space-y-8">
              <div className="inline-flex items-center gap-2 rounded-full border bg-muted px-4 py-1.5 text-sm">
                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                New: ARC Agents with autonomous workflow execution
              </div>
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
                Your AI Research
                <br />
                <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                  Copilot
                </span>
              </h1>
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground sm:text-xl">
                ARC helps you research faster by understanding your documents,
                answering questions with citations, and automating repetitive
                research workflows.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                <Button size="lg" asChild>
                  <Link href="/register">
                    Start Free Trial
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/demo">
                    <Zap className="mr-2 h-4 w-4" />
                    Live Demo
                  </Link>
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                No credit card required &middot; Free plan includes 50 AI messages/month
              </p>
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="border-t py-16">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {statsLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="text-center">
                      <div className="text-3xl font-bold tracking-tight">—</div>
                      <div className="text-sm text-muted-foreground mt-1">Loading...</div>
                    </div>
                  ))
                : stats.map((stat) => (
                    <div key={stat.label} className="text-center">
                      <div className="text-3xl font-bold tracking-tight">{stat.value || "—"}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {stat.label}
                      </div>
                    </div>
                  ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-24">
          <div className="container mx-auto px-4 max-w-6xl">
            <div className="text-center mb-16">
              <Badge variant="outline" className="mb-4">Platform</Badge>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Everything you need to research at scale
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
                From document ingestion to AI-powered analysis and automated
                workflows — ARC is a complete research platform.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature) => (
                <Card
                  key={feature.title}
                  className="group hover:shadow-lg transition-all hover:border-primary/30"
                >
                  <CardContent className="p-6">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
                      <feature.icon className="h-6 w-6" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      {feature.description}
                    </p>
                    <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      {feature.benefit}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="border-t py-24 bg-muted/30">
          <div className="container mx-auto px-4 max-w-5xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Get started in minutes
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-xl mx-auto">
                No complex setup. Just upload, ask, and automate.
              </p>
            </div>
            <div className="grid md:grid-cols-3 gap-8">
              {howItWorks.map((item) => (
                <div key={item.step} className="text-center">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground text-xl font-bold mx-auto mb-4">
                    {item.step}
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section id="use-cases" className="py-24">
          <div className="container mx-auto px-4 max-w-6xl">
            <div className="text-center mb-16">
              <Badge variant="outline" className="mb-4">Use Cases</Badge>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Built for research-intensive teams
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
                ARC adapts to how your team works — whether you are in
                academia, market research, legal, or product development.
              </p>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {useCases.map((useCase) => (
                <Card
                  key={useCase.title}
                  className="hover:shadow-md transition-all"
                >
                  <CardContent className="p-6 text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary mx-auto mb-4">
                      <useCase.icon className="h-6 w-6" />
                    </div>
                    <h3 className="font-semibold mb-2">{useCase.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {useCase.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="border-t py-24 bg-muted/30">
          <div className="container mx-auto px-4 max-w-5xl">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Trusted by research teams worldwide
              </h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {testimonials.map((t) => (
                <Card key={t.author} className="hover:shadow-md transition-all">
                  <CardContent className="p-6">
                    <Quote className="h-6 w-6 text-primary/40 mb-3" />
                    <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                      &ldquo;{t.quote}&rdquo;
                    </p>
                    <StarRating rating={t.rating} />
                    <div className="mt-3">
                      <p className="text-sm font-semibold">{t.author}</p>
                      <p className="text-xs text-muted-foreground">{t.role}</p>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-24">
          <div className="container mx-auto px-4">
            <div className="rounded-2xl bg-gradient-to-br from-primary/5 via-primary/10 to-primary/5 border p-12 md:p-16 text-center max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Stop digging. Start discovering.
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-lg mx-auto">
                Join researchers and analysts who use ARC to cut their
                research time by 60% or more.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button size="lg" asChild>
                  <Link href="/register">
                    Start Free Trial
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="/demo">
                    Try Live Demo
                  </Link>
                </Button>
              </div>
              <p className="mt-4 text-xs text-muted-foreground">
                Free plan includes 50 messages, 10 documents, and 1 knowledge base.
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              <span className="font-semibold">ARC - AI Research Copilot</span>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Shield className="h-4 w-4" />
                SOC 2 Compliant
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Globe className="h-4 w-4" />
                GDPR Ready
              </div>
              <Link
                href="/docs"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Docs
              </Link>
              <Link
                href="/pricing"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Pricing
              </Link>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; 2026 ARC - AI Research Copilot. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
