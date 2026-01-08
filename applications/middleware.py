from applications.models import VisitorLog


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


class VisitorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log only faculty application page visits
        if request.path == "/faculty/apply/":
            try:
                VisitorLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get("HTTP_USER_AGENT", ""),
                    device_type="Mobile"
                    if "Mobile" in request.META.get("HTTP_USER_AGENT", "")
                    else "Desktop",
                    path=request.path,
                    method=request.method,
                )
            except Exception:
                pass

        return response
