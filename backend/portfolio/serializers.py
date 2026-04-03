from rest_framework import serializers
from .models import Technology, Project, ProjectImage, Testimonial, ContactMessage
from config.utils import get_client_ip


class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = ['id', 'name', 'icon', 'category', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ['id', 'image', 'caption', 'order', 'created_at']
        read_only_fields = ['created_at']


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des projets (moins de détails)"""
    technologies = TechnologySerializer(many=True, read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    # Aliases pour compatibilité frontend
    description = serializers.CharField(source='short_description', read_only=True)
    image = serializers.ImageField(source='thumbnail', read_only=True)
    url = serializers.URLField(source='live_url', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'short_description', 'description',
            'thumbnail', 'image', 'technologies', 'category', 'category_display',
            'url', 'live_url', 'featured', 'order', 'completion_date'
        ]


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Serializer pour le détail d'un projet (toutes les infos)"""
    technologies = TechnologySerializer(many=True, read_only=True)
    images = ProjectImageSerializer(many=True, read_only=True)
    testimonials = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'short_description', 'description',
            'thumbnail', 'image_main', 'technologies', 'images',
            'github_url', 'live_url', 'category', 'category_display',
            'featured', 'order', 'is_published',
            'completion_date', 'created_at', 'updated_at', 'testimonials'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_testimonials(self, obj):
        testimonials = obj.testimonials.filter(is_published=True)
        return TestimonialSerializer(testimonials, many=True).data


class TestimonialSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source='project.title', read_only=True)
    
    class Meta:
        model = Testimonial
        fields = [
            'id', 'client_name', 'client_position', 'client_company',
            'client_photo', 'content', 'rating', 'project', 'project_title',
            'is_published', 'order', 'created_at'
        ]
        read_only_fields = ['created_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    """Serializer pour les messages de contact"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ContactMessage
        fields = [
            'id', 'name', 'email', 'phone', 'subject', 'message',
            'status', 'status_display', 'created_at', 'read_at', 'replied_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'read_at', 'replied_at']

    def validate_email(self, value):
        """Valider le format de l'email"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Format d'email invalide")
        return value.lower()

    def create(self, validated_data):
        """Créer un message et envoyer une notification par email"""
        # Récupérer les métadonnées de la requête
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]

        # Créer le message
        message = ContactMessage.objects.create(**validated_data)

        # Envoyer une notification par email (async pour ne pas bloquer)
        try:
            from .emails import send_contact_notification_email
            send_contact_notification_email(message)
        except Exception as e:
            # Logger l'erreur mais ne pas bloquer la création
            print(f"⚠️ Erreur lors de l'envoi de la notification: {e}")

        return message

