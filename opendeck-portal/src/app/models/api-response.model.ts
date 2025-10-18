/**
 * Paginated API Response
 * Generic interface for paginated responses from the API
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * API Error Response
 * Standard error response from the API
 */
export interface ApiErrorResponse {
  detail: string;
  status?: number;
  timestamp?: string;
}

/**
 * API Success Response
 * Generic success response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}
