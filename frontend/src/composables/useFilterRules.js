import { ref } from 'vue';
import rulesService from '@/services/rulesService';

export default function useFilterRules() {
  const filterRules = ref([]);
  const loading = ref(false);
  const error = ref(null);

  /**
   * Loads filtering rules
   */
  const loadFilterRules = async () => {
    try {
      loading.value = true;
      error.value = null;
      const response = await rulesService.getFilterRules();
      filterRules.value = response.data;
    } catch (err) {
      console.error('Failed to load filter rules:', err);
      error.value = 'Unable to load filtering rules. Please try again.';
    } finally {
      loading.value = false;
    }
  };

  /**
   * Add a filter rule
   */
  const addFilterRule = async (rule) => {
    try {
      loading.value = true;
      error.value = null;

      const response = await rulesService.createFilterRule(rule);
      filterRules.value.push(response.data);

      return { success: true, data: response.data };
    } catch (err) {
      console.error('Failed to add filter rule:', err);
      error.value = err.response?.data?.message || "Unable to add filtering rule.";
      return { success: false, error: error.value };
    } finally {
      loading.value = false;
    }
  };

  /**
   * Update a filter rule
   */
  const updateFilterRule = async (id, updatedRule) => {
    try {
      loading.value = true;
      error.value = null;

      const response = await rulesService.updateFilterRule(id, updatedRule);

      // Update rule locally
      const index = filterRules.value.findIndex(rule => rule.id === id);
      if (index !== -1) {
        filterRules.value[index] = response.data;
      }

      return { success: true, data: response.data };
    } catch (err) {
      console.error('Failed to update filter rule:', err);
      error.value = err.response?.data?.message || "Unable to update filtering rule.";
      return { success: false, error: error.value };
    } finally {
      loading.value = false;
    }
  };

  /**
   * Delete a filter rule
   */
  const deleteFilterRule = async (id) => {
    try {
      loading.value = true;
      error.value = null;

      await rulesService.deleteFilterRule(id);

      // Remove rule locally
      filterRules.value = filterRules.value.filter(rule => rule.id !== id);

      return { success: true };
    } catch (err) {
      console.error('Failed to delete filter rule:', err);
      error.value = err.response?.data?.message || "Unable to delete filtering rule.";
      return { success: false, error: error.value };
    } finally {
      loading.value = false;
    }
  };

  /**
   * Validate an email address
   */
  const validateEmail = (email) => {
    const re = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
  };

  return {
    filterRules,
    loading,
    error,
    loadFilterRules,
    addFilterRule,
    updateFilterRule,
    deleteFilterRule,
    validateEmail
  };
}
