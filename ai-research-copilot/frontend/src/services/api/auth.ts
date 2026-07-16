import apiClient from "./client";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  ChangePasswordRequest,
  User,
  OAuthProvider,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function setCookie(name: string, value: string, days: number) {
  if (typeof document === "undefined") return;
  const maxAge = days * 24 * 60 * 60;
  document.cookie = `${name}=${value}; path=/; max-age=${maxAge}; samesite=lax`;
}

function deleteCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; path=/; max-age=0`;
}

export function setAuthCookies(accessToken: string, refreshToken: string) {
  setCookie("access_token", accessToken, 7);
  setCookie("refresh_token", refreshToken, 7);
}

export function clearAuthCookies() {
  deleteCookie("access_token");
  deleteCookie("refresh_token");
}

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/login", data);
    const tokens = response.data;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    setAuthCookies(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/register", data);
    const tokens = response.data;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    setAuthCookies(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  refreshToken: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    const tokens = response.data;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    setAuthCookies(tokens.access_token, tokens.refresh_token);
    return tokens;
  },

  logout: async (): Promise<void> => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // ignore logout API errors
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    clearAuthCookies();
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },

  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await apiClient.post("/auth/change-password", data);
  },

  forgotPassword: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>("/auth/forgot-password", { email });
    return response.data;
  },

  resetPassword: async (token: string, newPassword: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>("/auth/reset-password", { token, new_password: newPassword });
    return response.data;
  },

  getOAuthUrl: (provider: OAuthProvider): string => {
    return `${API_BASE_URL}/auth/${provider}/login`;
  },
};
