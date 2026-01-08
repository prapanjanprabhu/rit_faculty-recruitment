from django.urls import path
from applications.views import faculty_data_views

urlpatterns = [
    path('faculty/', faculty_data_views.faculty_data, name='faculty_data'),

    path('faculty/view/<int:candidate_id>/', faculty_data_views.faculty_application_details, name='faculty_application_details'),

    path('faculty/update/', faculty_data_views.faculty_section_update, name='faculty_section_update'),

    path(
        "faculty/pdf/<int:candidate_id>/",
        faculty_data_views.faculty_data_pdf,
        name="faculty_data_pdf"
    ),
]
