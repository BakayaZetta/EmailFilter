import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor pour ajouter le token JWT à chaque requête
api.interceptors.request.use(config => {
  // Utiliser getters du store si disponible, sinon utiliser sessionStorage comme fallback
  const token = sessionStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor pour gérer les erreurs de réponse
api.interceptors.response.use(
  response => response,
  error => {
    const requestUrl = error.config?.url || '';
    const isAuthEndpoint = requestUrl.includes('/auth/');

    // Gestion des erreurs globales (ex: 401 Unauthorized, etc.)
    if (error.response?.status === 401 && !isAuthEndpoint) {
      // Ne pas rediriger vers login si on est déjà sur la page login
      // Vérifier si l'URL actuelle contient "/login"
      const isLoginPage = window.location.pathname.includes('/login');

      // Créer une nouvelle instance du store
      const authStore = useAuthStore();

      // Appeler l'action logout du store
      authStore.logout();

      // Ne rediriger que si nous ne sommes pas déjà sur la page de connexion
      if (!isLoginPage) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
