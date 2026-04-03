"""
Utilitaires partagés entre les applications Django
"""


def get_client_ip(request) -> str:
    """Extrait l'adresse IP réelle du client depuis la requête.

    Prend en compte les proxies (X-Forwarded-For).
    La première IP de la liste est celle du client originel.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
