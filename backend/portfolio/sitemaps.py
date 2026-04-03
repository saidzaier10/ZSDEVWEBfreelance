from django.contrib.sitemaps import Sitemap
from django.conf import settings
from .models import Project

FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

STATIC_FRONTEND_URLS = {
    'home': '/',
    'portfolio': '/portfolio',
    'contact': '/contact',
    'login': '/login',
    'register': '/register',
}


class ProjectSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'

    def items(self):
        return Project.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"{FRONTEND_URL}/portfolio/{obj.slug}"


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    protocol = 'https'

    def items(self):
        return list(STATIC_FRONTEND_URLS.keys())

    def location(self, item):
        return f"{FRONTEND_URL}{STATIC_FRONTEND_URLS.get(item, '/')}"
