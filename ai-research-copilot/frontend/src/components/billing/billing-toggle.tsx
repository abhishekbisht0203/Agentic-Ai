"use client";

import * as React from "react";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import type { BillingInterval } from "@/types/billing";

interface BillingToggleProps {
  interval: BillingInterval;
  onChange: (interval: BillingInterval) => void;
}

export function BillingToggle({ interval, onChange }: BillingToggleProps) {
  return (
    <div className="flex items-center justify-center gap-3">
      <Label
        htmlFor="billing-toggle"
        className={`text-sm cursor-pointer transition-colors ${
          interval === "month"
            ? "text-foreground font-medium"
            : "text-muted-foreground"
        }`}
      >
        Monthly
      </Label>
      <Switch
        id="billing-toggle"
        checked={interval === "year"}
        onCheckedChange={(checked) =>
          onChange(checked ? "year" : "month")
        }
      />
      <Label
        htmlFor="billing-toggle"
        className={`text-sm cursor-pointer transition-colors ${
          interval === "year"
            ? "text-foreground font-medium"
            : "text-muted-foreground"
        }`}
      >
        Yearly
        <Badge variant="secondary" className="ml-1.5 text-xs">
          Save 20%
        </Badge>
      </Label>
    </div>
  );
}
