"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { useCallback } from "react";

export function useAuth() {
  const router = useRouter();
  const store = useAuthStore();

  const login = useCallback(
    async (email: string, password: string) => {
      await store.login({ email, password });
      router.push("/dashboard");
    },
    [store, router]
  );

  const register = useCallback(
    async (data: { email: string; username: string; password: string; full_name?: string }) => {
      await store.register(data);
      router.push("/dashboard");
    },
    [store, router]
  );

  const logout = useCallback(async () => {
    await store.logout();
    router.push("/login");
  }, [store, router]);

  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login,
    register,
    logout,
    clearError: store.clearError,
  };
}
