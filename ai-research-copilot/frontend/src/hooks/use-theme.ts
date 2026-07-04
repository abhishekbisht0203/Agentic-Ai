"use client";

import { useTheme as useNextTheme } from "next-themes";
import { useThemeStore } from "@/store/theme-store";

export function useTheme() {
  const { theme: nextTheme, setTheme: setNextTheme } = useNextTheme();
  const { theme: storeTheme, setTheme: setStoreTheme } = useThemeStore();

  const setTheme = (theme: "light" | "dark" | "system") => {
    setNextTheme(theme);
    setStoreTheme(theme);
  };

  return {
    theme: nextTheme ?? storeTheme,
    setTheme,
    resolvedTheme: nextTheme,
  };
}
