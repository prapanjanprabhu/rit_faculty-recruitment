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
    TeachingSubject,
    Contribution,
    SponsoredProject,
    Qualification,
    Programme,
    Publication,
    Referee,
    ProgrammesPublications, Degree, Designation, Department, LevelOfEducation, Document_Type, Document, Certificate_Permission,
)
import os
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import FileSystemStorage
from applications.models import VisitorLog, ApplicationUsageLog
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage

# views.py
from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
import json

# Create a custom template filter for indexing lists
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
    Department, Degree, Language, Community
)

def to_int(v, d=0):
    try: return int(v)
    except: return d


def individual_summary_sheet(request):

    # bootstrap languages + communities once
    try: Language.create_default_languages()
    except: pass
    try: Community.create_default_communities()
    except: pass

    if request.method == "POST":
        post = request.POST
        files = request.FILES

        data = request.session.get("summary", {})

        # simple fields
        data["name"] = post.get("name", "")
        data["age"] = to_int(post.get("age"))
        data["present_organization"] = post.get("present_organization", "")
        data["overall_specialization"] = post.get("overall_specialization", "")
        data["specialization"] = data["overall_specialization"]

        # community
        data["community"] = to_int(post.get("community"), None)

        # languages multiple
        data["languages"] = [to_int(x) for x in post.getlist("languages[]")]

        # departments multiple
        data["departments"] = [to_int(x) for x in post.getlist("departments[]")]

        # position + designation
        data["position_applied"] = to_int(post.get("position_applied"), None)
        data["present_designation"] = to_int(post.get("present_designation"), None)

        # qualifications structured
        qualifications = []
        q_qual = post.getlist("qualification[]")
        q_spec = post.getlist("specialization[]")
        q_inst = post.getlist("institute[]")
        q_year = post.getlist("year[]")

        for i in range(len(q_qual)):
            qualifications.append({
                "qualification": to_int(q_qual[i]),
                "specialization": q_spec[i],
                "institute": q_inst[i],
                "year": to_int(q_year[i], None),
            })
        data["qualifications"] = qualifications

        # projects structured
        projects = []
        p_title = post.getlist("project_title[]")
        p_dur = post.getlist("project_duration[]")
        p_amt = post.getlist("project_amount[]")
        p_agency = post.getlist("project_agency[]")
        for i in range(len(p_title)):
            if p_title[i].strip():
                projects.append({
                    "title": p_title[i],
                    "duration": p_dur[i],
                    "amount": to_int(p_amt[i], 0),
                    "agency": p_agency[i]
                })
        data["projects"] = projects

        # numeric fields
        nums = [
            "assistant_professor_years","associate_professor_years",
            "professor_years","other_years",
            "research_experience_years","industry_experience_years",
            "journal_national","journal_international",
            "conference_national","conference_international",
            "mtech_completed","mtech_ongoing",
            "phd_completed","phd_ongoing"
        ]
        for f in nums:
            data[f] = to_int(post.get(f))

        # computed
        data["journal_publications"] = data["journal_national"] + data["journal_international"]
        data["conference_publications"] = data["conference_national"] + data["conference_international"]
        data["students_guided_completed"] = data["mtech_completed"] + data["phd_completed"]
        data["students_guided_ongoing"] = data["mtech_ongoing"] + data["phd_ongoing"]

        # image temporary
        if files.get("photo"):
            if not request.session.session_key:
                request.session.save()
            tmp_path = default_storage.save(
                f"tmp/photo_{request.session.session_key}_{files['photo'].name}",
                files["photo"]
            )
            data["photo"] = tmp_path
            data["photo_original"] = files["photo"].name


        # persist to session
        request.session["summary"] = data

        # NOTE — DB saving happens only on NEXT step
        return redirect("individual_data_sheet")

    # GET request (rehydrate everything)
    data = request.session.get("summary", {})

    return render(
        request,
        "faculty_requirement/faculty/individual_summary_sheet.html",
        {
            "data": data,
            "designations": Designation.objects.all(),
            "departments": Department.objects.all(),
            "degrees": Degree.objects.all(),
            "languages": Language.objects.all(),
            "communities": Community.objects.all(),
        },
    )








def individual_data_sheet(request):
    if request.method == "POST":
        data = request.POST.dict()
        data.pop("csrfmiddlewaretoken", None)
        request.session["personal"] = data
        return redirect("educational_qualifications")

    return render(
        request,
        "faculty_requirement/faculty/individual_data_sheet.html",
        {"data": request.session.get("personal", {})},
    )



from itertools import zip_longest

