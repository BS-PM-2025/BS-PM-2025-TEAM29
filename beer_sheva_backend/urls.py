from django.contrib import admin
from django.urls import path, include
from user import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('reports.urls')),
    path('user/', include('user.urls')),
    path('register/', user_views.register_view, name='register'),  # optional shortcut
    path('login/', user_views.user_login, name='login'),
    path('reset_password/', user_views.reset_password_view, name='reset_password'),
]
