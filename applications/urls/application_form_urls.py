from django.urls import path
from applications.views import application_form_views as views

urlpatterns = [

    # PAGE 1 — A. INDIVIDUAL SUMMARY SHEET
    path(
        "",
        views.individual_summary_sheet,
        name="individual_summary_sheet"
    ),

    # PAGE 2 — B. INDIVIDUAL DATA SHEET
    path(
        "individual-data-sheet/",
        views.individual_data_sheet,
        name="individual_data_sheet"
    ),

    # PAGE 3 — EDUCATION + THESIS
    path(
        "educational-qualifications/",
        views.educational_qualifications,
        name="educational_qualifications"
    ),

    # PAGE 4 — ACADEMIC + INDUSTRY EXPERIENCE
    path(
        "academic-and-industry-experience/",
        views.academic_and_industry_experience,
        name="academic_and_industry_experience"
    ),

    # PAGE 5 — TEACHING + CONTRIBUTIONS
    path(
        "teaching-and-contributions/",
        views.teaching_and_contributions,
        name="teaching_and_contributions"
    ),

    # PAGE 6 — PROGRAMMES + PUBLICATIONS
    path(
        "programmes-and-publications/",
        views.programmes_and_publications,
        name="programmes_and_publications"
    ),

    # PAGE 7 — REFEREES + FINAL SUBMIT
    path(
        "referees-and-declaration/",
        views.referees_and_declaration,
        name="referees_and_declaration"
    ),

    # SUCCESS PAGE
    path(
        "application-success/",
        views.application_success,
        name="application_success"
    ),
]