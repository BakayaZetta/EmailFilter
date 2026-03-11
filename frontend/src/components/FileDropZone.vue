<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue';
import axios from 'axios';
import mailService from '@/services/mailService';

const props = defineProps({
  accept: {
    type: String,
    default: '.eml'
  },
  maxSize: {
    type: Number,
    default: 1000 * 1024 * 1024 // 1GB par défaut
  },
  isOpen: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['upload-success', 'upload-error', 'scan-finished', 'close']);

const isDragging = ref(false);
const dropZone = ref(null);
const modal = ref(null);

// Gestion des fichiers multiples
const files = ref([]);
const addedFiles = computed(() => files.value.filter(f => !f.uploaded && !f.uploading));
const uploadingFiles = computed(() => files.value.filter(f => f.uploading));
const uploadedFiles = computed(() => files.value.filter(f => f.uploaded));
const failedFiles = computed(() => files.value.filter(f => f.error));
const processingFiles = computed(() => files.value.filter(f => f.processing));
const scanPollers = new Map();

// Empêcher le navigateur d'ouvrir les fichiers
const preventDefaults = (e) => {
  e.preventDefault();
  e.stopPropagation();
};

const highlight = () => {
  isDragging.value = true;
};

const unhighlight = () => {
  isDragging.value = false;
};

const handleDrop = (e) => {
  preventDefaults(e);
  unhighlight();

  const dt = e.dataTransfer;
  const newFiles = dt.files;

  handleFiles(newFiles);
};

// Ajoute les fichiers à la liste sans les uploader immédiatement
const handleFiles = (fileList) => {
  if (fileList.length === 0) return;

  // Filtrer les fichiers valides et ajouter à la liste
  [...fileList].forEach(file => {
    // Vérifier l'extension
    if (!file.name.endsWith(props.accept)) {
      files.value.push({
        id: generateId(),
        file,
        error: `Only ${props.accept} files are allowed.`,
        uploading: false,
        uploaded: false,
        processing: false,
        processed: false,
        processingProgress: 0,
        progress: 0
      });
      return;
    }

    // Vérifier la taille
    if (file.size > props.maxSize) {
      files.value.push({
        id: generateId(),
        file,
        error: `File size exceeds ${props.maxSize / (1024 * 1024)}MB.`,
        uploading: false,
        uploaded: false,
        processing: false,
        processed: false,
        processingProgress: 0,
        progress: 0
      });
      return;
    }

    // Ajouter le fichier valide
    files.value.push({
      id: generateId(),
      file,
      error: null,
      uploading: false,
      uploaded: false,
      processing: false,
      processed: false,
      processingProgress: 0,
      progress: 0
    });
  });
};

const clearScanPoller = (fileId) => {
  const poller = scanPollers.get(fileId);
  if (!poller) {
    return;
  }

  clearInterval(poller.progressIntervalId);
  clearInterval(poller.statusIntervalId);
  clearTimeout(poller.timeoutId);
  scanPollers.delete(fileId);
};

const finishProcessing = (fileItem, status = 'finished') => {
  clearScanPoller(fileItem.id);
  fileItem.processingProgress = 100;
  fileItem.processing = false;
  fileItem.processed = true;

  emit('scan-finished', {
    fileName: fileItem.file.name,
    status
  });
};

const startProcessingIndicator = (fileItem, requestId = null) => {
  fileItem.processing = true;
  fileItem.processed = false;
  fileItem.processingProgress = 5;

  const progressIntervalId = setInterval(() => {
    if (fileItem.processingProgress < 95) {
      fileItem.processingProgress += 5;
    }
  }, 1200);

  const timeoutId = setTimeout(() => {
    finishProcessing(fileItem, 'timeout');
  }, 180000);

  let statusIntervalId = null;
  if (requestId) {
    statusIntervalId = setInterval(async () => {
      try {
        const response = await axios.get(`/analyse/status/${requestId}`);
        const status = response?.data?.status;

        if (status === 'finished' || status === 'failed') {
          finishProcessing(fileItem, status);
        }
      } catch (error) {
        if (error?.response?.status !== 404) {
          console.error(`Scan status polling error for ${fileItem.file.name}:`, error);
        }
      }
    }, 2000);
  }

  scanPollers.set(fileItem.id, {
    progressIntervalId,
    statusIntervalId,
    timeoutId
  });
};

// Génère un ID unique pour chaque fichier
const generateId = () => {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
};

// Upload d'un fichier spécifique
const uploadFile = async (fileItem) => {
  if (fileItem.uploading || fileItem.uploaded) return;

  try {
    fileItem.uploading = true;
    fileItem.progress = 0;
    fileItem.error = null;

    const emailData = {
      subject: fileItem.file.name, // Assuming file name as subject
      content: await fileItem.file.text(), // Read file content
      sender: 'unknown@example.com', // Placeholder sender
      userId: 1, // Placeholder user ID
      receivedDate: new Date().toISOString(),
    };

    const response = await mailService.uploadEmail(emailData);

    fileItem.uploaded = true;
    fileItem.uploading = false;
    const requestId = response?.request_id || null;
    startProcessingIndicator(fileItem, requestId);

    emit('upload-success', {
      fileName: fileItem.file.name,
      requestId,
      response,
    });
  } catch (error) {
    console.error('Upload error:', error);
    fileItem.error = error.response?.data?.message || 'Upload failed. Please try again.';
    fileItem.uploading = false;

    emit('upload-error', {
      fileName: fileItem.file.name,
      error,
    });
  }
};

// Upload tous les fichiers non encore uploadés en parallèle
const uploadAllFiles = async () => {
  const filesToUpload = files.value.filter(f => !f.uploaded && !f.uploading && !f.error);

  if (filesToUpload.length === 0) return;

  // Marquer tous les fichiers comme "uploading" avant de commencer
  filesToUpload.forEach(file => {
    file.uploading = true;
    file.progress = 0;
    file.error = null;
  });

  // Créer un tableau de promesses pour tous les uploads
  const uploadPromises = filesToUpload.map(fileItem => {
    const formData = new FormData();
    formData.append('file', fileItem.file);

    return axios.post('/analyse/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        fileItem.progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
      }
    })
    .then(response => {
      fileItem.uploaded = true;
      fileItem.uploading = false;
      const requestId = response?.data?.request_id || null;

      emit('upload-success', {
        fileName: fileItem.file.name,
        requestId,
        response: response.data
      });

      startProcessingIndicator(fileItem, requestId);

      return { success: true, fileItem, response };
    })
    .catch(error => {
      console.error(`Upload error for ${fileItem.file.name}:`, error);
      fileItem.error = error.response?.data?.message || 'Upload failed. Please try again.';
      fileItem.uploading = false;

      emit('upload-error', {
        fileName: fileItem.file.name,
        error
      });

      return { success: false, fileItem, error };
    });
  });

  // Exécuter tous les uploads en parallèle et attendre leur résolution
  try {
    await Promise.allSettled(uploadPromises);
    console.log('All upload requests completed');
  } catch (error) {
    console.error('Error during parallel uploads:', error);
  }
};

