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

  // Computed property pour vérifier si tous les mails sont sélectionnés
  const allSelected = computed(() => {
    return mails.value.length > 0 && selectedMails.value.length === mails.value.length;
  });

  // Mails triés selon les critères actuels
  const sortedMails = computed(() => {
    if (!mails.value?.length) return [];

    const sortedMails = [...mails.value];

    sortedMails.sort((a, b) => {
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

    return sortedMails;
  });

  // Charger les mails par statut
  const loadMails = async (statusList) => {
    loading.value = true;
    error.value = null;
    selectedMails.value = [];
    expandedMailId.value = null;

    try {
      mails.value = await mailService.getMailsByStatus(statusList);
    } catch (err) {
      console.error(`Failed to load mails with status ${statusList}:`, err);
      error.value = `Failed to load emails. Please try again later.`;
    } finally {
      loading.value = false;
    }
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
  };
}
