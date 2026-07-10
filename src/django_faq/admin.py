# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from django.contrib import admin

from django_faq.models import FaqAssociation, FaqChannel, FaqGroup, FaqGroupT9N, FaqItem, FaqItemT9N
from django_faq.services import channel_service


class FaqGroupT9NInline(admin.TabularInline):
    model = FaqGroupT9N
    extra = 0


class FaqItemT9NInline(admin.TabularInline):
    model = FaqItemT9N
    extra = 0


class FaqAssociationInline(admin.TabularInline):
    model = FaqAssociation
    extra = 0


class FaqGroupAdmin(admin.ModelAdmin):
    list_display = ("idx", "name", "position", "is_active")
    list_filter = ("is_active",)
    search_fields = ["idx", "name"]
    ordering = ("position", "name")
    filter_horizontal = ("channels",)
    inlines = [FaqGroupT9NInline]


class FaqItemAdmin(admin.ModelAdmin):
    list_display = ("url_key", "question_short", "group", "position", "is_active")
    list_filter = ("is_active", "group")
    search_fields = ["url_key", "question"]
    ordering = ("position",)
    inlines = [FaqItemT9NInline, FaqAssociationInline]

    @admin.display(description="Question")
    def question_short(self, obj):
        return obj.question[:80]


@admin.action(description="Sync channels from PIM")
def sync_channels_from_pim(modeladmin, request, queryset):
    count = channel_service.sync_channels_from_pim()
    modeladmin.message_user(request, f"Synced {count} FAQ channels from PIM.")


class FaqChannelAdmin(admin.ModelAdmin):
    list_display = ("idx", "name", "default_language")
    search_fields = ["idx", "name"]
    actions = [sync_channels_from_pim]


admin.site.register(FaqChannel, FaqChannelAdmin)
admin.site.register(FaqGroup, FaqGroupAdmin)
admin.site.register(FaqItem, FaqItemAdmin)
admin.site.register(FaqGroupT9N)
admin.site.register(FaqItemT9N)
admin.site.register(FaqAssociation)
