# views_faculty_requirement.py  (keep as ONE clean file)
# -----------------------------------------------------
from datetime import date
import os
from itertools import zip_longest

from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template.defaulttags import register

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
    Referee,
    Degree,
    Designation,
    Department,
    LevelOfEducation,
    Document_Type,
    Certificate_Permission,
    EducationCertificate,
    ProgrammePublicationEntry,
    TeachingContributionEntry,
)

# -----------------------------
# Template helpers
# -----------------------------
@register.filter
def index(indexable, i):
    try:
        return indexable[i]
    except (IndexError, TypeError):
        return ""


# -----------------------------
# Safe converters
# -----------------------------
def safe_int2(v, default=0):
    """
    Safe int -> returns default if None/blank/invalid
    (Used in summary sheet + numeric fields)
    """
    try:
        if v is None:
            return default
        s = str(v).strip()
        if s == "":
            return default
        return int(s)
    except (TypeError, ValueError):
        return default


def safe_int(v):
    """
    Safe int -> returns None if invalid (used while saving DB nullable ints)
    """
    try:
        if v is None:
            return None
        s = str(v).strip()
        if s == "":
            return None
        return int(s)
    except (TypeError, ValueError):
        return None


def to_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


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


def calculate_age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


# =====================================================
# 1) SUMMARY SHEET  (projects collected here)
# =====================================================
def individual_summary_sheet(request):
    if request.method == "POST":
        post = request.POST
        files = request.FILES

        data = request.session.get("summary", {})

        data["present_organization"] = (post.get("present_organization", "") or "").strip()
        data["overall_specialization"] = (post.get("overall_specialization", "") or "").strip()
        data["specialization"] = data["overall_specialization"]

        # departments (MULTI)
        dept_ids = []
        for x in post.getlist("departments[]"):
            v = safe_int2(x, 0)
            if v:
                dept_ids.append(v)
        data["departments"] = dept_ids

        # position + designation (FK IDs)
        data["position_applied"] = safe_int2(post.get("position_applied"), 0) or None
        data["present_designation"] = safe_int2(post.get("present_designation"), 0) or None

        # arrears
        data["arrears_ug"] = safe_int2(post.get("arrears_ug"), 0)
        data["arrears_pg"] = safe_int2(post.get("arrears_pg"), 0)

        # ✅ NEW: Professional Experience fields (store in SUMMARY -> later save to PositionApplication)
        data["total_experience_years"] = safe_int2(post.get("total_experience_years"), 0)
        data["present_post_years"] = safe_int2(post.get("present_post_years"), 0)

        # qualifications
        qualifications = []
        q_qual = post.getlist("qualification[]")
        q_spec = post.getlist("specialization[]")
        q_inst = post.getlist("institute[]")
        q_year = post.getlist("year[]")

        for i in range(len(q_qual)):
            if (q_qual[i] or "").strip() or (q_spec[i] or "").strip() or (q_inst[i] or "").strip():
                qualifications.append(
                    {
                        "qualification": safe_int2(q_qual[i], 0) or None,
                        "specialization": (q_spec[i] or "").strip(),
                        "institute": (q_inst[i] or "").strip(),
                        "year": safe_int2(q_year[i], 0) or None,
                    }
                )
        data["qualifications"] = qualifications

        # ✅ Sponsored Projects (Completed Sponsored Projects table) stored in SUMMARY
        projects = []
        p_title = post.getlist("project_title[]")
        p_dur = post.getlist("project_duration[]")
        p_amt = post.getlist("project_amount[]")
        p_agency = post.getlist("project_agency[]")
        p_status = post.getlist("project_status[]")  # ✅ NEW

        for i in range(len(p_title)):
            title = (p_title[i] or "").strip()
            if not title:
                continue

            status_val = (p_status[i] if i < len(p_status) else "completed") or "completed"
            status_val = status_val.strip().lower()
            if status_val not in ("completed", "ongoing"):
                status_val = "completed"

            projects.append(
                {
                    "title": title,
                    "duration": (p_dur[i] or "").strip(),
                    "amount": safe_int2(p_amt[i], 0),
                    "agency": (p_agency[i] or "").strip(),
                    "status": status_val,  # ✅ NEW
                }
            )

        data["projects"] = projects

        nums = [
            "assistant_professor_years",
            "associate_professor_years",
            "professor_years",
            "other_years",
            "research_experience_years",
            "industry_experience_years",
            "journal_national",
            "journal_international",
            "conference_national",
            "conference_international",
            "mtech_completed",
            "mtech_ongoing",
            "phd_completed",
            "phd_ongoing",
        ]
        for f in nums:
            data[f] = safe_int2(post.get(f), 0)

        data["journal_publications"] = (data.get("journal_national") or 0) + (data.get("journal_international") or 0)
        data["conference_publications"] = (data.get("conference_national") or 0) + (
            data.get("conference_international") or 0
        )
        data["students_guided_completed"] = (data.get("mtech_completed") or 0) + (data.get("phd_completed") or 0)
        data["students_guided_ongoing"] = (data.get("mtech_ongoing") or 0) + (data.get("phd_ongoing") or 0)

        # photo handling (tmp)
        if files.get("photo"):
            if not request.session.session_key:
                request.session.save()
            tmp_path = default_storage.save(
                f"tmp/photo_{request.session.session_key}_{files['photo'].name}",
                files["photo"],
            )
            data["photo"] = tmp_path
            data["photo_original"] = files["photo"].name
            data["photo_name"] = files["photo"].name

        request.session["summary"] = data
        request.session.modified = True
        return redirect("individual_data_sheet")

    data = request.session.get("summary", {})
    return render(
        request,
        "faculty_requirement/faculty/individual_summary_sheet.html",
        {
            "data": data,
            "designations": Designation.objects.all(),
            "departments": Department.objects.all(),
            "degrees": Degree.objects.all(),
        },
    )

# =====================================================
# 2) INDIVIDUAL DATA SHEET
# =====================================================
def individual_data_sheet(request):
    if request.method == "POST":
        data = request.POST.dict()
        data.pop("csrfmiddlewaretoken", None)

        # ✅ multi select: must use getlist
        data["languages"] = request.POST.getlist("languages[]") or []
        data["community"] = (request.POST.get("community") or "").strip()

        request.session["personal"] = data
        request.session.modified = True
        return redirect("educational_qualifications")

    return render(
        request,
        "faculty_requirement/faculty/individual_data_sheet.html",
        {"data": request.session.get("personal", {})},
    )


# =====================================================
# 3) EDUCATIONAL QUALIFICATIONS
# =====================================================
def educational_qualifications(request):
    """
    RULES:
    ✅ default show UG + PG blocks
    ✅ must submit UG + PG qualifications
    ✅ must upload UG + PG certificates
    ✅ if selected dept requires extra cert (PhD/SSLC/HSC etc) -> must upload those too
    ✅ If GATE/NET score entered -> corresponding certificate must be uploaded
    """

    summary = request.session.get("summary", {})
    selected_dept_ids = summary.get("departments", [])

    def infer_level_from_docname(name: str):
        n = (name or "").lower()
        if "sslc" in n:
            return "SSLC"
        if "hsc" in n or "higher secondary" in n:
            return "HSC"
        if "ug" in n or "undergraduate" in n:
            return "UG"
        if "pg" in n or "postgraduate" in n:
            return "PG"
        if "phd" in n or "doctorate" in n:
            return "PhD"
        return None

    required_levels = {"UG", "PG"}

    if selected_dept_ids:
        req_docs = (
            Certificate_Permission.objects.filter(department_id__in=selected_dept_ids, is_required=True)
            .select_related("document_type")
        )
        for p in req_docs:
            lvl = infer_level_from_docname(p.document_type.document_type)
            if lvl:
                required_levels.add(lvl)

    education_rows = request.session.get("education", [])
    tmp_certs = request.session.get("education_tmp_certificates", {})

    research = request.session.get("research_details", {}) or {}
    research_tmp = request.session.get("research_tmp_uploads", {}) or {}

    if request.method == "POST":
        categories = request.POST.getlist("category[]")
        degrees = request.POST.getlist("degree[]")
        specializations = request.POST.getlist("specialization[]")
        years = request.POST.getlist("year_of_passing[]")
        institutions = request.POST.getlist("institution[]")
        universities = request.POST.getlist("university[]")
        percentages = request.POST.getlist("percentage[]")
        classes = request.POST.getlist("class_obtained[]")

        cert_files = request.FILES.getlist("edu_certificate[]")

        new_rows = []
        new_tmp_certs = dict(tmp_certs)

        for idx, (cat, deg, spe, year, inst, uni, per, cls) in enumerate(
            zip_longest(
                categories,
                degrees,
                specializations,
                years,
                institutions,
                universities,
                percentages,
                classes,
                fillvalue="",
            )
        ):
            cat = clean_str(cat)
            deg = clean_str(deg)
            spe = clean_str(spe)
            year = clean_str(year)
            inst = clean_str(inst)
            uni = clean_str(uni)
            per = clean_str(per)
            cls = clean_str(cls)

            if not (cat or deg or spe or year or inst or uni or per or cls):
                continue

            level_obj = LevelOfEducation.objects.filter(id=safe_int(cat)).first()
            level_name = (level_obj.name if level_obj else "").strip()

            if idx < len(cert_files) and cert_files[idx]:
                f = cert_files[idx]
                if not request.session.session_key:
                    request.session.save()
                tmp_path = default_storage.save(
                    f"tmp/edu_{request.session.session_key}_{idx}_{f.name}",
                    f,
                )
                new_tmp_certs[str(idx)] = tmp_path

            new_rows.append(
                {
                    "category": cat,
                    "degree": deg,
                    "specialization": spe,
                    "year_of_passing": year,
                    "institution": inst,
                    "university": uni,
                    "percentage": per,
                    "class_obtained": cls,
                    "level_name": level_name,
                    "certificate_name": os.path.basename(new_tmp_certs.get(str(idx), ""))
                    if new_tmp_certs.get(str(idx))
                    else "",
                }
            )

        # ✅ required levels present
        present_levels = {(r.get("level_name") or "").strip() for r in new_rows}
        missing_levels = [lvl for lvl in required_levels if lvl not in present_levels]
        if missing_levels:
            return render(
                request,
                "faculty_requirement/faculty/educational_qualifications.html",
                {
                    "education": new_rows,
                    "research": research,
                    "research_tmp": research_tmp,
                    "levels": LevelOfEducation.objects.all().order_by("name"),
                    "departments": Department.objects.select_related("degree").all(),
                    "required_levels": sorted(required_levels),
                    "error": f"Missing required qualification(s): {', '.join(missing_levels)}",
                    "degrees": Degree.objects.all(),
                },
            )

        # ✅ required level certificates present
        level_to_has_cert = {}
        for i, r in enumerate(new_rows):
            lvl = (r.get("level_name") or "").strip()
            has = bool(new_tmp_certs.get(str(i)))
            if lvl:
                level_to_has_cert[lvl] = level_to_has_cert.get(lvl, False) or has

        missing_certs = [lvl for lvl in required_levels if not level_to_has_cert.get(lvl)]
        if missing_certs:
            return render(
                request,
                "faculty_requirement/faculty/educational_qualifications.html",
                {
                    "education": new_rows,
                    "research": research,
                    "research_tmp": research_tmp,
                    "levels": LevelOfEducation.objects.all().order_by("name"),
                    "departments": Department.objects.select_related("degree").all(),
                    "required_levels": sorted(required_levels),
                    "error": f"Upload required certificate(s): {', '.join(missing_certs)}",
                    "degrees": Degree.objects.all(),
                },
            )

        # ===========================
        # ✅ GATE / NET-SLET (score -> cert mandatory)
        # ===========================
        gate_score = (request.POST.get("gate_score") or "").strip()
        net_score = (request.POST.get("net_slet_score") or "").strip()

        gate_file = request.FILES.get("gate_certificate")
        net_file = request.FILES.get("net_slet_certificate")

        gate_has_existing_tmp = bool(research_tmp.get("gate_certificate_tmp"))
        net_has_existing_tmp = bool(research_tmp.get("net_slet_certificate_tmp"))

        if gate_score and not (gate_file or gate_has_existing_tmp):
            return render(
                request,
                "faculty_requirement/faculty/educational_qualifications.html",
                {
                    "education": new_rows,
                    "research": {
                        **(research or {}),
                        "gate_score": gate_score,
                        "net_slet_score": net_score,
                        "mode_ug": request.POST.get("mode_ug") or "",
                        "mode_pg": request.POST.get("mode_pg") or "",
                        "mode_phd": request.POST.get("mode_phd") or "",
                        "phd_thesis_title": request.POST.get("phd_thesis_title") or "",
                    },
                    "research_tmp": research_tmp,
                    "levels": LevelOfEducation.objects.all().order_by("name"),
                    "departments": Department.objects.select_related("degree").all(),
                    "required_levels": sorted(required_levels),
                    "error": "GATE score entered. Please upload the GATE certificate.",
                    "degrees": Degree.objects.all(),
                },
            )

        if net_score and not (net_file or net_has_existing_tmp):
            return render(
                request,
                "faculty_requirement/faculty/educational_qualifications.html",
                {
                    "education": new_rows,
                    "research": {
                        **(research or {}),
                        "gate_score": gate_score,
                        "net_slet_score": net_score,
                        "mode_ug": request.POST.get("mode_ug") or "",
                        "mode_pg": request.POST.get("mode_pg") or "",
                        "mode_phd": request.POST.get("mode_phd") or "",
                        "phd_thesis_title": request.POST.get("phd_thesis_title") or "",
                    },
                    "research_tmp": research_tmp,
                    "levels": LevelOfEducation.objects.all().order_by("name"),
                    "departments": Department.objects.select_related("degree").all(),
                    "required_levels": sorted(required_levels),
                    "error": "NET/SLET score entered. Please upload the NET/SLET certificate.",
                    "degrees": Degree.objects.all(),
                },
            )

        # Save tmp uploads (if uploaded now)
        new_research_tmp = dict(research_tmp)
        if not request.session.session_key:
            request.session.save()

        if gate_file:
            tmp_path = default_storage.save(
                f"tmp/gate_{request.session.session_key}_{gate_file.name}",
                gate_file,
            )
            new_research_tmp["gate_certificate_tmp"] = tmp_path
            new_research_tmp["gate_certificate_name"] = gate_file.name

        if net_file:
            tmp_path = default_storage.save(
                f"tmp/net_{request.session.session_key}_{net_file.name}",
                net_file,
            )
            new_research_tmp["net_slet_certificate_tmp"] = tmp_path
            new_research_tmp["net_slet_certificate_name"] = net_file.name

        request.session["research_details"] = {
            "mode_ug": request.POST.get("mode_ug") or "",
            "mode_pg": request.POST.get("mode_pg") or "",
            "mode_phd": request.POST.get("mode_phd") or "",
            "gate_score": gate_score,
            "net_slet_score": net_score,
            "phd_thesis_title": request.POST.get("phd_thesis_title") or "",
        }
        request.session["research_tmp_uploads"] = new_research_tmp

        request.session["education"] = new_rows
        request.session["education_tmp_certificates"] = new_tmp_certs
        request.session.modified = True
        return redirect("academic_and_industry_experience")

    # ✅ GET default UG + PG
    if not education_rows:
        ug = LevelOfEducation.objects.filter(name__iexact="UG").first()
        pg = LevelOfEducation.objects.filter(name__iexact="PG").first()
        education_rows = [
            {
                "category": str(ug.id) if ug else "",
                "degree": "",
                "specialization": "",
                "year_of_passing": "",
                "institution": "",
                "university": "",
                "percentage": "",
                "class_obtained": "",
                "level_name": "UG",
                "certificate_name": "",
            },
            {
                "category": str(pg.id) if pg else "",
                "degree": "",
                "specialization": "",
                "year_of_passing": "",
                "institution": "",
                "university": "",
                "percentage": "",
                "class_obtained": "",
                "level_name": "PG",
                "certificate_name": "",
            },
        ]

    return render(
        request,
        "faculty_requirement/faculty/educational_qualifications.html",
        {
            "education": education_rows,
            "research": request.session.get("research_details", {}),
            "research_tmp": request.session.get("research_tmp_uploads", {}),
            "levels": LevelOfEducation.objects.all().order_by("name"),
            "departments": Department.objects.select_related("degree").all(),
            "required_levels": sorted(required_levels),
            "error": None,
            "degrees": Degree.objects.all(),
        },
    )


def academic_and_industry_experience(request):
    if request.method == "POST":
        # ---------------- ACADEMIC ----------------
        academic_list = []
        for i in range(len(request.POST.getlist("academic_institution[]"))):
            academic_list.append(
                {
                    "institution": request.POST.getlist("academic_institution[]")[i],
                    "designation": request.POST.getlist("academic_designation[]")[i],
                    "joining_date": request.POST.getlist("academic_joining_date[]")[i],
                    "relieving_date": request.POST.getlist("academic_relieving_date[]")[i],
                    "years": request.POST.getlist("academic_years[]")[i],
                    "months": request.POST.getlist("academic_months[]")[i],
                    "days": request.POST.getlist("academic_days[]")[i],
                }
            )

        # ---------------- INDUSTRY ----------------
        industry_list = []
        for i in range(len(request.POST.getlist("industry_organization[]"))):
            industry_list.append(
                {
                    "organization": request.POST.getlist("industry_organization[]")[i],
                    "designation": request.POST.getlist("industry_designation[]")[i],
                    "nature_of_work": request.POST.getlist("industry_nature[]")[i],
                    "joining_date": request.POST.getlist("industry_joining_date[]")[i],
                    "relieving_date": request.POST.getlist("industry_relieving_date[]")[i],
                    "years": request.POST.getlist("industry_years[]")[i],
                    "months": request.POST.getlist("industry_months[]")[i],
                    "days": request.POST.getlist("industry_days[]")[i],
                }
            )

        # ---------------- ✅ PROFESSIONAL ACTIVITY ----------------
        pa_list = []
        pa_award = request.POST.getlist("pa_award[]")
        pa_particular = request.POST.getlist("pa_particular[]")
        pa_agency = request.POST.getlist("pa_agency[]")
        pa_year = request.POST.getlist("pa_year[]")

        max_len = max(len(pa_award), len(pa_particular), len(pa_agency), len(pa_year), 0)
        for i in range(max_len):
            award = (pa_award[i] if i < len(pa_award) else "").strip()
            particular = (pa_particular[i] if i < len(pa_particular) else "").strip()
            agency = (pa_agency[i] if i < len(pa_agency) else "").strip()
            year = (pa_year[i] if i < len(pa_year) else "").strip()

            # skip fully empty row
            if not (award or particular or agency or year):
                continue

            pa_list.append(
                {
                    "award": award,
                    "particular": particular,
                    "agency": agency,
                    "year": safe_int2(year, 0) or None,  # uses your helper
                }
            )

        request.session["academic_experience"] = academic_list
        request.session["industry_experience"] = industry_list
        request.session["professional_activities"] = pa_list
        request.session.modified = True
        return redirect("teaching_and_contributions")

    return render(
        request,
        "faculty_requirement/faculty/academic_and_industry_experience.html",
        {
            "academic": request.session.get("academic_experience", []),
            "industry": request.session.get("industry_experience", []),
            "professional_activities": request.session.get("professional_activities", []),
        },
    )


# =====================================================
# 5) TEACHING + CONTRIBUTIONS
# =====================================================
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
            rows.append(
                {
                    "level": "UG",
                    "subject": subject,
                    "pass_percentage": ug_pass[i] or "",
                    "department_contribution": (ug_dept[i] or "").strip(),
                    "college_contribution": (ug_college[i] or "").strip(),
                }
            )

        # ------- PG -------
        pg_subject = request.POST.getlist("pg_subject[]")
        pg_pass = request.POST.getlist("pg_pass_percentage[]")
        pg_dept = request.POST.getlist("pg_department_contribution[]")
        pg_college = request.POST.getlist("pg_college_contribution[]")

        for i in range(len(pg_subject)):
            subject = (pg_subject[i] or "").strip()
            if not subject:
                continue
            rows.append(
                {
                    "level": "PG",
                    "subject": subject,
                    "pass_percentage": pg_pass[i] or "",
                    "department_contribution": (pg_dept[i] or "").strip(),
                    "college_contribution": (pg_college[i] or "").strip(),
                }
            )

        request.session["teaching_entries"] = rows
        request.session.modified = True
        return redirect("programmes_and_publications")

    ug_entries = [r for r in data if r.get("level") == "UG"]
    pg_entries = [r for r in data if r.get("level") == "PG"]

    return render(
        request,
        "faculty_requirement/faculty/teaching_and_contributions.html",
        {
            "ug_entries": ug_entries,
            "pg_entries": pg_entries,
        },
    )


