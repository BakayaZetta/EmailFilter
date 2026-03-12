import api from '@/services/api';

export default {
  async getUsers() {
    const response = await api.get('/admin/users');
    return response.data;
  },

  async getUserProfile(userId) {
    const response = await api.get(`/admin/users/${userId}/profile`);
    return response.data;
  },

  async createUser(payload) {
    const response = await api.post('/admin/users', payload);
    return response.data;
  },

  async updateUserRole(userId, role) {
    const response = await api.put(`/admin/users/${userId}/role`, { role });
    return response.data;
  },

  async deactivateUser(userId) {
    const response = await api.put(`/admin/users/${userId}/deactivate`);
    return response.data;
  },

  async getLogs(limit = 200) {
    const response = await api.get('/admin/logs', { params: { limit } });
    return response.data;
  },

  async getScans() {
    const response = await api.get('/admin/scans');
    return response.data;
  },

  async getQueuedScans(limit = 100) {
    const response = await api.get('/admin/scans/queued', { params: { limit } });
    return response.data;
  },

  async clearQueuedScans() {
    const response = await api.post('/admin/scans/queued/clear');
    return response.data;
  }
};
