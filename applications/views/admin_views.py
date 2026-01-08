from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Count, Max


from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from applications.models import AdminLoginLog, VisitorLog, ApplicationUsageLog, AdminPasswordOTP


def is_admin(user):
    return user.is_authenticated and user.is_superuser and user.is_active

@csrf_protect
def admin_login(request):

    # Already authenticated
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect("admin_dashboard")
        return HttpResponseForbidden("Unauthorized")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        ip = get_client_ip(request)
        ua = get_user_agent(request)

        user = authenticate(request, username=username, password=password)

        if user and is_admin(user):
            # ✅ Django already protects against session fixation
            login(request, user)

            # ✅ Rotate session key SAFELY (no CSRF break)
            request.session.cycle_key()

            AdminLoginLog.objects.create(
                user=user,
                username_attempted=username,
                action="LOGIN_SUCCESS",
                ip_address=ip,
                user_agent=ua,
                session_key=request.session.session_key,
            )

            return redirect("admin_home")

        # ❗ Failed login audit
        AdminLoginLog.objects.create(
            user=None,
            username_attempted=username,
            action="LOGIN_FAILED",
            ip_address=ip,
            user_agent=ua,
        )

        messages.error(request, "Invalid admin credentials")

    return render(request, "faculty_requirement/admin/admin_login.html")




@login_required(login_url="admin_login")
@user_passes_test(is_admin, login_url="admin_login")
def admin_dashboard(request):
    """
    Admin-only dashboard
    """
    return render(request, "faculty_requirement/admin/admin_dashboard.html")


@login_required(login_url="admin_login")
def admin_logout(request):
    AdminLoginLog.objects.create(
        user=request.user,
        username_attempted=request.user.username,
        action="LOGOUT",
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        session_key=request.session.session_key,
    )

    logout(request)
    request.session.flush()
    return redirect("/")

def logs(request):
    return render(request, "faculty_requirement/admin/logs.html")