// Supprimer un fichier de la liste
const removeFile = (fileItem) => {
  clearScanPoller(fileItem.id);
  const index = files.value.findIndex(f => f.id === fileItem.id);
  if (index !== -1) {
    files.value.splice(index, 1);
  }
};

// Effacer tous les fichiers
const clearAllFiles = () => {
  files.value.forEach(fileItem => clearScanPoller(fileItem.id));
  files.value = [];
};

// Gérer le clic sur le bouton "Browse"
const handleBrowseClick = (e) => {
  e.stopPropagation();

  const input = document.createElement('input');
  input.type = 'file';
  input.accept = props.accept;
  input.multiple = true;
  input.addEventListener('change', (e) => {
    handleFiles(e.target.files);
  });
  input.click();
};

// Fonction pour fermer la modal
const closeModal = () => {
  emit('close');
};

// Gestionnaire de la touche Escape
const handleEscape = (e) => {
  if (e.key === 'Escape' && props.isOpen) {
    closeModal();
  }
};

// Gestionnaire de clic en dehors de la modal
const handleOutsideClick = (e) => {
  if (modal.value && props.isOpen && !modal.value.contains(e.target)) {
    closeModal();
  }
};

// Initialisation des event listeners - Modifications pour corriger le drag & drop
onMounted(() => {
  // Observer les changements dans isOpen pour attacher les event listeners
  // seulement quand la modal est visible
  watch(() => props.isOpen, (isOpen) => {
    if (isOpen) {
      nextTick(() => {
        setupDragAndDropListeners();
      });
    } else {
      cleanupDragAndDropListeners();
    }
  }, { immediate: true });

  // Ajouter les listeners globaux
  document.addEventListener('keydown', handleEscape);
  document.addEventListener('mousedown', handleOutsideClick);
});

// Fonction pour configurer tous les listeners de drag & drop
const setupDragAndDropListeners = () => {
  const zone = dropZone.value;
  if (!zone) return;

  console.log('Setting up drag and drop listeners'); // Debug

  // Ajouter les événements sur la zone de drop
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    zone.addEventListener(eventName, preventDefaults, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    zone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    zone.addEventListener(eventName, unhighlight, false);
  });

  zone.addEventListener('drop', handleDrop, false);

  // Ajouter aussi des événements sur la modal pour s'assurer que le drag
  // fonctionne même quand le curseur se déplace
  const modalElement = modal.value;
  if (modalElement) {
    ['dragenter', 'dragover', 'drop'].forEach(eventName => {
      modalElement.addEventListener(eventName, preventDefaults, false);
    });
  }
};

