import {
  CURRENCY_CONFIG,
  COUNTRY_CURRENCY_MAP,
  DEFAULT_CURRENCY,
  DEFAULT_COUNTRY,
  type CurrencyCode,
} from "./constants";
import type { CountryDetection } from "@/types/billing";

export function formatCurrency(
  amount: number,
  currency: CurrencyCode = DEFAULT_CURRENCY
): string {
  const config = CURRENCY_CONFIG[currency];
  if (!config) {
    return `$${(amount / 100).toFixed(2)}`;
  }

  const amountInMajorUnits = amount / 100;

  try {
    return new Intl.NumberFormat(config.locale, {
      style: "currency",
      currency: currency,
      minimumFractionDigits: config.decimalPlaces,
      maximumFractionDigits: config.decimalPlaces,
    }).format(amountInMajorUnits);
  } catch {
    return `${config.symbol}${amountInMajorUnits.toFixed(config.decimalPlaces)}`;
  }
}

export function formatCurrencyCompact(
  amount: number,
  currency: CurrencyCode = DEFAULT_CURRENCY
): string {
  const config = CURRENCY_CONFIG[currency];
  if (!config) {
    return `$${(amount / 100).toFixed(0)}`;
  }

  const amountInMajorUnits = amount / 100;

  if (amountInMajorUnits >= 1000000) {
    const millions = amountInMajorUnits / 1000000;
    return `${config.symbol}${millions.toFixed(1)}M`;
  }
  if (amountInMajorUnits >= 1000) {
    const thousands = amountInMajorUnits / 1000;
    return `${config.symbol}${thousands.toFixed(1)}K`;
  }

  return formatCurrency(amount, currency);
}

export function detectCountryFromHeaders(headers: Headers): CountryDetection {
  const cfCountry = headers.get("cf-ipcountry");
  const vercelCountry = headers.get("x-vercel-ip-country");
  const xCountry = headers.get("x-country");

  const country =
    cfCountry || vercelCountry || xCountry || DEFAULT_COUNTRY;

  const currency = COUNTRY_CURRENCY_MAP[country] || DEFAULT_CURRENCY;

  const acceptLanguage = headers.get("accept-language");
  const language = acceptLanguage?.split(",")[0]?.split("-")[0] || "en";

  const timezone = headers.get("x-timezone") || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";

  return {
    country,
    currency,
    language,
    timezone,
  };
}

export function detectCountryFromRequest(
  request: Request
): CountryDetection {
  return detectCountryFromHeaders(request.headers);
}

export function getCurrencyForCountry(country: string): CurrencyCode {
  return COUNTRY_CURRENCY_MAP[country] || DEFAULT_CURRENCY;
}

export function getSupportedCurrencies(): CurrencyCode[] {
  return Object.keys(CURRENCY_CONFIG) as CurrencyCode[];
}

export function isValidCurrency(currency: string): currency is CurrencyCode {
  return currency in CURRENCY_CONFIG;
}