def educational_qualifications(request):
    if request.method == "POST":

        education_list = []

        categories = request.POST.getlist("category[]")
        degrees = request.POST.getlist("degree[]")
        specializations = request.POST.getlist("specialization[]")
        years = request.POST.getlist("year_of_passing[]")
        institutions = request.POST.getlist("institution[]")
        universities = request.POST.getlist("university[]")
        percentages = request.POST.getlist("percentage[]")
        classes = request.POST.getlist("class_obtained[]")

        for category, degree, specialization, year, institution, university, percentage, class_obtained in zip_longest(
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
            if not (category or degree or specialization):
                continue

            education_list.append({
                "category": category,
                "degree": degree,
                "specialization": specialization,
                "year_of_passing": year,
                "institution": institution,
                "university": university,
                "percentage": percentage,
                "class_obtained": class_obtained,
            })

        request.session["education"] = education_list

        request.session["research_details"] = {
            "mode_ug": request.POST.get("mode_ug"),
            "mode_pg": request.POST.get("mode_pg"),
            "mode_phd": request.POST.get("mode_phd"),
            "arrears_ug": request.POST.get("arrears_ug"),
            "arrears_pg": request.POST.get("arrears_pg"),
            "gate_score": request.POST.get("gate_score"),
            "net_slet_score": request.POST.get("net_slet_score"),
            "me_thesis_title": request.POST.get("me_thesis_title"),
            "phd_thesis_title": request.POST.get("phd_thesis_title"),
        }

        return redirect("academic_and_industry_experience")

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

    subjects = request.session.get("subjects", [])
    contributions = request.session.get("contributions", [])
    summary = request.session.get("summary", {})

    department_id = summary.get("department")

    all_documents = Document_Type.objects.all()

    required_doc_ids = set(
        Certificate_Permission.objects.filter(
            department_id=department_id,
            is_required=True
        ).values_list("document_type_id", flat=True)
    )

    uploaded_docs = request.session.get("uploaded_documents", {})

    if request.method == "POST":

        subjects = (
            [{"level": "UG", "subject_and_result": s}
             for s in request.POST.getlist("ug_subjects[]")] +
            [{"level": "PG", "subject_and_result": s}
             for s in request.POST.getlist("pg_subjects[]")]
        )

        contributions = (
            [{"level": "Department", "description": d}
             for d in request.POST.getlist("department_contributions[]")] +
            [{"level": "College", "description": c}
             for c in request.POST.getlist("college_contributions[]")]
        )

        # ✅ TEMP DOCUMENT UPLOAD (MERGE)
        for doc in all_documents:
            field = f"document_{doc.id}"
            if field in request.FILES:
                tmp_path = default_storage.save(
                    f"tmp/doc_{doc.id}_{request.FILES[field].name}",
                    request.FILES[field]
                )
                uploaded_docs[str(doc.id)] = tmp_path

        missing_required = [
            doc.document_type
            for doc in all_documents
            if doc.id in required_doc_ids and str(doc.id) not in uploaded_docs
        ]

        if missing_required:
            return render(
                request,
                "faculty_requirement/faculty/teaching_and_contributions.html",
                {
                    "subjects": subjects,
                    "contributions": contributions,
                    "all_documents": all_documents,
                    "required_doc_ids": required_doc_ids,
                    "uploaded_docs": [
                        {"id": int(k), "name": os.path.basename(v)}
                        for k, v in uploaded_docs.items()
                    ],
                    "error": f"Required documents missing: {', '.join(missing_required)}",
                },
            )

        request.session["subjects"] = subjects
        request.session["contributions"] = contributions
        request.session["uploaded_documents"] = uploaded_docs

        return redirect("programmes_and_publications")

    return render(
        request,
        "faculty_requirement/faculty/teaching_and_contributions.html",
        {
            "subjects": subjects,
            "contributions": contributions,
            "all_documents": all_documents,
            "required_doc_ids": required_doc_ids,
            "uploaded_docs": [
                {"id": int(k), "name": os.path.basename(v)}
                for k, v in uploaded_docs.items()
            ],
        },
    )



def programmes_and_publications(request):
    if request.method == "POST":

        request.session["programmes"] = [
            {
                "programme_type": p.strip(),
                "category": c.strip(),
                "count": to_int(cnt),
            }
            for p,c,cnt in zip(
                request.POST.getlist("programme_type[]"),
                request.POST.getlist("programme_category[]"),
                request.POST.getlist("programme_count[]"),
            ) if p.strip()
        ]

        request.session["publications"] = [
            {"title":t.strip(),"indexing":i}
            for t,i in zip(
                request.POST.getlist("publication_title[]"),
                request.POST.getlist("publication_indexing[]")
            ) if t.strip()
        ]

        request.session["research_publications"] = [
            {"details":d.strip()}
            for d in request.POST.getlist("research_publication_details[]")
            if d.strip()
        ]

        request.session["research_scholars"] = request.POST.get("research_scholars_details","").strip()

        request.session["memberships"] = [
            {"details":d.strip()}
            for d in request.POST.getlist("membership_details[]")
            if d.strip()
        ]

        request.session["awards"] = [
            {"details":d.strip()}
            for d in request.POST.getlist("award_details[]")
            if d.strip()
        ]

        request.session["sponsored_projects"] = [
            {
                "title":t.strip(),
                "status":s,
                "funding_agency":a.strip(),
                "amount": safe_int(amt),
                "duration":d
            }
            for t,s,a,amt,d in zip(
                request.POST.getlist("project_title[]"),
                request.POST.getlist("project_status[]"),
                request.POST.getlist("funding_agency[]"),
                request.POST.getlist("project_amount[]"),
                request.POST.getlist("project_duration[]"),
            ) if t.strip()
        ]

        return redirect("referees_and_declaration")

    return render(request,"faculty_requirement/faculty/programmes_and_publications.html",{
        "programmes": request.session.get("programmes",[]),
        "publications": request.session.get("publications",[]),
        "research_publications": request.session.get("research_publications",[]),
        "research_scholars": request.session.get("research_scholars",""),
        "sponsored_projects": request.session.get("sponsored_projects",[]),
        "memberships": request.session.get("memberships",[]),
        "awards": request.session.get("awards",[]),
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

from applications.models import (
    Candidate, PositionApplication, Designation, Department, Degree,
    Language, Community, Qualification, SponsoredProject, Education,
    AcademicExperience, IndustryExperience, TeachingSubject, Contribution,
    Programme, Publication, ProgrammesPublications, Referee, Document,
    Document_Type, LevelOfEducation
)


from datetime import date

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

def referees_and_declaration(request):
    if request.method != "POST":
        return render(request,"faculty_requirement/faculty/referees_and_declaration.html",{"referees":[]})

    personal = request.session.get("personal",{})
    summary = request.session.get("summary",{})
    education = request.session.get("education",[])
    research = request.session.get("research_details",{})
    academic = request.session.get("academic_experience",[])
    industry = request.session.get("industry_experience",[])
    subjects = request.session.get("subjects",[])
    contributions = request.session.get("contributions",[])
    programmes = request.session.get("programmes",[])
    publications = request.session.get("publications",[])
    research_publications = request.session.get("research_publications",[])
    research_scholars = request.session.get("research_scholars","")
    sponsored_projects = request.session.get("sponsored_projects",[])
    memberships = request.session.get("memberships",[])
    awards = request.session.get("awards",[])
    uploaded_docs = request.session.get("uploaded_documents",{})

    candidate_id = request.session.get("candidate_id")

    with transaction.atomic():

        if not candidate_id:
            candidate = Candidate.objects.create(
                name=personal.get("name"),
                email=personal.get("email"),
                phone_primary=personal.get("phone_primary")
            )
            request.session["candidate_id"] = candidate.id
        else:
            candidate = Candidate.objects.select_for_update().get(id=candidate_id)

        community_obj = None
        if summary.get("community"):
            community_obj = Community.objects.filter(id=summary["community"]).first()

        candidate.name = personal.get("name")
        candidate.email = personal.get("email")
        candidate.gender = personal.get("gender")
        candidate.phone_primary = personal.get("phone_primary")
        candidate.phone_secondary = personal.get("phone_secondary")
        candidate.address = personal.get("address")
        candidate.caste = personal.get("caste")
        candidate.mother_name_and_occupation = personal.get("mother_name_and_occupation")

        dob = personal.get("date_of_birth")
        candidate.date_of_birth = parse_date(dob) if dob else None
        candidate.age = calculate_age(candidate.date_of_birth)

        candidate.total_experience_years = safe_int(personal.get("total_experience_years"))
        candidate.present_post_years = safe_int(personal.get("present_post_years"))

        candidate.save()

        # photo
        tmp = summary.get("photo")
        original = summary.get("photo_original")
        if tmp and default_storage.exists(tmp):
            safe_name = slugify(candidate.name or "candidate")
            fname = original or "profile.jpg"
            with default_storage.open(tmp,"rb") as f:
                candidate.photo.save(
                    f"{safe_name}-{candidate.id}/{fname}",
                    ContentFile(f.read()),
                    save=True
                )
            default_storage.delete(tmp)

        # documents
        Document.objects.filter(candidate=candidate).delete()
        for doc_id,tmp_path in uploaded_docs.items():
            if default_storage.exists(tmp_path):
                doc_type = Document_Type.objects.filter(id=int(doc_id)).first()
                if doc_type:
                    ext = os.path.splitext(tmp_path)[1]
                    safe_name = slugify(candidate.name or "candidate")
                    filename = f"{safe_name}-{candidate.id}_{doc_type.document_type}{ext}"
                    with default_storage.open(tmp_path,"rb") as f:
                        Document.objects.create(
                            candidate=candidate,
                            document_type=doc_type,
                            file=ContentFile(
                                f.read(),
                                name=f"candidate/{safe_name}-{candidate.id}/documents/{filename}"
                            )
                        )
                default_storage.delete(tmp_path)

        # position app
        designation_obj = Designation.objects.filter(id=summary.get("present_designation")).first()

        position_app,_ = PositionApplication.objects.update_or_create(
            candidate=candidate,
            defaults={
                "position_applied_id": summary.get("position_applied"),
                "community": community_obj,
                "present_designation": designation_obj.name if designation_obj else None,
                "present_organization": summary.get("present_organization"),
                "specialization": summary.get("overall_specialization"),
                "assistant_professor_years": to_int(summary.get("assistant_professor_years")),
                "associate_professor_years": to_int(summary.get("associate_professor_years")),
                "professor_years": to_int(summary.get("professor_years")),
                "other_years": to_int(summary.get("other_years")),
                "research_experience_years": to_int(summary.get("research_experience_years")),
                "industry_experience_years": to_int(summary.get("industry_experience_years")),
                "journal_publications": to_int(summary.get("journal_publications")),
                "conference_publications": to_int(summary.get("conference_publications")),
                "students_guided_completed": to_int(summary.get("students_guided_completed")),
                "students_guided_ongoing": to_int(summary.get("students_guided_ongoing")),
            }
        )

        position_app.languages.set(Language.objects.filter(id__in=summary.get("languages",[])))
        position_app.departments.set(Department.objects.filter(id__in=summary.get("departments",[])))

        # qualification
        Qualification.objects.filter(candidate=candidate).delete()
        for q in summary.get("qualifications",[]):
            Qualification.objects.create(
                candidate=candidate,
                qualification_id=q.get("qualification"),
                specialization=q.get("specialization"),
                institute=q.get("institute"),
                year=safe_int(q.get("year")),
            )

        # sponsored
        SponsoredProject.objects.filter(candidate=candidate).delete()
        for p in sponsored_projects:
            SponsoredProject.objects.create(
                candidate=candidate,
                title=p.get("title"),
                duration=p.get("duration"),
                amount=safe_int(p.get("amount")) or 0,
                agency=p.get("funding_agency"),
            )

        # education
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

        # research single
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

        # academic
        AcademicExperience.objects.filter(candidate=candidate).delete()
        for a in academic:
            AcademicExperience.objects.create(candidate=candidate, **a)

        # industry
        IndustryExperience.objects.filter(candidate=candidate).delete()
        for i in industry:
            IndustryExperience.objects.create(candidate=candidate, **i)

        # teaching
        TeachingSubject.objects.filter(candidate=candidate).delete()
        for s in subjects:
            TeachingSubject.objects.create(candidate=candidate, **s)

        # contributions
        Contribution.objects.filter(candidate=candidate).delete()
        for c in contributions:
            Contribution.objects.create(candidate=candidate, **c)

        # programmes
        Programme.objects.filter(candidate=candidate).delete()
        for p in programmes:
            Programme.objects.create(
                candidate=candidate,
                programme_type=p.get("programme_type"),
                category=p.get("category"),
                count=safe_int(p.get("count")),
            )

        # publications
        Publication.objects.filter(candidate=candidate).delete()
        for p in publications:
            Publication.objects.create(candidate=candidate, **p)

        # combined json
        ProgrammesPublications.objects.update_or_create(
            candidate=candidate,
            defaults={
                "programmes": json.dumps(programmes),
                "publications": json.dumps(publications),
                "research_publications_details": json.dumps(research_publications),
                "research_scholars_details": research_scholars,
                "sponsored_projects": json.dumps(sponsored_projects),
                "memberships": json.dumps(memberships),
                "awards": json.dumps(awards),
            }
        )

        # referees
        Referee.objects.filter(candidate=candidate).delete()
        for n,d,o,c in zip(
            request.POST.getlist("ref_name[]"),
            request.POST.getlist("ref_designation[]"),
            request.POST.getlist("ref_organization[]"),
            request.POST.getlist("ref_contact[]")
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



