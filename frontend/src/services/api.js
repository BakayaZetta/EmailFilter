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
    // Gestion des erreurs globales (ex: 401 Unauthorized, etc.)
    if (error.response?.status === 401) {
      // Créer une nouvelle instance du store
      const authStore = useAuthStore();
      // Appeler l'action logout du store
      authStore.logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
