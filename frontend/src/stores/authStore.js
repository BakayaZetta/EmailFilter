import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isLoggedIn: false,
    user: null,
    token: null,
  }),

  actions: {
    initialize() {
      const token = sessionStorage.getItem('token');
      const userStr = sessionStorage.getItem('user');

      if (token && userStr) {
        try {
          this.token = token;
          this.user = JSON.parse(userStr);
          this.isLoggedIn = true;
        } catch (error) {
          this.logout();
          console.error('Failed to parse user data:', error);
        }
      }
    },

    login(userData, token) {
      this.user = userData;
      this.token = token;
      this.isLoggedIn = true;

      // Store in sessionStorage
      sessionStorage.setItem('token', token);
      sessionStorage.setItem('user', JSON.stringify(userData));
    },

    logout() {
      this.user = null;
      this.token = null;
      this.isLoggedIn = false;

      // Clear sessionStorage
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('user');
    }
  }
});
