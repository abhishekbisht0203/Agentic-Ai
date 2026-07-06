"use client";

import * as React from "react";
import {
  CreditCard,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  ArrowUpCircle,
  ArrowDownCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime } from "@/utils/helpers";
import type { BillingHistoryEntry, BillingEventType } from "@/types/billing";

const EVENT_ICONS: Record<
  BillingEventType,
  React.ComponentType<{ className?: string }>
> = {
  subscription_created: CheckCircle2,
  subscription_updated: RefreshCw,
  subscription_canceled: XCircle,
  payment_succeeded: CreditCard,
  payment_failed: AlertTriangle,
  plan_upgraded: ArrowUpCircle,
  plan_downgraded: ArrowDownCircle,
};

const EVENT_VARIANTS: Record<
  BillingEventType,
  "default" | "secondary" | "destructive" | "outline"
> = {
  subscription_created: "default",
  subscription_updated: "secondary",
  subscription_canceled: "destructive",
  payment_succeeded: "default",
  payment_failed: "destructive",
  plan_upgraded: "default",
  plan_downgraded: "secondary",
};

interface BillingHistoryProps {
  history: BillingHistoryEntry[];
}

export function BillingHistory({ history }: BillingHistoryProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Billing History</CardTitle>
        <CardDescription>View your billing activity</CardDescription>
      </CardHeader>
      <CardContent>
        {history.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">
            No billing history yet
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Event</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {history.map((entry) => {
                const Icon = EVENT_ICONS[entry.type] || CreditCard;
                return (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <Badge variant={EVENT_VARIANTS[entry.type]}>
                          {entry.type.replace(/_/g, " ")}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {entry.description}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDateTime(entry.createdAt)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
