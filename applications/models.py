import os
from django.db import models

from django.db import models
from django.contrib.auth.models import User

import os
from applications.utils import candidate_profile_path, candidate_document_path


# === Organization Masters ===
class Degree(models.Model):
    degree_code = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    degree = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["degree"]
        indexes = [
            models.Index(fields=["degree_code"]),
            models.Index(fields=["degree"]),
        ]

    def __str__(self):
        return f"{self.degree_code} - {self.degree}"

class Department(models.Model):
    name = models.CharField(
        max_length=150,
        null=True,
        blank=True
    )

    code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    degree = models.ForeignKey(
        'Degree',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departments'
    )

    class Meta:
        ordering = ["degree", "name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["code"]),
            models.Index(fields=["degree"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

class Designation(models.Model):
    name = models.CharField(max_length=150, unique=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class LevelOfEducation(models.Model):
    name = models.CharField(max_length=150, unique=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.name


class Document_Type(models.Model):
    document_type = models.CharField(max_length=150, unique=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.document_type



class Certificate_Permission(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="certificate_permissions", null=True, blank=True
    )

    document_type = models.ForeignKey(
        Document_Type,
        on_delete=models.CASCADE,
        related_name="certificate_permissions", null=True, blank=True
    )

    is_required = models.BooleanField(default=False)



    def __str__(self):
        return f"{self.department} - {self.document_type}"



class Candidate(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)
    community = models.CharField(max_length=100, null=True, blank=True)
    caste = models.CharField(max_length=100, null=True, blank=True)
    pan_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_primary = models.CharField(max_length=100, null=True, blank=True)
    phone_secondary = models.CharField(max_length=100, null=True, blank=True)
    photo = models.ImageField(
        upload_to=candidate_profile_path,
        null=True,
        blank=True
    )
    address = models.TextField(null=True, blank=True)
    total_experience_years = models.IntegerField(null=True, blank=True)
    present_post_years = models.IntegerField(null=True, blank=True)
    mother_name_and_occupation = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name or "Unnamed Candidate"


class Document(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    document_type = models.ForeignKey('Document_Type', on_delete=models.CASCADE)  # Assuming Document_Type exists
    file = models.FileField(upload_to=candidate_document_path, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class PositionApplication(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position_applied = models.ForeignKey('Designation', on_delete=models.SET_NULL, null=True, blank=True)  # Assuming Designation exists
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)  # Assuming Department exists
    present_designation = models.CharField(max_length=200, null=True, blank=True)
    present_organization = models.CharField(max_length=200, null=True, blank=True)
    specialization = models.CharField(max_length=200, null=True, blank=True)
    assistant_professor_years = models.PositiveIntegerField(default=0, null=True, blank=True)
    associate_professor_years = models.PositiveIntegerField(default=0, null=True, blank=True)
    professor_years = models.PositiveIntegerField(default=0, null=True, blank=True)
    other_years = models.PositiveIntegerField(default=0, null=True, blank=True)
    research_experience_years = models.PositiveIntegerField(default=0, null=True, blank=True)
    industry_experience_years = models.PositiveIntegerField(default=0, null=True, blank=True)
    journal_publications = models.PositiveIntegerField(default=0, null=True, blank=True)
    conference_publications = models.PositiveIntegerField(default=0, null=True, blank=True)
    students_guided_completed = models.PositiveIntegerField(default=0, null=True, blank=True)
    students_guided_ongoing = models.PositiveIntegerField(default=0, null=True, blank=True)
    community_and_caste = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, null=True, blank=True)


class Qualification(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    qualification = models.ForeignKey(Degree,on_delete=models.SET_NULL,null=True,blank=True)
    specialization = models.CharField(max_length=100, null=True, blank=True)
    institute = models.CharField(max_length=200, null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)


class SponsoredProject(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    title = models.CharField(max_length=300, null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True)
    amount = models.PositiveIntegerField(null=True, blank=True)
    agency = models.CharField(max_length=200, null=True, blank=True)


class Education(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    category = models.ForeignKey(LevelOfEducation, on_delete=models.SET_NULL, null=True, blank=True)  # SSLC / HSC / UG / PG / PhD
    degree = models.ForeignKey(Degree, on_delete=models.SET_NULL,null=True, blank=True)
    specialization = models.CharField(max_length=100, null=True, blank=True)
    year_of_passing = models.CharField(max_length=10, null=True, blank=True)
    institution = models.CharField(max_length=200, null=True, blank=True)
    university = models.CharField(max_length=200, null=True, blank=True)
    percentage = models.CharField(max_length=20, null=True, blank=True)
    class_obtained = models.CharField(max_length=50, null=True, blank=True)


class ResearchDetails(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True)
    mode_ug = models.CharField(max_length=30, null=True, blank=True)
    mode_pg = models.CharField(max_length=30, null=True, blank=True)
    mode_phd = models.CharField(max_length=30, null=True, blank=True)
    arrears_ug = models.IntegerField(null=True, blank=True)
    arrears_pg = models.IntegerField(null=True, blank=True)
    gate_score = models.CharField(max_length=50, null=True, blank=True)
    net_slet_score = models.CharField(max_length=50, null=True, blank=True)
    me_thesis_title = models.TextField(null=True, blank=True)
    phd_thesis_title = models.TextField(null=True, blank=True)


class AcademicExperience(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    institution = models.CharField(max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    relieving_date = models.CharField(max_length=50, null=True, blank=True)  # "Till Date" allowed
    years = models.IntegerField(null=True, blank=True)
    months = models.IntegerField(null=True, blank=True)
    days = models.IntegerField(null=True, blank=True)


class IndustryExperience(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    organization = models.CharField(max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    nature_of_work = models.CharField(max_length=200, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    relieving_date = models.DateField(null=True, blank=True)
    years = models.IntegerField(null=True, blank=True)
    months = models.IntegerField(null=True, blank=True)
    days = models.IntegerField(null=True, blank=True)


class TeachingSubject(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, null=True, blank=True)  # UG / PG
    subject_and_result = models.CharField(max_length=200, null=True, blank=True)


class Contribution(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    level = models.CharField(max_length=50, null=True, blank=True)  # Department / College
    description = models.CharField(max_length=200, null=True, blank=True)


class Programme(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    programme_type = models.CharField(max_length=50, null=True, blank=True)  # Workshop / FDP etc
    category = models.CharField(max_length=50, null=True, blank=True)  # Participated / Organized
    count = models.IntegerField(null=True, blank=True)


class Publication(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    indexing = models.CharField(max_length=100, null=True, blank=True)


class Referee(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True, blank=True)
    designation = models.CharField(max_length=200, null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)






class AdminLoginLog(models.Model):
    ACTION_CHOICES = (
        ("LOGIN_SUCCESS", "Login Success"),
        ("LOGIN_FAILED", "Login Failed"),
        ("LOGOUT", "Logout"),
    )

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    username_attempted = models.CharField(max_length=150, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    session_key = models.CharField(max_length=40, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Admin Login Log"
        verbose_name_plural = "Admin Login Logs"

    def __str__(self):
        return f"{self.username_attempted} - {self.action} - {self.timestamp}"

class VisitorLog(models.Model):
    user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["ip_address"]),
            models.Index(fields=["timestamp"]),
        ]

class ApplicationUsageLog(models.Model):
    ACTION_CHOICES = [
        ("FORM_SUBMITTED", "Form Submitted"),
    ]

    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="usage_logs"
    )

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    timestamp = models.DateTimeField(auto_now_add=True)


# models.py
class ProgrammesPublications(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="programmes_publications"
    )

    programmes = models.CharField(max_length=1000, default="", null=True)
    publications = models.CharField(max_length=1000, default="", null=True)

    research_publications_details = models.CharField(max_length=1000, default="", null=True)
    research_scholars_details = models.TextField(blank=True, null=True)

    sponsored_projects = models.CharField(max_length=1000, default="", null=True)
    memberships = models.CharField(max_length=1000, default="", null=True)
    awards = models.CharField(max_length=1000, default="", null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Programmes & Publications - {self.candidate.name}"
    

import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class AdminPasswordOTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]


