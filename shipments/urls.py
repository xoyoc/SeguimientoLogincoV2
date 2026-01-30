from django.urls import path
from .views import (
    ShipmentListView,
    ShipmentDetailView,
    ShipmentCreateView,
    ShipmentUpdateView,
    ShipmentDeleteView,
    get_next_consecutive_view,
)

urlpatterns = [
    path('', ShipmentListView.as_view(), name='shipment-list'),
    path('<int:pk>/', ShipmentDetailView.as_view(), name='shipment-detail'),
    path('create/', ShipmentCreateView.as_view(), name='shipment-create'),
    path('<int:pk>/edit/', ShipmentUpdateView.as_view(), name='shipment-edit'),
    path('<int:pk>/delete/', ShipmentDeleteView.as_view(), name='shipment-delete'),
    path('api/next-consecutive/', get_next_consecutive_view, name='shipment-next-consecutive'),
]
