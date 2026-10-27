"""URL configuration for myproject (DevHelp AI)."""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

# Custom Error Handlers used by Django in production (DEBUG=False)
handler400 = 'myapp.views.custom_bad_request_view'
handler403 = 'myapp.views.custom_permission_denied_view'
handler404 = 'myapp.views.custom_page_not_found_view'
handler500 = 'myapp.views.custom_server_error_view'


def demo_error_view(request, code):
    """Local demonstration endpoint to preview all custom error pages."""
    template_name = f"myapp/{code}.html"
    status_code = int(code) if str(code).isdigit() else 500
    return render(request, template_name, status=status_code)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('myapp.urls')),

    # Local preview endpoints for custom error pages
    path('demo-error/<str:code>/', demo_error_view, name='demo_error'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'myapp' / 'static')

