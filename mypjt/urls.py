from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(
        pattern_name='books:index', permanent=False, http_method_names=['get', 'head', 'options'],
    )),
    path('admin/', admin.site.urls),
    path('books/', include('books.urls')),
    path('accounts/', include('accounts.urls')),
]
