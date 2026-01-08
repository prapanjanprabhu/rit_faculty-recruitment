# admin.py
from django.contrib import admin
from applications.models import AdminLoginLog

@admin.register(AdminLoginLog)
class AdminLoginLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "username_attempted",
        "action",
        "ip_address",
    )
    list_filter = ("action", "timestamp")
    search_fields = ("username_attempted", "ip_address")

    readonly_fields = [f.name for f in AdminLoginLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
