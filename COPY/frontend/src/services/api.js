import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Assurez-vous que la baseURL est correcte
const api = axios.create({
  baseURL: '/api', // Ceci doit être /api sans slash final
  headers: {
    'Content-Type': 'application/json',
  },
});

// Ajouter des intercepteurs pour le débogage
api.interceptors.request.use(
  config => {
    console.log('Request:', config.method.toUpperCase(), config.baseURL + config.url, config.data);
    // Utiliser getters du store si disponible, sinon utiliser sessionStorage comme fallback
    const token = sessionStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Interceptor pour gérer les erreurs de réponse
api.interceptors.response.use(
  response => {
    console.log('Response:', response.status, response.data);
    return response;
  },
  error => {
    console.error('Response error:', error.response?.status, error.response?.data);
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