// Fonction pour nettoyer tous les listeners de drag & drop
const cleanupDragAndDropListeners = () => {
  const zone = dropZone.value;
  if (!zone) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    zone.removeEventListener(eventName, preventDefaults);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    zone.removeEventListener(eventName, highlight);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    zone.removeEventListener(eventName, unhighlight);
  });

  zone.removeEventListener('drop', handleDrop);

  // Nettoyer aussi les événements sur la modal
  const modalElement = modal.value;
  if (modalElement) {
    ['dragenter', 'dragover', 'drop'].forEach(eventName => {
      modalElement.removeEventListener(eventName, preventDefaults);
    });
  }
};

// Nettoyage des event listeners
onUnmounted(() => {
  files.value.forEach(fileItem => clearScanPoller(fileItem.id));
  document.removeEventListener('keydown', handleEscape);
  document.removeEventListener('mousedown', handleOutsideClick);
  cleanupDragAndDropListeners();
});

// Réinitialiser les fichiers quand la modal se ferme
watch(() => props.isOpen, (isOpen) => {
  if (!isOpen) {
    nextTick(() => {
      clearAllFiles();
    });
  }
});

// Ajout d'une fonction pour calculer la progression globale
const calculateOverallProgress = () => {
  if (uploadingFiles.value.length === 0) return 0;

  // Calculer la moyenne de progression de tous les fichiers en cours d'upload
  const totalProgress = uploadingFiles.value.reduce((sum, file) => sum + file.progress, 0);

  // Tenir compte également des fichiers déjà uploadés
  const completedWeight = uploadedFiles.value.length * 100;
  const totalItems = uploadingFiles.value.length + uploadedFiles.value.length;

  if (totalItems === 0) return 0;

  return Math.round((totalProgress + completedWeight) / totalItems);
};

</script>

