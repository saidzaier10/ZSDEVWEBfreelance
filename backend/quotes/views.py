"""
API Views pour les devis - Version refactorisée avec services
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

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
from .serializers import (
    CompanySerializer,
    ProjectCategorySerializer,
    ProjectTypeSerializer,
    DesignOptionSerializer,
    ComplexityLevelSerializer,
    SupplementaryOptionSerializer,
    QuoteTemplateSerializer,
    QuoteListSerializer,
    QuoteDetailSerializer,
    QuoteCreateSerializer,
    QuoteEmailLogSerializer,
    QuoteStatisticsSerializer
)
from .services import QuoteService, PDFService
from .utils import QuoteStatus, handle_service_errors


class CompanyViewSet(viewsets.ModelViewSet):
    """API pour gérer les informations de l'entreprise"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        """Seuls les admins peuvent créer/modifier/supprimer"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]


@method_decorator(cache_page(60 * 30), name='dispatch')  # Cache 30 minutes
class ProjectCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour récupérer les catégories de projets - Cached 30min"""
    queryset = ProjectCategory.objects.filter(is_active=True)
    serializer_class = ProjectCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'  # Permet de récupérer par slug au lieu de id


@method_decorator(cache_page(60 * 30), name='dispatch')  # Cache 30 minutes
class ProjectTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour récupérer les types de projets - Cached 30min"""
    queryset = ProjectType.objects.filter(is_active=True)
    serializer_class = ProjectTypeSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Filtrer par catégorie si spécifié"""
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get('category', None)

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset.select_related('category')


@method_decorator(cache_page(60 * 30), name='dispatch')  # Cache 30 minutes
class DesignOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour récupérer les options de design - Cached 30min"""
    queryset = DesignOption.objects.filter(is_active=True)
    serializer_class = DesignOptionSerializer
    permission_classes = [permissions.AllowAny]


@method_decorator(cache_page(60 * 30), name='dispatch')  # Cache 30 minutes
class ComplexityLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour récupérer les niveaux de complexité - Cached 30min"""
    queryset = ComplexityLevel.objects.filter(is_active=True)
    serializer_class = ComplexityLevelSerializer
    permission_classes = [permissions.AllowAny]


@method_decorator(cache_page(60 * 30), name='dispatch')  # Cache 30 minutes
class SupplementaryOptionViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour récupérer les options supplémentaires - Cached 30min"""
    queryset = SupplementaryOption.objects.filter(is_active=True)
    serializer_class = SupplementaryOptionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """Filtrer par type de facturation et/ou catégorie"""
        queryset = super().get_queryset()

        # Filtrage par type de facturation
        billing_type = self.request.query_params.get('billing_type', None)
        if billing_type:
            queryset = queryset.filter(billing_type=billing_type)

        # Filtrage intelligent par catégorie
        category_slug = self.request.query_params.get('category', None)
        if category_slug:
            try:
                category = ProjectCategory.objects.get(slug=category_slug)

                # Récupère les options spécifiques à cette catégorie OU les options universelles
                from django.db.models import Q
                # Get IDs of options that have no categories (universal options)
                universal_option_ids = SupplementaryOption.objects.filter(
                    is_active=True
                ).exclude(
                    compatible_categories__isnull=False
                ).values_list('id', flat=True)

                # Filter for category-specific OR universal options
                queryset = queryset.filter(
                    Q(compatible_categories=category) |  # Options spécifiques
                    Q(id__in=universal_option_ids)  # Options universelles
                ).distinct()

            except ProjectCategory.DoesNotExist:
                pass

        return queryset.prefetch_related('compatible_categories')


