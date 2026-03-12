import api from '@/services/api';

export default {
  /**
   * Get mails by status
   * @param {string} statusList - Comma-separated list of statuses
   * @returns {Promise} Promise with mail data
   */
  async getMailsByStatus(statusList, page = 1, limit = 50) {
    const response = await api.get('/mails/status', {
      params: { status: statusList, page, limit, _t: Date.now() },
      headers: {
        'Cache-Control': 'no-cache',
        Pragma: 'no-cache'
      }
    });

    const payload = response.data;
    const mailRows = Array.isArray(payload) ? payload : (payload.data || []);
    const pagination = Array.isArray(payload)
      ? { page: 1, limit: mailRows.length, total: mailRows.length, totalPages: 1 }
      : (payload.pagination || { page: 1, limit: mailRows.length, total: mailRows.length, totalPages: 1 });

    // Normaliser les données pour compatibilité en préservant plus d'informations
    const items = mailRows.map(mail => {
      const destinataire = mail.recipient || mail.to || mail.Destinataire || '';

      return {
        ID_Mail: mail.id || mail.ID_Mail,
        ID_Utilisateur: mail.user?.id || mail.ID_Utilisateur,
        Emetteur: mail.sender || mail.Emetteur,
        Destinataire: destinataire,
        Sujet: mail.subject || mail.Sujet,
        Date_Reception: mail.receivedDate || mail.Date_Reception,
        Statut: mail.status || mail.Statut,
        originalData: mail
      };
    });

    return { items, pagination };
  },

  /**
   * Get mail details by ID
   * @param {number} mailId - Mail ID
   * @returns {Promise} Promise with mail details
   */
  async getMailDetails(mailId) {
    const response = await api.get(`/mails/${mailId}/complete`);
    return response.data;
  },

  /**
   * Update mail status
   * @param {number} mailId - Mail ID
   * @param {string} status - New status
   * @returns {Promise} Promise with updated mail
   */
  async updateMailStatus(mailId, status) {
    const response = await api.put(`/mails/${mailId}/status`, { status });
    return response.data;
  },

  /**
   * Bulk update mail status
   * @param {Array<number>} mailIds - Array of mail IDs
   * @param {string} status - New status
   * @returns {Promise} Promise with operation status
   */
  async bulkUpdateMailStatus(mailIds, status) {
    const promises = mailIds.map(mailId =>
      this.updateMailStatus(mailId, status)
    );
    return Promise.all(promises);
  },

  /**
   * Upload an email
   * @param {Object} emailData - The email data to upload
   * @returns {Promise} Promise with the uploaded email
   */
  async uploadEmail(emailData) {
    const response = await api.post('/mails/upload', emailData);
    return response.data;
  }
}
