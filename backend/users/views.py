from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .serializers import RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer
from config.utils import get_client_ip
import logging

logger = logging.getLogger('users')


class RegisterRateThrottle(AnonRateThrottle):
    """Rate limiting spécifique pour l'inscription"""
    rate = '100/hour'  # Augmenté pour le développement


class LoginRateThrottle(AnonRateThrottle):
    """Rate limiting spécifique pour le login"""
    rate = '100/hour'  # Augmenté pour le développement


class RegisterView(generics.CreateAPIView):
    """Inscription d'un nouvel utilisateur"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [RegisterRateThrottle]

    def create(self, request, *args, **kwargs):
        logger.info(f"Tentative d'inscription depuis IP: {get_client_ip(request)}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"Nouvel utilisateur inscrit: {user.username} (ID: {user.id})")
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    

class LoginView(APIView):
    """Connexion utilisateur"""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        username = request.data.get('username', 'unknown')
        logger.info(f"Tentative de connexion pour: {username} depuis IP: {get_client_ip(request)}")
        
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            logger.info(f"Connexion réussie pour: {username}")
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.warning(f"Échec de connexion pour: {username} - Raison: {str(e)}")
            raise
    

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Voir et modifier le profil de l'utilisateur connecté"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        logger.info(f"Mise à jour du profil utilisateur: {request.user.username}")
        return super().update(request, *args, **kwargs)


class LogoutView(APIView):
    """Déconnexion (blacklist le refresh token)"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            
            if not refresh_token:
                logger.warning(f"Déconnexion sans token pour: {request.user.username}")
                return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"Déconnexion réussie pour: {request.user.username}")
            
            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion pour {request.user.username}: {str(e)}")
            return Response({"message": "Déconnexion réussie"}, status=status.HTTP_200_OK)