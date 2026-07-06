"use client";

import * as React from "react";
import { Download, ExternalLink, FileText } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, type CurrencyCode } from "@/lib/billing";
import { formatDate } from "@/utils/helpers";
import type { Invoice, InvoiceStatus } from "@/types/billing";

const STATUS_VARIANTS: Record<
  InvoiceStatus,
  "default" | "secondary" | "destructive" | "outline"
> = {
  paid: "default",
  open: "secondary",
  draft: "outline",
  uncollectible: "destructive",
  void: "outline",
};

interface InvoiceTableProps {
  invoices: Invoice[];
  currency: CurrencyCode;
}

export function InvoiceTable({ invoices, currency }: InvoiceTableProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Invoices</CardTitle>
            <CardDescription>View and download your invoices</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {invoices.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <p className="text-muted-foreground">No invoices yet</p>
            <p className="text-sm text-muted-foreground/70">
              Your invoices will appear here after your first payment
            </p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Invoice</TableHead>
                <TableHead>Amount</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow key={invoice.id}>
                  <TableCell className="text-muted-foreground">
                    {formatDate(invoice.createdAt)}
                  </TableCell>
                  <TableCell>
                    {invoice.invoiceNumber || invoice.stripeInvoiceId.slice(-8)}
                  </TableCell>
                  <TableCell className="font-medium">
                    {formatCurrency(invoice.amount, invoice.currency as CurrencyCode)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={STATUS_VARIANTS[invoice.status]}>
                      {invoice.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      {invoice.invoiceUrl && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            window.open(invoice.invoiceUrl!, "_blank")
                          }
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      )}
                      {invoice.pdfUrl && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() =>
                            window.open(invoice.pdfUrl!, "_blank")
                          }
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
