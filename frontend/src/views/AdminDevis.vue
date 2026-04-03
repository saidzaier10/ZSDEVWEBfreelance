<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-900 py-12 transition-colors duration-200">
    <div class="container mx-auto px-4 lg:px-8">
      <!-- En-tête -->
      <div class="mb-8">
        <h1 class="text-4xl font-display font-bold gradient-text mb-2">
          Administration des Devis
        </h1>
        <p class="text-dark-600 dark:text-dark-300">
          Gérez tous les devis de la plateforme
        </p>
      </div>

      <!-- Statistiques -->
      <QuoteStats
        v-if="statistics"
        :statistics="statistics"
        :quotes="quotes"
      />

      <!-- Graphiques Analytics -->
      <QuoteCharts
        v-if="!loading && quotes.length > 0"
        :quotes="quotes"
      />

      <!-- Filtres et recherche -->
      <QuoteFilters
        v-model:search="searchQuery"
        v-model:status="filterStatus"
        :filtered-count="filteredQuotes.length"
        @export-excel="handleExportExcel"
        @export-pdf="handleExportPDF"
      >
        <template #extra-actions>
          <Button
            v-if="selectedQuotes.length > 0"
            variant="primary"
            size="md"
            @click="showBulkModal = true"
          >
            <template #icon-left>
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
              </svg>
            </template>
            Actions ({{ selectedQuotes.length }})
          </Button>

          <Button
            v-if="selectedQuotes.length > 0"
            variant="secondary"
            size="md"
            @click="clearSelection"
          >
            <template #icon-left>
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </template>
            Désélectionner
          </Button>
        </template>
      </QuoteFilters>

      <!-- Chargement -->
      <LoadingSpinner
        v-if="loading"
        message="Chargement des devis..."
      />

      <!-- Table des devis -->
      <QuoteTable
        v-else-if="filteredQuotes.length > 0"
        :quotes="paginatedQuotes"
        :selected-quotes="selectedQuotes"
        :is-all-selected="isAllSelected"
        :sending="sending"
        :downloading="downloading"
        :current-page="currentPage"
        :total-pages="totalPages"
        :start-index="startIndex"
        :end-index="endIndex"
        :total="filteredQuotes.length"
        @toggle-selection="toggleQuoteSelection"
        @toggle-select-all="toggleSelectAll"
        @edit="openEditModal"
        @send="handleSendQuote"
        @download="handleDownloadPDF"
        @previous-page="previousPage"
        @next-page="nextPage"
      />

      <!-- Liste vide -->
      <EmptyState
        v-else
        title="Aucun devis trouvé"
        message="Aucun devis ne correspond à vos critères de recherche."
        icon="document"
      />
    </div>

    <!-- Modale d'édition -->
    <QuoteEditModal
      :show="showEditModal"
      :quote="editingQuote"
      :saving="savingQuote"
      @close="closeEditModal"
      @save="handleSaveQuote"
    />

    <!-- Modale d'actions groupées -->
    <QuoteBulkActionsModal
      :show="showBulkModal"
      :selected-quotes="selectedQuotes"
      :quotes="quotes"
      :processing="bulkProcessing"
      @close="showBulkModal = false"
      @send-all="handleBulkSend"
      @export-excel="handleBulkExportExcel"
      @export-pdf="handleBulkExportPDF"
      @delete-all="handleBulkDelete"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { LoadingSpinner, EmptyState, Button } from '@/components/ui'
import QuoteCharts from '@/components/QuoteCharts.vue'
import QuoteStats from './admin/components/QuoteStats.vue'
import QuoteFilters from './admin/components/QuoteFilters.vue'
import QuoteTable from './admin/components/QuoteTable.vue'
import QuoteEditModal from './admin/components/QuoteEditModal.vue'
import QuoteBulkActionsModal from './admin/components/QuoteBulkActionsModal.vue'
import { useQuoteAdmin } from './admin/composables/useQuoteAdmin'
import { useQuoteFilters } from './admin/composables/useQuoteFilters'
import { useQuoteSelection } from './admin/composables/useQuoteSelection'
import { useQuoteExport } from './admin/composables/useQuoteExport'

