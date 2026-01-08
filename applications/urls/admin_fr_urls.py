from django.urls import path, include
from applications.urls import main_fr_urls
from applications.views import main_fr_views, admin_views

urlpatterns = [
   path("admin-login/", admin_views.admin_login, name="admin_login"),
   path("admin-dashboard/", admin_views.admin_dashboard, name="admin_dashboard"),
   path("admin-logout/", admin_views.admin_logout, name="admin_logout"),

   path("admin-home/", main_fr_views.admin_home, name="admin_home"),
   path("logs/", admin_views.logs, name="logs"),
   path("logs/admin-logs/", admin_views.admin_logs, name="admin_logs"),
   path("logs/visitor-logs/", admin_views.user_logs, name="user_logs"),


   path("admin/forgot-password/", admin_views.admin_forgot_password, name="admin_forgot_password"),
path("admin/verify-otp/", admin_views.admin_verify_otp, name="admin_verify_otp"),
]
