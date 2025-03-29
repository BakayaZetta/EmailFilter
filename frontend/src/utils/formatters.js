/**
 * Formater la date pour l'affichage au format h:min:s d/m/y
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
export function formatDateTime(dateString) {
  if (!dateString) return 'N/A';

  const date = new Date(dateString);

  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();

  return `${hours}:${minutes}:${seconds} ${day}/${month}/${year}`;
}

/**
 * Obtenir les classes pour l'indicateur de statut
 * @param {string} status - Mail status
 * @returns {string} CSS class
 */
export function getStatusClass(status) {
  switch(status?.toUpperCase()) {
    case 'QUARANTINE': return 'bg-yellow-500';
    case 'ERROR': return 'bg-red-500';
    case 'SAFE': return 'bg-green-500';
    case 'DELETED': return 'bg-red-300';
    case 'PASS': return 'bg-blue-500';
    default: return 'bg-gray-500';
  }
}

/**
 * Obtenir une map des statuts et couleurs pour la légende
 * @returns {Array<Object>} Status map
 */
export function getStatusMap() {
  return [
    { name: 'Safe', color: 'bg-green-500' },
    { name: 'Pass', color: 'bg-blue-500' },
    { name: 'Quarantine', color: 'bg-yellow-500' },
    { name: 'Deleted', color: 'bg-red-300' },
    { name: 'Error', color: 'bg-red-500' }
  ];
}
