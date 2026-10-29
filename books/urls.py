from django.urls import path
from . import views

app_name = 'books'
urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('categories/<int:category_pk>/', views.index, name='category'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/update/', views.update, name='update'),
    path('<int:pk>/delete/', views.delete, name='delete'),
    path('<int:pk>/like/', views.like, name='like'),
]
