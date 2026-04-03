/**
 * Constantes de l'application
 * Centralise toutes les constantes pour éviter la duplication et les erreurs de frappe
 */

/**
 * Labels des catégories de projets portfolio
 */
export const PORTFOLIO_CATEGORY_LABELS = {
  'web': 'Site Web',
  'ecommerce': 'E-commerce',
  'mobile': 'Application Mobile',
  'api': 'API / Backend',
  'other': 'Autre'
}

/**
 * Statuts des devis
 */
export const QUOTE_STATUSES = {
  DRAFT: 'draft',
  SENT: 'sent',
  VIEWED: 'viewed',
  ACCEPTED: 'accepted',
  REJECTED: 'rejected',
  EXPIRED: 'expired'
}

/**
 * Labels français des statuts de devis
 */
export const QUOTE_STATUS_LABELS = {
  [QUOTE_STATUSES.DRAFT]: 'Brouillon',
  [QUOTE_STATUSES.SENT]: 'Envoyé',
  [QUOTE_STATUSES.VIEWED]: 'Consulté',
  [QUOTE_STATUSES.ACCEPTED]: 'Accepté',
  [QUOTE_STATUSES.REJECTED]: 'Refusé',
  [QUOTE_STATUSES.EXPIRED]: 'Expiré'
}

/**
 * Classes CSS pour les badges de statut
 * Utilise Tailwind CSS
 */
export const QUOTE_STATUS_CLASSES = {
  [QUOTE_STATUSES.DRAFT]: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  [QUOTE_STATUSES.SENT]: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
  [QUOTE_STATUSES.VIEWED]: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-400',
  [QUOTE_STATUSES.ACCEPTED]: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
  [QUOTE_STATUSES.REJECTED]: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
  [QUOTE_STATUSES.EXPIRED]: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
}

/**
 * Couleurs des icônes par statut
 */
export const QUOTE_STATUS_COLORS = {
  [QUOTE_STATUSES.DRAFT]: 'text-gray-600',
  [QUOTE_STATUSES.SENT]: 'text-blue-500',
  [QUOTE_STATUSES.VIEWED]: 'text-indigo-500',
  [QUOTE_STATUSES.ACCEPTED]: 'text-green-500',
  [QUOTE_STATUSES.REJECTED]: 'text-red-500',
  [QUOTE_STATUSES.EXPIRED]: 'text-gray-500'
}

/**
 * Types de remise
 */
export const DISCOUNT_TYPES = {
  NONE: '',
  PERCENT: 'percent',
  FIXED: 'fixed'
}

/**
 * Labels des types de remise
 */
export const DISCOUNT_TYPE_LABELS = {
  [DISCOUNT_TYPES.NONE]: 'Aucune remise',
  [DISCOUNT_TYPES.PERCENT]: 'Pourcentage (%)',
  [DISCOUNT_TYPES.FIXED]: 'Montant fixe (€)'
}

/**
 * Classes CSS communes pour les cartes
 */
export const CARD_CLASSES = {
  base: 'bg-white dark:bg-dark-800 rounded-xl shadow-sm border border-gray-200 dark:border-dark-700',
  padding: {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  }
}

/**
 * Classes CSS communes pour les boutons
 */
export const BUTTON_CLASSES = {
  base: 'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors duration-200',
  sizes: {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  },
  variants: {
    primary: 'bg-primary-600 hover:bg-primary-700 text-white',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-800 dark:bg-dark-700 dark:hover:bg-dark-600 dark:text-white',
    success: 'bg-green-600 hover:bg-green-700 text-white',
    danger: 'bg-red-600 hover:bg-red-700 text-white',
    warning: 'bg-yellow-600 hover:bg-yellow-700 text-white',
    info: 'bg-blue-600 hover:bg-blue-700 text-white',
    outline: 'border-2 border-primary-600 text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20'
  }
}

/**
 * Classes CSS pour les inputs
 */
export const INPUT_CLASSES = {
  base: 'w-full px-3 py-2 rounded-lg border bg-white dark:bg-dark-700 text-dark-800 dark:text-dark-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors',
  states: {
    default: 'border-gray-300 dark:border-dark-600',
    error: 'border-red-500 dark:border-red-500',
    success: 'border-green-500 dark:border-green-500',
    disabled: 'opacity-50 cursor-not-allowed'
  }
}

/**
 * Types de toast/notification
 */
export const TOAST_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
}

/**
 * Durées par défaut des toasts (en ms)
 */
export const TOAST_DURATIONS = {
  [TOAST_TYPES.SUCCESS]: 5000,
  [TOAST_TYPES.ERROR]: 7000,
  [TOAST_TYPES.WARNING]: 6000,
  [TOAST_TYPES.INFO]: 5000
}

/**
 * Configuration de pagination
 */
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100]
}

/**
 * Taux de TVA par défaut
 */
export const DEFAULT_TAX_RATE = 0.20 // 20%

/**
 * Formats d'export disponibles
 */
export const EXPORT_FORMATS = {
  EXCEL: 'excel',
  PDF: 'pdf',
  CSV: 'csv'
}

/**
 * Messages d'erreur communs
 */
export const ERROR_MESSAGES = {
  REQUIRED_FIELD: 'Ce champ est requis',
  INVALID_EMAIL: 'Email invalide',
  INVALID_PHONE: 'Numéro de téléphone invalide',
  MIN_LENGTH: (min) => `Minimum ${min} caractères requis`,
  MAX_LENGTH: (max) => `Maximum ${max} caractères autorisés`,
  NETWORK_ERROR: 'Erreur de connexion au serveur',
  UNAUTHORIZED: 'Vous n\'êtes pas autorisé à effectuer cette action',
  NOT_FOUND: 'Ressource non trouvée',
  SERVER_ERROR: 'Erreur serveur, veuillez réessayer',
  GENERIC_ERROR: 'Une erreur est survenue'
}

/**
 * Messages de succès communs
 */
export const SUCCESS_MESSAGES = {
  SAVED: 'Enregistré avec succès',
  UPDATED: 'Mis à jour avec succès',
  DELETED: 'Supprimé avec succès',
  SENT: 'Envoyé avec succès',
  CREATED: 'Créé avec succès'
}

/**
 * Regex pour la validation
 */
export const VALIDATION_REGEX = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE_FR: /^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$/,
  PASSWORD: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/ // Min 8 chars, 1 maj, 1 min, 1 chiffre
}

/**
 * Breakpoints responsive (correspond à Tailwind)
 */
export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
}
