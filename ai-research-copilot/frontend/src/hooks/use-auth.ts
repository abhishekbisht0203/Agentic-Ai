"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";
import { useCallback } from "react";

export function useAuth() {
  const router = useRouter();

  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const error = useAuthStore((s) => s.error);

  const loginAction = useAuthStore((s) => s.login);
  const registerAction = useAuthStore((s) => s.register);
  const logoutAction = useAuthStore((s) => s.logout);
  const clearError = useAuthStore((s) => s.clearError);

  const login = useCallback(
    async (email: string, password: string) => {
      await loginAction({ email, password });
      router.push("/dashboard");
    },
    [loginAction, router]
  );

  const register = useCallback(
    async (data: { email: string; username: string; password: string; full_name?: string }) => {
      await registerAction(data);
      router.push("/dashboard");
    },
    [registerAction, router]
  );

  const logout = useCallback(async () => {
    await logoutAction();
    router.push("/login");
  }, [logoutAction, router]);

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    register,
    logout,
    clearError,
  };
}
