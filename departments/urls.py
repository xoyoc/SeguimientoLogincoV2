from django.urls import path
from .views import (
    DepartmentListView,
    DepartmentDetailView,
    DepartmentCreateView,
    DepartmentUpdateView,
    DepartmentDeleteView,
    department_analytics_view
)

urlpatterns = [
    path('', DepartmentListView.as_view(), name='department-list'),
    path('analytics/', department_analytics_view, name='department-analytics'),
    path('<int:pk>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('create/', DepartmentCreateView.as_view(), name='department-create'),
    path('<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department-edit'),
    path('<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department-delete'),
]
