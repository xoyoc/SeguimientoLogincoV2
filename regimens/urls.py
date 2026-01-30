from django.urls import path
from .views import (
    RegimenListView,
    RegimenCreateView,
    RegimenUpdateView,
    RegimenDeleteView,
)

urlpatterns = [
    path('', RegimenListView.as_view(), name='regimen-list'),
    path('crear/', RegimenCreateView.as_view(), name='regimen-create'),
    path('<int:pk>/editar/', RegimenUpdateView.as_view(), name='regimen-edit'),
    path('<int:pk>/eliminar/', RegimenDeleteView.as_view(), name='regimen-delete'),
]
