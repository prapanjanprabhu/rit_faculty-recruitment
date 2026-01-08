from django.urls import path, include
from applications.urls import main_fr_urls
from applications.views import main_fr_views, admin_views, organizations_views

urlpatterns = [
    path("organizations/", organizations_views.organizations, name="organizations"),
    path("degree/", organizations_views.degree, name="degree"),
    path("department/", organizations_views.department, name="department"),
    path("designation/", organizations_views.designation, name="designation"),
    path("level_of_education/", organizations_views.level_of_education, name="level_of_education"),
    path("document_type/", organizations_views.document_type, name="document_type"),
    path("certificate_permission/", organizations_views.certificate_permission, name="certificate_permission"),
]
