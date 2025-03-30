import { ref, computed } from 'vue';
import mailService from '@/services/mailService';

export function useMailTable() {
  // États
  const mails = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const expandedMailId = ref(null);
  const selectedMails = ref([]);

  // Tri
  const sortColumn = ref('Date_Reception');
  const sortDirection = ref('desc');

  // Recherche
  const searchQuery = ref({
    status: '',
    sender: '',
    recipient: '',
    subject: '',
    dateFrom: '',
    dateTo: ''
  });

  // Computed property pour vérifier si tous les mails sont sélectionnés
  const allSelected = computed(() => {
    return filteredMails.value.length > 0 && selectedMails.value.length === filteredMails.value.length;
  });

  // Mails filtrés selon les critères de recherche
  const filteredMails = computed(() => {
    if (!mails.value?.length) return [];

    return mails.value.filter(mail => {
      // Filtrer par statut
      if (searchQuery.value.status &&
          mail.Statut?.toLowerCase() !== searchQuery.value.status.toLowerCase()) {
        return false;
      }

      // Filtrer par expéditeur
      if (searchQuery.value.sender &&
          !mail.Emetteur?.toLowerCase().includes(searchQuery.value.sender.toLowerCase())) {
        return false;
      }

      // Filtrer par destinataire (ID_Utilisateur ou email)
      if (searchQuery.value.recipient) {
        const searchTerm = searchQuery.value.recipient.toLowerCase();

        // Récupérer différentes propriétés possibles pour le destinataire
        const userId = String(mail.ID_Utilisateur || '');
        const destinataire = String(mail.Destinataire || '');

        // Debug temporaire - voir dans la console ce qui est disponible
        // console.log('Mail destinataire debug:', {
        //   mailId: mail.ID_Mail,
        //   userId: userId,
        //   destinataire: destinataire,
        //   searchTerm: searchTerm
        // });

        // Vérifier les correspondances
        const idMatch = userId.toLowerCase().includes(searchTerm);
        const emailMatch = destinataire.toLowerCase().includes(searchTerm);

        // Si ni l'ID ni l'email ne correspondent, exclure ce mail
        if (!idMatch && !emailMatch) {
          return false;
        }
      }

      // Filtrer par sujet
      if (searchQuery.value.subject &&
          !mail.Sujet?.toLowerCase().includes(searchQuery.value.subject.toLowerCase())) {
        return false;
      }

      // Filtrer par date (de)
      if (searchQuery.value.dateFrom) {
        const dateFrom = new Date(searchQuery.value.dateFrom);
        const mailDate = new Date(mail.Date_Reception);
        if (mailDate < dateFrom) return false;
      }

      // Filtrer par date (à)
      if (searchQuery.value.dateTo) {
        const dateTo = new Date(searchQuery.value.dateTo);
        dateTo.setHours(23, 59, 59, 999); // Fin de journée
        const mailDate = new Date(mail.Date_Reception);
        if (mailDate > dateTo) return false;
      }

      return true;
    });
  });

  // Mails triés selon les critères actuels (après filtrage)
  const sortedMails = computed(() => {
    if (!filteredMails.value?.length) return [];

    const sorted = [...filteredMails.value];

    sorted.sort((a, b) => {
      let valA, valB;

      // Déterminer les valeurs à comparer selon la colonne
      switch(sortColumn.value) {
        case 'Statut':
          valA = a.Statut || '';
          valB = b.Statut || '';
          break;
        case 'ID_Utilisateur':
          valA = a.ID_Utilisateur || 0;
          valB = b.ID_Utilisateur || 0;
          break;
        case 'Emetteur':
          valA = a.Emetteur || '';
          valB = b.Emetteur || '';
          break;
        case 'Sujet':
          valA = a.Sujet || '';
          valB = b.Sujet || '';
          break;
        case 'Date_Reception':
          valA = new Date(a.Date_Reception || 0).getTime();
          valB = new Date(b.Date_Reception || 0).getTime();
          break;
        default:
          valA = a[sortColumn.value] || '';
          valB = b[sortColumn.value] || '';
      }

      // Comparaison selon la direction
      if (sortDirection.value === 'asc') {
        return valA > valB ? 1 : valA < valB ? -1 : 0;
      } else {
        return valA < valB ? 1 : valA > valB ? -1 : 0;
      }
    });

    return sorted;
  });

  // Mettre à jour les critères de recherche
  const updateSearchQuery = (query) => {
    // Convertir explicitement les valeurs de status en majuscules pour correspondre au format du backend
    if (query.status) {
      query.status = query.status.toUpperCase();
    }

    // Date range - s'assurer que les dates sont dans le bon format
    if (query.dateFrom && typeof query.dateFrom === 'string') {
      // S'assurer que dateFrom commence au début de la journée
      const dateFrom = new Date(query.dateFrom);
      dateFrom.setHours(0, 0, 0, 0);
      query.dateFrom = dateFrom.toISOString();
    }

    if (query.dateTo && typeof query.dateTo === 'string') {
      // S'assurer que dateTo va jusqu'à la fin de la journée
      const dateTo = new Date(query.dateTo);
      dateTo.setHours(23, 59, 59, 999);
      query.dateTo = dateTo.toISOString();
    }

    searchQuery.value = { ...searchQuery.value, ...query };
  };

  // Réinitialiser les critères de recherche
  const resetSearch = () => {
    searchQuery.value = {
      status: '',
      sender: '',
      recipient: '',
      subject: '',
      dateFrom: '',
      dateTo: ''
    };
  };

  // Charger les mails par statut
  const loadMails = async (statusList, keepSearch = false) => {
    loading.value = true;
    error.value = null;
    selectedMails.value = [];
    expandedMailId.value = null;

    // Ne réinitialise la recherche que si le paramètre keepSearch est false
    if (!keepSearch) {
      resetSearch();
    }

    try {
      mails.value = await mailService.getMailsByStatus(statusList);
    } catch (err) {
      console.error(`Failed to load mails with status ${statusList}:`, err);
      error.value = `Failed to load emails. Please try again later.`;
    } finally {
      loading.value = false;
    }
  };

  // Puis ajouter une méthode pour rafraîchir les données tout en conservant la recherche
  const refreshWithCurrentFilters = async (statusList) => {
    await loadMails(statusList, true); // true pour garder les critères de recherche
  };

  // Actions de sélection
  const toggleSelectAll = () => {
    if (allSelected.value) {
      selectedMails.value = [];
    } else {
      selectedMails.value = mails.value.map(mail => mail.ID_Mail);
    }
  };

  const toggleSelect = (mailId) => {
    const index = selectedMails.value.indexOf(mailId);
    if (index === -1) {
      selectedMails.value.push(mailId);
    } else {
      selectedMails.value.splice(index, 1);
    }
  };

  const isSelected = (mailId) => {
    return selectedMails.value.includes(mailId);
  };

  // Actions d'expansion
  const toggleExpand = (mailId) => {
    expandedMailId.value = expandedMailId.value === mailId ? null : mailId;
  };

  // Actions de tri
  const toggleSort = (column) => {
    if (sortColumn.value === column) {
      sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
    } else {
      sortColumn.value = column;
      sortDirection.value = 'asc';
    }
  };

  const getSortIcon = (column) => {
    if (sortColumn.value !== column) {
      return 'pi-filter text-gray-300';
    }
    return sortDirection.value === 'asc'
      ? 'pi-sort-amount-up-alt text-blue-500'
      : 'pi-sort-amount-down text-blue-500';
  };

  // Actions sur les mails
  const bulkUpdateStatus = async (status) => {
    if (selectedMails.value.length === 0) return;

    try {
      loading.value = true;
      await mailService.bulkUpdateMailStatus(selectedMails.value, status);
      // Recharger les mails du même statut
      await loadMails(mails.value[0]?.Statut || '');
    } catch (err) {
      console.error(`Failed to update mail status to ${status}:`, err);
      error.value = `Failed to update mail status. Please try again.`;
    } finally {
      loading.value = false;
    }
  };

  const updateMailStatus = async (mailId, status) => {
    try {
      await mailService.updateMailStatus(mailId, status);
      // Recharger les mails du même statut
      await loadMails(mails.value[0]?.Statut || '');
    } catch (err) {
      console.error(`Failed to update mail status to ${status}:`, err);
      error.value = `Failed to update mail status. Please try again.`;
    }
  };

  return {
    // État
    mails,
    loading,
    error,
    expandedMailId,
    selectedMails,
    sortColumn,
    sortDirection,
    sortedMails,
    allSelected,
    searchQuery,

    // Méthodes
    loadMails,
    toggleSelectAll,
    toggleSelect,
    isSelected,
    toggleExpand,
    toggleSort,
    getSortIcon,
    bulkUpdateStatus,
    updateMailStatus,
    updateSearchQuery,
    resetSearch,
    refreshWithCurrentFilters
  };
}
