import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthState, LoginRequest, RegisterRequest } from "@/types";
import { authApi, clearAuthCookies, setAuthCookies } from "@/services/api/auth";

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (data: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.login(data);
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: unknown) {
          const message =
            error instanceof Error ? error.message : "Login failed";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register(data);
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: unknown) {
          const message =
            error instanceof Error ? error.message : "Registration failed";
          set({ error: message, isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        await authApi.logout();
        clearAuthCookies();
        set({ user: null, isAuthenticated: false });
      },

      fetchUser: async () => {
        const token = localStorage.getItem("access_token");
        if (!token) {
          set({ isAuthenticated: false, isLoading: false });
          clearAuthCookies();
          return;
        }
        set({ isLoading: true });
        try {
          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          clearAuthCookies();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      handleOAuthCallback: async (hash: string) => {
        set({ isLoading: true, error: null });
        try {
          const params = new URLSearchParams(hash.replace(/^#/, ""));
          const accessToken = params.get("access_token");
          const refreshToken = params.get("refresh_token");
          const errorParam = params.get("error");

          if (errorParam) {
            set({ error: "OAuth authentication failed", isLoading: false });
            return;
          }

          if (!accessToken || !refreshToken) {
            set({ error: "Missing tokens from OAuth response", isLoading: false });
            return;
          }

          localStorage.setItem("access_token", accessToken);
          localStorage.setItem("refresh_token", refreshToken);
          setAuthCookies(accessToken, refreshToken);

          const user = await authApi.getMe();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: unknown) {
          const message =
            error instanceof Error ? error.message : "OAuth callback failed";
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          clearAuthCookies();
          set({ error: message, isLoading: false, user: null, isAuthenticated: false });
        }
      },

      setUser: (user) => set({ user }),
      clearError: () => set({ error: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
