from django.urls import path

from . import views

urlpatterns = [
    path('lab/course-list/baseline/', views.course_list_baseline, name='course_list_baseline'),
    path('lab/course-list/optimized/', views.course_list_optimized, name='course_list_optimized'),
    path('lab/course-members/baseline/', views.course_members_baseline, name='course_members_baseline'),
    path('lab/course-members/optimized/', views.course_members_optimized, name='course_members_optimized'),
    path('lab/course-dashboard/baseline/', views.course_dashboard_baseline, name='course_dashboard_baseline'),
    path('lab/course-dashboard/optimized/', views.course_dashboard_optimized, name='course_dashboard_optimized'),
    path('lab/bulk/create-contents/', views.bulk_create_contents, name='bulk_create_contents'),
    path('lab/bulk/update-prices/', views.bulk_update_course_prices, name='bulk_update_course_prices'),
]
