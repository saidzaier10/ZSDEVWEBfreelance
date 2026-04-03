"""
Serializers pour l'API Quotes Premium
"""
from rest_framework import serializers
from django.utils import timezone
from .models import (
    Company,
    ProjectCategory,
    ProjectType,
    DesignOption,
    ComplexityLevel,
    SupplementaryOption,
    QuoteTemplate,
    Quote,
    QuoteEmailLog
)


class CompanySerializer(serializers.ModelSerializer):
    """Serializer pour les informations de l'entreprise"""

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'logo', 'email', 'phone', 'address',
            'siret', 'tva_number', 'primary_color', 'footer_text',
            'email_signature', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectCategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories de projets"""

    project_types_count = serializers.SerializerMethodField()
    compatible_options_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color', 'order',
            'is_active', 'project_types_count', 'compatible_options_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_project_types_count(self, obj):
        """Compte le nombre de types de projets dans cette catégorie"""
        return obj.project_types.filter(is_active=True).count()

    def get_compatible_options_count(self, obj):
        """Compte les options spécifiques à cette catégorie"""
        return obj.compatible_options.filter(is_active=True).count()


class ProjectTypeSerializer(serializers.ModelSerializer):
    """Serializer pour les types de projets"""

    category_detail = ProjectCategorySerializer(source='category', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    class Meta:
        model = ProjectType
        fields = [
            'id', 'category', 'category_detail', 'category_name',
            'name', 'description', 'base_price', 'estimated_days',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DesignOptionSerializer(serializers.ModelSerializer):
    """Serializer pour les options de design"""

    class Meta:
        model = DesignOption
        fields = ['id', 'name', 'description', 'price_supplement', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplexityLevelSerializer(serializers.ModelSerializer):
    """Serializer pour les niveaux de complexité"""

    class Meta:
        model = ComplexityLevel
        fields = ['id', 'name', 'description', 'price_multiplier', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SupplementaryOptionSerializer(serializers.ModelSerializer):
    """Serializer pour les options supplémentaires"""

    billing_type_display = serializers.CharField(source='get_billing_type_display', read_only=True)
    compatible_categories_detail = ProjectCategorySerializer(
        source='compatible_categories',
        many=True,
        read_only=True
    )
    is_universal = serializers.SerializerMethodField()

    class Meta:
        model = SupplementaryOption
        fields = [
            'id', 'name', 'description', 'price', 'billing_type', 'billing_type_display',
            'compatible_categories', 'compatible_categories_detail', 'is_universal',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_universal(self, obj):
        """Indique si l'option est disponible pour toutes les catégories"""
        return not obj.compatible_categories.exists()


class QuoteTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les templates de devis"""
    
    project_type_detail = ProjectTypeSerializer(source='project_type', read_only=True)
    design_option_detail = DesignOptionSerializer(source='design_option', read_only=True)
    complexity_level_detail = ComplexityLevelSerializer(source='complexity_level', read_only=True)
    supplementary_options_detail = SupplementaryOptionSerializer(source='supplementary_options', many=True, read_only=True)
    
    class Meta:
        model = QuoteTemplate
        fields = [
            'id', 'name', 'description',
            'project_type', 'project_type_detail',
            'design_option', 'design_option_detail',
            'complexity_level', 'complexity_level_detail',
            'supplementary_options', 'supplementary_options_detail',
            'default_description', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class QuoteListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des devis"""

    # Relations en objets complets pour le frontend
    project_type = ProjectTypeSerializer(read_only=True)
    design_option = DesignOptionSerializer(read_only=True)
    complexity_level = ComplexityLevelSerializer(read_only=True)
    supplementary_options = SupplementaryOptionSerializer(many=True, read_only=True)

    # Informations sur l'utilisateur créateur (pour les admins)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True, allow_null=True)
    created_by_id = serializers.IntegerField(source='created_by.id', read_only=True, allow_null=True)

    # Champs calculés
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_type_name = serializers.CharField(source='project_type.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    total_price = serializers.DecimalField(source='total_ttc', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'client_name', 'client_email', 'client_phone',
            'company_name', 'project_type', 'project_type_name',
            'design_option', 'complexity_level', 'supplementary_options',
            'project_description',  # Description du projet (nécessaire pour l'édition)
            'status', 'status_display', 'total_ttc', 'total_price',
            'is_expired', 'created_at', 'expires_at', 'signature_token',
            'pdf_file',  # Ajout du fichier PDF pour téléchargement
            'created_by_username', 'created_by_email', 'created_by_id',  # Info utilisateur
            'discount_type', 'discount_value', 'discount_reason', 'discount_amount',  # Remises
            'sent_at', 'viewed_at', 'signed_at', 'signer_name'  # Timeline
        ]


class QuoteDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour un devis"""
    
    # Relations en détail
    project_type_detail = ProjectTypeSerializer(source='project_type', read_only=True)
    design_option_detail = DesignOptionSerializer(source='design_option', read_only=True)
    complexity_level_detail = ComplexityLevelSerializer(source='complexity_level', read_only=True)
    supplementary_options_detail = SupplementaryOptionSerializer(source='supplementary_options', many=True, read_only=True)
    
    # Champs calculés
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    discount_type_display = serializers.CharField(source='get_discount_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    signature_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Quote
        fields = [
            # Identifiants
            'id', 'quote_number',
            
            # Client
            'client_name', 'client_email', 'client_phone',
            'company_name', 'client_address',
            
            # Configuration
            'project_type', 'project_type_detail',
            'design_option', 'design_option_detail',
            'complexity_level', 'complexity_level_detail',
            'supplementary_options', 'supplementary_options_detail',
            'template',
            
            # Détails projet
            'project_description', 'deadline',
            
            # Financier
            'subtotal_ht', 'discount_type', 'discount_type_display',
            'discount_value', 'discount_reason', 'discount_amount',
            'tva_rate', 'tva_amount', 'total_ttc',
            
            # Paiements
            'payment_first', 'payment_second', 'payment_final',
            
            # Planning
            'estimated_duration_days', 'estimated_start_date', 'estimated_end_date',
            
            # PDF
            'pdf_file',
            
            # Signature
            'signature_token', 'signature_url', 'signature_image',
            'signed_at', 'signer_name', 'client_ip',
            
            # Statut
            'status', 'status_display', 'expires_at', 'is_expired',
            
            # Notes internes (visible uniquement par staff)
            'internal_notes', 'assigned_to',
            
            # Dates
            'created_at', 'updated_at', 'sent_at', 'viewed_at',
            'accepted_at', 'rejected_at'
        ]
        read_only_fields = [
            'id', 'quote_number', 'subtotal_ht', 'discount_amount',
            'tva_amount', 'total_ttc', 'payment_first', 'payment_second',
            'payment_final', 'estimated_duration_days', 'signature_token',
            'signature_url', 'is_expired', 'created_at', 'updated_at'
        ]
    
    def to_representation(self, instance):
        """Masquer les notes internes pour les non-staff"""
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Si l'utilisateur n'est pas staff, masquer les notes internes
        if request and not (request.user and request.user.is_staff):
            data.pop('internal_notes', None)
            data.pop('assigned_to', None)
        
        return data


class QuoteCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de devis"""

    class Meta:
        model = Quote
        fields = [
            'client_name', 'client_email', 'client_phone',
            'company_name', 'client_address',
            'project_type', 'design_option', 'complexity_level',
            'supplementary_options', 'template',
            'project_description', 'deadline',
            'discount_type', 'discount_value', 'discount_reason',
            'tva_rate', 'estimated_start_date'
        ]

    def validate_client_email(self, value):
        """Validation de l'email"""
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Format d'email invalide")
        return value.lower()

    def validate_discount_value(self, value):
        """Validation de la remise"""
        if value < 0:
            raise serializers.ValidationError("La remise ne peut pas être négative")
        if value > 100 and self.initial_data.get('discount_type') == 'percent':
            raise serializers.ValidationError("La remise ne peut pas dépasser 100%")
        return value

    def create(self, validated_data):
        """Créer le devis et recalculer les prix avec les options supplémentaires"""
        # Extraire les options supplémentaires (relation M2M)
        supplementary_options = validated_data.pop('supplementary_options', [])

        # AJOUT : Récupérer l'utilisateur connecté depuis le contexte
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user

        # Créer l'instance (sans les options supplémentaires pour l'instant)
        quote = Quote.objects.create(**validated_data)


        # Ajouter les options supplémentaires
        if supplementary_options:
            quote.supplementary_options.set(supplementary_options)

            # Recalculer les prix avec les options supplémentaires
            prices = quote.calculate_prices(skip_m2m=False)
            quote.subtotal_ht = prices['subtotal_ht']
            quote.discount_amount = prices['discount_amount']
            quote.tva_amount = prices['tva_amount']
            quote.total_ttc = prices['total_ttc']
            quote.payment_first = prices['payment_first']
            quote.payment_second = prices['payment_second']
            quote.payment_final = prices['payment_final']
            quote.estimated_duration_days = prices['estimated_duration_days']

            # Sauvegarder avec les nouveaux prix
            quote.save(update_fields=[
                'subtotal_ht', 'discount_amount', 'tva_amount', 'total_ttc',
                'payment_first', 'payment_second', 'payment_final', 'estimated_duration_days'
            ])

        return quote


class QuoteEmailLogSerializer(serializers.ModelSerializer):
    """Serializer pour les logs d'emails"""
    
    email_type_display = serializers.CharField(source='get_email_type_display', read_only=True)
    
    class Meta:
        model = QuoteEmailLog
        fields = '__all__'
        read_only_fields = ['id', 'sent_at']


class QuoteStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des devis"""
    
    total_quotes = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    status_breakdown = serializers.DictField()
    conversion_rate = serializers.FloatField()
    
    quotes_by_month = serializers.ListField()
    top_project_types = serializers.ListField()