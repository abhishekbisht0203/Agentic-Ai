export * from "./auth";
export * from "./chat";
export * from "./document";
export * from "./agent";
export * from "./workflow";
export * from "./analytics";
export * from "./billing";

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}