// Composables
const {
  quotes,
  statistics,
  loading,
  sending,
  downloading,
  loadData,
  sendQuote,
  downloadPDF,
  saveQuote: saveQuoteAPI,
  bulkDeleteQuotes
} = useQuoteAdmin()

const {
  searchQuery,
  filterStatus,
  filteredQuotes,
  paginatedQuotes,
  currentPage,
  totalPages,
  startIndex,
  endIndex,
  nextPage,
  previousPage
} = useQuoteFilters(quotes)

const {
  selectedQuotes,
  isAllSelected,
  toggleQuoteSelection,
  toggleSelectAll,
  clearSelection
} = useQuoteSelection(paginatedQuotes)

const {
  handleExportExcel: exportExcel,
  handleExportPDF: exportPDF
} = useQuoteExport() || {}

// Modal states
const showEditModal = ref(false)
const editingQuote = ref(null)
const savingQuote = ref(false)
const showBulkModal = ref(false)
const bulkProcessing = ref(false)

// Open edit modal
const openEditModal = (quote) => {
  editingQuote.value = quote
  showEditModal.value = true
}

// Close edit modal
const closeEditModal = () => {
  showEditModal.value = false
  editingQuote.value = null
  savingQuote.value = false
}

// Save quote
const handleSaveQuote = async (formData) => {
  savingQuote.value = true
  const success = await saveQuoteAPI(editingQuote.value.id, formData)
  savingQuote.value = false

  if (success) {
    closeEditModal()
    await loadData()
  }
}

// Send quote
const handleSendQuote = async (quoteId) => {
  await sendQuote(quoteId)
  await loadData()
}

// Download PDF
const handleDownloadPDF = async (quoteId, quoteNumber) => {
  await downloadPDF(quoteId, quoteNumber)
}

// Export handlers
const handleExportExcel = () => {
  const quotesToExport = selectedQuotes.value.length > 0
    ? quotes.value.filter(q => selectedQuotes.value.includes(q.id))
    : filteredQuotes.value

  exportExcel(quotesToExport, 'devis_admin')
  clearSelection()
}

const handleExportPDF = () => {
  const quotesToExport = selectedQuotes.value.length > 0
    ? quotes.value.filter(q => selectedQuotes.value.includes(q.id))
    : filteredQuotes.value

  exportPDF(quotesToExport, 'rapport_devis_admin')
  clearSelection()
}

// Bulk actions
const handleBulkSend = async () => {
  bulkProcessing.value = true
  const selectedItems = quotes.value.filter(q => selectedQuotes.value.includes(q.id))
  const sendableQuotes = selectedItems.filter(q =>
    ['draft', 'viewed', 'rejected'].includes(q.status)
  )

  for (const quote of sendableQuotes) {
    await sendQuote(quote.id)
  }

  bulkProcessing.value = false
  showBulkModal.value = false
  clearSelection()
  await loadData()
}

const handleBulkExportExcel = () => {
  const quotesToExport = quotes.value.filter(q => selectedQuotes.value.includes(q.id))
  exportExcel(quotesToExport, 'devis_selected')
  showBulkModal.value = false
  clearSelection()
}

const handleBulkExportPDF = () => {
  const quotesToExport = quotes.value.filter(q => selectedQuotes.value.includes(q.id))
  exportPDF(quotesToExport, 'rapport_devis_selected')
  showBulkModal.value = false
  clearSelection()
}

const handleBulkDelete = async () => {
  if (!confirm('Êtes-vous sûr de vouloir supprimer ces devis ? Cette action est irréversible.')) {
    return
  }

  bulkProcessing.value = true
  await bulkDeleteQuotes(selectedQuotes.value)
  bulkProcessing.value = false
  showBulkModal.value = false
  clearSelection()
}

// Load data on mount
loadData()
</script>