class QuoteTemplateViewSet(viewsets.ModelViewSet):
    """API pour récupérer les templates de devis"""
    queryset = QuoteTemplate.objects.filter(is_active=True)
    serializer_class = QuoteTemplateSerializer
    
    def get_permissions(self):
        """Admins uniquement pour modification"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        """Admins voient tout, autres voient seulement actifs"""
        if self.request.user and self.request.user.is_staff:
            return QuoteTemplate.objects.all()
        return QuoteTemplate.objects.filter(is_active=True)


class QuoteViewSet(viewsets.ModelViewSet):
    """API pour gérer les devis"""
    queryset = Quote.objects.all().select_related(
        'project_type',
        'design_option',
        'complexity_level',
        'template'
    ).prefetch_related('supplementary_options')
    # pagination_class = None  # Pagination activée pour de meilleures performances
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action"""
        if self.action == 'list':
            return QuoteListSerializer
        elif self.action == 'create':
            return QuoteCreateSerializer
        return QuoteDetailSerializer
    
    def get_permissions(self):
        """Permissions par action"""
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['list', 'retrieve']:
            # Utilisateurs authentifiés peuvent voir leurs propres devis
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        """
        Admins voient tout, utilisateurs authentifiés voient leurs propres devis
        Les utilisateurs non-authentifiés ne voient rien (sauf via actions publiques)
        """
        queryset = super().get_queryset()

        # Admins voient tous les devis
        if self.request.user and self.request.user.is_staff:
            status_filter = self.request.query_params.get('status', None)
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            return queryset

        # Utilisateurs authentifiés voient leurs propres devis
        if self.request.user and self.request.user.is_authenticated:
            return queryset.filter(created_by=self.request.user)

        # Utilisateurs non-authentifiés ne voient rien (utiliser les actions publiques)
        return queryset.none()
    
    def create(self, request, *args, **kwargs):
        """Créer un devis avec génération PDF et envoi email"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quote = serializer.save()

        # Utiliser le service pour créer le devis complet (PDF + email)
        QuoteService.create_quote(quote)

        detail_serializer = QuoteDetailSerializer(quote, context={'request': request})

        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='my-quotes')
    def my_quotes(self, request):
        """Récupère les devis de l'utilisateur connecté

        - Pour les admins : retourne TOUS les devis de tous les utilisateurs
        - Pour les utilisateurs normaux : retourne uniquement leurs propres devis

        GET /api/quotes/my-quotes/
        GET /api/quotes/my-quotes/?status=sent
        GET /api/quotes/my-quotes/?user_id=5  (admin uniquement)
        """
        # Les admins voient tous les devis, les autres uniquement les leurs
        if request.user.is_staff:
            queryset = Quote.objects.all()

            # Filtrer par utilisateur spécifique si demandé (admin uniquement)
            user_id = request.query_params.get('user_id', None)
            if user_id:
                queryset = queryset.filter(created_by_id=user_id)
        else:
            # Utilisateurs normaux : seulement leurs devis
            queryset = Quote.objects.filter(created_by=request.user)

        queryset = queryset.select_related(
            'project_type',
            'design_option',
            'complexity_level',
            'created_by'
        ).prefetch_related('supplementary_options').order_by('-created_at')

        # Filtrer par statut si demandé
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        serializer = QuoteListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='download-pdf')
    @handle_service_errors
    def download_pdf(self, request, pk=None):
        """Télécharger le PDF du devis"""
        quote = self.get_object()
        return PDFService.generate_pdf_response(quote)
    
    @action(detail=True, methods=['post'], url_path='send-email')
    @handle_service_errors
    def send_email(self, request, pk=None):
        """Envoyer le devis par email"""
        quote = self.get_object()
        result = QuoteService.send_quote(quote)

        return Response({
            'message': result['message'],
            'sent_at': quote.sent_at
        })
    
    @action(detail=False, methods=['get'], url_path='public/(?P<token>[^/.]+)', permission_classes=[permissions.AllowAny])
    def public_view(self, request, token=None):
        """Voir un devis avec le token public (sans authentification)"""
        quote = get_object_or_404(Quote, signature_token=token)

        # Marquer comme consulté via le service
        QuoteService.mark_as_viewed(quote)

        serializer = QuoteDetailSerializer(quote, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='sign/(?P<token>[^/.]+)', permission_classes=[permissions.AllowAny])
    @handle_service_errors
    def sign_quote(self, request, token=None):
        """Signer électroniquement un devis"""
        quote = get_object_or_404(Quote, signature_token=token)

        # Normaliser les données de signature
        signature_data = {
            'signature': request.data.get('signature') or request.data.get('signature_data'),
            'signer_name': request.data.get('signer_name') or request.data.get('signature_name'),
            'terms_accepted': request.data.get('terms_accepted', False)
        }

        # Normaliser terms_accepted en booléen
        if isinstance(signature_data['terms_accepted'], str):
            signature_data['terms_accepted'] = signature_data['terms_accepted'].lower() in ('true', '1', 'yes', 'on')
        else:
            signature_data['terms_accepted'] = bool(signature_data['terms_accepted'])

        # Utiliser le service pour traiter la signature
        result = QuoteService.sign_quote(quote, signature_data, request)

        serializer = QuoteDetailSerializer(quote, context={'request': request})
        return Response({
            'message': result['message'],
            'quote': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='reject')
    @handle_service_errors
    def reject(self, request, pk=None):
        """Rejeter un devis"""
        quote = self.get_object()

        # Préparer les données de refus
        rejection_data = {
            'rejection_reason': request.data.get('reason', '')
        }

        # Utiliser le service pour rejeter le devis
        QuoteService.reject_quote(quote, rejection_data)

        serializer = QuoteDetailSerializer(quote, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='statistics', permission_classes=[permissions.IsAdminUser])
    def statistics(self, request):
        """Statistiques des devis (admin uniquement)"""
        stats_data = QuoteService.get_statistics()
        serializer = QuoteStatisticsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='duplicate')
    @handle_service_errors
    def duplicate(self, request, pk=None):
        """Dupliquer un devis"""
        original_quote = self.get_object()

        # Utiliser le service pour dupliquer le devis
        new_quote = QuoteService.duplicate_quote(original_quote, request.user)

        serializer = QuoteDetailSerializer(new_quote, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='bulk-delete', permission_classes=[permissions.IsAdminUser])
    def bulk_delete(self, request):
        """Supprimer plusieurs devis"""
        quote_ids = request.data.get('ids', [])
        if not quote_ids:
            return Response({'error': 'Aucun ID fourni'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtrer les devis qui existent
        quotes = Quote.objects.filter(id__in=quote_ids)
        count = quotes.count()
        quotes.delete()
        
        return Response({'message': f'{count} devis supprimés avec succès'})


class QuoteEmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API pour consulter les logs d'emails"""
    queryset = QuoteEmailLog.objects.all()
    serializer_class = QuoteEmailLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filtrer par devis si spécifié"""
        queryset = super().get_queryset()
        quote_id = self.request.query_params.get('quote', None)
        if quote_id:
            queryset = queryset.filter(quote_id=quote_id)
        return queryset
