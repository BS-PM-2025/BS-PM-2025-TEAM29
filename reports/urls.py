# reports/urls.py
from django.urls import path
from . import views
from admin_backend import views as admin_views
from worker_backend import views as worker_views
from user import views as user_views
urlpatterns = [
    path('', views.report_list, name='report_list'), #Malik
    path('add/', views.add_report, name='add_report'), #Firas BSPM25T29-16
    path('confirmation/<str:report_id>/', views.report_confirmation, name='report_confirmation'), #Ibrahim BSPM25T29-3
    path('map/', views.map_view, name='map_view'), #Malik
    path('worker/dashboard/', worker_views.worker_dashboard, name='worker-dashboard'), #Ibrahim BSPM25T29-151
    path("admin/dashboard/", admin_views.admin_dashboard, name="admin-dashboard"),
    path("admin/reports/<str:report_id>/", admin_views.admin_report_details, name="admin-report-details"),
    path("reports/<str:report_id>/", views.report_detail, name="report_detail"),
    path('logout/', user_views.logout_view, name='logout_view'),
    path('contact/', views.contact_us, name='contact_us'),

]

