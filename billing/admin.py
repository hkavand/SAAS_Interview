from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "username",
        "email",
        "subscription_status",
        "current_plan",
        "total_amount_paid",
        "is_staff",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Subscription Info",
            {
                "fields": (
                    "subscription_status",
                    "current_plan",
                    "total_amount_paid",
                )
            },
        ),
    )
