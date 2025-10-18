/**
 * User Model
 * Represents a user in the system
 */
export interface User {
  id: number;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
}

/**
 * Login Request DTO
 * Used for login requests
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Register Request DTO
 * Used for user registration
 */
export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

/**
 * Auth Token Response
 * Response containing authentication token
 */
export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * Auth State
 * Current authentication state
 */
export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
}
