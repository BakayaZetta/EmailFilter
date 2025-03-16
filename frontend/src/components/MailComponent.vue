<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import api from '@/services/api';

// Props pour recevoir le mail à afficher
const props = defineProps({
  mail: {
    type: Object,
    required: true
  },
  expanded: {
    type: Boolean,
    default: false
  }
});

// Émissions pour communiquer avec le composant parent
const emit = defineEmits(['close']);

// État local du composant
const loading = ref(false);
const mailDetails = ref(null);
const showRawHtml = ref(false);

// Fonction pour charger les détails complets du mail
const loadMailDetails = async () => {
  if (!props.mail?.ID_Mail) return;

  loading.value = true;
  try {
    const response = await api.get(`/mails/${props.mail.ID_Mail}/complete`);
    mailDetails.value = response.data;
  } catch (error) {
    console.error('Erreur lors du chargement des détails du mail:', error);
  } finally {
    loading.value = false;
  }
};

// Fonction pour fermer le composant
const close = () => {
  emit('close');
};

// Fonction pour empêcher les clics sur le contenu des emails
const preventClicks = (event) => {
  let target = event.target;
  while (target) {
    if (target.tagName && target.tagName.toLowerCase() === 'a') {
      event.preventDefault();
      event.stopPropagation();
      alert('Link clicking is disabled for security reasons. This email may be a phishing attempt.');
      return;
    }
    target = target.parentElement;
  }
};

// Catégoriser les analyses par type
const categorizedAnalyses = computed(() => {
  if (!mailDetails.value?.analyses) return { SPF: [], DKIM: [], DMARC: [], AI: [] };

  const result = {
    SPF: mailDetails.value.analyses.filter(a => a.type === 'SPF'),
    DKIM: mailDetails.value.analyses.filter(a => a.type === 'DKIM'),
    DMARC: mailDetails.value.analyses.filter(a => a.type === 'DMARC'),
    AI: mailDetails.value.analyses.filter(a => a.type === 'AI')
  };
  return result;
});

