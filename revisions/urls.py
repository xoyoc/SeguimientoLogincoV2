from django.urls import path
from .views import (
    RevisionListView, RevisionDetailView, RevisionCreateView,
    RevisionUpdateView, RevisionDeleteView, quick_add_revision
)

urlpatterns = [
    path('', RevisionListView.as_view(), name='revision-list'),
    path('<int:pk>/', RevisionDetailView.as_view(), name='revision-detail'),
    path('create/', RevisionCreateView.as_view(), name='revision-create'),
    path('<int:pk>/edit/', RevisionUpdateView.as_view(), name='revision-edit'),
    path('<int:pk>/delete/', RevisionDeleteView.as_view(), name='revision-delete'),
    path('quick-add/', quick_add_revision, name='revision-quick-add'),
]
