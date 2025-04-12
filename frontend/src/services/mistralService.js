import axios from 'axios';

/**
 * Service pour interagir avec l'API Mistral
 */
export default {
  /**
   * Demande une explication à Mistral pour un email spécifique
   * Cette implémentation envoie une requête directe au service Python
   * @param {number|string} emailId - L'identifiant de l'email
   * @param {Object} mailDetails - Les détails complets de l'email
   * @returns {Promise} Promise contenant l'explication
   */
  async getExplanation(emailId, mailDetails) {
    try {
      // Préparer les données à envoyer
      const requestData = {
        emailId: emailId,
        // Envoyer les détails complets du mail
        emailData: mailDetails
      };

      // Appel direct au service Python sans passer par /api/
      const response = await axios.post('/analyse/mistral/', requestData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Si la réponse est réussie mais sans explication, utiliser une explication par défaut
      if (response.data && !response.data.explanation) {
        return {
          explanation: "Aucune explication détaillée n'a été fournie par le service d'analyse.",
          status: response.data.status || 'success'
        };
      }

      return response.data;
    } catch (error) {
      console.error('Error getting Mistral explanation:', error);

      // En cas d'erreur, revenir à une explication simulée pour une meilleure UX
      return {
        explanation: this._generateFallbackExplanation(emailId, error, mailDetails),
        status: 'fallback'
      };
    }
  },

  /**
   * Génère une explication de fallback en cas d'échec de l'appel à l'API
   * @private
   * @param {number|string} emailId - L'identifiant de l'email
   * @param {Error} error - L'erreur rencontrée
   * @param {Object} mailDetails - Les détails du mail si disponibles
   * @returns {string} Explication au format markdown
   */
  _generateFallbackExplanation(emailId, error, mailDetails) {
    // Si nous avons des détails du mail, générer une explication plus pertinente
    if (mailDetails) {
      const subject = mailDetails.Sujet || 'Sans objet';
      const sender = mailDetails.Emetteur || 'inconnu';
      const status = mailDetails.Statut || 'UNKNOWN';

      return `# Analyse de l'email

## Informations sur l'email
- **Sujet**: ${subject}
- **Expéditeur**: ${sender}
- **Statut**: ${status}

## Explication provisoire
Nous n'avons pas pu obtenir une analyse automatisée complète pour cet email. Voici quelques points qui pourraient expliquer son statut:

${status === 'QUARANTINED' ? `
- L'email pourrait contenir des éléments suspects
- L'expéditeur pourrait ne pas être confirmé
- Des problèmes de vérification SPF, DKIM ou DMARC pourraient être présents
` : ''}

${status === 'SPAM' ? `
- L'email a été identifié comme spam potentiel
- Il pourrait contenir des mots-clés associés au spam
- L'expéditeur pourrait être sur une liste de surveillance
` : ''}

${status === 'DELIVERED' ? `
- L'email a passé toutes les vérifications de sécurité
- Aucun élément suspect n'a été détecté
` : ''}

## Message technique
\`\`\`
${error?.message || "Erreur de communication avec le service d'analyse"}
\`\`\`
`;
    }

    // Fallback si pas de détails
    return `# Problème de communication avec le service d'analyse

Nous n'avons pas pu obtenir une explication automatisée pour cet email (ID: ${emailId}).

## Raison possible

Le service d'analyse Mistral n'est pas accessible actuellement. Cela peut être dû à:

- Le service est en cours de maintenance
- Un problème de connectivité réseau
- Une erreur de configuration

## Message d'erreur technique

\`\`\`
${error?.message || "Erreur inconnue"}
\`\`\`

Veuillez réessayer ultérieurement ou contacter l'administrateur système si le problème persiste.`;
  }
};
