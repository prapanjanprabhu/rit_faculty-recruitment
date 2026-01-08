from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.utils import IntegrityError
from applications.models import Degree, Department, Designation, LevelOfEducation, Document_Type, Certificate_Permission
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.cache import never_cache
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


def is_admin(user):
    return user.is_authenticated and user.is_staff and user.is_active

@require_GET
@login_required(login_url="admin_login")
@user_passes_test(is_admin)
@never_cache
def organizations(request):
    return render(
        request,
        "faculty_requirement/admin/organizations.html",
        {
            "page_title": "Organization Settings"
        }
    )




from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.timezone import now


def send_audit_mail(
    *,
    title,
    header,
    action,
    user,
    description,
    details,
    previous=None,
    to_email=None
):
    """
    Generic audit mail sender for all admin CRUD actions
    """

    if not to_email:
        to_email = [settings.DEFAULT_FROM_EMAIL]

    context = {
        "title": title,
        "header": header,
        "action": action,
        "user": user.get_username(),
        "timestamp": now().strftime("%d-%m-%Y %I:%M %p"),
        "description": description,
        "details": details,
        "previous": previous,
    }

    html_content = render_to_string("faculty_requirement/emails/base_audit.html", context)

    msg = EmailMultiAlternatives(
        subject=title,
        body="Admin audit notification",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=to_email,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)



