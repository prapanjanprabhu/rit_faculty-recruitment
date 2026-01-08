from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, JsonResponse
from applications.models import *
from django.db.models import Count
from django.shortcuts import render
from django.db.models import Count, Case, When, Value, CharField
from django.utils.timezone import now
from datetime import timedelta

# =================================================
# LIST PAGE
# =================================================
def faculty_data(request):
    department_id = request.GET.get("department")
    designation_id = request.GET.get("designation")
    search = request.GET.get("search")

    applications_qs = (
        PositionApplication.objects
        .select_related("candidate", "department", "position_applied")
        .order_by("candidate__name")
    )

    if department_id:
        applications_qs = applications_qs.filter(department_id=department_id)

    if designation_id:
        applications_qs = applications_qs.filter(present_designation_id=designation_id)

    if search:
        applications_qs = applications_qs.filter(candidate__name__icontains=search)

    total_candidates = applications_qs.values("candidate").distinct().count()

    dept_counts = (
        applications_qs.values("department__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    designation_counts = (
        applications_qs.values("position_applied__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return render(request, "faculty_requirement/admin/faculty/faculty_data.html", {
        "applications": applications_qs,
        "departments": Department.objects.all(),
        "designations": Designation.objects.all(),
        "total_candidates": total_candidates,
        "dept_counts": dept_counts,
        "designation_counts": designation_counts,
        "selected_department": department_id,
        "selected_designation": designation_id,
        "search": search or "",
    })
# =================================================
# DETAIL PAGE (VIEW ALL DATA)
# =================================================
def faculty_application_details(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    position = PositionApplication.objects.filter(candidate=candidate).last() or PositionApplication()

    context = {
        'candidate': candidate,
        'position': position,
        'qualification': Qualification.objects.filter(candidate=candidate),
        'sponsored_projects': SponsoredProject.objects.filter(candidate=candidate),
        'education': Education.objects.filter(candidate=candidate),
        'research_details': ResearchDetails.objects.filter(candidate=candidate).last() or ResearchDetails(),
        'academic': AcademicExperience.objects.filter(candidate=candidate),
        'industry': IndustryExperience.objects.filter(candidate=candidate),
        'teaching': TeachingSubject.objects.filter(candidate=candidate),
        'contributions': Contribution.objects.filter(candidate=candidate),
        'programmes': Programme.objects.filter(candidate=candidate),
        'publications': Publication.objects.filter(candidate=candidate),
        'referees': Referee.objects.filter(candidate=candidate),
    }

    return render(
        request,
        "faculty_requirement/admin/faculty/faculty_application_details.html",
        context
    )


# =================================================
# UPDATE SECTION (INLINE SAVE)
# =================================================
def faculty_section_update(request):
    if request.method != 'POST':
        return JsonResponse({'success': False})

    candidate = get_object_or_404(Candidate, id=request.POST.get('candidate_id'))
    section = request.POST.get('section')
    obj_id = request.POST.get('id')

    try:
        if section == 'candidate':
            # Basic
            candidate.name = request.POST.get('name')
            candidate.email = request.POST.get('email')
            candidate.phone_primary = request.POST.get('phone_primary')
            # Extended
            candidate.age = request.POST.get('age') or None
            candidate.date_of_birth = request.POST.get('date_of_birth') or None
            candidate.gender = request.POST.get('gender')
            candidate.marital_status = request.POST.get('marital_status')
            candidate.community = request.POST.get('community')
            candidate.caste = request.POST.get('caste')
            candidate.pan_number = request.POST.get('pan_number')
            candidate.phone_secondary = request.POST.get('phone_secondary')
            candidate.address = request.POST.get('address') or ''
            candidate.total_experience_years = request.POST.get('total_experience_years') or None
            candidate.present_post_years = request.POST.get('present_post_years') or None
            candidate.mother_name_and_occupation = request.POST.get('mother_name_and_occupation')
            candidate.save()

        elif section == 'position':
            obj, _ = PositionApplication.objects.get_or_create(candidate=candidate)
            obj.position_applied = request.POST.get('position_applied')
            obj.department = request.POST.get('department')
            obj.present_designation = request.POST.get('present_designation')
            obj.present_organization = request.POST.get('present_organization')
            obj.specialization = request.POST.get('specialization')
            obj.assistant_professor_years = request.POST.get('assistant_professor_years') or 0
            obj.associate_professor_years = request.POST.get('associate_professor_years') or 0
            obj.professor_years = request.POST.get('professor_years') or 0
            obj.other_years = request.POST.get('other_years') or 0
            obj.research_experience_years = request.POST.get('research_experience_years') or 0
            obj.industry_experience_years = request.POST.get('industry_experience_years') or 0
            obj.journal_publications = request.POST.get('journal_publications') or 0
            obj.conference_publications = request.POST.get('conference_publications') or 0
            obj.students_guided_completed = request.POST.get('students_guided_completed') or 0
            obj.students_guided_ongoing = request.POST.get('students_guided_ongoing') or 0
            obj.community_and_caste = request.POST.get('community_and_caste')
            obj.save()

        elif section == 'research_details':
            obj, _ = ResearchDetails.objects.get_or_create(candidate=candidate)
            obj.mode_ug = request.POST.get('mode_ug')
            obj.mode_pg = request.POST.get('mode_pg')
            obj.mode_phd = request.POST.get('mode_phd')
            obj.arrears_ug = request.POST.get('arrears_ug') or None
            obj.arrears_pg = request.POST.get('arrears_pg') or None
            obj.gate_score = request.POST.get('gate_score')
            obj.net_slet_score = request.POST.get('net_slet_score')
            obj.me_thesis_title = request.POST.get('me_thesis_title')
            obj.phd_thesis_title = request.POST.get('phd_thesis_title')
            obj.save()

        elif section == 'education':
            if obj_id:
                obj = get_object_or_404(Education, id=obj_id, candidate=candidate)
            else:
                obj = Education(candidate=candidate)
            obj.category = request.POST.get('category')
            obj.degree = request.POST.get('degree')
            obj.specialization = request.POST.get('specialization')
            obj.year_of_passing = request.POST.get('year_of_passing')
            obj.institution = request.POST.get('institution')
            obj.university = request.POST.get('university')
            obj.percentage = request.POST.get('percentage')
            obj.class_obtained = request.POST.get('class_obtained')
            obj.save()

        elif section == 'qualification':
            if obj_id:
                obj = get_object_or_404(Qualification, id=obj_id, candidate=candidate)
            else:
                obj = Qualification(candidate=candidate)
            obj.qualification = request.POST.get('qualification')
            obj.specialization = request.POST.get('specialization')
            obj.institute = request.POST.get('institute')
            obj.year = request.POST.get('year') or None
            obj.save()

        elif section == 'sponsored_project':
            if obj_id:
                obj = get_object_or_404(SponsoredProject, id=obj_id, candidate=candidate)
            else:
                obj = SponsoredProject(candidate=candidate)
            obj.title = request.POST.get('title')
            obj.duration = request.POST.get('duration')
            obj.amount = request.POST.get('amount') or None
            obj.agency = request.POST.get('agency')
            obj.save()

        elif section == 'academic_experience':
            if obj_id:
                obj = get_object_or_404(AcademicExperience, id=obj_id, candidate=candidate)
            else:
                obj = AcademicExperience(candidate=candidate)
            obj.institution = request.POST.get('institution')
            obj.designation = request.POST.get('designation')
            obj.joining_date = request.POST.get('joining_date') or None
            obj.relieving_date = request.POST.get('relieving_date') or ''
            obj.years = request.POST.get('years') or None
            obj.months = request.POST.get('months') or None
            obj.days = request.POST.get('days') or None
            obj.save()

        elif section == 'industry_experience':
            if obj_id:
                obj = get_object_or_404(IndustryExperience, id=obj_id, candidate=candidate)
            else:
                obj = IndustryExperience(candidate=candidate)
            obj.organization = request.POST.get('organization')
            obj.designation = request.POST.get('designation')
            obj.nature_of_work = request.POST.get('nature_of_work')
            obj.joining_date = request.POST.get('joining_date') or None
            obj.relieving_date = request.POST.get('relieving_date') or None
            obj.years = request.POST.get('years') or None
            obj.months = request.POST.get('months') or None
            obj.days = request.POST.get('days') or None
            obj.save()

        elif section == 'teaching_subject':
            if obj_id:
                obj = get_object_or_404(TeachingSubject, id=obj_id, candidate=candidate)
            else:
                obj = TeachingSubject(candidate=candidate)
            obj.level = request.POST.get('level')
            obj.subject_and_result = request.POST.get('subject_and_result')
            obj.save()

        elif section == 'contribution':
            if obj_id:
                obj = get_object_or_404(Contribution, id=obj_id, candidate=candidate)
            else:
                obj = Contribution(candidate=candidate)
            obj.level = request.POST.get('level')
            obj.description = request.POST.get('description')
            obj.save()

        elif section == 'programme':
            if obj_id:
                obj = get_object_or_404(Programme, id=obj_id, candidate=candidate)
            else:
                obj = Programme(candidate=candidate)
            obj.programme_type = request.POST.get('programme_type')
            obj.category = request.POST.get('category')
            obj.count = request.POST.get('count') or 0
            obj.save()

        elif section == 'publication':
            if obj_id:
                obj = get_object_or_404(Publication, id=obj_id, candidate=candidate)
            else:
                obj = Publication(candidate=candidate)
            obj.title = request.POST.get('title')
            obj.indexing = request.POST.get('indexing')
            obj.save()

        elif section == 'referee':
            if obj_id:
                obj = get_object_or_404(Referee, id=obj_id, candidate=candidate)
            else:
                obj = Referee(candidate=candidate)
            obj.name = request.POST.get('name')
            obj.designation = request.POST.get('designation')
            obj.organization = request.POST.get('organization')
            obj.contact_number = request.POST.get('contact_number')
            obj.save()

        else:
            return JsonResponse({'success': False, 'error': 'Unknown section'})

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

from django.http import HttpResponse
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.http import HttpResponse
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from django.http import HttpResponse
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import lightgrey
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os
import tempfile
from django.conf import settings
from django.http import HttpResponse
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfMerger

import os
import tempfile
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PyPDF2 import PdfMerger
from django.conf import settings
def safe(val):
    return "N/A" if val in [None, "", [], 0] else val

import io
import os
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from PyPDF2 import PdfMerger


def safe(val):
    if val in [None, "", []]:
        return "N/A"
    return str(val)

def draw_header(canvas_obj, doc_obj, logo_path=None):
    width, height = A4

    top_y = height - 40   # starting top position
    line_gap = 18         # vertical spacing between lines

    # === Logo ===
    if logo_path and os.path.exists(logo_path):
        canvas_obj.drawImage(
            logo_path,
            40,
            top_y - 55,      # align logo with text block
            width=70,
            height=60,
            preserveAspectRatio=True,
            mask="auto"
        )

    # === Institute Name ===
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.drawCentredString(width / 2, top_y, "RAMCO INSTITUTE OF TECHNOLOGY")

    # === Subtitle ===
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.drawCentredString(
        width / 2,
        top_y - line_gap,
        "An Autonomous Institution, Rajapalayam - 626117"
    )

    # === Title ===
    canvas_obj.setFont("Helvetica-Bold", 12)
    canvas_obj.drawCentredString(
        width / 2,
        top_y - (line_gap * 2.2),
        "APPLICATION FOR FACULTY POSITION"
    )

    # === Caption ===
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawCentredString(
        width / 2,
        top_y - (line_gap * 3.2),
        "(Individual Summary & Data Sheet)"
    )

    # === Divider line ===
    canvas_obj.line(
        40,
        top_y - (line_gap * 4),
        width - 40,
        top_y - (line_gap * 4)
    )


def draw_watermark(canvas_obj, doc_obj):
    width, height = A4
    logo_path = os.path.join(settings.BASE_DIR, "static/images/ritlogo.png")

    canvas_obj.saveState()
    canvas_obj.setFillAlpha(0.25)  # 25% opacity - subtle but visible

    if os.path.exists(logo_path):
        try:
            # Center the logo perfectly
            canvas_obj.translate(width / 2, height / 2)  # Move to exact center of page
            # canvas_obj.rotate(15)  # Optional: uncomment for slight rotation if desired

            # Draw image centered at (0,0) after translation
            # Use negative half of width/height for perfect centering
            img_size = 300  # Adjust this value for desired watermark size
            canvas_obj.drawImage(
                logo_path,
                -img_size / 2, -img_size / 2,  # Perfect centering
                width=img_size,
                height=img_size,
                preserveAspectRatio=True,
                mask='auto'  # Keeps transparency if PNG has alpha channel
            )
        except Exception as e:
            print(f"Watermark logo error: {e}")
            # Fallback to text if image fails to load
            canvas_obj.setFont("Helvetica-Bold", 120)
            canvas_obj.setFillColorRGB(0.85, 0.85, 0.85)
            canvas_obj.drawCentredString(0, 0, "RIT")
    else:
        # Fallback: text watermark if logo file is missing
        canvas_obj.setFont("Helvetica-Bold", 120)
        canvas_obj.setFillColorRGB(0.85, 0.85, 0.85)
        canvas_obj.drawCentredString(0, 0, "RIT")

    canvas_obj.restoreState()
def safe_text(value):
    """Safely convert any value to string, return 'N/A' if None or empty"""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value).strip() or "N/A"

def faculty_data_pdf(request, candidate_id):
    # Fetch data
    candidate = Candidate.objects.get(id=candidate_id)
    application = PositionApplication.objects.filter(candidate=candidate).last()
    educations = Education.objects.filter(candidate=candidate).order_by('category')
    academics = AcademicExperience.objects.filter(candidate=candidate).order_by('-joining_date')
    industry_exps = IndustryExperience.objects.filter(candidate=candidate)
    research = ResearchDetails.objects.filter(candidate=candidate).first()
    subjects = TeachingSubject.objects.filter(candidate=candidate)
    contributions = Contribution.objects.filter(candidate=candidate)
    programmes = Programme.objects.filter(candidate=candidate)
    publications = Publication.objects.filter(candidate=candidate)
    referees = Referee.objects.filter(candidate=candidate)
    uploaded_docs = Document.objects.filter(candidate=candidate)  # Renamed to avoid conflict
    sponsored_projects = SponsoredProject.objects.filter(candidate=candidate)

    # In-memory buffer
    buffer = io.BytesIO()

    pdf_doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=120,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        wordWrap='LTR',
        splitLongWords=True,
    )
    normal_style = ParagraphStyle(
        'NormalWrap',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        alignment=0,
        wordWrap='LTR',
        splitLongWords=True,
    )
    header_style = ParagraphStyle(
        'HeaderWrap',
        parent=bold_style,
        fontSize=9,
        leading=11,
        alignment=1,
        wordWrap='LTR',
        splitLongWords=True,
    )

    elements = []

    logo_path = os.path.join(settings.BASE_DIR, "static/images/ritlogo.png")

    def header_footer(canvas, doc):
        draw_header(canvas, doc, logo_path)
        
        draw_watermark(canvas, doc)
        canvas.setFont("Helvetica", 9)
        
        canvas.drawRightString(A4[0] - 40, 30, f"Page {doc.page}")

    # ====================== A. INDIVIDUAL SUMMARY SHEET ======================
    elements.append(Spacer(1, 30))

    # Photo + Basic Info
    photo_path = candidate.photo.path if candidate.photo and os.path.exists(candidate.photo.path) else None
    photo_img = Image(photo_path, width=90, height=110) if photo_path else Paragraph("<i>No Photo</i>", normal_style)

    info_paragraph = Paragraph(f"""
        <b>Position applied for & Department:</b> {safe_text(application.position_applied.name if application.position_applied else 'N/A')} & {safe_text(application.department.name if application.department else 'N/A')}<br/><br/>
        <b>1. Name of the Candidate & Age:</b> {safe_text(candidate.name)} & {safe_text(candidate.age)}<br/><br/>
        <b>2. Present Occupation/Designation and Name of the Institute/Organisation currently working:</b><br/>
        {safe_text(application.present_designation)} / {safe_text(application.present_organization)}
    """, normal_style)

    summary_header = [[info_paragraph, photo_img]]
    summary_table = Table(summary_header, colWidths=[400, 120])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 8))  # Reduced spacing to move content up

    # 3. Qualifications (Simplified - only 4 columns)
    elements.append(Paragraph("<b>3. Qualifications:</b>", bold_style))
    qual_headers = ["Degree", "Ph.D. (Institution & Year of award)", "UG", "PG"]
    qual_rows = [[Paragraph(h, header_style) for h in qual_headers]]
    qual_data = [
        ["Pursuing (Anna University)", "--", "B.E", "M.E"],
        ["", "", "2008", "2013"],
    ]
    for row in qual_data:
        qual_rows.append([Paragraph(safe_text(cell), normal_style) for cell in row])

    qual_table = Table(qual_rows, colWidths=[140, 140, 80, 80])  # Minimized widths
    qual_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(qual_table)
    elements.append(Spacer(1, 8))

    elements.append(Paragraph(f"<b>4. Specialization:</b> {safe_text(application.specialization)}", normal_style))
    elements.append(Spacer(1, 12))

    # 5. Years of Service
    elements.append(Paragraph("<b>5. Years of Service as Assistant Professor / Associate Professor / Professor or equivalent:</b>", bold_style))
    service_data = [
        ["", "Assistant Professor", "Associate Professor", "Professor", "Others"],
        ["", safe_text(application.assistant_professor_years or 0),
         safe_text(application.associate_professor_years or 0),
         safe_text(application.professor_years or 0),
         safe_text(application.other_years or 0)]
    ]
    service_table = Table(service_data, colWidths=[150, 90, 90, 90, 90])
    service_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(service_table)
    elements.append(Spacer(1, 12))

    # 6. Research / Industry Experience
    ri_data = [
        [Paragraph("<b>6. Research / Industry Experience</b>", bold_style), Paragraph("<b>(in years)</b>", bold_style), ""],
        ["Research (other than PhD period)", safe_text(application.research_experience_years or 0), ""],
        ["Industry", safe_text(application.industry_experience_years or 0), ""]
    ]
    ri_table = Table(ri_data, colWidths=[300, 100, 100])
    ri_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(ri_table)
    elements.append(Spacer(1, 12))

    # 7. Publications
    pub_data = [
        [Paragraph("<b>7. No. of Research Publications</b>", bold_style), Paragraph("<b>National</b>", bold_style), Paragraph("<b>International</b>", bold_style)],
        ["In Journals", "--", safe_text(application.journal_publications or 0)],
        ["In Conferences", "--", safe_text(application.conference_publications or 0)]
    ]
    pub_table = Table(pub_data, colWidths=[300, 100, 100])
    pub_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    elements.append(pub_table)
    elements.append(Spacer(1, 12))

    # 8. Students Guided
    guide_data = [
        [Paragraph("<b>8. No. of Students guided for M.E./M.Tech./M.Phil.</b>", bold_style), Paragraph("<b>Completed</b>", bold_style), Paragraph("<b>On-going</b>", bold_style)],
        ["", safe_text(application.students_guided_completed or 0), safe_text(application.students_guided_ongoing or 0)],
    ]
    guide_table = Table(guide_data, colWidths=[300, 100, 100])
    guide_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
    elements.append(guide_table)
    elements.append(Spacer(1, 12))

    # 9. Sponsored Projects
    elements.append(Paragraph("<b>9. Completed Sponsored Projects:</b>", bold_style))
    if sponsored_projects:
        for proj in sponsored_projects:
            elements.append(Paragraph(f"• {safe_text(proj.title)} ({safe_text(proj.agency)}, ₹{safe_text(proj.amount)}, {safe_text(proj.duration)})", normal_style))
    else:
        elements.append(Paragraph("--", normal_style))
    elements.append(Spacer(1, 15))

    # 10. Community
    elements.append(Paragraph(f"<b>10. Community and Caste:</b> {safe_text(candidate.community)} / {safe_text(candidate.caste)}", normal_style))
    elements.append(Spacer(1, 30))

    # Signature
    sig_table_a = Table(
        [["", Paragraph("Signature of the Candidate with date", normal_style)]],
        colWidths=[350, 170]
    )
    sig_table_a.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    elements.append(sig_table_a)
    elements.append(PageBreak())

    # ====================== B. INDIVIDUAL DATA SHEET ======================
    elements.append(Paragraph("<font size=14><b>B. INDIVIDUAL DATA SHEET</b></font>", ParagraphStyle('Heading1', parent=styles['Heading1'], alignment=1)))
    elements.append(Spacer(1, 20))

    # Personal Info Table
    basic_rows = []
    for label, value in [
        ["Name of the Candidate", safe_text(candidate.name)],
        ["Date of Birth and Age", f"{candidate.date_of_birth.strftime('%d.%m.%Y') if candidate.date_of_birth else 'N/A'} ({safe_text(candidate.age)})"],
        ["Present Designation & Organization", f"{safe_text(application.present_designation)} / {safe_text(application.present_organization)}"],
        ["Residential Address", safe_text(candidate.address)],
        ["Contact Nos.", f"{safe_text(candidate.phone_primary)}, {safe_text(candidate.phone_secondary)}"],
        ["E-mail ID", safe_text(candidate.email)],
        ["Gender", safe_text(candidate.gender)],
        ["Marital Status", safe_text(candidate.marital_status)],
        ["Community and Caste", f"{safe_text(candidate.community)} / {safe_text(candidate.caste)}"],
        ["PAN No.", safe_text(candidate.pan_number)],
        ["Years of experience in present post", safe_text(candidate.present_post_years)],
        ["Mother's Name & Occupation", safe_text(candidate.mother_name_and_occupation)],
    ]:
        basic_rows.append([
            Paragraph(f"<b>{label}</b>", bold_style),
            Paragraph(value or "N/A", normal_style)
        ])

    basic_table = Table(basic_rows, colWidths=[230, 290])
    basic_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(basic_table)
    elements.append(Spacer(1, 20))

    # I. Educational Qualifications - Minimized columns & widths
    elements.append(Paragraph("<b>I. a) Educational Qualifications:</b>", bold_style))
    edu_headers = ["Category", "Degree", "Specialization", "Year", "% / Class"]
    edu_rows = [[Paragraph(h, header_style) for h in edu_headers]]

    for edu in educations:
        percentage_class = f"{safe_text(edu.percentage)} / {safe_text(edu.class_obtained)}".strip(' /')
        edu_rows.append([
            Paragraph(safe_text(edu.category.name if edu.category else ''), normal_style),
            Paragraph(safe_text(edu.degree.degree if edu.degree else ''), normal_style),
            Paragraph(safe_text(edu.specialization), normal_style),
            Paragraph(safe_text(edu.year_of_passing), normal_style),
            Paragraph(percentage_class or "N/A", normal_style),
        ])

    edu_table = Table(edu_rows, colWidths=[70, 90, 140, 60, 90])  # Minimized widths
    edu_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(edu_table)
    elements.append(Spacer(1, 10))

    # Research Details
    if research:
        elements.append(Paragraph(f"<b>Mode of Study (FT / PT):</b> UG: {safe_text(research.mode_ug)} | PG: {safe_text(research.mode_pg)} | Ph.D.: {safe_text(research.mode_phd)}", normal_style))
        elements.append(Paragraph(f"<b>No. of Arrears:</b> UG: {safe_text(research.arrears_ug)} | PG: {safe_text(research.arrears_pg)}", normal_style))
        elements.append(Paragraph(f"<b>GATE / NET / SLET Score:</b> {safe_text(research.gate_score or 'N/A')} / {safe_text(research.net_slet_score or 'N/A')}", normal_style))
        elements.append(Paragraph(f"<b>II. Title of M.E./M.Tech. Thesis:</b> {safe_text(research.me_thesis_title)}", normal_style))
        elements.append(Paragraph(f"<b>III. Title of Ph.D. Thesis:</b> {safe_text(research.phd_thesis_title)}", normal_style))
    elements.append(Spacer(1, 20))

    # IV. Academic Experience
    elements.append(Paragraph("<b>IV. Engineering College Academic Experience:</b>", bold_style))
    acad_rows = [[Paragraph(h, header_style) for h in ["Institution", "Designation", "Joining Date", "Relieving Date", "Experience"]]]
    total_y = total_m = total_d = 0
    for a in academics:
        exp = f"{safe_text(a.years or 0)}Y {safe_text(a.months or 0)}M {safe_text(a.days or 0)}D"
        acad_rows.append([
            Paragraph(safe_text(a.institution), normal_style),
            Paragraph(safe_text(a.designation), normal_style),
            Paragraph(a.joining_date.strftime('%d.%m.%Y') if a.joining_date else 'N/A', normal_style),
            Paragraph(safe_text(a.relieving_date), normal_style),
            Paragraph(exp, normal_style),
        ])
        total_y += a.years or 0
        total_m += a.months or 0
        total_d += a.days or 0
    acad_rows.append([Paragraph("<b>Total</b>", bold_style), "", "", "", Paragraph(f"<b>{total_y}Y {total_m}M {total_d}D</b>", bold_style)])

    acad_table = Table(acad_rows, colWidths=[160, 100, 80, 80, 100])
    acad_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
    ]))
    elements.append(acad_table)
    elements.append(Spacer(1, 20))

    # V. Industrial Experience
    elements.append(Paragraph("<b>V. Industrial Experience:</b>", bold_style))
    if industry_exps:
        for ie in industry_exps:
            exp = f"{safe_text(ie.years or 0)}Y {safe_text(ie.months or 0)}M {safe_text(ie.days or 0)}D"
            elements.append(Paragraph(f"• {safe_text(ie.organization)} - {safe_text(ie.designation)} ({exp})", normal_style))
    else:
        elements.append(Paragraph("No records found.", normal_style))
    elements.append(Spacer(1, 20))

    # VI & VII. Subjects Taught
    elements.append(Paragraph("<b>VI. Theory Subjects taught (UG):</b>", bold_style))
    ug_subjects = subjects.filter(level="UG")
    if ug_subjects:
        for sub in ug_subjects:
            elements.append(Paragraph(f"• {safe_text(sub.subject_and_result)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>VII. Theory Subjects taught (PG):</b>", bold_style))
    pg_subjects = subjects.filter(level="PG")
    if pg_subjects:
        for sub in pg_subjects:
            elements.append(Paragraph(f"• {safe_text(sub.subject_and_result)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    # Contributions
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>VIII. Contributions at Department Level:</b>", bold_style))
    dept_contrib = contributions.filter(level__icontains="Department")
    if dept_contrib:
        for c in dept_contrib:
            elements.append(Paragraph(f"• {safe_text(c.description)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    elements.append(Paragraph("<b>IX. Contributions at College Level:</b>", bold_style))
    college_contrib = contributions.filter(level__icontains="College")
    if college_contrib:
        for c in college_contrib:
            elements.append(Paragraph(f"• {safe_text(c.description)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    # Programmes
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>X. Programmes Participated:</b>", bold_style))
    participated = programmes.filter(category="Participated")
    if participated:
        for p in participated:
            elements.append(Paragraph(f"• {safe_text(p.programme_type)}: {safe_text(p.count)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    elements.append(Paragraph("<b>XI. Programmes Organized:</b>", bold_style))
    organized = programmes.filter(category="Organized")
    if organized:
        for p in organized:
            elements.append(Paragraph(f"• {safe_text(p.programme_type)}: {safe_text(p.count)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    # Publications
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>XII. Research Publications (Scopus indexed):</b>", bold_style))
    if publications:
        for pub in publications:
            elements.append(Paragraph(f"• {safe_text(pub.title)} <i>({safe_text(pub.indexing)})</i>", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    # Referees
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<b>XVII. Referees:</b>", bold_style))
    if referees:
        for ref in referees:
            elements.append(Paragraph(f"• {safe_text(ref.name)}<br/> {safe_text(ref.designation)}, {safe_text(ref.organization)}<br/> Contact: {safe_text(ref.contact_number)}", normal_style))
    else:
        elements.append(Paragraph("None listed.", normal_style))

    elements.append(Spacer(1, 60))

    # Final Signature
    final_sig = Table(
        [["", Paragraph("<b>Signature of the Candidate with date</b>", bold_style)]],
        colWidths=[350, 170]
    )
    final_sig.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(final_sig)

    # ====================== LAST PAGE: ATTACHED DOCUMENTS ======================
    elements.append(PageBreak())
    elements.append(Paragraph("<font size=12><b>Attached Documents</b></font>", bold_style))
    elements.append(Spacer(1, 12))

    if uploaded_docs.exists():
        doc_rows = [["Document Type", "Document Name"]]
        for uploaded_doc in uploaded_docs:
            # Adjust 'document_type' to your actual field name
            doc_type = getattr(uploaded_doc, 'document_type', 'Other')
            doc_name = os.path.basename(uploaded_doc.file.name) if uploaded_doc.file else "N/A"
            doc_rows.append([Paragraph(safe_text(doc_type), normal_style), Paragraph(safe_text(doc_name), normal_style)])

        doc_table = Table(doc_rows, colWidths=[180, 340])
        doc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(doc_table)
    else:
        elements.append(Paragraph("No additional documents attached.", normal_style))

    # Build PDF
    pdf_doc.build(elements, onFirstPage=header_footer, onLaterPages=header_footer)

    # Merge additional PDF documents
    merger = PdfMerger()
    buffer.seek(0)
    merger.append(buffer)
    for uploaded_doc in uploaded_docs:
        if uploaded_doc.file and str(uploaded_doc.file.name).lower().endswith(".pdf"):
            try:
                merger.append(uploaded_doc.file.path)
            except Exception as e:
                print(f"Merge error: {e}")
    final_buffer = io.BytesIO()
    merger.write(final_buffer)
    merger.close()
    buffer.close()
    final_buffer.seek(0)
    pdf_content = final_buffer.read()
    final_buffer.close()

    response = HttpResponse(pdf_content, content_type="application/pdf")
    filename = f"{candidate.name.replace(' ', '_')}_Faculty_Application_2025.pdf"
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response





