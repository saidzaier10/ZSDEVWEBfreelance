"""
Constants pour l'application quotes
Centralise toutes les constantes pour éviter la duplication
"""

# Statuts des devis
class QuoteStatus:
    """Statuts possibles d'un devis"""
    DRAFT = 'draft'
    SENT = 'sent'
    VIEWED = 'viewed'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    EXPIRED = 'expired'

    CHOICES = [
        (DRAFT, 'Brouillon'),
        (SENT, 'Envoyé'),
        (VIEWED, 'Consulté'),
        (ACCEPTED, 'Accepté'),
        (REJECTED, 'Refusé'),
        (EXPIRED, 'Expiré'),
    ]

    # Statuts qui permettent la signature
    SIGNABLE_STATUSES = [SENT, VIEWED]

    # Statuts qui permettent l'édition
    EDITABLE_STATUSES = [DRAFT]

    # Statuts qui permettent le renvoi
    RESENDABLE_STATUSES = [DRAFT, SENT, VIEWED, REJECTED]

    # Statuts qui peuvent expirer
    EXPIRABLE_STATUSES = [DRAFT, SENT, VIEWED]


# Types de facturation pour les options supplémentaires
class BillingType:
    """Types de facturation"""
    ONE_TIME = 'one_time'
    MONTHLY = 'monthly'
    YEARLY = 'yearly'

    CHOICES = [
        (ONE_TIME, 'Paiement unique'),
        (MONTHLY, 'Mensuel'),
        (YEARLY, 'Annuel'),
    ]


# Types de remise
class DiscountType:
    """Types de remise applicables"""
    PERCENT = 'percent'
    FIXED = 'fixed'

    CHOICES = [
        (PERCENT, 'Pourcentage'),
        (FIXED, 'Montant fixe'),
    ]


# Types d'emails
class EmailType:
    """Types d'emails envoyés"""
    CREATED = 'created'
    REMINDER = 'reminder'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'

    CHOICES = [
        (CREATED, 'Création du devis'),
        (REMINDER, 'Rappel'),
        (ACCEPTED, 'Acceptation'),
        (REJECTED, 'Refus'),
    ]


# Configuration des paiements
class PaymentConfig:
    """Configuration de la répartition des paiements"""
    FIRST_PAYMENT_PERCENT = 0.30  # 30%
    SECOND_PAYMENT_PERCENT = 0.40  # 40%
    FINAL_PAYMENT_PERCENT = 0.30  # 30%


# Configuration des devis
class QuoteConfig:
    """Configuration générale des devis"""
    DEFAULT_TVA_RATE = 20.00  # 20%
    DEFAULT_EXPIRATION_DAYS = 30  # 30 jours
    QUOTE_NUMBER_PREFIX = 'DEVIS'
    SIGNATURE_TOKEN_LENGTH = 64

    # Cache durée pour les options
    OPTIONS_CACHE_DURATION = 60 * 30  # 30 minutes


# Extensions de fichiers autorisées
class FileExtensions:
    """Extensions de fichiers autorisées"""
    SIGNATURE_ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}
    SIGNATURE_DEFAULT = 'png'


# Messages d'erreur standardisés
class ErrorMessages:
    """Messages d'erreur centralisés"""
    QUOTE_ALREADY_SIGNED = 'Ce devis a déjà été signé'
    QUOTE_EXPIRED = 'Ce devis a expiré'
    QUOTE_ACCEPTED_CANNOT_REJECT = 'Un devis accepté ne peut pas être rejeté'
    SIGNATURE_DATA_INCOMPLETE = 'Données de signature incomplètes'
    SIGNATURE_INVALID = 'Signature invalide'
    SIGNATURE_NAME_REQUIRED = 'Le nom du signataire est requis'
    TERMS_NOT_ACCEPTED = 'Les conditions doivent être acceptées'
    PDF_GENERATION_ERROR = 'Erreur lors de la génération du PDF'
    EMAIL_SEND_ERROR = 'Erreur lors de l\'envoi de l\'email'
    INVALID_DISCOUNT_VALUE = 'La valeur de la remise est invalide'
    DISCOUNT_EXCEEDS_TOTAL = 'La remise ne peut pas dépasser le montant total'


# Messages de succès standardisés
class SuccessMessages:
    """Messages de succès centralisés"""
    QUOTE_CREATED = 'Devis créé avec succès'
    QUOTE_SIGNED = 'Devis signé avec succès'
    QUOTE_REJECTED = 'Devis rejeté'
    QUOTE_SENT = 'Email envoyé avec succès'
    PDF_GENERATED = 'PDF généré avec succès'
    QUOTE_DUPLICATED = 'Devis dupliqué avec succès'


# Limites de validation
class ValidationLimits:
    """Limites pour la validation"""
    MIN_DISCOUNT_PERCENT = 0
    MAX_DISCOUNT_PERCENT = 100
    MIN_TVA_RATE = 0
    MAX_TVA_RATE = 100
    MIN_PRICE = 0
    MAX_PRICE = 999999.99