// Parseur pour les résultats d'analyse AI (qui sont stockés en JSON)
const parseAIResult = (resultText) => {
  try {
    // Add debug logging
    console.debug('Parsing AI result:', resultText);

    if (!resultText) return null;

    // Remove any prefix like "AI_PHISHING: " if present
    const prefixMatch = resultText.match(/^([A-Z_]+):\s*/);
    if (prefixMatch) {
      resultText = resultText.substring(prefixMatch[0].length);
      console.debug('Removed prefix, new text:', resultText);
    }

    // If the string looks like a Python dict (begins with { and ends with })
    if (resultText.trim().startsWith('{') && resultText.trim().endsWith('}')) {
      try {
        // 1. Replace Python-style single quotes with double quotes for JSON
        let processedText = resultText.replace(/'/g, '"');

        // 2. Fix malformed JSON where property names aren't properly quoted
        processedText = processedText.replace(/([{,]\s*)(\w+)(\s*:)/g, '$1"$2"$3');

        console.debug('Processed JSON text:', processedText);

        // 3. Try to parse the processed JSON
        const result = JSON.parse(processedText);

        // 4. Ensure the result has all expected properties
        return {
          phishing_count: result.phishing_count || 0,
          benign_count: result.benign_count || 0,
          phishing_avg_score: result.phishing_avg_score || 0,
          benign_avg_score: result.benign_avg_score || 0
        };
      } catch (e) {
        console.error('JSON parsing error:', e);
        throw e; // Re-throw for the outer catch block
      }
    } else {
      // If it doesn't look like JSON/dict at all
      console.warn('AI result doesn\'t look like JSON/dict format:', resultText);
      return {
        phishing_count: 0,
        benign_count: 0,
        phishing_avg_score: 0,
        benign_avg_score: 0,
        error: 'Format non reconnu'
      };
    }
  } catch (e) {
    console.error('Failed to parse AI result:', e);
    console.debug('Raw result text:', resultText);

    // Return a default structure to prevent UI errors
    return {
      phishing_count: 0,
      benign_count: 0,
      phishing_avg_score: 0,
      benign_avg_score: 0,
      error: 'Erreur de parsing'
    };
  }
};

// Obtenir une icône et une couleur basées sur le résultat de l'analyse
const getAnalysisIndicator = (analysis) => {
  const result = analysis.result.toLowerCase();

  if (result.includes('valid') || result.includes('pass')) {
    return { icon: 'pi-check-circle', color: 'text-green-500' };
  } else if (result.includes('invalid') || result.includes('fail')) {
    return { icon: 'pi-times-circle', color: 'text-red-500' };
  } else if (result.includes('warning') || result.includes('soft')) {
    return { icon: 'pi-exclamation-triangle', color: 'text-yellow-500' };
  } else {
    return { icon: 'pi-info-circle', color: 'text-gray-500' };
  }
};

// Déterminer si un email est globalement suspect en fonction des analyses
const isEmailSuspicious = computed(() => {
  if (!mailDetails.value) return true;

  // Vérifier les analyses SPF et DKIM
  const hasSPFFailure = categorizedAnalyses.value.SPF.some(a =>
    a.result.toLowerCase().includes('invalid') ||
    a.result.toLowerCase().includes('fail')
  );

  const hasDKIMFailure = categorizedAnalyses.value.DKIM.some(a => {
    const result = a.result.toLowerCase();
    return result.includes('invalid') ||
           result.includes('no dkim signature found') ||
           result.includes('dns error') ||
           result.includes('error during');
  });

  // Vérifier l'analyse AI
  const aiAnalyses = categorizedAnalyses.value.AI;
  let aiSuspicious = false;

  if (aiAnalyses.length > 0) {
    for (const analysis of aiAnalyses) {
      const aiResult = parseAIResult(analysis.result);
      if (aiResult && aiResult.phishing_count > aiResult.benign_count) {
        aiSuspicious = true;
        break;
      }
    }
  }

  // Vérifier si des liens suspects ont été détectés
  const hasSuspiciousLinks = mailDetails.value.links?.some(link =>
    link.status?.toLowerCase().includes('suspicious') ||
    link.status?.toLowerCase().includes('malicious')
  );

  // Vérifier si des pièces jointes suspectes ont été détectées
  const hasSuspiciousAttachments = mailDetails.value.attachments?.some(attachment =>
    attachment.status?.toLowerCase().includes('suspicious') ||
    attachment.status?.toLowerCase().includes('malicious')
  );

  return hasSPFFailure || hasDKIMFailure || aiSuspicious || hasSuspiciousLinks || hasSuspiciousAttachments;
});

// Formatage de la taille de pièce jointe en KB/MB
const formatFileSize = (sizeInBytes) => {
  if (!sizeInBytes) return 'Inconnu';

  if (sizeInBytes < 1024) {
    return `${sizeInBytes} B`;
  } else if (sizeInBytes < 1024 * 1024) {
    return `${(sizeInBytes / 1024).toFixed(1)} KB`;
  } else {
    return `${(sizeInBytes / (1024 * 1024)).toFixed(1)} MB`;
  }
};

// Obtenir l'icône pour un type de fichier
const getFileIcon = (fileType) => {
  if (!fileType) return 'pi-file';

  const type = fileType.toLowerCase();
  if (type.includes('pdf')) return 'pi-file-pdf';
  if (type.includes('word') || type.includes('doc')) return 'pi-file-word';
  if (type.includes('excel') || type.includes('xls')) return 'pi-file-excel';
  if (type.includes('image') || type.includes('png') || type.includes('jpg')) return 'pi-image';
  if (type.includes('zip') || type.includes('archive') || type.includes('rar')) return 'pi-box';
  if (type.includes('exe') || type.includes('application')) return 'pi-cog';

  return 'pi-file';
};

// Obtenir la classe de couleur pour le statut d'analyse
const getStatusColor = (status) => {
  if (!status) return 'text-gray-500';

  const lowerStatus = status.toLowerCase();
  if (lowerStatus.includes('malicious') || lowerStatus.includes('dangerous')) {
    return 'text-red-600';
  }
  if (lowerStatus.includes('suspicious')) {
    return 'text-yellow-600';
  }
  if (lowerStatus.includes('safe') || lowerStatus.includes('clean')) {
    return 'text-green-600';
  }

  return 'text-gray-500';
};

// Charger les détails du mail si le composant est développé
watch(() => props.expanded, (isExpanded) => {
  if (isExpanded && !mailDetails.value) {
    loadMailDetails();
  }
});

// Initialisation au montage
onMounted(() => {
  if (props.expanded) {
    loadMailDetails();
  }
});
</script>

<template>
  <div class="animate-fadeIn">
    <div class="bg-white rounded-md shadow p-4">
      <div v-if="loading" class="flex justify-center py-10">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span class="ml-3 text-blue-500">Chargement des détails...</span>
      </div>

      <div v-else-if="!mailDetails" class="bg-red-50 p-4 rounded text-red-700">
        Impossible de charger les détails du mail.
      </div>

      <div v-else>
        <!-- Section des résultats d'analyse avec barre de statut globale -->
        <div class="mb-4">
          <div
            :class="[
              'mb-3 p-2 rounded-lg text-white font-medium flex items-center',
              isEmailSuspicious ? 'bg-red-500' : 'bg-green-500'
            ]"
          >
            <i :class="`pi ${isEmailSuspicious ? 'pi-shield' : 'pi-check-circle'} mr-2`"></i>
            <span>{{ isEmailSuspicious ? 'Ce mail présente des signes suspects' : 'Ce mail semble sécurisé' }}</span>
          </div>

          <!-- Section des analyses -->
          <div class="mb-5">
            <h3 class="text-lg font-semibold mb-2">Analyses de sécurité</h3>
            <div v-if="!mailDetails.analyses || mailDetails.analyses.length === 0" class="text-sm text-gray-500 italic">
              Aucune analyse disponible pour ce message
            </div>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <!-- Résultats SPF -->
              <div v-if="categorizedAnalyses.SPF.length > 0" class="bg-gray-50 p-2 rounded border">
                <div class="flex items-center mb-1">
                  <i class="pi pi-shield mr-1"></i>
                  <span class="font-medium">SPF (Sender Policy Framework)</span>
                </div>
                <div v-for="analysis in categorizedAnalyses.SPF" :key="analysis.id" class="text-sm">
                  <div class="flex items-center mt-1">
                    <i :class="`pi ${getAnalysisIndicator(analysis).icon} ${getAnalysisIndicator(analysis).color} mr-1`"></i>
                    <span>{{ analysis.result.replace('SPF: ', '') }}</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    Analysé le {{ new Date(analysis.date).toLocaleString() }}
                  </div>
                </div>
              </div>

              <!-- Résultats DKIM -->
              <div v-if="categorizedAnalyses.DKIM.length > 0" class="bg-gray-50 p-2 rounded border">
                <div class="flex items-center mb-1">
                  <i class="pi pi-lock mr-1"></i>
                  <span class="font-medium">DKIM (DomainKeys Identified Mail)</span>
                </div>
                <div v-for="analysis in categorizedAnalyses.DKIM" :key="analysis.id" class="text-sm">
                  <div class="flex items-center mt-1">
                    <i :class="`pi ${getAnalysisIndicator(analysis).icon} ${getAnalysisIndicator(analysis).color} mr-1`"></i>
                    <span>{{ analysis.result.replace('DKIM: ', '') }}</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    Analysé le {{ new Date(analysis.date).toLocaleString() }}
                  </div>
                </div>
              </div>

              <!-- Résultats DMARC -->
              <div v-if="categorizedAnalyses.DMARC.length > 0" class="bg-gray-50 p-2 rounded border">
                <div class="flex items-center mb-1">
                  <i class="pi pi-verified mr-1"></i>
                  <span class="font-medium">DMARC (Domain-based Message Authentication)</span>
                </div>
                <div v-for="analysis in categorizedAnalyses.DMARC" :key="analysis.id" class="text-sm">
                  <div class="flex items-center mt-1">
                    <i :class="`pi ${getAnalysisIndicator(analysis).icon} ${getAnalysisIndicator(analysis).color} mr-1`"></i>
                    <span>{{ analysis.result.replace('DMARC: ', '') }}</span>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    Analysé le {{ new Date(analysis.date).toLocaleString() }}
                  </div>
                </div>
              </div>

              <!-- Résultats AI -->
              <div v-if="categorizedAnalyses.AI.length > 0" class="bg-gray-50 p-2 rounded border">
                <div class="flex items-center mb-1">
                  <i class="pi pi-chart-bar mr-1"></i>
                  <span class="font-medium">Analyse par Intelligence Artificielle</span>
                </div>
                <div v-for="analysis in categorizedAnalyses.AI" :key="analysis.id" class="text-sm">
                  <template v-if="parseAIResult(analysis.result) &&
                                 parseAIResult(analysis.result).phishing_count !== undefined &&
                                 parseAIResult(analysis.result).benign_count !== undefined">
                    <div class="mt-1">
                      <div class="grid grid-cols-2 gap-2">
                        <div class="p-1 rounded bg-red-50">
                          <div class="font-medium text-red-700">Phishing</div>
                          <div class="text-xs">Instances: {{ parseAIResult(analysis.result).phishing_count }}</div>
                          <div class="text-xs">Score moyen: {{ (parseAIResult(analysis.result).phishing_avg_score * 100 || 0).toFixed(2) }}%</div>
                        </div>
                        <div class="p-1 rounded bg-green-50">
                          <div class="font-medium text-green-700">Légitime</div>
                          <div class="text-xs">Instances: {{ parseAIResult(analysis.result).benign_count }}</div>
                          <div class="text-xs">Score moyen: {{ (parseAIResult(analysis.result).benign_avg_score * 100 || 0).toFixed(2) }}%</div>
                        </div>
                      </div>
                    </div>
                    <div class="mt-1 text-sm">
                      <span :class="parseAIResult(analysis.result).phishing_count > parseAIResult(analysis.result).benign_count ? 'text-red-600 font-medium' : 'text-green-600 font-medium'">
                        Verdict: {{ parseAIResult(analysis.result).phishing_count > parseAIResult(analysis.result).benign_count ? 'Potentiellement malveillant' : 'Probablement légitime' }}
                      </span>
                    </div>
                  </template>
                  <div v-else class="text-xs text-gray-500 mt-1">
                    Données d'analyse non disponibles ou dans un format incorrect
                    <div v-if="parseAIResult(analysis.result)?.error" class="text-red-500">
                      ({{ parseAIResult(analysis.result).error }})
                    </div>
                  </div>
                  <div class="text-xs text-gray-500 mt-1">
                    Analysé le {{ new Date(analysis.date).toLocaleString() }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Section des pièces jointes -->
          <div v-if="mailDetails.attachments && mailDetails.attachments.length > 0" class="mb-5">
            <h3 class="text-lg font-semibold mb-2">Pièces jointes ({{ mailDetails.attachments.length }})</h3>
            <div class="bg-gray-50 p-3 rounded">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <div v-for="attachment in mailDetails.attachments" :key="attachment.id"
                     class="flex items-center border p-2 rounded bg-white">
                  <div class="mr-3">
                    <i :class="`pi ${getFileIcon(attachment.type)} text-xl`"></i>
                  </div>
                  <div class="flex-grow">
                    <div class="text-sm font-medium truncate" :title="attachment.name">
                      {{ attachment.name }}
                    </div>
                    <div class="text-xs text-gray-500">
                      {{ formatFileSize(attachment.size) }} - {{ attachment.type || 'Type inconnu' }}
                    </div>
                  </div>
                  <div :class="`ml-2 text-xs font-medium ${getStatusColor(attachment.status)}`">
                    {{ attachment.status || 'Non analysé' }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Section des liens -->
          <div v-if="mailDetails.links && mailDetails.links.length > 0" class="mb-5">
            <h3 class="text-lg font-semibold mb-2">Liens détectés ({{ mailDetails.links.length }})</h3>
            <div class="bg-gray-50 p-3 rounded">
              <div class="space-y-1">
                <div v-for="link in mailDetails.links" :key="link.id"
                     class="flex items-center border p-2 rounded bg-white">
                  <div class="mr-2">
                    <i class="pi pi-link text-blue-500"></i>
                  </div>
                  <div class="flex-grow">
                    <div class="text-sm truncate" :title="link.url">
                      {{ link.url }}
                    </div>
                  </div>
                  <div :class="`ml-2 text-xs font-medium ${getStatusColor(link.status)}`">
                    {{ link.status || 'Non analysé' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- En-tête détaillé du mail -->
        <div class="mb-3 border-t border-b py-3">
          <div class="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span class="font-semibold">From:</span> {{ mailDetails.sender }}
            </div>
            <div>
              <span class="font-semibold">To:</span> {{ mailDetails.user?.email || `User ID: ${mailDetails.user?.id}` }}
            </div>
            <div>
              <span class="font-semibold">Subject:</span> {{ mailDetails.subject }}
            </div>
            <div>
              <span class="font-semibold">Date:</span> {{ new Date(mailDetails.receivedDate).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Corps du mail -->
        <div class="mb-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-sm font-semibold">Email Content</h3>
            <div class="flex space-x-2">
              <button @click="showRawHtml = !showRawHtml"
                class="text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded flex items-center"
                :class="{ 'bg-blue-100': showRawHtml }">
                <i class="pi" :class="showRawHtml ? 'pi-code' : 'pi-eye'"></i>
                <span class="ml-1">{{ showRawHtml ? 'Show Rendered' : 'Show Raw HTML' }}</span>
              </button>
              <button @click="close()"
                class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded flex items-center">
                <i class="pi pi-times mr-1"></i> Close
              </button>
            </div>
          </div>

          <!-- Indicateur de sécurité -->
          <div class="bg-red-100 text-red-800 px-3 py-1 mb-3 text-sm rounded flex items-center">
            <i class="pi pi-lock mr-1 text-sm"></i>
            <span>Secure View: Links and forms are disabled</span>
          </div>

          <!-- Contenu interprété (par défaut) -->
          <div v-if="!showRawHtml" class="email-content bg-white p-3 rounded border relative" @click="preventClicks">
            <div v-html="mailDetails.content || '<em>The content of this email is not available or is empty.</em>'"></div>
          </div>

          <!-- Contenu brut (option) -->
          <div v-else
            class="whitespace-pre-wrap text-sm bg-gray-50 p-3 rounded border overflow-auto max-h-[400px] font-mono">
            {{ mailDetails.content || "The content of this email is not available or is empty." }}
          </div>

          <!-- Avertissement de sécurité -->
          <div class="text-xs text-amber-600 mt-1 flex items-center">
            <i class="pi pi-exclamation-triangle text-xs mr-1"></i>
            <span>Warning: This email may contain unsafe content</span>
          </div>
        </div>

        <!-- Pied de page avec action fermer -->
        <div class="mt-3 flex justify-end">
          <button @click="close()"
            class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 px-2 py-1 rounded flex items-center">
            <i class="pi pi-times mr-1"></i> Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Animation pour l'apparition du contenu développé */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.2s ease-out forwards;
}

/* Styles pour le contenu des emails */
.email-content {
  max-height: 500px;
  overflow: auto;
  position: relative;
  /* Pour le positionnement des éléments enfants */
}

/* Styles de base pour le HTML des emails */
.email-content :deep(table) {
  border-collapse: collapse;
  margin: 0.5rem 0;
}

.email-content :deep(td),
.email-content :deep(th) {
  border: 1px solid #ddd;
  padding: 0.5rem;
}

.email-content :deep(img) {
  max-width: 100%;
  height: auto;
}

.email-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}

/* Styles pour les liens dans le contenu rendu sécurisé */
.email-content :deep(a) {
  color: #3b82f6;
  text-decoration: line-through;
  /* Barrer les liens pour indiquer qu'ils ne sont pas cliquables */
  cursor: not-allowed;
  pointer-events: all;
  position: relative;
}

/* Ajouter un effet visuel sur survol des liens pour indiquer qu'ils ne sont pas cliquables */
.email-content :deep(a):hover::after {
  content: "⛔ Link disabled";
  position: absolute;
  bottom: 100%;
  left: 0;
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 5px;
  border-radius: 3px;
  font-size: 10px;
  white-space: nowrap;
}

/* Désactiver les formulaires et les éléments interactifs */
.email-content :deep(form),
.email-content :deep(button),
.email-content :deep(input),
.email-content :deep(select),
.email-content :deep(textarea) {
  pointer-events: none;
  opacity: 0.7;
  cursor: not-allowed;
}

/* Style pour le conteneur sécurisé */
.secured-email-content {
  position: relative;
}
</style>
