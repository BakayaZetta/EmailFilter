import axios from 'axios';

/**
 * Service to interact with Mistral API
 */
export default {
  /**
   * Request an explanation from Mistral for a specific email
   * This implementation sends a direct request to the Python service
   * @param {number|string} emailId - Email identifier
   * @param {Object} mailDetails - Complete email details
   * @returns {Promise} Promise containing the explanation
   */
  async getExplanation(emailId, mailDetails) {
    try {
      // Prepare data to send
      const requestData = {
        emailId: emailId,
        // Send complete mail details
        emailData: mailDetails
      };

      // Direct call to Python service without going through /api/
      const response = await axios.post('/analyse/mistral/', requestData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // If response is successful but without explanation, use a default explanation
      if (response.data && !response.data.explanation) {
        return {
          explanation: "No detailed explanation was provided by the analysis service.",
          status: response.data.status || 'success'
        };
      }

      return response.data;
    } catch (error) {
      console.error('Error getting Mistral explanation:', error);

      // In case of error, fall back to a simulated explanation for better UX
      return {
        explanation: this._generateFallbackExplanation(emailId, error, mailDetails),
        status: 'fallback'
      };
    }
  },

  /**
   * Generate a fallback explanation if the API call fails
   * @private
   * @param {number|string} emailId - Email identifier
   * @param {Error} error - The error encountered
   * @param {Object} mailDetails - Mail details if available
   * @returns {string} Explanation in markdown format
   */
  _generateFallbackExplanation(emailId, error, mailDetails) {
    // If we have mail details, generate a more relevant explanation
    if (mailDetails) {
      const subject = mailDetails.Sujet || 'No subject';
      const sender = mailDetails.Emetteur || 'unknown';
      const status = mailDetails.Statut || 'UNKNOWN';

      return `# Email Analysis

## Email Information
- **Subject**: ${subject}
- **Sender**: ${sender}
- **Status**: ${status}

## Provisional Explanation
We couldn't get a complete automated analysis for this email. Here are some points that could explain its status:

${status === 'QUARANTINED' ? `
- The email may contain suspicious elements
- The sender may not be confirmed
- SPF, DKIM or DMARC verification issues may be present
` : ''}

${status === 'SPAM' ? `
- The email has been identified as potential spam
- It may contain keywords associated with spam
- The sender may be on a watchlist
` : ''}

${status === 'DELIVERED' ? `
- The email passed all security checks
- No suspicious elements were detected
` : ''}

## Technical Message
\`\`\`
${error?.message || "Communication error with analysis service"}
\`\`\`
`;
    }

    // Fallback if no details
    return `# Communication problem with analysis service

We couldn't get an automated explanation for this email (ID: ${emailId}).

## Possible reason

The Mistral analysis service is currently unavailable. This may be due to:

- The service is undergoing maintenance
- A network connectivity issue
- A configuration error

## Technical error message

\`\`\`
${error?.message || "Unknown error"}
\`\`\`

Please try again later or contact your system administrator if the problem persists.`;
  }
};
