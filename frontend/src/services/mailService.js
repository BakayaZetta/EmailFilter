import api from '@/services/api';

export default {
  /**
   * Get mails by status
   * @param {string} statusList - Comma-separated list of statuses
   * @returns {Promise} Promise with mail data
   */
  async getMailsByStatus(statusList) {
    const response = await api.get('/mails/status', {
      params: { status: statusList }
    });

    // Normaliser les données pour compatibilité en préservant plus d'informations
    return response.data.map(mail => {
      // Extraire l'email du destinataire si disponible
      const destinataire = mail.recipient || mail.to || mail.Destinataire ||
        (mail.user?.email ? mail.user.email : `User ID: ${mail.ID_Utilisateur || mail.user?.id}`);

      return {
        ID_Mail: mail.id || mail.ID_Mail,
        ID_Utilisateur: mail.user?.id || mail.ID_Utilisateur,
        Emetteur: mail.sender || mail.Emetteur,
        Destinataire: destinataire,
        Sujet: mail.subject || mail.Sujet,
        Date_Reception: mail.receivedDate || mail.Date_Reception,
        Statut: mail.status || mail.Statut,
        // Conserver l'objet complet original également
        originalData: mail
      };
    });
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
  }
}