<template>
  <!-- Modal backdrop - ajout effet de flou -->
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-opacity-20 backdrop-blur-sm z-50 flex items-center justify-center p-4 transition-opacity duration-300"
    @click="closeModal"
  >
    <!-- Modal - ombre plus prononcée et effet de relief -->
    <div
      ref="modal"
      class="bg-white rounded-lg shadow-2xl w-full max-w-3xl max-h-[80vh] overflow-hidden flex flex-col transform transition-all duration-300 scale-in-center border border-gray-100"
      style="box-shadow: rgba(17, 12, 46, 0.15) 0px 48px 100px 0px;"
      @click.stop
    >
      <!-- Modal header -->
      <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 class="text-lg font-medium text-gray-900">Upload Email Files</h3>
        <button @click="closeModal" class="text-gray-400 hover:text-gray-500">
          <i class="pi pi-times"></i>
        </button>
      </div>

      <!-- Modal body -->
      <div class="px-6 py-4 overflow-y-auto flex-grow">
        <!-- Barre de progression globale si un upload est en cours -->
        <div v-if="uploadingFiles.length > 0" class="mb-4">
          <div class="flex justify-between items-center mb-1">
            <span class="text-sm font-medium text-gray-700">Overall Progress</span>
            <span class="text-sm text-gray-500">{{ calculateOverallProgress() }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2.5">
            <div
              class="bg-blue-500 h-2.5 rounded-full transition-all duration-300"
              :style="{ width: `${calculateOverallProgress()}%` }"
            ></div>
          </div>
        </div>

        <!-- Drop zone -->
        <div
          ref="dropZone"
          class="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors mb-4 relative"
          :class="[
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
          ]"
          @click.stop="handleBrowseClick"
        >
          <div class="space-y-3">
            <div class="flex flex-col items-center justify-center">
              <i class="pi pi-cloud-upload text-3xl text-gray-400"></i>
              <p class="mt-2 text-sm font-medium text-gray-700">
                Drop your .eml files here, or click to select
              </p>
            </div>
            <p class="text-xs text-gray-500">
              Only .eml files are accepted (max size: {{ maxSize / (1024 * 1024) }}MB)
            </p>
          </div>
        </div>

        <!-- Files list -->
        <div v-if="files.length > 0" class="mt-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2">Files ({{ files.length }})</h4>

          <!-- List of files -->
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div
              v-for="fileItem in files"
              :key="fileItem.id"
              class="bg-gray-50 border rounded-md p-3 flex items-center"
            >
              <!-- File icon -->
              <div class="mr-3 text-gray-400">
                <i class="pi pi-file"></i>
              </div>

              <!-- File info -->
              <div class="flex-grow min-w-0">
                <p class="text-sm font-medium text-gray-900 truncate">{{ fileItem.file.name }}</p>
                <p class="text-xs text-gray-500">
                  {{ (fileItem.file.size / 1024).toFixed(2) }} KB
                </p>

                <!-- Error message -->
                <p v-if="fileItem.error" class="text-xs text-red-500 mt-1">
                  {{ fileItem.error }}
                </p>

                <!-- Progress bar for uploading files -->
                <div v-else-if="fileItem.uploading" class="mt-1.5">
                  <div class="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      class="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      :style="{ width: `${fileItem.progress}%` }"
                    ></div>
                  </div>
                  <p class="text-xs text-gray-500 mt-0.5">{{ fileItem.progress }}%</p>
                </div>

                <div v-else-if="fileItem.processing" class="mt-1.5">
                  <div class="w-full bg-amber-100 rounded-full h-1.5">
                    <div
                      class="bg-amber-500 h-1.5 rounded-full transition-all duration-500"
                      :style="{ width: `${fileItem.processingProgress}%` }"
                    ></div>
                  </div>
                  <p class="text-xs text-amber-700 mt-0.5">Scanning in background... {{ fileItem.processingProgress }}%</p>
                </div>

                <!-- Success message -->
                <p v-else-if="fileItem.uploaded" class="text-xs text-green-500 mt-1 flex items-center">
                  <i class="pi pi-check-circle mr-1"></i> Upload complete
                </p>
              </div>

              <!-- Action buttons -->
              <div>
                <!-- Remove button -->
                <button
                  v-if="!fileItem.uploading"
                  @click.stop="removeFile(fileItem)"
                  class="text-gray-400 hover:text-gray-600"
                  title="Remove file"
                >
                  <i class="pi pi-times"></i>
                </button>

                <!-- Upload single file button -->
                <button
                  v-if="!fileItem.uploading && !fileItem.uploaded && !fileItem.error"
                  @click.stop="uploadFile(fileItem)"
                  class="ml-2 text-blue-500 hover:text-blue-600"
                  title="Upload this file"
                >
                  <i class="pi pi-upload"></i>
                </button>

                <!-- Spinner for uploading -->
                <div v-if="fileItem.uploading" class="ml-2 text-blue-500">
                  <i class="pi pi-spinner animate-spin"></i>
                </div>
              </div>
            </div>
          </div>

          <!-- File statistics -->
          <div class="mt-3 text-xs text-gray-500 flex space-x-4">
            <span v-if="addedFiles.length > 0">
              <i class="pi pi-file text-gray-400 mr-1"></i> {{ addedFiles.length }} pending
            </span>
            <span v-if="uploadingFiles.length > 0">
              <i class="pi pi-spinner animate-spin text-blue-500 mr-1"></i> {{ uploadingFiles.length }} uploading
            </span>
            <span v-if="uploadedFiles.length > 0">
              <i class="pi pi-check-circle text-green-500 mr-1"></i> {{ uploadedFiles.length }} completed
            </span>
            <span v-if="processingFiles.length > 0">
              <i class="pi pi-clock text-amber-500 mr-1"></i> {{ processingFiles.length }} scanning
            </span>
            <span v-if="failedFiles.length > 0">
              <i class="pi pi-times-circle text-red-500 mr-1"></i> {{ failedFiles.length }} failed
            </span>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="text-center text-gray-500 mt-4">
          <p>No files added yet.</p>
        </div>
      </div>

      <!-- Modal footer with actions -->
      <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <!-- Left side: file count -->
        <div class="text-sm text-gray-500">
          {{ files.length }} file(s) selected
        </div>

        <!-- Right side: action buttons -->
        <div class="flex space-x-2">
          <button
            @click="clearAllFiles"
            class="px-3 py-1.5 border border-gray-300 rounded-md text-gray-700 text-sm hover:bg-gray-50"
            :disabled="files.length === 0"
          >
            Clear All
          </button>
          <button
            @click="closeModal"
            class="px-3 py-1.5 border border-gray-300 rounded-md text-gray-700 text-sm hover:bg-gray-50"
          >
            Close
          </button>
          <button
            @click="uploadAllFiles"
            class="px-3 py-1.5 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600"
            :disabled="addedFiles.length === 0"
          >
            Upload All
          </button>
        </div>
      </div>
    </div>
  </div>

</template>

<style scoped>
/* Animation d'entrée pour la modal */
.scale-in-center {
  animation: scale-in-center 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) both;
}

@keyframes scale-in-center {
  0% {
    transform: scale(0.9);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