@login_required(login_url="admin_login")
@user_passes_test(is_admin)
def admin_logs(request):

    # ---------------- BASE QUERYSET ----------------
    base_qs = AdminLoginLog.objects.all()

    # ---------------- FILTER VALUES ----------------
    username = request.GET.get("username", "")
    action = request.GET.get("action", "")
    ip = request.GET.get("ip", "")
    ua = request.GET.get("ua", "")

    if username:
        base_qs = base_qs.filter(username_attempted=username)

    if action:
        base_qs = base_qs.filter(action=action)

    if ip:
        base_qs = base_qs.filter(ip_address=ip)

    if ua:
        base_qs = base_qs.filter(user_agent=ua)

    # ---------------- ANALYTICS (FILTER AWARE) ----------------
    analytics = {
        "total": base_qs.count(),
        "success": base_qs.filter(action="LOGIN_SUCCESS").count(),
        "failed": base_qs.filter(action="LOGIN_FAILED").count(),
        "unique_users": base_qs.values("username_attempted").distinct().count(),
        "unique_ips": base_qs.values("ip_address").distinct().count(),
        "last_login": base_qs.aggregate(last=Max("timestamp"))["last"],
    }

    # ---------------- LOG TABLE ----------------
    logs_qs = (
        base_qs.only(
            "timestamp",
            "username_attempted",
            "action",
            "ip_address",
            "user_agent",
        )
        .order_by("-timestamp")
    )

    paginator = Paginator(logs_qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ---------------- DROPDOWNS (NO DUPLICATES – MySQL SAFE) ----------------
    usernames = (
        AdminLoginLog.objects
        .exclude(username_attempted__isnull=True)
        .exclude(username_attempted="")
        .order_by("username_attempted")
        .values_list("username_attempted", flat=True)
        .distinct()[:200]
    )

    ips = (
        AdminLoginLog.objects
        .exclude(ip_address__isnull=True)
        .order_by("ip_address")
        .values_list("ip_address", flat=True)
        .distinct()[:200]
    )

    user_agents = (
        AdminLoginLog.objects
        .exclude(user_agent__isnull=True)
        .exclude(user_agent="")
        .order_by("user_agent")
        .values_list("user_agent", flat=True)
        .distinct()[:200]
    )

    return render(
        request,
        "faculty_requirement/admin/admin_logs.html",
        {
            "page_obj": page_obj,
            "analytics": analytics,
            "usernames": usernames,
            "ips": ips,
            "user_agents": user_agents,
            "filters": {
                "username": username,
                "action": action,
                "ip": ip,
                "ua": ua,
            },
        },
    )

import random
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta

def generate_otp():
    return str(random.randint(100000, 999999))

def hash_otp(otp):
    return make_password(otp)

def otp_expiry(minutes=10):
    return timezone.now() + timedelta(minutes=minutes)


from django.core.mail import send_mail
from django.conf import settings

def send_admin_otp(email, otp):
    send_mail(
        subject="Admin Password Reset OTP",
        message=f"""
Your OTP for admin password reset is: {otp}

This OTP is valid for 10 minutes.
If you didn’t request this, ignore this email.
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_protect
def admin_forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        request.session['admin_email'] = email
        ip = get_client_ip(request)

        user = User.objects.filter(
            email__iexact=email,
            is_active=True
        ).first()

        # ❌ Don’t leak user existence
        if not user or not is_admin(user):
            messages.success(
                request,
                "If the email exists, an OTP has been sent."
            )
            return redirect("admin_forgot_password")

        otp = generate_otp()

        AdminPasswordOTP.objects.create(
            user=user,
            otp_hash=hash_otp(otp),
            expires_at=otp_expiry(),
            ip_address=ip
        )

        send_admin_otp(user.email, otp)

        messages.success(request, "OTP sent to your email.")
        request.session["reset_admin_id"] = user.id
        return redirect("admin_verify_otp")

    return render(request, "faculty_requirement/admin/admin_forgot_password.html")


@csrf_protect
def admin_verify_otp(request):
    admin_id = request.session.get("reset_admin_id")

    email = request.session.get("admin_email", "")
    if not admin_id:
        return redirect("admin_login")

    if request.method == "POST":
        otp = request.POST.get("otp", "").strip()
        new_password = request.POST.get("password")

        record = (
            AdminPasswordOTP.objects
            .filter(
                user_id=admin_id,
                is_used=False,
                expires_at__gte=timezone.now()
            )
            .order_by("-created_at")
            .first()
        )

        if not record or not check_password(otp, record.otp_hash):
            messages.error(request, "Invalid or expired OTP")
            return redirect("admin_verify_otp")

        user = record.user
        user.set_password(new_password)
        user.save(update_fields=["password"])

        record.is_used = True
        record.save(update_fields=["is_used"])

        request.session.pop("reset_admin_id", None)

        messages.success(request, "Password reset successful")
        return redirect("admin_login")

    return render(request, "faculty_requirement/admin/admin_verify_otp.html", {"email": email})


# @login_required(login_url="admin_login")
# @user_passes_test(is_admin)
# def user_logs(request):

#     base_qs = VisitorLog.objects.select_related("user").all()

#     # ---------------- FILTERS ----------------
#     user_id = request.GET.get("user", "")
#     ip = request.GET.get("ip", "")
#     device = request.GET.get("device", "")
#     method = request.GET.get("method", "")

#     if user_id:
#         base_qs = base_qs.filter(user__id=user_id)

#     if ip:
#         base_qs = base_qs.filter(ip_address=ip)

#     if device:
#         base_qs = base_qs.filter(device_type=device)

#     if method:
#         base_qs = base_qs.filter(method=method)

#     # ---------------- ANALYTICS ----------------
#     analytics = {
#         "total": base_qs.count(),
#         "authenticated": base_qs.filter(user__isnull=False).count(),
#         "anonymous": base_qs.filter(user__isnull=True).count(),
#         "unique_ips": base_qs.values("ip_address").distinct().count(),
#         "last_activity": base_qs.aggregate(last=Max("timestamp"))["last"],
#     }

#     # ---------------- TABLE ----------------
#     logs_qs = (
#         base_qs.only(
#             "timestamp",
#             "user",
#             "ip_address",
#             "device_type",
#             "path",
#             "method",
#             "user_agent",
#         )
#         .order_by("-timestamp")
#     )

#     paginator = Paginator(logs_qs, 50)
#     page_obj = paginator.get_page(request.GET.get("page"))

#     # ---------------- DROPDOWNS ----------------
#     users = (
#         VisitorLog.objects
#         .exclude(user__isnull=True)
#         .values("user__id", "user__username")
#         .distinct()[:200]
#     )

#     ips = (
#         VisitorLog.objects
#         .order_by("ip_address")
#         .values_list("ip_address", flat=True)
#         .distinct()[:200]
#     )

#     return render(
#         request,
#         "faculty_requirement/admin/user_logs.html",
#         {
#             "page_obj": page_obj,
#             "analytics": analytics,
#             "users": users,
#             "ips": ips,
#             "filters": {
#                 "user": user_id,
#                 "ip": ip,
#                 "device": device,
#                 "method": method,
#             },
#         },
#     )


@login_required(login_url="admin_login")
@user_passes_test(is_admin)
def user_logs(request):

    # ---------------- BASE QUERYSET ----------------
    base_qs = (
        ApplicationUsageLog.objects
        .select_related("candidate")
        .all()
    )

    # ---------------- FILTERS ----------------
    candidate_id = request.GET.get("candidate", "")
    action = request.GET.get("action", "")
    ip = request.GET.get("ip", "")
    device = request.GET.get("device", "")

    if candidate_id:
        base_qs = base_qs.filter(candidate__id=candidate_id)

    if action:
        base_qs = base_qs.filter(action=action)

    if ip:
        base_qs = base_qs.filter(ip_address=ip)

    if device:
        base_qs = base_qs.filter(device_type=device)

    # ---------------- ANALYTICS ----------------
    analytics = {
        "total": base_qs.count(),
        "submitted": base_qs.filter(action="FORM_SUBMITTED").count(),
        "unique_candidates": base_qs.values("candidate").distinct().count(),
        "unique_ips": base_qs.values("ip_address").distinct().count(),
        "last_activity": base_qs.aggregate(last=Max("timestamp"))["last"],
    }

    # ---------------- TABLE ----------------
    logs_qs = (
        base_qs.only(
            "timestamp",
            "candidate",
            "action",
            "ip_address",
            "device_type",
            "user_agent",
        )
        .order_by("-timestamp")
    )

    paginator = Paginator(logs_qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ---------------- DROPDOWNS ----------------
    candidates = (
        ApplicationUsageLog.objects
        .values("candidate__id", "candidate__name")
        .distinct()[:200]
    )

    ips = (
        ApplicationUsageLog.objects
        .order_by("ip_address")
        .values_list("ip_address", flat=True)
        .distinct()[:200]
    )

    return render(
        request,
        "faculty_requirement/admin/user_logs.html",
        {
            "page_obj": page_obj,
            "analytics": analytics,
            "candidates": candidates,
            "ips": ips,
            "filters": {
                "candidate": candidate_id,
                "action": action,
                "ip": ip,
                "device": device,
            },
        },
    )




def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "unknown")
