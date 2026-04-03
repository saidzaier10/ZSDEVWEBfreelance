"""
Middleware de sécurité personnalisé pour l'application
"""

import logging
import re
from django.http import JsonResponse
from django.conf import settings
from config.utils import get_client_ip

logger = logging.getLogger('django.security')


class SecurityMiddleware:
    """
    Middleware de sécurité pour ajouter des protections supplémentaires
    """
    
    # User agents suspects
    SUSPICIOUS_USER_AGENTS = [
        'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus', 'burp', 
        'metasploit', 'havij', 'acunetix', 'w3af', 'dirbuster',
        'wget', 'curl', 'python-requests', 'postman'  # Bloquer les outils automatisés en production
    ]
    
    # Patterns d'attaque SQL Injection
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bSELECT\b.*\bFROM\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(1=1|1'='1)",
    ]
    
    # Patterns d'attaque XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"<iframe[^>]*>",
    ]
    
    # Taille maximale des requêtes (10 MB)
    MAX_REQUEST_SIZE = 10 * 1024 * 1024

    # Whitelisted paths (skip WAF checks)
    WHITELISTED_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifications avant le traitement de la requête
        
        # Mode "Observation" : si True, on loggue mais on ne bloque pas
        block_mode = getattr(settings, 'WAF_BLOCK_MODE', True)
        
        # 0. Ignorer les chemins whitelistés
        for path in self.WHITELISTED_PATHS:
            if request.path.startswith(path):
                return self.get_response(request)

        # 1. Vérifier la taille de la requête
        if self.is_request_too_large(request):
            logger.warning(f"Requête trop volumineuse détectée depuis {get_client_ip(request)}")
            if block_mode:
                return JsonResponse(
                    {'error': 'Requête trop volumineuse'},
                    status=413
                )
        
        # 2. Vérifier le User-Agent (uniquement en production)
        if not settings.DEBUG and self.is_suspicious_user_agent(request):
            logger.warning(f"User-Agent suspect détecté: {request.META.get('HTTP_USER_AGENT')} depuis {get_client_ip(request)}")
            if block_mode:
                return JsonResponse(
                    {'error': 'Accès refusé'},
                    status=403
                )
        
        # 3. Détecter les tentatives d'injection SQL/XSS dans l'URL
        if self.contains_malicious_patterns(request.path) or self.contains_malicious_patterns(request.GET.urlencode()):
            logger.error(f"Tentative d'attaque détectée dans l'URL: {request.path} depuis {get_client_ip(request)}")
            if block_mode:
                return JsonResponse(
                    {'error': 'Requête invalide'},
                    status=400
                )
        
        # 4. Vérifier le body pour les attaques (seulement pour POST/PUT/PATCH)
        if request.method in ['POST', 'PUT', 'PATCH']:
            if hasattr(request, 'body') and request.body:
                try:
                    body_str = request.body.decode('utf-8', errors='ignore')
                    if self.contains_malicious_patterns(body_str):
                        logger.error(f"Tentative d'attaque détectée dans le body depuis {get_client_ip(request)}")
                        if block_mode:
                            return JsonResponse(
                                {'error': 'Contenu de la requête invalide'},
                                status=400
                            )
                except Exception as e:
                    logger.debug(f"Impossible de décoder le body: {str(e)}")
        
        # Traiter la requête normalement
        response = self.get_response(request)
        
        # Ajouter des en-têtes de sécurité à la réponse
        response = self.add_security_headers(response)
        
        return response

    def is_request_too_large(self, request):
        """Vérifier si la requête dépasse la taille maximale"""
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                if int(content_length) > self.MAX_REQUEST_SIZE:
                    return True
            except ValueError:
                pass
        return False

    def is_suspicious_user_agent(self, request):
        """Vérifier si le User-Agent est suspect"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Vérifier si c'est un User-Agent vide
        if not user_agent:
            return True
        
        # Vérifier contre la liste des User-Agents suspects
        for suspicious_agent in self.SUSPICIOUS_USER_AGENTS:
            if suspicious_agent.lower() in user_agent:
                return True
        
        return False

    def contains_malicious_patterns(self, text):
        """Détecter les patterns d'attaques SQL Injection et XSS"""
        if not text:
            return False
        
        text_upper = text.upper()
        
        # Vérifier les patterns SQL Injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        
        # Vérifier les patterns XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

    def add_security_headers(self, response):
        """Ajouter des en-têtes de sécurité à la réponse.

        Note: CSP et X-Frame-Options sont gérés uniquement par Nginx pour éviter
        les headers en double. Seuls les headers non couverts par Nginx sont ajoutés ici.
        """
        # Permissions Policy (anciennement Feature Policy)
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response

class RequestLoggingMiddleware:
    """
    Middleware pour logger toutes les requêtes
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django')

    def __call__(self, request):
        # Logger la requête entrante
        self.log_request(request)
        
        # Traiter la requête
        response = self.get_response(request)
        
        # Logger la réponse
        self.log_response(request, response)
        
        return response

    def log_request(self, request):
        """Logger les informations de la requête"""
        ip = get_client_ip(request)
        method = request.method
        path = request.path
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        
        self.logger.info(f"{method} {path} - User: {user} - IP: {ip}")

    def log_response(self, request, response):
        """Logger la réponse"""
        # Logger seulement les erreurs et les succès importants
        if response.status_code >= 400:
            ip = get_client_ip(request)
            self.logger.warning(
                f"Response {response.status_code} for {request.method} {request.path} - IP: {ip}"
            )

