from django.urls import path, include
from applications.urls import application_form_urls, admin_fr_urls, organizations_urls, faculty_data_urls

urlpatterns = [
    path("", include(application_form_urls)),
    path("admin/", include(admin_fr_urls)),
    path("resources/", include(organizations_urls)),
    path("faculty_data/", include(faculty_data_urls)),
]
