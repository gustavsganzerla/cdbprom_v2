from django.urls import path
from . import views
from .views import PromoterQueryView, PromoterDownloadCSVView, DownloadPredictView 

urlpatterns = [
        path('home/', views.home, name='home'),
        path('query/', views.query, name='query'),
        path('resources/', views.resources, name='resources'),
        path('resources_api_db/', views.resources_api_db, name='resources_api_db'),
        path('resources_api_prediction/', views.resources_api_prediction, name='resources_api_prediction'),
        path('contact/', views.contact, name='contact'),
        path('about/', views.about, name='about'),
        path('api/query/', PromoterQueryView.as_view(), name='promoter-query'),
        path('api/download/', PromoterDownloadCSVView.as_view(), name='download-query'),
        path('api/downloadPredict', DownloadPredictView.as_view(), name='download_predict'),
        path('docker/', views.docker, name='docker'),
        path('autocomplete_organism_name/', views.autocomplete_organism_name, name='autocomplete_organism_name'),
        path('organisms/', views.organisms, name='organisms'),
        path('predict/', views.predict, name='predict')
]
