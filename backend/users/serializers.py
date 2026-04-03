from rest_framework import serializers, validators
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator, RegexValidator
import nh3
import re

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    # Validation stricte du téléphone
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Le numéro de téléphone doit être au format international (ex: +33612345678)"
            )
        ]
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'phone', 'company_name']
        extra_kwargs = {
            'email': {
                'required': True,
                'validators': [EmailValidator(message="Adresse email invalide")]
            },
            'username': {
                'min_length': 3,
                'max_length': 30,
                'validators': [
                    RegexValidator(
                        regex=r'^[\w.@+-]+$',
                        message="Le nom d'utilisateur ne peut contenir que des lettres, chiffres et @/./+/-/_"
                    ),
                    validators.UniqueValidator(queryset=User.objects.all(), message="Ce nom d'utilisateur est déjà pris.")
                ]
            },
            'company_name': {
                'max_length': 200
            }
        }

    def validate_username(self, value):
        """Validation personnalisée du nom d'utilisateur"""
        # Nettoyer le username
        value = nh3.clean(value, tags=set()).strip()
        
        # Vérifier qu'il n'est pas vide après nettoyage
        if not value:
            raise serializers.ValidationError("Le nom d'utilisateur ne peut pas être vide")
        
        # Vérifier la longueur
        if len(value) < 3:
            raise serializers.ValidationError("Le nom d'utilisateur doit contenir au moins 3 caractères")
        
        if len(value) > 30:
            raise serializers.ValidationError("Le nom d'utilisateur ne peut pas dépasser 30 caractères")
        
        # Vérifier qu'il ne contient pas de mots interdits
        forbidden_words = ['admin', 'root', 'administrator', 'superuser', 'system']
        if any(word in value.lower() for word in forbidden_words):
            raise serializers.ValidationError("Ce nom d'utilisateur n'est pas autorisé")
        
        return value

    def validate_email(self, value):
        """Validation personnalisée de l'email"""
        # Nettoyer et normaliser l'email
        value = nh3.clean(value, tags=set()).strip().lower()
        
        # Vérifier le format avec une regex stricte
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Format d'email invalide")
        
        # Vérifier que le domaine n'est pas suspect
        suspicious_domains = ['tempmail.com', 'throwaway.email', '10minutemail.com']
        domain = value.split('@')[1]
        if domain in suspicious_domains:
            raise serializers.ValidationError("Ce domaine email n'est pas autorisé")
        
        return value

    def validate_phone(self, value):
        """Validation personnalisée du téléphone"""
        if not value:
            return value
        
        # Nettoyer le téléphone
        value = nh3.clean(value, tags=set()).strip()
        
        # Supprimer les espaces et tirets
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        
        return cleaned

    def validate_company_name(self, value):
        """Validation du nom de l'entreprise"""
        if not value:
            return value
        
        # Nettoyer le nom de l'entreprise
        value = nh3.clean(value, tags=set()).strip()
        
        # Limiter la longueur
        if len(value) > 200:
            raise serializers.ValidationError("Le nom de l'entreprise ne peut pas dépasser 200 caractères")
        
        return value

    def validate(self, attrs):
        """Validation globale"""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Les mots de passe ne correspondent pas."
            })
        
        # Vérifier que le mot de passe ne contient pas le username ou l'email
        username = attrs.get('username', '').lower()
        email = attrs.get('email', '').lower().split('@')[0]
        password = attrs.get('password', '').lower()
        
        if username in password:
            raise serializers.ValidationError({
                "password": "Le mot de passe ne doit pas contenir le nom d'utilisateur"
            })
        
        if email in password:
            raise serializers.ValidationError({
                "password": "Le mot de passe ne doit pas contenir l'email"
            })
        
        return attrs

    def create(self, validated_data):
        """Créer un utilisateur avec les données validées"""
        validated_data.pop('password2')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data.get('phone', ''),
            company_name=validated_data.get('company_name', ''),
            user_type='client'
        )
        user.set_password(validated_data['password'])
        user.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour afficher les informations utilisateur"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'company_name', 'user_type', 'avatar', 'created_at', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'username', 'user_type', 'created_at']
    
    def validate_phone(self, value):
        """Validation du téléphone lors de la mise à jour"""
        if not value:
            return value
        
        value = nh3.clean(value, tags=set()).strip()
        cleaned = re.sub(r'[\s\-\(\)]', '', value)
        
        phone_regex = r'^\+?1?\d{9,15}$'
        if not re.match(phone_regex, cleaned):
            raise serializers.ValidationError("Format de téléphone invalide")
        
        return cleaned
    
    def validate_company_name(self, value):
        """Validation du nom de l'entreprise lors de la mise à jour"""
        if not value:
            return value
        
        value = nh3.clean(value, tags=set()).strip()
        
        if len(value) > 200:
            raise serializers.ValidationError("Le nom de l'entreprise ne peut pas dépasser 200 caractères")
        
        return value


class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Serializer pour la connexion avec username/password"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_username(self, value):
        """Nettoyer le username"""
        return nh3.clean(value, tags=set()).strip()

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Vérifier que les champs ne sont pas vides
        if not username or not password:
            raise serializers.ValidationError('Le nom d\'utilisateur et le mot de passe sont requis')
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError('Identifiants incorrects')
        
        if not user.is_active:
            raise serializers.ValidationError('Ce compte a été désactivé')
        
        # Générer les tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return {
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }