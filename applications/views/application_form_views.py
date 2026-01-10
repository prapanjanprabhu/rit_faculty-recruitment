from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from applications.models import (
    Candidate,
    Document,
    PositionApplication,
    Education,
    ResearchDetails,
    AcademicExperience,
    IndustryExperience,
    SponsoredProject,
    Qualification,
    Referee, Degree, Designation, Department, LevelOfEducation, Document_Type, Document, Certificate_Permission,
)
import os
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import FileSystemStorage
from applications.models import VisitorLog, ApplicationUsageLog
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage


from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
import json


from django.template.defaulttags import register

@register.filter
def index(indexable, i):
    try:
        return indexable[i]
    except (IndexError, TypeError):
        return ''

def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default



from django.shortcuts import render, redirect
from django.db import transaction
from django.core.files.storage import default_storage
from applications.models import (
    Candidate, PositionApplication, Designation,
    Department, Degree
)

def to_int(v, d=0):
    try: return int(v)
    except: return d


def individual_summary_sheet(request):
    if request.method == "POST":
        post = request.POST
        files = request.FILES

        data = request.session.get("summary", {})

        # simple fields (✅ name + age removed)
        data["present_organization"] = post.get("present_organization", "").strip()
        data["overall_specialization"] = post.get("overall_specialization", "").strip()
        data["specialization"] = data["overall_specialization"]

        data["languages"] = post.getlist("languages[]") or []
        data["community"] = post.get("community") or ""

        # departments (FK IDs, unchanged)
        data["departments"] = [to_int(x) for x in post.getlist("departments[]")]

        # position + designation (FK IDs)
        data["position_applied"] = to_int(post.get("position_applied"))
        data["present_designation"] = to_int(post.get("present_designation"))

        # qualifications
        qualifications = []
        q_qual = post.getlist("qualification[]")
        q_spec = post.getlist("specialization[]")
        q_inst = post.getlist("institute[]")
        q_year = post.getlist("year[]")

        for i in range(len(q_qual)):
            if q_qual[i] or q_spec[i] or q_inst[i]:
                qualifications.append({
                    "qualification": to_int(q_qual[i]),
                    "specialization": q_spec[i].strip(),
                    "institute": q_inst[i].strip(),
                    "year": safe_int(q_year[i]),
                })
        data["qualifications"] = qualifications

        # projects
        projects = []
        p_title = post.getlist("project_title[]")
        p_dur = post.getlist("project_duration[]")
        p_amt = post.getlist("project_amount[]")
        p_agency = post.getlist("project_agency[]")

        for i in range(len(p_title)):
            title = p_title[i].strip()
            if title:
                projects.append({
                    "title": title,
                    "duration": p_dur[i].strip(),
                    "amount": to_int(p_amt[i], 0),
                    "agency": p_agency[i].strip(),
                })
        data["projects"] = projects

        # numeric computed fields
        nums = [
            "assistant_professor_years","associate_professor_years",
            "professor_years","other_years",
            "research_experience_years","industry_experience_years",
            "journal_national","journal_international",
            "conference_national","conference_international",
            "mtech_completed","mtech_ongoing",
            "phd_completed","phd_ongoing",
        ]
        for f in nums:
            data[f] = to_int(post.get(f))

        data["journal_publications"] = (data["journal_national"] or 0) + (data["journal_international"] or 0)
        data["conference_publications"] = (data["conference_national"] or 0) + (data["conference_international"] or 0)
        data["students_guided_completed"] = (data["mtech_completed"] or 0) + (data["phd_completed"] or 0)
        data["students_guided_ongoing"] = (data["mtech_ongoing"] or 0) + (data["phd_ongoing"] or 0)

        # photo handling
        if files.get("photo"):
            if not request.session.session_key:
                request.session.save()
            tmp_path = default_storage.save(
                f"tmp/photo_{request.session.session_key}_{files['photo'].name}",
                files["photo"]
            )
            data["photo"] = tmp_path
            data["photo_original"] = files["photo"].name

        request.session["summary"] = data
        return redirect("individual_data_sheet")

    # GET
    data = request.session.get("summary", {})

    return render(
        request,
        "faculty_requirement/faculty/individual_summary_sheet.html",
        {
            "data": data,
            "designations": Designation.objects.all(),
            "departments": Department.objects.all(),
            "degrees": Degree.objects.all(),
        }
    )




def individual_data_sheet(request):
    if request.method == "POST":
        data = request.POST.dict()
        data.pop("csrfmiddlewaretoken", None)

       
        data.pop("community", None)
        data.pop("caste", None)
        data.pop("present_designation", None)
        data.pop("present_organization", None)

        request.session["personal"] = data
        return redirect("educational_qualifications")

    return render(
        request,
        "faculty_requirement/faculty/individual_data_sheet.html",
        {"data": request.session.get("personal", {})},
    )




from itertools import zip_longest
from django.shortcuts import render, redirect
from django.db import transaction
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.dateparse import parse_date
import os, json

def safe_int(v):
    try:
        return int(v)
    except:
        return None

def clean_str(v, none_if_empty=False):
    """
    Converts None -> "" (or None if none_if_empty=True)
    Strips spaces. Keeps actual text.
    """
    if v is None:
        return None if none_if_empty else ""
    s = str(v).strip()
    if none_if_empty and s == "":
        return None
    return s









from itertools import zip_longest

from itertools import zip_longest
from django.shortcuts import render, redirect

def educational_qualifications(request):
    if request.method == "POST":
        # pull all POST lists (must match your input names exactly)
        categories       = request.POST.getlist("category[]")
        degrees          = request.POST.getlist("degree[]")
        specializations  = request.POST.getlist("specialization[]")
        years            = request.POST.getlist("year_of_passing[]")
        institutions     = request.POST.getlist("institution[]")
        universities     = request.POST.getlist("university[]")
        percentages      = request.POST.getlist("percentage[]")
        classes          = request.POST.getlist("class_obtained[]")

        education_list = []

        # zip and build structured entries
        for cat, deg, spe, year, inst, uni, per, cls in zip_longest(
            categories,
            degrees,
            specializations,
            years,
            institutions,
            universities,
            percentages,
            classes,
            fillvalue=""
        ):
            # normalize
            cat  = clean_str(cat)
            deg  = clean_str(deg)
            spe  = clean_str(spe)
            year = clean_str(year)
            inst = clean_str(inst)
            uni  = clean_str(uni)
            per  = clean_str(per)
            cls  = clean_str(cls)

            # skip fully empty rows
            if not (cat or deg or spe or year or inst or uni or per or cls):
                continue

            education_list.append({
                # keep raw ids as strings in session; convert at DB save time
                "category": cat,
                "degree": deg,
                "specialization": spe,
                "year_of_passing": year,
                "institution": inst,
                "university": uni,
                "percentage": per,
                "class_obtained": cls,
            })

        # IMPORTANT: session must be json-serializable => list of dicts only ✅
        request.session["education"] = education_list

        # research block (unchanged, but sanitize)
        request.session["research_details"] = {
            "mode_ug": request.POST.get("mode_ug") or "",
            "mode_pg": request.POST.get("mode_pg") or "",
            "mode_phd": request.POST.get("mode_phd") or "",
            "arrears_ug": request.POST.get("arrears_ug") or "",
            "arrears_pg": request.POST.get("arrears_pg") or "",
            "gate_score": request.POST.get("gate_score") or "",
            "net_slet_score": request.POST.get("net_slet_score") or "",
            "me_thesis_title": request.POST.get("me_thesis_title") or "",
            "phd_thesis_title": request.POST.get("phd_thesis_title") or "",
        }

        # ensure session is committed
        request.session.modified = True

        return redirect("academic_and_industry_experience")

    # GET: rehydrate
    return render(
        request,
        "faculty_requirement/faculty/educational_qualifications.html",
        {
            "education": request.session.get("education", []),
            "research": request.session.get("research_details", {}),
            "levels": LevelOfEducation.objects.all().order_by("name"),
            "departments": Department.objects.select_related("degree").all(),
        }
    )



def academic_and_industry_experience(request):
    if request.method == "POST":

        academic_list = []
        for i in range(len(request.POST.getlist("academic_institution[]"))):
            academic_list.append({
                "institution": request.POST.getlist("academic_institution[]")[i],
                "designation": request.POST.getlist("academic_designation[]")[i],
                "joining_date": request.POST.getlist("academic_joining_date[]")[i],
                "relieving_date": request.POST.getlist("academic_relieving_date[]")[i],
                "years": request.POST.getlist("academic_years[]")[i],
                "months": request.POST.getlist("academic_months[]")[i],
                "days": request.POST.getlist("academic_days[]")[i],
            })

        industry_list = []
        for i in range(len(request.POST.getlist("industry_organization[]"))):
            industry_list.append({
                "organization": request.POST.getlist("industry_organization[]")[i],
                "designation": request.POST.getlist("industry_designation[]")[i],
                "nature_of_work": request.POST.getlist("industry_nature[]")[i],
                "joining_date": request.POST.getlist("industry_joining_date[]")[i],
                "relieving_date": request.POST.getlist("industry_relieving_date[]")[i],
                "years": request.POST.getlist("industry_years[]")[i],
                "months": request.POST.getlist("industry_months[]")[i],
                "days": request.POST.getlist("industry_days[]")[i],
            })

        request.session["academic_experience"] = academic_list
        request.session["industry_experience"] = industry_list

        return redirect("teaching_and_contributions")

    return render(
        request,
        "faculty_requirement/faculty/academic_and_industry_experience.html",
        {
            "academic": request.session.get("academic_experience", []),
            "industry": request.session.get("industry_experience", []),
        }
    )


from django.core.files.storage import default_storage

def teaching_and_contributions(request):
    data = request.session.get("teaching_entries", [])

    if request.method == "POST":
        rows = []

        # ------- UG -------
        ug_subject = request.POST.getlist("ug_subject[]")
        ug_pass = request.POST.getlist("ug_pass_percentage[]")
        ug_dept = request.POST.getlist("ug_department_contribution[]")
        ug_college = request.POST.getlist("ug_college_contribution[]")

        for i in range(len(ug_subject)):
            subject = (ug_subject[i] or "").strip()
            if not subject:
                continue
            rows.append({
                "level": "UG",
                "subject": subject,
                "pass_percentage": ug_pass[i] or "",
                "department_contribution": (ug_dept[i] or "").strip(),
                "college_contribution": (ug_college[i] or "").strip(),
            })

        # ------- PG -------
        pg_subject = request.POST.getlist("pg_subject[]")
        pg_pass = request.POST.getlist("pg_pass_percentage[]")
        pg_dept = request.POST.getlist("pg_department_contribution[]")
        pg_college = request.POST.getlist("pg_college_contribution[]")

        for i in range(len(pg_subject)):
            subject = (pg_subject[i] or "").strip()
            if not subject:
                continue
            rows.append({
                "level": "PG",
                "subject": subject,
                "pass_percentage": pg_pass[i] or "",
                "department_contribution": (pg_dept[i] or "").strip(),
                "college_contribution": (pg_college[i] or "").strip(),
            })

        request.session["teaching_entries"] = rows
        request.session.modified = True

        return redirect("programmes_and_publications")

    # split for UI
    ug_entries = [r for r in data if r.get("level") == "UG"]
    pg_entries = [r for r in data if r.get("level") == "PG"]

    return render(
        request,
        "faculty_requirement/faculty/teaching_and_contributions.html",
        {
            "ug_entries": ug_entries,
            "pg_entries": pg_entries,
        }
    )



def programmes_and_publications(request):
    if request.method == "POST":

        programme_types = request.POST.getlist("programme_type[]")
        programme_counts = request.POST.getlist("programme_count[]")

        # ✅ must exist in HTML as name="programme_category[]"
        programme_categories = request.POST.getlist("programme_category[]")

        request.session["programmes"] = [
            {
                "programme_type": (p or "").strip(),
                "category": (c or "").strip(),
                "count": to_int(cnt),
            }
            for p, c, cnt in zip(programme_types, programme_categories, programme_counts)
            if (p or "").strip()
        ]

        request.session["publications"] = [
            {"title": (t or "").strip(), "indexing": i}
            for t, i in zip(
                request.POST.getlist("publication_title[]"),
                request.POST.getlist("publication_indexing[]")
            )
            if (t or "").strip()
        ]

        request.session["research_publications"] = [
            {"details": (d or "").strip()}
            for d in request.POST.getlist("research_publication_details[]")
            if (d or "").strip()
        ]

        request.session["research_scholars"] = (request.POST.get("research_scholars_details", "") or "").strip()

        request.session["memberships"] = [
            {"details": (d or "").strip()}
            for d in request.POST.getlist("membership_details[]")
            if (d or "").strip()
        ]

        request.session["awards"] = [
            {"details": (d or "").strip()}
            for d in request.POST.getlist("award_details[]")
            if (d or "").strip()
        ]

        request.session["sponsored_projects"] = [
            {
                "title": (t or "").strip(),
                "status": s,
                "funding_agency": (a or "").strip(),
                "amount": safe_int(amt),
                "duration": d
            }
            for t, s, a, amt, d in zip(
                request.POST.getlist("project_title[]"),
                request.POST.getlist("project_status[]"),
                request.POST.getlist("funding_agency[]"),
                request.POST.getlist("project_amount[]"),
                request.POST.getlist("project_duration[]"),
            )
            if (t or "").strip()
        ]

        return redirect("referees_and_declaration")

    return render(request, "faculty_requirement/faculty/programmes_and_publications.html", {
        "programmes": request.session.get("programmes", []),
        "publications": request.session.get("publications", []),
        "research_publications": request.session.get("research_publications", []),
        "research_scholars": request.session.get("research_scholars", ""),
        "sponsored_projects": request.session.get("sponsored_projects", []),
        "memberships": request.session.get("memberships", []),
        "awards": request.session.get("awards", []),
    })





from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime

def to_int(v, d=0):
    try: return int(v)
    except: return d


from django.shortcuts import render, redirect
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.text import slugify
from django.utils.dateparse import parse_date
import json, os, re
from applications.models import ProgrammePublicationEntry

from applications.models import (
    Candidate, PositionApplication, Designation, Department, Degree,
    Qualification, SponsoredProject, Education,
    AcademicExperience, IndustryExperience,
     Referee, Document,
    Document_Type, LevelOfEducation
)


from datetime import date
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

import json
import os

def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return (
        today.year
        - dob.year
        - ((today.month, today.day) < (dob.month, dob.day))
    )

def safe_int(v):
    try: return int(v)
    except: return None

from datetime import date
from django.db import transaction
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import json, os
from applications.models import TeachingContributionEntry
def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return (
        today.year - dob.year
        - ((today.month, today.day) < (dob.month, dob.day))
    )

def safe_int(v):
    try: return int(v)
    except: return None


def referees_and_declaration(request):
    if request.method != "POST":
        return render(
            request,
            "faculty_requirement/faculty/referees_and_declaration.html",
            {"referees": []}
        )

    personal              = request.session.get("personal", {})
    summary               = request.session.get("summary", {})
    education             = request.session.get("education", [])
    research              = request.session.get("research_details", {})
    academic              = request.session.get("academic_experience", [])
    industry              = request.session.get("industry_experience", [])
    subjects              = request.session.get("subjects", [])
    contributions         = request.session.get("contributions", [])
    programmes            = request.session.get("programmes", [])
    publications          = request.session.get("publications", [])
    research_publications = request.session.get("research_publications", [])
    research_scholars     = request.session.get("research_scholars", "")
    sponsored_projects    = request.session.get("sponsored_projects", [])
    memberships           = request.session.get("memberships", [])
    awards                = request.session.get("awards", [])
    uploaded_docs         = request.session.get("uploaded_documents", {})

    candidate_id = request.session.get("candidate_id")

    with transaction.atomic():

        # =============================
        # CANDIDATE (CREATE OR UPDATE)
        # =============================
        if not candidate_id:
            candidate = Candidate.objects.create(
                name=personal.get("name"),
                email=personal.get("email"),
                phone_primary=personal.get("phone_primary"),
            )
            request.session["candidate_id"] = candidate.id
        else:
            candidate = Candidate.objects.select_for_update().get(id=candidate_id)

        candidate.name = personal.get("name")
        candidate.email = personal.get("email")
        candidate.gender = personal.get("gender")
        candidate.phone_primary = personal.get("phone_primary")
        candidate.phone_secondary = personal.get("phone_secondary")
        candidate.address = personal.get("address")
        candidate.caste = personal.get("caste")
        # candidate.mother_name_and_occupation = personal.get("mother_name_and_occupation")


        candidate.marital_status = (personal.get("marital_status") or "").strip() or None
        candidate.pan_number = (personal.get("pan_number") or "").strip() or None

        dob = personal.get("date_of_birth")
        candidate.date_of_birth = parse_date(dob) if dob else None
        candidate.age = calculate_age(candidate.date_of_birth)

        candidate.total_experience_years = safe_int(personal.get("total_experience_years"))
        candidate.present_post_years = safe_int(personal.get("present_post_years"))

        candidate.save()

        # =============================
        # PHOTO
        # =============================
        tmp = summary.get("photo")
        original = summary.get("photo_original")
        if tmp and default_storage.exists(tmp):
            safe_name = slugify(candidate.name or "candidate")
            fname = original or "profile.jpg"
            with default_storage.open(tmp, "rb") as f:
                candidate.photo.save(
                    f"{safe_name}-{candidate.id}/{fname}",
                    ContentFile(f.read()),
                    save=True
                )
            default_storage.delete(tmp)

        # =============================
        # DOCUMENTS
        # =============================
        Document.objects.filter(candidate=candidate).delete()
        for doc_id, tmp_path in uploaded_docs.items():
            if default_storage.exists(tmp_path):
                doc_type = Document_Type.objects.filter(id=int(doc_id)).first()
                if doc_type:
                    ext = os.path.splitext(tmp_path)[1]
                    safe_name = slugify(candidate.name or "candidate")
                    filename = f"{safe_name}-{candidate.id}_{doc_type.document_type}{ext}"
                    with default_storage.open(tmp_path, "rb") as f:
                        Document.objects.create(
                            candidate=candidate,
                            document_type=doc_type,
                            file=ContentFile(
                                f.read(),
                                name=f"candidate/{safe_name}-{candidate.id}/documents/{filename}"
                            )
                        )
                default_storage.delete(tmp_path)

        # =============================
        # POSITION APPLICATION
        # =============================
        community_value  = summary.get("community")
        languages_value  = summary.get("languages", [])
        designation_obj  = Designation.objects.filter(id=summary.get("present_designation")).first()

        position_app, _ = PositionApplication.objects.update_or_create(
            candidate=candidate,
            defaults={
                "position_applied_id": summary.get("position_applied"),
                "community": community_value,
                "languages": languages_value,
                "present_designation": designation_obj.name if designation_obj else None,
                "present_organization": summary.get("present_organization"),
                "specialization": summary.get("overall_specialization"),
                "assistant_professor_years": safe_int(summary.get("assistant_professor_years")),
                "associate_professor_years": safe_int(summary.get("associate_professor_years")),
                "professor_years": safe_int(summary.get("professor_years")),
                "other_years": safe_int(summary.get("other_years")),
                "research_experience_years": safe_int(summary.get("research_experience_years")),
                "industry_experience_years": safe_int(summary.get("industry_experience_years")),
                "journal_publications": safe_int(summary.get("journal_publications")),
                "conference_publications": safe_int(summary.get("conference_publications")),
                "students_guided_completed": safe_int(summary.get("students_guided_completed")),
                "students_guided_ongoing": safe_int(summary.get("students_guided_ongoing")),
            }
        )

        position_app.departments.set(
            Department.objects.filter(id__in=summary.get("departments", []))
        )

        # =============================
        # QUALIFICATIONS
        # =============================
        Qualification.objects.filter(candidate=candidate).delete()
        for q in summary.get("qualifications", []):
            Qualification.objects.create(
                candidate=candidate,
                qualification_id=q.get("qualification"),
                specialization=q.get("specialization"),
                institute=q.get("institute"),
                year=safe_int(q.get("year")),
            )

        # =============================
        # SPONSORED PROJECTS (if you still use this table elsewhere, keep)
        # =============================
        SponsoredProject.objects.filter(candidate=candidate).delete()
        for p in sponsored_projects:
            SponsoredProject.objects.create(
                candidate=candidate,
                title=p.get("title"),
                duration=p.get("duration"),
                amount=safe_int(p.get("amount")) or 0,
                agency=p.get("funding_agency"),
            )

        # =============================
        # EDUCATION
        # =============================
        Education.objects.filter(candidate=candidate).delete()
        for e in education:
            Education.objects.create(
                candidate=candidate,
                category=LevelOfEducation.objects.filter(id=safe_int(e.get("category"))).first(),
                degree=Degree.objects.filter(id=safe_int(e.get("degree"))).first(),
                specialization=e.get("specialization"),
                year_of_passing=e.get("year_of_passing"),
                institution=e.get("institution"),
                university=e.get("university"),
                percentage=e.get("percentage"),
                class_obtained=e.get("class_obtained"),
            )

        # =============================
        # RESEARCH DETAILS
        # =============================
        ResearchDetails.objects.filter(candidate=candidate).delete()
        if research:
            ResearchDetails.objects.create(
                candidate=candidate,
                mode_ug=research.get("mode_ug"),
                mode_pg=research.get("mode_pg"),
                mode_phd=research.get("mode_phd"),
                arrears_ug=safe_int(research.get("arrears_ug")),
                arrears_pg=safe_int(research.get("arrears_pg")),
                gate_score=research.get("gate_score"),
                net_slet_score=research.get("net_slet_score"),
                me_thesis_title=research.get("me_thesis_title"),
                phd_thesis_title=research.get("phd_thesis_title"),
            )

        # =============================
        # EXPERIENCE
        # =============================
        AcademicExperience.objects.filter(candidate=candidate).delete()
        for a in academic:
            AcademicExperience.objects.create(candidate=candidate, **a)

        IndustryExperience.objects.filter(candidate=candidate).delete()
        for i in industry:
            IndustryExperience.objects.create(candidate=candidate, **i)

        # =============================
        # TEACHING + CONTRIBUTIONS
        # =============================
        TeachingContributionEntry.objects.filter(candidate=candidate).delete()

        teaching_entries = request.session.get("teaching_entries", [])
        bulk = []

        for r in teaching_entries:
            bulk.append(TeachingContributionEntry(
                candidate=candidate,
                level=r.get("level"),
                subject=r.get("subject"),
                pass_percentage=safe_int(r.get("pass_percentage")),
                department_contribution=r.get("department_contribution"),
                college_contribution=r.get("college_contribution"),
            ))

        if bulk:
            TeachingContributionEntry.objects.bulk_create(bulk)

        # ==========================================================
        # PROGRAMMES + PUBLICATIONS (✅ ONE TABLE, ✅ NO JSON, ✅ NORMAL)
        # ==========================================================
        # IMPORTANT:
        # - Remove usage of Programme, Publication, ProgrammesPublications for this page
        # - Store everything in ProgrammePublicationEntry

        ProgrammePublicationEntry.objects.filter(candidate=candidate).delete()

        rows = []

        # Programmes
        for p in programmes:
            if (p.get("programme_type") or "").strip():
                rows.append(ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="PROGRAMME",
                    programme_type=p.get("programme_type"),
                    programme_category=p.get("category"),
                    programme_count=safe_int(p.get("count")),
                ))

        # Publications (General)
        for pub in publications:
            if (pub.get("title") or "").strip():
                rows.append(ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="PUBLICATION",
                    publication_title=pub.get("title"),
                    publication_indexing=pub.get("indexing"),
                ))

        # Research publications (Scopus indexed)
        for rp in research_publications:
            if (rp.get("details") or "").strip():
                rows.append(ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="RESEARCH_PUB",
                    details=rp.get("details"),
                ))

        # Research scholars (single text)
        if (research_scholars or "").strip():
            rows.append(ProgrammePublicationEntry(
                candidate=candidate,
                entry_type="RESEARCH_SCHOLARS",
                details=research_scholars,
            ))

        # Sponsored projects (store in same single table also)
        for sp in sponsored_projects:
            if (sp.get("title") or "").strip():
                rows.append(ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="SPONSORED_PROJECT",
                    project_title=sp.get("title"),
                    project_status=sp.get("status"),
                    project_funding_agency=sp.get("funding_agency"),
                    project_amount=safe_int(sp.get("amount")),
                    project_duration=sp.get("duration"),
                ))

        # Memberships
        for m in memberships:
            if (m.get("details") or "").strip():
                rows.append(ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="MEMBERSHIP",
                    details=m.get("details"),
                ))

        # Awards
        for a in awards:
            if (a.get("details") or "").strip():
                rows.append(ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="AWARD",
                    details=a.get("details"),
                ))

        if rows:
            ProgrammePublicationEntry.objects.bulk_create(rows)

        # =============================
        # REFEREES
        # =============================
        Referee.objects.filter(candidate=candidate).delete()
        for n, d, o, c in zip(
            request.POST.getlist("ref_name[]"),
            request.POST.getlist("ref_designation[]"),
            request.POST.getlist("ref_organization[]"),
            request.POST.getlist("ref_contact[]"),
        ):
            if n.strip():
                Referee.objects.create(
                    candidate=candidate,
                    name=n,
                    designation=d,
                    organization=o,
                    contact_number=c,
                )

    request.session.flush()
    return redirect("application_success")





def application_success(request):
    return render(request, "faculty_requirement/faculty/application_success.html")



