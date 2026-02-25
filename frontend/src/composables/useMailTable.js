import { ref, computed } from 'vue';
import mailService from '@/services/mailService';
import axios from 'axios';

export function useMailTable() {
  // State
  const mails = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const expandedMailId = ref(null);
  const selectedMails = ref([]);
  const currentPage = ref(1);
  const pageSize = ref(50);
  const totalItems = ref(0);
  const totalPages = ref(1);
  const currentStatusList = ref('');

  // Sorting
  const sortColumn = ref('Date_Reception');
  const sortDirection = ref('desc');

  // Search
  const searchQuery = ref({
    status: '',
    sender: '',
    recipient: '',
    subject: '',
    dateFrom: '',
    dateTo: ''
  });

  // Mistral states
  const mistralLoading = ref(false);
  const mistralResponse = ref(null);
  const mistralError = ref(null);
  const mistralEmailId = ref(null);

  // Check if all emails are selected
  const allSelected = computed(() => {
    return filteredMails.value.length > 0 && selectedMails.value.length === filteredMails.value.length;
  });

  // Emails filtered by search criteria
  const filteredMails = computed(() => {
    if (!mails.value?.length) return [];

    return mails.value.filter(mail => {
      // Filter by status
      if (searchQuery.value.status &&
          mail.Statut?.toLowerCase() !== searchQuery.value.status.toLowerCase()) {
        return false;
      }

      // Filter by sender
      if (searchQuery.value.sender &&
          !mail.Emetteur?.toLowerCase().includes(searchQuery.value.sender.toLowerCase())) {
        return false;
      }

      // Filter by recipient (User ID or email)
      if (searchQuery.value.recipient) {
        const searchTerm = searchQuery.value.recipient.toLowerCase();
        const userId = String(mail.ID_Utilisateur || '');
        const destinataire = String(mail.Destinataire || '');
        const idMatch = userId.toLowerCase().includes(searchTerm);
        const emailMatch = destinataire.toLowerCase().includes(searchTerm);
        if (!idMatch && !emailMatch) {
          return false;
        }
      }

      // Filter by subject
      if (searchQuery.value.subject &&
          !mail.Sujet?.toLowerCase().includes(searchQuery.value.subject.toLowerCase())) {
        return false;
      }

      // Filter by date (from)
      if (searchQuery.value.dateFrom) {
        const dateFrom = new Date(searchQuery.value.dateFrom);
        const mailDate = new Date(mail.Date_Reception);
        if (mailDate < dateFrom) return false;
      }

      // Filter by date (to)
      if (searchQuery.value.dateTo) {
        const dateTo = new Date(searchQuery.value.dateTo);
        dateTo.setHours(23, 59, 59, 999); // End of day
        const mailDate = new Date(mail.Date_Reception);
        if (mailDate > dateTo) return false;
      }

      return true;
    });
  });

  // Emails sorted by current criteria (after filtering)
  const sortedMails = computed(() => {
    if (!filteredMails.value?.length) return [];

    const sorted = [...filteredMails.value];

    sorted.sort((a, b) => {
      let valA, valB;

      // Determine values to compare based on column
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

      // Compare based on direction
      if (sortDirection.value === 'asc') {
        return valA > valB ? 1 : valA < valB ? -1 : 0;
      } else {
        return valA < valB ? 1 : valA > valB ? -1 : 0;
      }
    });

    return sorted;
  });

  // Update search criteria
  const updateSearchQuery = (query) => {
    // Explicitly convert status values to uppercase to match backend format
    if (query.status) {
      query.status = query.status.toUpperCase();
    }

    // Ensure dates are in the correct format
    if (query.dateFrom && typeof query.dateFrom === 'string') {
      // Ensure dateFrom starts at the beginning of the day
      const dateFrom = new Date(query.dateFrom);
      dateFrom.setHours(0, 0, 0, 0);
      query.dateFrom = dateFrom.toISOString();
    }

    if (query.dateTo && typeof query.dateTo === 'string') {
      // Ensure dateTo extends to the end of the day
      const dateTo = new Date(query.dateTo);
      dateTo.setHours(23, 59, 59, 999);
      query.dateTo = dateTo.toISOString();
    }

    searchQuery.value = { ...searchQuery.value, ...query };
  };

  // Reset search criteria
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

  // Load emails by status
  const loadMails = async (statusList, keepSearch = false, page = 1) => {
    loading.value = true;
    error.value = null;
    selectedMails.value = [];
    expandedMailId.value = null;
    currentStatusList.value = statusList;
    currentPage.value = page;

    // Only reset search if keepSearch parameter is false
    if (!keepSearch) {
      resetSearch();
    }

    try {
      const result = await mailService.getMailsByStatus(statusList, currentPage.value, pageSize.value);
      mails.value = result.items;
      totalItems.value = result.pagination.total;
      totalPages.value = result.pagination.totalPages;
      pageSize.value = result.pagination.limit;
    } catch (err) {
      console.error(`Failed to load mails with status ${statusList}:`, err);
      error.value = `Failed to load emails. Please try again later.`;
    } finally {
      loading.value = false;
    }
  };

  // Method to refresh data while preserving search criteria
  const refreshWithCurrentFilters = async (statusList) => {
    await loadMails(statusList, true, currentPage.value); // true to keep search criteria
  };

  const setPage = async (page) => {
    const requested = Number(page);
    if (Number.isNaN(requested) || requested < 1 || requested > totalPages.value || requested === currentPage.value) {
      return;
    }
    await loadMails(currentStatusList.value, true, requested);
  };

  // Selection actions
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

  // Expansion actions
  const toggleExpand = (mailId) => {
    expandedMailId.value = expandedMailId.value === mailId ? null : mailId;
  };

  // Sorting actions
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

  // Email actions
  const bulkUpdateStatus = async (status) => {
    if (selectedMails.value.length === 0) return;

    try {
      loading.value = true;
      await mailService.bulkUpdateMailStatus(selectedMails.value, status);
      await loadMails(currentStatusList.value, true, currentPage.value);
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
      await loadMails(currentStatusList.value, true, currentPage.value);
    } catch (err) {
      console.error(`Failed to update mail status to ${status}:`, err);
      error.value = `Failed to update mail status. Please try again.`;
    }
  };

  // Method to call Mistral API directly
  const askMistral = async (emailId) => {
    mistralLoading.value = true;
    mistralError.value = null;
    mistralResponse.value = null;
    mistralEmailId.value = emailId;

    try {
      // First, retrieve all detailed email data
      const emailDetails = await mailService.getMailDetails(emailId);

      // Then send these detailed data to Mistral API
      const response = await axios.post('/analyse/mistral', {
        emailId: emailId,
        emailData: emailDetails // Send complete email data
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.data && response.data.explanation) {
        mistralResponse.value = response.data.explanation;
      } else {
        mistralResponse.value = "No explanation available.";
      }
    } catch (error) {
      console.error("Error requesting explanation from Mistral:", error);

      mistralResponse.value = `# Problem analyzing the email

We couldn't generate a satisfactory explanation for this email.

## Possible causes:
- Insufficient data for analysis
- The AI service couldn't process the information correctly
- Connection issue with the analysis service

Please review email details manually to understand why it was filtered.`;

    } finally {
      mistralLoading.value = false;
    }
  };

  const resetMistral = () => {
    mistralLoading.value = false;
    mistralResponse.value = null;
    mistralError.value = null;
    mistralEmailId.value = null;
  };

  return {
    // State
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
    currentPage,
    pageSize,
    totalItems,
    totalPages,

    // Methods
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
    refreshWithCurrentFilters,
    setPage,

    // Mistral states and methods
    mistralLoading,
    mistralResponse,
    mistralError,
    mistralEmailId,
    askMistral,
    resetMistral
  };
}