# =====================================================
# 6) PROGRAMMES + PUBLICATIONS  (NO sponsored projects here)
# =====================================================
def programmes_and_publications(request):
    if request.method == "POST":
        programme_types = request.POST.getlist("programme_type[]")
        programme_counts = request.POST.getlist("programme_count[]")
        programme_categories = request.POST.getlist("programme_category[]")

        request.session["programmes"] = [
            {"programme_type": (p or "").strip(), "category": (c or "").strip(), "count": to_int(cnt)}
            for p, c, cnt in zip(programme_types, programme_categories, programme_counts)
            if (p or "").strip()
        ]

        request.session["publications"] = [
            {"title": (t or "").strip(), "indexing": i}
            for t, i in zip(
                request.POST.getlist("publication_title[]"),
                request.POST.getlist("publication_indexing[]"),
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

        # ✅ ensure old key removed (XIV removed)
        request.session.pop("sponsored_projects", None)

        request.session.modified = True
        return redirect("referees_and_declaration")

    return render(
        request,
        "faculty_requirement/faculty/programmes_and_publications.html",
        {
            "programmes": request.session.get("programmes", []),
            "publications": request.session.get("publications", []),
            "research_publications": request.session.get("research_publications", []),
            "research_scholars": request.session.get("research_scholars", ""),
            "memberships": request.session.get("memberships", []),
            "awards": request.session.get("awards", []),
        },
    )


# =====================================================
# 7) REFEREES + DECLARATION  (FINAL SAVE)
# =====================================================
# views_faculty_requirement.py

import os
from datetime import date
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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
    Referee,
    Degree,
    Designation,
    Department,
    LevelOfEducation,
    Document_Type,
    Certificate_Permission,
    EducationCertificate,
    ProgrammePublicationEntry,
    TeachingContributionEntry,
    ProfessionalActivity,  # ✅ add this if you created the model
)


def referees_and_declaration(request):
    """
    FINAL STEP:
    - Shows Referees form on GET
    - On POST:
        - Creates/updates Candidate
        - Moves temp uploads to final
        - Saves all related sections + referees
        - Flush session and redirects to success
    """

    # --------------------------
    # GET -> Show form
    # --------------------------
    if request.method != "POST":
        # If you want prefill, keep session referees (optional)
        session_refs = request.session.get("referees", []) or []
        if not session_refs:
            session_refs = [
                {"name": "", "designation": "", "organization": "", "email": "", "whatsapp": ""}
            ]

        return render(
            request,
            "faculty_requirement/faculty/referees_and_declaration.html",
            {"referees": session_refs},
        )

    # --------------------------
    # POST -> Final Save
    # --------------------------
    personal = request.session.get("personal", {}) or {}
    summary = request.session.get("summary", {}) or {}
    education = request.session.get("education", []) or {}
    research = request.session.get("research_details", {}) or {}
    academic = request.session.get("academic_experience", []) or []
    industry = request.session.get("industry_experience", []) or []
    programmes = request.session.get("programmes", []) or []
    publications = request.session.get("publications", []) or []
    research_publications = request.session.get("research_publications", []) or []
    research_scholars = request.session.get("research_scholars", "") or ""
    memberships = request.session.get("memberships", []) or []
    awards = request.session.get("awards", []) or []
    uploaded_docs = request.session.get("uploaded_documents", {}) or {}

    # ✅ Sponsored Projects from Summary Sheet
    summary_projects = summary.get("projects", []) or []

    # ✅ Professional Activity from Experience page session
    professional_activities = request.session.get("professional_activities", []) or []

    tmp_certs = request.session.get("education_tmp_certificates", {}) or {}
    research_tmp = request.session.get("research_tmp_uploads", {}) or {}

    candidate_id = request.session.get("candidate_id")

    # ✅ Declaration must be checked
    declaration = request.POST.get("declaration") == "1"
    if not declaration:
        # Keep user on page with error (do not lose rows)
        posted_refs = []
        for n, d, o, em, wa in zip(
            request.POST.getlist("ref_name[]"),
            request.POST.getlist("ref_designation[]"),
            request.POST.getlist("ref_organization[]"),
            request.POST.getlist("ref_email[]"),
            request.POST.getlist("ref_whatsapp[]"),
        ):
            posted_refs.append(
                {
                    "name": n, "designation": d, "organization": o, "email": em, "whatsapp": wa
                }
            )
        if not posted_refs:
            posted_refs = [{"name": "", "designation": "", "organization": "", "email": "", "whatsapp": ""}]

        return render(
            request,
            "faculty_requirement/faculty/referees_and_declaration.html",
            {
                "referees": posted_refs,
                "error": "Please accept the declaration to submit your application.",
            },
        )

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
        candidate.community = personal.get("community")
        candidate.languages = personal.get("languages", [])
        candidate.marital_status = (personal.get("marital_status") or "").strip() or None
        candidate.pan_number = (personal.get("pan_number") or "").strip() or None

        dob = personal.get("date_of_birth")
        candidate.date_of_birth = parse_date(dob) if dob else None
        candidate.age = calculate_age(candidate.date_of_birth)



        candidate.save()

        # =============================
        # PHOTO (tmp -> final)
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
                    save=True,
                )
            default_storage.delete(tmp)

        # =============================
        # DOCUMENTS
        # =============================
        Document.objects.filter(candidate=candidate).delete()
        for doc_id, tmp_path in uploaded_docs.items():
            if tmp_path and default_storage.exists(tmp_path):
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
                                name=f"candidate/{safe_name}-{candidate.id}/documents/{filename}",
                            ),
                        )
                default_storage.delete(tmp_path)

        # =============================
        # POSITION APPLICATION
        # =============================
        designation_obj = Designation.objects.filter(id=summary.get("present_designation")).first()

        position_app, _ = PositionApplication.objects.update_or_create(
            candidate=candidate,
            defaults={
                "position_applied_id": summary.get("position_applied"),
                "present_designation": designation_obj.name if designation_obj else None,
                "present_organization": summary.get("present_organization"),
                "specialization": summary.get("overall_specialization"),
                "arrears_ug": safe_int(summary.get("arrears_ug")),
                "arrears_pg": safe_int(summary.get("arrears_pg")),
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
                "total_experience_years": safe_int(summary.get("total_experience_years")),
                "present_post_years": safe_int(summary.get("present_post_years")),

            },
        )
        position_app.departments.set(Department.objects.filter(id__in=summary.get("departments", [])))

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
        # ✅ SPONSORED PROJECTS (SUMMARY SHEET)
        # =============================
        SponsoredProject.objects.filter(candidate=candidate).delete()

        for p in summary_projects:
            title = (p.get("title") or "").strip()
            if not title:
                continue

            status_val = (p.get("status") or "completed").strip().lower()
            if status_val not in ("completed", "ongoing"):
                status_val = "completed"

            SponsoredProject.objects.create(
                candidate=candidate,
                title=title,
                duration=(p.get("duration") or "").strip() or None,
                amount=safe_int(p.get("amount")),
                agency=(p.get("agency") or "").strip() or None,
                status=status_val,
            )

        # =============================
        # EDUCATION
        # =============================
        Education.objects.filter(candidate=candidate).delete()
        index_to_level = {}

        for idx, e in enumerate(education):
            level_obj = LevelOfEducation.objects.filter(id=safe_int(e.get("category"))).first()
            level_name = (level_obj.name if level_obj else "").strip()

            Education.objects.create(
                candidate=candidate,
                category=level_obj,
                degree=Degree.objects.filter(id=safe_int(e.get("degree"))).first(),
                specialization=e.get("specialization"),
                year_of_passing=e.get("year_of_passing"),
                institution=e.get("institution"),
                university=e.get("university"),
                percentage=e.get("percentage"),
                class_obtained=e.get("class_obtained"),
            )
            index_to_level[idx] = level_name

        # =============================
        # EDUCATION CERTIFICATES
        # =============================
        current_levels = {lvl for lvl in index_to_level.values() if lvl}
        EducationCertificate.objects.filter(candidate=candidate).exclude(level__in=current_levels).delete()

        for idx, level_name in index_to_level.items():
            if not level_name:
                continue

            tmp_path = tmp_certs.get(str(idx))
            if tmp_path and default_storage.exists(tmp_path):
                ext = os.path.splitext(tmp_path)[1]
                safe_name = slugify(candidate.name or "candidate")
                file_name = f"{safe_name}-{candidate.id}_{level_name}_certificate{ext}"

                with default_storage.open(tmp_path, "rb") as f:
                    EducationCertificate.objects.update_or_create(
                        candidate=candidate,
                        level=level_name,
                        defaults={
                            "file": ContentFile(
                                f.read(),
                                name=f"candidate/{safe_name}-{candidate.id}/education_certificates/{file_name}",
                            )
                        },
                    )
                default_storage.delete(tmp_path)

        # =============================
        # RESEARCH DETAILS (Gate/Net certs)
        # =============================
        ResearchDetails.objects.filter(candidate=candidate).delete()

        if research:
            rd = ResearchDetails.objects.create(
                candidate=candidate,
                mode_ug=research.get("mode_ug"),
                mode_pg=research.get("mode_pg"),
                mode_phd=research.get("mode_phd"),
                gate_score=research.get("gate_score"),
                net_slet_score=research.get("net_slet_score"),
                phd_thesis_title=research.get("phd_thesis_title"),
            )

            gate_tmp = research_tmp.get("gate_certificate_tmp")
            gate_name = research_tmp.get("gate_certificate_name") or "gate_certificate"
            if gate_tmp and default_storage.exists(gate_tmp):
                with default_storage.open(gate_tmp, "rb") as f:
                    rd.gate_certificate.save(gate_name, ContentFile(f.read()), save=True)
                default_storage.delete(gate_tmp)

            net_tmp = research_tmp.get("net_slet_certificate_tmp")
            net_name = research_tmp.get("net_slet_certificate_name") or "net_slet_certificate"
            if net_tmp and default_storage.exists(net_tmp):
                with default_storage.open(net_tmp, "rb") as f:
                    rd.net_slet_certificate.save(net_name, ContentFile(f.read()), save=True)
                default_storage.delete(net_tmp)

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
        # ✅ PROFESSIONAL ACTIVITY
        # =============================
        ProfessionalActivity.objects.filter(candidate=candidate).delete()
        for r in professional_activities:
            award = (r.get("award") or "").strip()
            particular = (r.get("particular") or "").strip()
            agency = (r.get("agency") or "").strip()
            year = r.get("year")

            if not (award or particular or agency or year):
                continue

            ProfessionalActivity.objects.create(
                candidate=candidate,
                award=award or None,
                particular=particular or None,
                agency=agency or None,
                year=year if year else None,
            )

        # =============================
        # TEACHING + CONTRIBUTIONS
        # =============================
        TeachingContributionEntry.objects.filter(candidate=candidate).delete()
        teaching_entries = request.session.get("teaching_entries", []) or []

        bulk = [
            TeachingContributionEntry(
                candidate=candidate,
                level=r.get("level"),
                subject=r.get("subject"),
                pass_percentage=safe_int(r.get("pass_percentage")),
                department_contribution=r.get("department_contribution"),
                college_contribution=r.get("college_contribution"),
            )
            for r in teaching_entries
        ]
        if bulk:
            TeachingContributionEntry.objects.bulk_create(bulk)

        # =============================
        # PROGRAMMES + PUBLICATIONS
        # =============================
        ProgrammePublicationEntry.objects.filter(candidate=candidate).delete()
        rows = []

        for p in programmes:
            if (p.get("programme_type") or "").strip():
                rows.append(
                    ProgrammePublicationEntry(
                        candidate=candidate,
                        entry_type="PROGRAMME",
                        programme_type=p.get("programme_type"),
                        programme_category=p.get("category"),
                        programme_count=safe_int(p.get("count")),
                    )
                )

        for pub in publications:
            if (pub.get("title") or "").strip():
                rows.append(
                    ProgrammePublicationEntry(
                        candidate=candidate,
                        entry_type="PUBLICATION",
                        publication_title=pub.get("title"),
                        publication_indexing=pub.get("indexing"),
                    )
                )

        for rp in research_publications:
            if (rp.get("details") or "").strip():
                rows.append(
                    ProgrammePublicationEntry(
                        candidate=candidate,
                        entry_type="RESEARCH_PUB",
                        details=rp.get("details"),
                    )
                )

        if (research_scholars or "").strip():
            rows.append(
                ProgrammePublicationEntry(
                    candidate=candidate,
                    entry_type="RESEARCH_SCHOLARS",
                    details=research_scholars,
                )
            )

        for m in memberships:
            if (m.get("details") or "").strip():
                rows.append(
                    ProgrammePublicationEntry(
                        candidate=candidate,
                        entry_type="MEMBERSHIP",
                        details=m.get("details"),
                    )
                )

        for a in awards:
            if (a.get("details") or "").strip():
                rows.append(
                    ProgrammePublicationEntry(
                        candidate=candidate,
                        entry_type="AWARD",
                        details=a.get("details"),
                    )
                )

        if rows:
            ProgrammePublicationEntry.objects.bulk_create(rows)

        # =============================
        # REFEREES
        # =============================
        Referee.objects.filter(candidate=candidate).delete()

        posted_referees = []
        for n, d, o, em, wa in zip(
            request.POST.getlist("ref_name[]"),
            request.POST.getlist("ref_designation[]"),
            request.POST.getlist("ref_organization[]"),
            request.POST.getlist("ref_email[]"),
            request.POST.getlist("ref_whatsapp[]"),
        ):
            n = (n or "").strip()
            d = (d or "").strip()
            o = (o or "").strip()
            em = (em or "").strip()
            wa = (wa or "").strip()

            posted_referees.append({"name": n, "designation": d, "organization": o, "email": em, "whatsapp": wa})

            if n:
                Referee.objects.create(
                    candidate=candidate,
                    name=n,
                    designation=d or None,
                    organization=o or None,
                    email=em or None,
                    whatsapp_number=wa or None,
                )

        # optional: keep for user if error later (but now success)
        request.session["referees"] = posted_referees

    # Clear everything after successful save
    request.session.flush()
    return redirect("application_success")




def application_success(request):
    return render(request, "faculty_requirement/faculty/application_success.html")
