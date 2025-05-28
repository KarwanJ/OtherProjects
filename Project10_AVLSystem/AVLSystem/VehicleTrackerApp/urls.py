# tracker/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static

from . import views
from .views import PhoneViewSet

router = DefaultRouter()
router.register(r'phones', PhoneViewSet)

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/save_position/', views.save_position, name='save_position'),
    path('api/save_track_shapefile/', views.save_track_as_shapefile, name='save_track_as_shapefile'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
    path('api/phones/latest/', views.get_latest_phones, name='get_latest_phones'),
    path('api/phones/<str:phone_id>/latest/', views.get_phone_latest, name='get_phone_latest'),
path('api/tracks/<str:phone_id>/', views.get_phone_tracks, name='get_phone_tracks'),
] + static('/shapefiles/', document_root='shapefiles')
