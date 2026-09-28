import api from './api';
import type { User, AuthTokenResponse, RegisterRequest, LoginRequest } from '../types';
import { setAuthTokens, clearAuthTokens } from '../utils/storage';

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/auth/register/', data);
    return response.data;
  },

  async login(data: LoginRequest): Promise<AuthTokenResponse> {
    const response = await api.post<AuthTokenResponse>('/auth/login/', data);
    if (response.data.access_token) {
      setAuthTokens(response.data.access_token, response.data.refresh_token);
    }
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me/');
    return response.data;
  },

  logout(): void {
    clearAuthTokens();
  },
};