@login_required
@require_http_methods(["GET", "POST"])
def degree(request):

    if request.method == "POST":
        op = request.POST.get("operation")

        degree_code = (request.POST.get("degree_code") or "").strip()
        degree_name = (request.POST.get("degree") or "").strip()

        try:
            if op == "create":

                if not degree_code or not degree_name:
                    messages.error(request, "Degree Code and Degree Name are required.")
                    return redirect("degree")

                if Degree.objects.filter(
                    degree_code__iexact=degree_code,
                    degree__iexact=degree_name
                ).exists():
                    messages.error(
                        request,
                        "This Degree Code and Degree Name combination already exists."
                    )
                    return redirect("degree")

                Degree.objects.create(
                    degree_code=degree_code,
                    degree=degree_name
                )

                messages.success(request, "Degree created successfully.")

            elif op == "edit":
                obj = get_object_or_404(Degree, id=request.POST.get("id"))

                old_data = {
                    "Degree Code": obj.degree_code,
                    "Degree Name": obj.degree,
                }

                if not degree_code or not degree_name:
                    messages.error(request, "Degree Code and Degree Name are required.")
                    return redirect("degree")

                if Degree.objects.exclude(id=obj.id).filter(
                    degree_code__iexact=degree_code,
                    degree__iexact=degree_name
                ).exists():
                    messages.error(
                        request,
                        "Another degree with the same code and name already exists."
                    )
                    return redirect("degree")

                obj.degree_code = degree_code
                obj.degree = degree_name
                obj.save()

                # 📧 SEND AUDIT EMAIL
                send_audit_mail(
                    title="Degree Updated",
                    header="Degree Update Notification",
                    action="Updated",
                    user=request.user,
                    description="A degree record was updated in the admin panel.",
                    details={
                        "Degree Code": obj.degree_code,
                        "Degree Name": obj.degree,
                    },
                    previous=old_data,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Degree updated successfully.")

            elif op == "delete":
                obj = get_object_or_404(Degree, id=request.POST.get("id"))

                old_data = {
                    "Degree Code": obj.degree_code,
                    "Degree Name": obj.degree,
                }

                obj.delete()

                # 📧 SEND AUDIT EMAIL
                send_audit_mail(
                    title="Degree Deleted",
                    header="Degree Deletion Notification",
                    action="Deleted",
                    user=request.user,
                    description="A degree record was deleted from the admin panel.",
                    details=old_data,
                    previous=None,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Degree deleted successfully.")

            else:
                messages.error(request, "Invalid operation.")

        except Exception:
            messages.error(request, "Unexpected error occurred.")
            raise  # remove in production if needed

        return redirect("degree")

    degrees = Degree.objects.all()
    return render(
        request,
        "faculty_requirement/admin/degree.html",
        {"degrees": degrees}
    )




@login_required
@require_http_methods(["GET", "POST"])
def department(request):

    if request.method == "POST":
        op = request.POST.get("operation")

        name = (request.POST.get("name") or "").strip()
        code = (request.POST.get("code") or "").strip().upper()
        degree_id = request.POST.get("degree_id")

        try:
            if op == "create":

                if not name or not code or not degree_id:
                    messages.error(request, "Name, Code and Degree are required.")
                    return redirect("department")

                # 🔐 Duplicate guard (same degree only)
                if Department.objects.filter(
                    degree_id=degree_id,
                    name__iexact=name
                ).exists():
                    messages.error(
                        request,
                        "This department name already exists under the selected degree."
                    )
                    return redirect("department")

                if Department.objects.filter(
                    degree_id=degree_id,
                    code__iexact=code
                ).exists():
                    messages.error(
                        request,
                        "This department code already exists under the selected degree."
                    )
                    return redirect("department")

                Department.objects.create(
                    name=name,
                    code=code,
                    degree_id=degree_id
                )

                messages.success(request, "Department created successfully.")

            elif op == "edit":
                obj = get_object_or_404(Department, id=request.POST.get("id"))

                old_data = {
                    "Department Name": obj.name,
                    "Department Code": obj.code,
                    "Degree": obj.degree.degree if obj.degree else "—",
                }

                if not name or not code or not degree_id:
                    messages.error(request, "Name, Code and Degree are required.")
                    return redirect("department")

                # 🔐 Duplicate guard on update
                if Department.objects.exclude(id=obj.id).filter(
                    degree_id=degree_id,
                    name__iexact=name
                ).exists():
                    messages.error(
                        request,
                        "Another department with the same name exists under this degree."
                    )
                    return redirect("department")

                if Department.objects.exclude(id=obj.id).filter(
                    degree_id=degree_id,
                    code__iexact=code
                ).exists():
                    messages.error(
                        request,
                        "Another department with the same code exists under this degree."
                    )
                    return redirect("department")

                obj.name = name
                obj.code = code
                obj.degree_id = degree_id
                obj.save()

                # 📧 SEND AUDIT EMAIL (UPDATE)
                send_audit_mail(
                    title="Department Updated",
                    header="Department Update Notification",
                    action="Updated",
                    user=request.user,
                    description="A department record was updated in the admin panel.",
                    details={
                        "Department Name": obj.name,
                        "Department Code": obj.code,
                        "Degree": obj.degree.degree if obj.degree else "—",
                    },
                    previous=old_data,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Department updated successfully.")

            elif op == "delete":
                obj = get_object_or_404(Department, id=request.POST.get("id"))

                old_data = {
                    "Department Name": obj.name,
                    "Department Code": obj.code,
                    "Degree": obj.degree.degree if obj.degree else "—",
                }

                obj.delete()

                # 📧 SEND AUDIT EMAIL (DELETE → RED HEADER)
                send_audit_mail(
                    title="Department Deleted",
                    header="Department Deletion Notification",
                    action="Deleted",
                    user=request.user,
                    description="A department record was deleted from the admin panel.",
                    details=old_data,
                    previous=None,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Department deleted successfully.")

            else:
                messages.error(request, "Invalid operation.")

        except Exception:
            messages.error(request, "Unexpected error occurred.")
            raise  # remove in production if you want

        return redirect("department")

    departments = (
        Department.objects
        .select_related("degree")
        .order_by("degree__degree", "name")
    )

    degrees = Degree.objects.all().order_by("degree")

    return render(
        request,
        "faculty_requirement/admin/departments.html",
        {
            "departments": departments,
            "degrees": degrees
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def designation(request):

    if request.method == "POST":
        op = request.POST.get("operation")
        name = (request.POST.get("name") or "").strip()

        try:
            if op == "create":

                if not name:
                    messages.error(request, "Designation name is required.")
                    return redirect("designation")

                # 🔐 Duplicate guard
                if Designation.objects.filter(name__iexact=name).exists():
                    messages.error(
                        request,
                        "This designation already exists."
                    )
                    return redirect("designation")

                Designation.objects.create(name=name)
                messages.success(request, "Designation created successfully.")

            elif op == "edit":
                obj = get_object_or_404(Designation, id=request.POST.get("id"))

                old_data = {
                    "Designation Name": obj.name,
                }

                if not name:
                    messages.error(request, "Designation name is required.")
                    return redirect("designation")

                # 🔐 Duplicate guard on update
                if Designation.objects.exclude(id=obj.id).filter(
                    name__iexact=name
                ).exists():
                    messages.error(
                        request,
                        "Another designation with the same name already exists."
                    )
                    return redirect("designation")

                obj.name = name
                obj.save()

                # 📧 SEND AUDIT EMAIL (UPDATE)
                send_audit_mail(
                    title="Designation Updated",
                    header="Designation Update Notification",
                    action="Updated",
                    user=request.user,
                    description="A designation record was updated in the admin panel.",
                    details={
                        "Designation Name": obj.name,
                    },
                    previous=old_data,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Designation updated successfully.")

            elif op == "delete":
                obj = get_object_or_404(Designation, id=request.POST.get("id"))

                old_data = {
                    "Designation Name": obj.name,
                }

                obj.delete()

                # 📧 SEND AUDIT EMAIL (DELETE → RED HEADER)
                send_audit_mail(
                    title="Designation Deleted",
                    header="Designation Deletion Notification",
                    action="Deleted",
                    user=request.user,
                    description="A designation record was deleted from the admin panel.",
                    details=old_data,
                    previous=None,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Designation deleted successfully.")

            else:
                messages.error(request, "Invalid operation.")

        except Exception:
            messages.error(request, "Unexpected error occurred.")
            raise  # remove in production if needed

        return redirect("designation")

    designations = Designation.objects.all().order_by("name")
    return render(
        request,
        "faculty_requirement/admin/designation.html",
        {"designations": designations}
    )


@login_required
@require_http_methods(["GET", "POST"])
def level_of_education(request):

    if request.method == "POST":
        op = request.POST.get("operation")
        name = (request.POST.get("name") or "").strip()

        try:
            if op == "create":

                if not name:
                    messages.error(request, "Level name is required.")
                    return redirect("level_of_education")

                if LevelOfEducation.objects.filter(name__iexact=name).exists():
                    messages.error(request, "This level already exists.")
                    return redirect("level_of_education")

                LevelOfEducation.objects.create(name=name)
                messages.success(request, "Level created successfully.")

            elif op == "edit":
                obj = get_object_or_404(LevelOfEducation, id=request.POST.get("id"))

                old_data = {
                    "Level Name": obj.name,
                }

                if not name:
                    messages.error(request, "Level name is required.")
                    return redirect("level_of_education")

                if LevelOfEducation.objects.exclude(id=obj.id).filter(
                    name__iexact=name
                ).exists():
                    messages.error(
                        request,
                        "Another level with the same name already exists."
                    )
                    return redirect("level_of_education")

                obj.name = name
                obj.save()

                # 📧 AUDIT MAIL (UPDATE)
                send_audit_mail(
                    title="Level of Education Updated",
                    header="Level Update Notification",
                    action="Updated",
                    user=request.user,
                    description="A level of education was updated in the admin panel.",
                    details={"Level Name": obj.name},
                    previous=old_data,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Level updated successfully.")

            elif op == "delete":
                obj = get_object_or_404(LevelOfEducation, id=request.POST.get("id"))

                old_data = {
                    "Level Name": obj.name,
                }

                obj.delete()

                # 📧 AUDIT MAIL (DELETE)
                send_audit_mail(
                    title="Level of Education Deleted",
                    header="Level Deletion Notification",
                    action="Deleted",
                    user=request.user,
                    description="A level of education was deleted from the admin panel.",
                    details=old_data,
                    previous=None,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Level deleted successfully.")

            else:
                messages.error(request, "Invalid operation.")

        except Exception:
            messages.error(request, "Unexpected error occurred.")
            raise

        return redirect("level_of_education")

    levels = LevelOfEducation.objects.all().order_by("name")
    return render(
        request,
        "faculty_requirement/admin/level_of_education.html",
        {"levels": levels}
    )


@login_required
@require_http_methods(["GET", "POST"])
def document_type(request):

    if request.method == "POST":
        op = request.POST.get("operation")
        document_type_value = (request.POST.get("document_type") or "").strip()

        try:
            if op == "create":

                if not document_type_value:
                    messages.error(request, "Document Type is required.")
                    return redirect("document_type")

                if Document_Type.objects.filter(
                    document_type__iexact=document_type_value
                ).exists():
                    messages.error(request, "This document type already exists.")
                    return redirect("document_type")

                Document_Type.objects.create(
                    document_type=document_type_value
                )
                messages.success(request, "Document Type created successfully.")

            elif op == "edit":
                obj = get_object_or_404(Document_Type, id=request.POST.get("id"))

                old_data = {
                    "Document Type": obj.document_type,
                }

                if not document_type_value:
                    messages.error(request, "Document Type is required.")
                    return redirect("document_type")

                if Document_Type.objects.exclude(id=obj.id).filter(
                    document_type__iexact=document_type_value
                ).exists():
                    messages.error(
                        request,
                        "Another document type with the same name already exists."
                    )
                    return redirect("document_type")

                obj.document_type = document_type_value
                obj.save()

                # 📧 AUDIT MAIL (UPDATE)
                send_audit_mail(
                    title="Document Type Updated",
                    header="Document Type Update Notification",
                    action="Updated",
                    user=request.user,
                    description="A document type was updated in the admin panel.",
                    details={"Document Type": obj.document_type},
                    previous=old_data,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Document Type updated successfully.")

            elif op == "delete":
                obj = get_object_or_404(Document_Type, id=request.POST.get("id"))

                old_data = {
                    "Document Type": obj.document_type,
                }

                obj.delete()

                # 📧 AUDIT MAIL (DELETE)
                send_audit_mail(
                    title="Document Type Deleted",
                    header="Document Type Deletion Notification",
                    action="Deleted",
                    user=request.user,
                    description="A document type was deleted from the admin panel.",
                    details=old_data,
                    previous=None,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(request, "Document Type deleted successfully.")

            else:
                messages.error(request, "Invalid operation.")

        except Exception:
            messages.error(request, "Unexpected error occurred.")
            raise

        return redirect("document_type")

    document_types = Document_Type.objects.all().order_by("document_type")
    return render(
        request,
        "faculty_requirement/admin/document_type.html",
        {"document_types": document_types}
    )


@login_required
@require_http_methods(["GET", "POST"])
def certificate_permission(request):

    if request.method == "POST":
        op = request.POST.get("operation")

        department_id = request.POST.get("department")
        document_type_id = request.POST.get("document_type")
        is_required = request.POST.get("is_required") == "on"

        try:
            if op == "create":

                if not department_id or not document_type_id:
                    messages.error(
                        request,
                        "Department and Document Type are required."
                    )
                    return redirect("certificate_permission")

                if Certificate_Permission.objects.filter(
                    department_id=department_id,
                    document_type_id=document_type_id
                ).exists():
                    messages.error(
                        request,
                        "This document type is already assigned to this department."
                    )
                    return redirect("certificate_permission")

                Certificate_Permission.objects.create(
                    department_id=department_id,
                    document_type_id=document_type_id,
                    is_required=is_required
                )

                messages.success(
                    request,
                    "Certificate permission assigned successfully."
                )

            elif op == "edit":
                obj = get_object_or_404(
                    Certificate_Permission,
                    id=request.POST.get("id")
                )

                old_data = {
                    "Department": obj.department.name,
                    "Document Type": obj.document_type.document_type,
                    "Required": "Yes" if obj.is_required else "No",
                }

                if not department_id or not document_type_id:
                    messages.error(
                        request,
                        "Department and Document Type are required."
                    )
                    return redirect("certificate_permission")

                if Certificate_Permission.objects.exclude(id=obj.id).filter(
                    department_id=department_id,
                    document_type_id=document_type_id
                ).exists():
                    messages.error(
                        request,
                        "Another permission with the same department and document type already exists."
                    )
                    return redirect("certificate_permission")

                obj.department_id = department_id
                obj.document_type_id = document_type_id
                obj.is_required = is_required
                obj.save()

                # 📧 AUDIT MAIL (UPDATE)
                send_audit_mail(
                    title="Certificate Permission Updated",
                    header="Certificate Permission Update Notification",
                    action="Updated",
                    user=request.user,
                    description="A certificate permission was updated in the admin panel.",
                    details={
                        "Department": obj.department.name,
                        "Document Type": obj.document_type.document_type,
                        "Required": "Yes" if obj.is_required else "No",
                    },
                    previous=old_data,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(
                    request,
                    "Certificate permission updated successfully."
                )

            elif op == "delete":
                obj = get_object_or_404(
                    Certificate_Permission,
                    id=request.POST.get("id")
                )

                old_data = {
                    "Department": obj.department.name,
                    "Document Type": obj.document_type.document_type,
                    "Required": "Yes" if obj.is_required else "No",
                }

                obj.delete()

                # 📧 AUDIT MAIL (DELETE)
                send_audit_mail(
                    title="Certificate Permission Deleted",
                    header="Certificate Permission Deletion Notification",
                    action="Deleted",
                    user=request.user,
                    description="A certificate permission was deleted from the admin panel.",
                    details=old_data,
                    previous=None,
                    to_email=["vijayanand23102005@gmail.com"],
                )

                messages.success(
                    request,
                    "Certificate permission deleted successfully."
                )

            else:
                messages.error(request, "Invalid operation.")

        except Exception:
            messages.error(request, "Unexpected error occurred.")
            raise

        return redirect("certificate_permission")

    context = {
        "departments": Department.objects.all().order_by("name"),
        "document_types": Document_Type.objects.all().order_by("document_type"),
        "permissions": (
            Certificate_Permission.objects
            .select_related("department", "document_type")
            .order_by("department__name", "document_type__document_type")
        ),
    }

    return render(
        request,
        "faculty_requirement/admin/certificate_permission.html",
        context
    )

