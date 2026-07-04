import Link from "next/link";
import {
  Bot,
  BookOpen,
  FileText,
  GitBranch,
  BarChart3,
  MessageSquare,
  ArrowRight,
  Zap,
  Shield,
  Globe,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: MessageSquare,
    title: "AI Chat",
    description:
      "Conversational AI with streaming, citations, and multi-model support.",
  },
  {
    icon: BookOpen,
    title: "Knowledge Base",
    description:
      "Build and query knowledge bases from your documents with RAG.",
  },
  {
    icon: Bot,
    title: "AI Agents",
    description:
      "Configure and deploy specialized agents for research, analysis, and more.",
  },
  {
    icon: GitBranch,
    title: "Workflow Builder",
    description:
      "Visual workflow editor to automate complex research pipelines.",
  },
  {
    icon: FileText,
    title: "Document Center",
    description:
      "Upload, process, and analyze documents with intelligent chunking.",
  },
  {
    icon: BarChart3,
    title: "Analytics",
    description:
      "Track usage, visualize data, and generate comprehensive reports.",
  },
];

const stats = [
  { label: "Documents Processed", value: "10K+" },
  { label: "Queries Answered", value: "100K+" },
  { label: "Uptime", value: "99.9%" },
  { label: "Enterprise Users", value: "500+" },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Bot className="h-4 w-4" />
            </div>
            <span className="text-lg font-bold">AI Research Copilot</span>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="#features"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </Link>
            <Link
              href="#"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Pricing
            </Link>
            <Link
              href="#"
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
        <section className="py-24 md:py-32">
          <div className="container mx-auto px-4 text-center">
            <div className="mx-auto max-w-3xl space-y-6">
              <div className="inline-flex items-center rounded-full border bg-muted px-3 py-1 text-sm">
                <Zap className="mr-1 h-3 w-3 text-amber-500" />
                Powered by cutting-edge AI
              </div>
              <h1 className="text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
                Your Enterprise{" "}
                <span className="bg-gradient-to-r from-blue-600 to-violet-600 bg-clip-text text-transparent">
                  AI Research
                </span>{" "}
                Platform
              </h1>
              <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                Chat with AI, analyze documents, build knowledge bases, and
                automate research workflows — all in one powerful platform.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                <Button size="lg" asChild>
                  <Link href="/register">
                    Start Free Trial
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="#">Watch Demo</Link>
                </Button>
              </div>
            </div>
          </div>
        </section>

        <section className="border-t py-16">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {stats.map((stat) => (
                <div key={stat.label} className="text-center">
                  <div className="text-3xl font-bold">{stat.value}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="features" className="py-24">
          <div className="container mx-auto px-4">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Everything you need
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
                A comprehensive suite of AI-powered tools for research,
                analysis, and knowledge management.
              </p>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-lg border p-6 hover:shadow-md transition-all"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t py-24">
          <div className="container mx-auto px-4">
            <div className="rounded-2xl bg-muted/50 p-12 text-center">
              <h2 className="text-3xl font-bold">
                Ready to transform your research?
              </h2>
              <p className="mt-4 text-lg text-muted-foreground max-w-xl mx-auto">
                Join hundreds of teams using AI Research Copilot to accelerate
                their workflows.
              </p>
              <div className="mt-8 flex items-center justify-center gap-4">
                <Button size="lg" asChild>
                  <Link href="/register">
                    Get Started Free
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              <span className="font-semibold">AI Research Copilot</span>
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
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; 2026 AI Research Copilot. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
