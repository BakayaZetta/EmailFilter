import api from './api';

/**
 * Service pour gérer les règles de filtrage
 */
const rulesService = {
  /**
   * Récupère toutes les règles de filtrage
   * @returns {Promise} Les règles de filtrage
   */
  getFilterRules() {
    return api.get('/filter-rules');
  },

  /**
   * Récupère une règle spécifique
   * @param {Number} id - ID de la règle
   * @returns {Promise} La règle spécifiée
   */
  getFilterRule(id) {
    return api.get(`/filter-rules/${id}`);
  },

  /**
   * Ajoute une nouvelle règle de filtrage
   * @param {Object} rule - Règle à ajouter
   * @returns {Promise} La règle ajoutée
   */
  createFilterRule(rule) {
    return api.post('/filter-rules', rule);
  },

  /**
   * Met à jour une règle existante
   * @param {Number} id - ID de la règle
   * @param {Object} rule - Données mises à jour
   * @returns {Promise} La règle mise à jour
   */
  updateFilterRule(id, rule) {
    return api.put(`/filter-rules/${id}`, rule);
  },

  /**
   * Supprime une règle de filtrage
   * @param {Number} id - ID de la règle à supprimer
   * @returns {Promise} Résultat de la suppression
   */
  deleteFilterRule(id) {
    return api.delete(`/filter-rules/${id}`);
  }
};

export default rulesService;
