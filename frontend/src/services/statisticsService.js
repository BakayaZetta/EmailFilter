import api from '@/services/api';

export default {
  /**
   * Get mail statistics
   * @param {string} period - Time period ('week', 'month', 'year', 'all')
   * @returns {Promise} Promise with statistics data
   */
  async getStatistics(period = 'month') {
    try {
      const response = await api.get('/statistics', {
        params: { period }
      });

      // Récupérer également les données historiques
      const historyResponse = await api.get('/statistics/history', {
        params: { period }
      });

      console.log('History data received:', historyResponse.data);

      // Transformer les données historiques en format exploitable
      let mailsOverTime = [];

      if (historyResponse.data && historyResponse.data.mailsOverTime) {
        // Vérifier si mailsOverTime est un tableau valide
        const rawData = historyResponse.data.mailsOverTime;

        if (Array.isArray(rawData) && rawData.length > 0) {
          // Si le premier élément est un tableau (comme dans votre console.log)
          if (Array.isArray(rawData[0])) {
            mailsOverTime = rawData[0].map(item => {
              // Convertir les valeurs en nombres
              return {
                date: item.date,
                total: parseInt(item.total || 0),
                quarantine: parseInt(item.quarantine || 0),
                safe: parseInt(item.safe || 0),
                error: parseInt(item.error || 0),
                deleted: parseInt(item.deleted || 0),
                pass: parseInt(item.pass || 0)
              };
            });
          } else {
            // S'il s'agit déjà d'un tableau d'objets
            mailsOverTime = rawData.map(item => {
              return {
                date: item.date,
                total: parseInt(item.total || 0),
                quarantine: parseInt(item.quarantine || 0),
                safe: parseInt(item.safe || 0),
                error: parseInt(item.error || 0),
                deleted: parseInt(item.deleted || 0),
                pass: parseInt(item.pass || 0)
              };
            });
          }
        }
      }

      // Combiner les deux réponses
      return {
        ...response.data,
        mailsOverTime: mailsOverTime
      };
    } catch (error) {
      console.error('Error fetching statistics:', error);

      // En cas d'erreur, retourner des données minimales pour éviter les erreurs d'affichage
      return {
        totalMails: 0,
        mailsByStatus: {},
        threatsByCategory: {},
        topSenders: [],
        detectRatio: 0,
        mailsOverTime: []
      };
    }
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

    // Transformer les données comme ci-dessus
    let mailsOverTime = [];
    if (response.data && response.data.mailsOverTime) {
      const rawData = response.data.mailsOverTime;
      if (Array.isArray(rawData) && rawData.length > 0) {
        if (Array.isArray(rawData[0])) {
          mailsOverTime = rawData[0].map(item => ({
            date: item.date,
            total: parseInt(item.total || 0),
            quarantine: parseInt(item.quarantine || 0),
            safe: parseInt(item.safe || 0),
            error: parseInt(item.error || 0),
            deleted: parseInt(item.deleted || 0),
            pass: parseInt(item.pass || 0)
          }));
        }
      }
    }

    return { mailsOverTime };
  }
}
