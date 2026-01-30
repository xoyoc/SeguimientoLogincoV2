from django.urls import path
from .views import TrackingListView, TrackingDetailView, TrackingCreateView, TrackingUpdateView, TrackingDeleteView

urlpatterns = [
    path('', TrackingListView.as_view(), name='tracking-list'),
    path('<int:pk>/', TrackingDetailView.as_view(), name='tracking-detail'),
    path('create/', TrackingCreateView.as_view(), name='tracking-create'),
    path('<int:pk>/edit/', TrackingUpdateView.as_view(), name='tracking-edit'),
    path('<int:pk>/delete/', TrackingDeleteView.as_view(), name='tracking-delete'),
]
