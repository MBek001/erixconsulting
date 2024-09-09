from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ContactMessage, TeamMembership, Service, Comment, Conversation, About



class UsersAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff', 'is_superuser', 'profile_picture'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')
admin.site.register(User, UsersAdmin)


class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

admin.site.register(ContactMessage, ContactMessageAdmin)


class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'instagram', 'twitter', 'facebook', 'youtube', 'linkedin')
    search_fields = ('user__email', 'role')
    ordering = ('user',)

admin.site.register(TeamMembership, TeamMembershipAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)
    filter_horizontal = ('members',)

admin.site.register(Service, ServiceAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'created_at')
    search_fields = ('user__email', 'service__name')
    ordering = ('-created_at',)

admin.site.register(Comment, CommentAdmin)


class ConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'staff', 'created_at')
    search_fields = ('user__email', 'staff__user__email')
    ordering = ('-created_at',)

admin.site.register(Conversation, ConversationAdmin)


class AboutAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_phone')
    search_fields = ('company_name',)
    ordering = ('company_name',)

admin.site.register(About, AboutAdmin)
