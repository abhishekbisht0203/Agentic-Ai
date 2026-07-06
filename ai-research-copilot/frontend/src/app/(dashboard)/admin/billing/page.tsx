"use client";

import * as React from "react";
import {
  DollarSign,
  Users,
  CreditCard,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Globe,
  Banknote,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { billingApi } from "@/services/api/billing";
import { formatCurrency, formatCurrencyCompact } from "@/lib/billing";
import { formatDate } from "@/utils/helpers";
import type { CurrencyCode, PaymentStatus } from "@/types/billing";

export default function AdminBillingPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["admin-billing-stats"],
    queryFn: billingApi.getAdminStats,
    staleTime: 60 * 1000,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64 mt-2" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <DollarSign className="h-6 w-6" />
          Billing Dashboard
        </h1>
        <p className="text-muted-foreground">
          Revenue overview and subscription analytics
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MRR</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrencyCompact(stats?.mrr || 0, "USD")}
            </div>
            <p className="text-xs text-muted-foreground">
              Monthly Recurring Revenue
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ARR</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrencyCompact(stats?.arr || 0, "USD")}
            </div>
            <p className="text-xs text-muted-foreground">
              Annual Recurring Revenue
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Customers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.totalCustomers || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.activeSubscriptions || 0} active subscriptions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Failed Payments
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.failedPayments || 0}
            </div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Refunds</CardTitle>
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrencyCompact(stats?.refunds || 0, "USD")}
            </div>
            <p className="text-xs text-muted-foreground">Last 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Revenue by Plan */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Revenue by Plan
            </CardTitle>
            <CardDescription>
              Subscription distribution across plans
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!stats?.revenueByPlan?.length ? (
              <p className="text-muted-foreground text-center py-4">
                No subscription data yet
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Plan</TableHead>
                    <TableHead className="text-right">Count</TableHead>
                    <TableHead className="text-right">MRR</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.revenueByPlan.map((item) => (
                    <TableRow key={item.plan}>
                      <TableCell>
                        <Badge variant="outline">{item.plan}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{item.count}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrencyCompact(item.revenue, "USD")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Banknote className="h-5 w-5" />
              Revenue by Currency
            </CardTitle>
            <CardDescription>
              Breakdown across supported currencies
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!stats?.revenueByCurrency?.length ? (
              <p className="text-muted-foreground text-center py-4">
                No currency data yet
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Currency</TableHead>
                    <TableHead className="text-right">Count</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stats.revenueByCurrency.map((item) => (
                    <TableRow key={item.currency}>
                      <TableCell>
                        <Badge variant="outline">{item.currency.toUpperCase()}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{item.count}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrencyCompact(
                          item.revenue,
                          item.currency.toUpperCase() as CurrencyCode
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Country Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Customer Distribution by Country
          </CardTitle>
          <CardDescription>Geographic distribution of subscribers</CardDescription>
        </CardHeader>
        <CardContent>
          {!stats?.revenueByCountry?.length ? (
            <p className="text-muted-foreground text-center py-4">
              No country data yet
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Country</TableHead>
                  <TableHead className="text-right">Customers</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.revenueByCountry
                  .sort((a, b) => b.count - a.count)
                  .slice(0, 20)
                  .map((item) => (
                    <TableRow key={item.country}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="text-lg">
                            {getCountryFlag(item.country)}
                          </span>
                          {item.country}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        {item.count}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Recent Payments */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Payments</CardTitle>
          <CardDescription>Last 30 days of payment activity</CardDescription>
        </CardHeader>
        <CardContent>
          {!stats?.recentPayments?.length ? (
            <p className="text-muted-foreground text-center py-4">
              No recent payments
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Amount</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Failure</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.recentPayments.map((payment) => (
                  <TableRow key={payment.id}>
                    <TableCell className="text-muted-foreground">
                      {formatDate(payment.createdAt)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {formatCurrency(
                        payment.amount,
                        payment.currency as CurrencyCode
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          payment.status === "succeeded"
                            ? "default"
                            : payment.status === "failed"
                              ? "destructive"
                              : "secondary"
                        }
                      >
                        {payment.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {payment.failureReason || "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function getCountryFlag(countryCode: string): string {
  const codePoints = countryCode
    .toUpperCase()
    .split("")
    .map((char) => 0x1f1a5 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}
