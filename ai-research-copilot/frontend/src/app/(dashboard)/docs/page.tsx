"use client";

import * as React from "react";
import Link from "next/link";
import {
  BookOpen,
  MessageSquare,
  FileText,
  Brain,
  GitBranch,
  BarChart3,
  Database,
  Search,
  ArrowRight,
  ChevronRight,
  HelpCircle,
  Zap,
  Shield,
  Upload,
  Settings,
  Code,
  ExternalLink,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const docSections = [
  {
    id: "getting-started",
    title: "Getting Started",
    icon: Zap,
    description: "Quick start guide to get up and running",
    articles: [
      {
        title: "Introduction to ARC",
        content:
          "ARC (AI Research Copilot) is an intelligent platform that helps you research, analyze, and manage documents using AI-powered agents. Upload documents, create knowledge bases, chat with ARC, and automate complex workflows.",
      },
      {
        title: "Creating Your Account",
        content:
          "Sign up using your email address or connect with Google/GitHub for quick access. After verifying your email, you'll be directed to the dashboard where you can start exploring the platform.",
      },
      {
        title: "Navigating the Dashboard",
        content:
          "The dashboard provides an overview of your activity, including recent chats, document counts, and knowledge base status. Use the sidebar to navigate between different sections: ARC Chat, Documents, Knowledge Base, Agents, Workflows, and Analytics.",
      },
    ],
  },
  {
    id: "ai-chat",
    title: "ARC Chat",
    icon: MessageSquare,
    description: "Have intelligent conversations with ARC",
    articles: [
      {
        title: "Starting a Chat",
        content:
          "Click on 'ARC Chat' in the sidebar to start a new conversation. You can ask questions about your uploaded documents, request summaries, analysis, or general research assistance. ARC uses your knowledge bases for context-aware responses.",
      },
      {
        title: "Chat with Documents",
        content:
          "When you have documents uploaded, ARC can answer questions directly from your content. Simply reference a document or ask a question, and ARC will search through your knowledge bases to find relevant information.",
      },
      {
        title: "AI Models",
        content:
          "The platform supports multiple AI models including GPT-4o, Claude 3.5 Sonnet, and GPT-3.5 Turbo. You can select your preferred model in the chat settings or let the system choose the best model for your query.",
      },
    ],
  },
  {
    id: "documents",
    title: "Documents",
    icon: FileText,
    description: "Upload and manage your research documents",
    articles: [
      {
        title: "Uploading Documents",
        content:
          "Navigate to the Documents section and click 'Upload'. Supported formats include PDF, DOCX, TXT, and Markdown. Documents are automatically processed, chunked, and indexed for AI search capabilities.",
      },
      {
        title: "Document Processing",
        content:
          "When you upload a document, it goes through several processing steps: text extraction, chunking into smaller segments, embedding generation for semantic search, and storage in your knowledge base. This process typically takes a few seconds.",
      },
      {
        title: "Organizing Documents",
        content:
          "Group related documents into Knowledge Bases for better organization. Each Knowledge Base can contain multiple documents and serves as a context source for AI conversations. Create separate knowledge bases for different research topics.",
      },
    ],
  },
  {
    id: "knowledge-base",
    title: "Knowledge Base",
    icon: Database,
    description: "Create searchable knowledge repositories",
    articles: [
      {
        title: "What is a Knowledge Base?",
        content:
          "A Knowledge Base is a collection of documents organized around a specific topic or research area. It enables the AI to search and retrieve relevant information when answering your questions. You can create multiple knowledge bases for different projects.",
      },
      {
        title: "Creating a Knowledge Base",
        content:
          "Go to Knowledge Base and click 'Create Knowledge Base'. Give it a name and description, then upload or attach documents. The system will automatically index all content for semantic search.",
      },
      {
        title: "Using Knowledge Bases in Chat",
        content:
          "When chatting with AI, you can specify which knowledge base to use for context. The AI will search through the selected knowledge base to provide accurate, document-backed answers.",
      },
    ],
  },
  {
    id: "agents",
    title: "ARC Agents",
    icon: Brain,
    description: "Deploy autonomous AI agents",
    articles: [
      {
        title: "What are AI Agents?",
        content:
          "ARC Agents are autonomous assistants that can perform complex tasks, conduct research, and generate reports. Unlike simple chat, agents can plan multi-step workflows, use tools, and deliver comprehensive results.",
      },
      {
        title: "Creating an Agent",
        content:
          "Navigate to Agents and click 'Create Agent'. Define the agent's role, capabilities, and the knowledge bases it can access. You can configure the agent's personality, expertise areas, and output format.",
      },
      {
        title: "Running an Agent",
        content:
          "Once created, you can assign tasks to your agent. The agent will work through the task step by step, consulting your documents as needed, and deliver a comprehensive result. Monitor progress in real-time.",
      },
    ],
  },
  {
    id: "workflows",
    title: "Workflows",
    icon: GitBranch,
    description: "Automate research processes",
    articles: [
      {
        title: "Building Workflows",
        content:
          "Workflows allow you to chain multiple AI operations together. Create a workflow by adding steps like document analysis, web research, data extraction, and report generation. Each step can use different AI models and tools.",
      },
      {
        title: "Running Workflows",
        content:
          "Select a workflow and provide the input data or documents. The workflow will execute each step sequentially, passing results from one step to the next. Track progress and view intermediate results in real-time.",
      },
      {
        title: "Workflow Templates",
        content:
          "Start with pre-built workflow templates for common tasks like literature review, competitive analysis, market research, and data extraction. Customize templates to fit your specific needs.",
      },
    ],
  },
  {
    id: "analytics",
    title: "Analytics",
    icon: BarChart3,
    description: "Track usage and insights",
    articles: [
      {
        title: "Analytics Dashboard",
        content:
          "The Analytics section provides insights into your platform usage. View message history, document processing stats, agent activity, and token consumption. Charts and graphs help you understand usage patterns.",
      },
      {
        title: "Reports",
        content:
          "Generate detailed reports on your research activity. Export usage data, document summaries, and conversation histories. Reports can be downloaded in various formats for record-keeping or sharing with your team.",
      },
    ],
  },
  {
    id: "api",
    title: "API Reference",
    icon: Code,
    description: "Integrate with the platform API",
    articles: [
      {
        title: "Authentication",
        content:
          "All API requests require authentication using JWT tokens. Obtain a token via the /api/v1/auth/login endpoint and include it in the Authorization header as 'Bearer <token>'.",
      },
      {
        title: "REST Endpoints",
        content:
          "The API follows REST conventions. Key endpoints include /api/v1/documents (CRUD for documents), /api/v1/chat (send messages), /api/v1/knowledge-bases (manage KBs), and /api/v1/agents (manage agents).",
      },
      {
        title: "Rate Limits",
        content:
          "Free tier: 100 requests/minute. Pro tier: 1,000 requests/minute. Enterprise: Unlimited. Exceeding limits returns HTTP 429. Implement exponential backoff in your integration code.",
      },
    ],
  },
];

const faqs = [
  {
    question: "What file formats are supported?",
    answer:
      "We support PDF, DOCX, TXT, and Markdown files. Documents are automatically processed and indexed for AI search.",
  },
  {
    question: "How does the AI use my documents?",
    answer:
      "When you ask a question, the AI searches through your knowledge bases for relevant information. It retrieves the most relevant chunks from your documents and uses them to generate accurate, context-aware responses.",
  },
  {
    question: "Can I use multiple AI models?",
    answer:
      "Yes! The platform supports GPT-4o, Claude 3.5 Sonnet, and GPT-3.5 Turbo. You can select the model per conversation or let the system choose the best one for your query.",
  },
  {
    question: "Is my data secure?",
    answer:
      "Absolutely. All data is encrypted at rest and in transit. Your documents are stored securely and are never shared with other users. We follow industry-standard security practices including SOC 2 compliance.",
  },
  {
    question: "Can I share knowledge bases with my team?",
    answer:
      "Yes, with the Pro or Enterprise plan. You can invite team members, assign roles, and share knowledge bases across your organization.",
  },
  {
    question: "What happens when I reach my plan limits?",
    answer:
      "When you reach your monthly limits, you'll receive a notification. You can still access your existing data, but new AI requests will be paused until the next billing cycle or until you upgrade your plan.",
  },
  {
    question: "How do I cancel my subscription?",
    answer:
      "Go to Settings > Billing and click 'Manage Billing'. You can cancel your subscription at any time. Your account will remain active until the end of the current billing period.",
  },
];

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [activeSection, setActiveSection] = React.useState<string | null>(null);

  const filteredSections = docSections
    .map((section) => ({
      ...section,
      articles: section.articles.filter(
        (article) =>
          article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          article.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
          section.title.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    }))
    .filter(
      (section) =>
        section.articles.length > 0 ||
        section.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Documentation</h1>
        <p className="text-muted-foreground">
          Learn how to use ARC
        </p>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search documentation..."
          className="pl-9"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-4">
        {docSections.slice(0, 4).map((section) => (
          <Card
            key={section.id}
            className="cursor-pointer hover:shadow-md transition-all"
            onClick={() => {
              setActiveSection(section.id);
              document
                .getElementById(section.id)
                ?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <section.icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{section.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {section.articles.length} articles
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Documentation Sections */}
      <div className="space-y-8">
        {filteredSections.map((section) => (
          <div key={section.id} id={section.id}>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <section.icon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">{section.title}</h2>
                <p className="text-sm text-muted-foreground">
                  {section.description}
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {section.articles.map((article, index) => (
                <Card key={index} className="hover:shadow-md transition-all">
                  <CardHeader>
                    <CardTitle className="text-base">
                      {article.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {article.content}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>

      <Separator className="my-8" />

      {/* FAQ Section */}
      <div id="faq">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <HelpCircle className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">
              Frequently Asked Questions
            </h2>
            <p className="text-sm text-muted-foreground">
              Common questions and answers
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            <Accordion type="single" collapsible className="w-full">
              {faqs.map((faq, index) => (
                <AccordionItem key={index} value={`faq-${index}`}>
                  <AccordionTrigger className="text-left">
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent className="text-muted-foreground">
                    {faq.answer}
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>
      </div>

      {/* Contact Support */}
      <Card>
        <CardContent className="pt-6 text-center">
          <h3 className="font-semibold mb-2">Still need help?</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Can&apos;t find what you&apos;re looking for? Our support team is
            here to help.
          </p>
          <Button variant="outline">
            <ExternalLink className="mr-2 h-4 w-4" />
            Contact Support
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
