from django.contrib import admin

from .models import Ticket, TicketMessage


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("user", "subject", "category", "status", "priority", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("user__email", "subject")


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ("ticket", "sender", "created_at")
    search_fields = ("ticket__subject", "sender__email", "message")
