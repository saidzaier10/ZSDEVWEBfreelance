from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import secrets
import string
from .utils.constants import QuoteStatus, BillingType, PaymentConfig, QuoteConfig

User = get_user_model()


class Company(models.Model):
    """Informations de l'entreprise (pour personnalisation des devis)"""
    name = models.CharField(max_length=200, default="Zsdevweb")
    logo = models.ImageField(upload_to='company/logos/', blank=True, null=True)
    email = models.EmailField(default="contact@zsdevweb.com")
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    siret = models.CharField(max_length=14, blank=True)
    tva_number = models.CharField(max_length=20, blank=True, verbose_name="Numéro TVA")
    
    # Personnalisation PDF
    primary_color = models.CharField(max_length=7, default="#1a56db", help_text="Couleur hexadécimale")
    footer_text = models.TextField(
        blank=True,
        default="Merci de votre confiance | www.zsdevweb.com"
    )
    
    # Configuration emails
    email_signature = models.TextField(
        blank=True,
        default="Cordialement,\nL'équipe Zsdevweb"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprise"
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_instance(cls):
        """Récupère ou crée l'instance unique"""
        instance, created = cls.objects.get_or_create(id=1)
        return instance


class ProjectCategory(models.Model):
    """Catégories principales de projets (Site Vitrine, E-commerce, Application Web)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    slug = models.SlugField(max_length=100, unique=True, help_text="Identifiant URL-friendly")
    description = models.TextField(help_text="Description de la catégorie")
    icon = models.CharField(max_length=50, blank=True, help_text="Classe CSS d'icône (ex: fas fa-globe)")
    color = models.CharField(max_length=7, default="#2563eb", help_text="Couleur hexadécimale")
    order = models.IntegerField(default=0, help_text="Ordre d'affichage")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Catégorie de projet"
        verbose_name_plural = "Catégories de projets"

    def __str__(self):
        return self.name


class ProjectType(models.Model):
    """Types de projets (Site vitrine, E-commerce, etc.)"""
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.CASCADE,
        related_name='project_types',
        verbose_name="Catégorie",
        null=True,  # Temporaire pour la migration
        blank=True
    )
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    estimated_days = models.IntegerField(default=10, help_text="Nombre de jours estimés")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Type de projet"
        verbose_name_plural = "Types de projets"

    def __str__(self):
        return self.name


class DesignOption(models.Model):
    """Options de design (Simple, Moderne, Premium)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price_supplement = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_supplement']
        verbose_name = "Option de design"
        verbose_name_plural = "Options de design"

    def __str__(self):
        return self.name


class ComplexityLevel(models.Model):
    """Niveaux de complexité (Basique, Intermédiaire, Avancé)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('1'))])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_multiplier']
        verbose_name = "Niveau de complexité"
        verbose_name_plural = "Niveaux de complexité"

    def __str__(self):
        return self.name


class SupplementaryOption(models.Model):
    """Options supplémentaires (SEO, Maintenance, etc.)"""
    BILLING_TYPE_CHOICES = BillingType.CHOICES

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    billing_type = models.CharField(max_length=20, choices=BILLING_TYPE_CHOICES, default='one_time')

    # Filtrage intelligent par catégorie
    compatible_categories = models.ManyToManyField(
        ProjectCategory,
        related_name='compatible_options',
        blank=True,
        verbose_name="Catégories compatibles",
        help_text="Si vide, l'option est disponible pour toutes les catégories"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Option supplémentaire"
        verbose_name_plural = "Options supplémentaires"

    def __str__(self):
        return f"{self.name} ({self.get_billing_type_display()})"

    def is_compatible_with_category(self, category):
        """Vérifie si l'option est compatible avec une catégorie donnée"""
        if not self.compatible_categories.exists():
            return True  # Si aucune catégorie spécifiée, compatible avec toutes
        return self.compatible_categories.filter(id=category.id).exists()


class QuoteTemplate(models.Model):
    """Templates de devis réutilisables"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Nom du template")
    description = models.TextField(blank=True)
    
    # Configuration par défaut
    project_type = models.ForeignKey(ProjectType, on_delete=models.CASCADE)
    design_option = models.ForeignKey(DesignOption, on_delete=models.CASCADE)
    complexity_level = models.ForeignKey(ComplexityLevel, on_delete=models.CASCADE)
    supplementary_options = models.ManyToManyField(SupplementaryOption, blank=True)
    
    # Texte par défaut
    default_description = models.TextField(
        verbose_name="Description par défaut",
        help_text="Texte prérempli pour ce type de projet"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Template de devis"
        verbose_name_plural = "Templates de devis"
    
    def __str__(self):
        return self.name


class Quote(models.Model):
    """Devis créés par les utilisateurs"""
    STATUS_CHOICES = QuoteStatus.CHOICES

    # Informations client
    client_name = models.CharField(max_length=200, verbose_name="Nom du client")
    client_email = models.EmailField(verbose_name="Email du client")
    client_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone")
    company_name = models.CharField(max_length=200, blank=True, verbose_name="Nom de l'entreprise")
    client_address = models.TextField(blank=True, verbose_name="Adresse")

    # Configuration du projet
    project_type = models.ForeignKey(ProjectType, on_delete=models.PROTECT, verbose_name="Type de projet")
    design_option = models.ForeignKey(DesignOption, on_delete=models.PROTECT, verbose_name="Option de design")
    complexity_level = models.ForeignKey(ComplexityLevel, on_delete=models.PROTECT, verbose_name="Niveau de complexité")
    supplementary_options = models.ManyToManyField(SupplementaryOption, blank=True, verbose_name="Options supplémentaires")

    # Template utilisé (optionnel)
    template = models.ForeignKey(
        QuoteTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Créé depuis le template"
    )

    # Détails du projet
    project_description = models.TextField(verbose_name="Description du projet")
    deadline = models.DateField(null=True, blank=True, verbose_name="Date limite souhaitée")

    # Calculs financiers
    subtotal_ht = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Sous-total HT",
        default=0
    )
    
    # Système de remise
    discount_type = models.CharField(
        max_length=10,
        choices=[('percent', 'Pourcentage'), ('fixed', 'Montant fixe')],
        blank=True,
        verbose_name="Type de remise"
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Valeur de la remise"
    )
    discount_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Raison de la remise",
        help_text="Ex: Client fidèle, Promotion, etc."
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Montant de la remise"
    )
    
    tva_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('20.00'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name="Taux TVA (%)"
    )
    tva_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Montant TVA",
        default=0
    )
    total_ttc = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total TTC",
        default=0
    )

    # Conditions de paiement
    payment_first = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="1er paiement (30%)",
        default=0
    )
    payment_second = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="2ème paiement (40%)",
        default=0
    )
    payment_final = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Paiement final (30%)",
        default=0
    )

    # Durée estimée
    estimated_duration_days = models.IntegerField(
        default=0,
        verbose_name="Durée estimée (jours)"
    )
    estimated_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de début estimée"
    )
    estimated_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de fin estimée"
    )
    
    # PDF du devis
    pdf_file = models.FileField(
        upload_to='quotes/pdf/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Fichier PDF"
    )
    
    # Signature électronique
    signature_token = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="Token de signature"
    )
    signature_image = models.ImageField(
        upload_to='quotes/signatures/',
        blank=True,
        null=True,
        verbose_name="Image de la signature"
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Signé le"
    )
    signer_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nom du signataire")

    client_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP du client"
    )
    
    # Statut et suivi
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Statut")
    quote_number = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Numéro de devis")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="Expire le")
    
    # Notes internes (invisible au client)
    internal_notes = models.TextField(
        blank=True,
        verbose_name="Notes internes",
        help_text="Visible uniquement par les admins"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_quotes',
        verbose_name="Assigné à"
    )

    # Utilisateur qui a créé le devis
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_quotes',
        verbose_name="Créé par"
    )
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Envoyé le")
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Consulté le")
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Accepté le")
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name="Refusé le")
    rejection_reason = models.TextField(blank=True, verbose_name="Raison du refus")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['created_by', '-created_at']),
            models.Index(fields=['signature_token']),
            models.Index(fields=['quote_number']),
        ]
        verbose_name = "Devis"
        verbose_name_plural = "Devis"

    def __str__(self):
        return f"Devis #{self.quote_number or self.id} - {self.client_name}"
    
    def calculate_prices(self, skip_m2m=False):
        """
        Calcule tous les prix du devis avec remise et génère la répartition des paiements.

        Cette méthode est le cœur du calcul tarifaire. Elle agrège tous les composants
        du devis (type de projet, design, complexité, options) et applique la remise
        puis la TVA pour obtenir le prix final TTC.

        Étapes du calcul :
        1. Prix de base du type de projet
        2. Ajout du supplément de design
        3. Application du multiplicateur de complexité
        4. Ajout des options supplémentaires (one_time uniquement)
        5. Application de la remise (pourcentage ou montant fixe)
        6. Calcul de la TVA
        7. Obtention du total TTC
        8. Répartition en 3 paiements (30% / 40% / 30%)

        Args:
            skip_m2m: Si True, ignore les relations ManyToMany (utilisé lors de la création
                     initiale du devis avant qu'il ait un ID en base)

        Returns:
            dict: Dictionnaire contenant tous les montants calculés
        """
        # 1. Prix de base du type de projet
        subtotal = Decimal('0.00')

        if self.project_type:
            subtotal = self.project_type.base_price

        # 2. Option de design
        if self.design_option:
            subtotal += self.design_option.price_supplement

        # 3. Multiplicateur de complexité
        if self.complexity_level:
            subtotal *= self.complexity_level.price_multiplier

        # 4. Options supplémentaires (paiement unique uniquement)
        # Ne pas accéder aux M2M si l'objet n'a pas encore d'ID
        if not skip_m2m and self.pk:
            for option in self.supplementary_options.filter(billing_type='one_time'):
                subtotal += option.price

        # 5. Calcul de la remise
        discount_amount = Decimal('0.00')
        if self.discount_value > 0:
            if self.discount_type == 'percent':
                discount_amount = subtotal * (self.discount_value / Decimal('100'))
            elif self.discount_type == 'fixed':
                discount_amount = self.discount_value

        # 6. Sous-total après remise
        subtotal_after_discount = subtotal - discount_amount

        # 7. TVA
        tva_amount = subtotal_after_discount * (self.tva_rate / Decimal('100'))

        # 8. Total TTC
        total_ttc = subtotal_after_discount + tva_amount

        # 9. Répartition des paiements
        payment_first = total_ttc * Decimal(str(PaymentConfig.FIRST_PAYMENT_PERCENT))
        payment_second = total_ttc * Decimal(str(PaymentConfig.SECOND_PAYMENT_PERCENT))
        payment_final = total_ttc * Decimal(str(PaymentConfig.FINAL_PAYMENT_PERCENT))

        # 10. Durée estimée
        estimated_days = self.project_type.estimated_days if self.project_type else 10
        if self.complexity_level:
            estimated_days = int(estimated_days * float(self.complexity_level.price_multiplier))

        return {
            'subtotal_ht': round(subtotal, 2),
            'discount_amount': round(discount_amount, 2),
            'subtotal_after_discount': round(subtotal_after_discount, 2),
            'tva_amount': round(tva_amount, 2),
            'total_ttc': round(total_ttc, 2),
            'payment_first': round(payment_first, 2),
            'payment_second': round(payment_second, 2),
            'payment_final': round(payment_final, 2),
            'estimated_duration_days': estimated_days,
        }
    
    def generate_quote_number(self):
        """
        Génère un numéro de devis unique au format : DEVIS-YYYYMM-XXX

        Format :
        - DEVIS : préfixe fixe
        - YYYYMM : année et mois (ex: 202511 pour novembre 2025)
        - XXX : numéro séquentiel sur 3 chiffres (001, 002, 003, etc.)

        Exemple : DEVIS-202511-042 (42ème devis de novembre 2025)

        La numérotation recommence à 001 chaque mois.
        """
        if not self.quote_number:
            date_part = timezone.now().strftime('%Y%m')
            # Compte les devis existants pour ce mois et incrémente
            count = Quote.objects.filter(
                quote_number__startswith=f'DEVIS-{date_part}'
            ).count() + 1
            self.quote_number = f'DEVIS-{date_part}-{count:03d}'
    
    def generate_signature_token(self):
        """
        Génère un token unique sécurisé pour la signature électronique.

        Le token fait 64 caractères alphanumériques et est généré avec le module
        secrets (cryptographiquement sécurisé) pour éviter toute prédiction.

        Ce token est utilisé dans l'URL de signature : /devis/sign/{token}/
        Il permet d'identifier de manière unique et sécurisée un devis sans authentification.
        """
        if not self.signature_token:
            alphabet = string.ascii_letters + string.digits
            self.signature_token = ''.join(secrets.choice(alphabet) for _ in range(64))
    
    def calculate_expiration_date(self):
        """Calcule la date d'expiration selon QuoteConfig.DEFAULT_EXPIRATION_DAYS"""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=QuoteConfig.DEFAULT_EXPIRATION_DAYS)
    
    def check_if_expired(self):
        """Vérifie et marque le devis comme expiré si nécessaire"""
        if self.expires_at and timezone.now() > self.expires_at and self.status in ['draft', 'sent', 'viewed']:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return True
        return False
    
    @property
    def is_expired(self):
        """Vérifie si le devis est expiré"""
        return self.expires_at and timezone.now() > self.expires_at
    
    @property
    def signature_url(self):
        """URL de signature électronique"""
        if self.signature_token:
            return f"/devis/sign/{self.signature_token}/"
        return None
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour automatiser les calculs et générations.

        Actions automatiques lors de la sauvegarde :
        1. Génération du numéro de devis si absent (format : DEVIS-YYYYMM-XXX)
        2. Génération du token de signature sécurisé (64 caractères)
        3. Calcul de la date d'expiration (30 jours après création)
        4. Calcul automatique de tous les prix (HT, remise, TVA, TTC)

        Note : Le calcul des prix ignore les relations ManyToMany lors de la première
        sauvegarde (création) car l'objet n'a pas encore d'ID en base.
        """
        # Vérifier si c'est une création (l'objet n'a pas encore d'ID en base)
        is_new = self.pk is None

        # Génération automatique du numéro de devis si absent
        if not self.quote_number:
            self.generate_quote_number()

        # Génération automatique du token de signature
        if not self.signature_token:
            self.generate_signature_token()

        # Calcul automatique de la date d'expiration (30 jours)
        if not self.expires_at:
            self.calculate_expiration_date()

        # Calcul des prix (skip M2M si création car pas encore d'ID)
        prices = self.calculate_prices(skip_m2m=is_new)
        self.subtotal_ht = prices['subtotal_ht']
        self.discount_amount = prices['discount_amount']
        self.tva_amount = prices['tva_amount']
        self.total_ttc = prices['total_ttc']
        self.payment_first = prices['payment_first']
        self.payment_second = prices['payment_second']
        self.payment_final = prices['payment_final']
        self.estimated_duration_days = prices['estimated_duration_days']

        # Calculer les dates estimées
        if self.estimated_start_date and not self.estimated_end_date:
            self.estimated_end_date = self.estimated_start_date + timedelta(days=self.estimated_duration_days)

        super().save(*args, **kwargs)

        # Si c'était une création et qu'il y a des options supplémentaires à ajouter,
        # recalculer les prix après que les M2M soient sauvegardées
        # Cela sera géré par le serializer/view


class QuoteEmailLog(models.Model):
    """Log des emails envoyés pour les devis"""
    EMAIL_TYPE_CHOICES = [
        ('created', 'Création du devis'),
        ('reminder', 'Rappel'),
        ('accepted', 'Acceptation'),
        ('rejected', 'Refus'),
    ]
    
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPE_CHOICES)
    recipient = models.EmailField()
    subject = models.CharField(max_length=200)
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Log d'email"
        verbose_name_plural = "Logs d'emails"
    
    def __str__(self):
        return f"{self.get_email_type_display()} - {self.recipient} - {self.sent_at.strftime('%d/%m/%Y')}"