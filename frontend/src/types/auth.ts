import type { User } from './user';

export interface AuthTokenResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
