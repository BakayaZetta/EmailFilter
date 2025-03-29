import api from '@/services/api';

export default {
  /**
   * Get mail statistics
   * @param {string} period - Time period ('week', 'month', 'year', 'all')
   * @returns {Promise} Promise with statistics data
   */
  async getStatistics(period = 'month') {
    const response = await api.get('/statistics', {
      params: { period }
    });

    // Récupérer également les données historiques
    const historyResponse = await api.get('/statistics/history', {
      params: { period }
    });

    // Combiner les deux réponses
    return {
      ...response.data,
      mailsOverTime: historyResponse.data.mailsOverTime || []
    };
  },

  /**
   * Get historical data for charts
   * @param {string} period - Time period ('week', 'month', 'year', 'all')
   * @returns {Promise} Promise with historical data
   */
  async getHistoricalData(period = 'month') {
    const response = await api.get('/statistics/history', {
      params: { period }
    });
    return response.data;
  }
}
