from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count
from accounts.models import (
    User, ContactMessage, TeamMembership, Service, Comment,
    Conversation, BlogPost, CharAi, TelegramUserMessage, ChatRequest, RequestHistory
)


# Custom Admin Site Configuration
admin.site.site_header = "Eric's Consulting Administration"
admin.site.site_title = "Eric's Consulting Admin"
admin.site.index_title = "Welcome to Eric's Consulting Admin Panel"


class UsersAdmin(BaseUserAdmin):
    """Enhanced User Admin with better display and functionality"""
    list_display = ('email', 'full_name', 'phone_number', 'profile_preview', 'is_staff_badge', 'join_date')
    list_filter = ('is_staff', 'is_superuser', 'join_date')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-join_date',)
    list_per_page = 25

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'

    def profile_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return format_html('<span style="color: #999;">No image</span>')
    profile_preview.short_description = 'Profile Picture'

    def is_staff_badge(self, obj):
        if obj.is_staff:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">Staff</span>')
        return format_html('<span style="background: #6c757d; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">User</span>')
    is_staff_badge.short_description = 'Status'

    fieldsets = (
        ('Account Credentials', {'fields': ('email', 'password')}),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone_number', 'profile_picture'),
            'description': 'User personal details and contact information'
        }),
        ('Permissions & Access', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {'fields': ('last_login', 'join_date'), 'classes': ('collapse',)}),
    )

    add_fieldsets = (
        ('Create New User', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'password1', 'password2', 'is_staff', 'is_superuser', 'profile_picture'),
            'description': 'Fill in the required fields to create a new user account'
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')
    readonly_fields = ('join_date', 'last_login')


admin.site.register(User, UsersAdmin)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Enhanced Contact Message Admin"""
    list_display = ('name', 'email', 'subject', 'message_preview', 'created_at_formatted')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'formatted_message')
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'

    def message_preview(self, obj):
        if len(obj.message) > 50:
            return obj.message[:50] + '...'
        return obj.message
    message_preview.short_description = 'Message Preview'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%b %d, %Y %I:%M %p')
    created_at_formatted.short_description = 'Received On'
    created_at_formatted.admin_order_field = 'created_at'

    def formatted_message(self, obj):
        return format_html('<div style="padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.6;">{}</div>', obj.message)
    formatted_message.short_description = 'Full Message'

    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email')
        }),
        ('Message Details', {
            'fields': ('subject', 'formatted_message')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        # Custom action example
        count = queryset.count()
        self.message_user(request, f'{count} message(s) marked as read.')
    mark_as_read.short_description = "Mark selected messages as read"


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    """Enhanced Team Membership Admin with social links"""
    list_display = ('member_info', 'role_badge', 'social_links_preview', 'services_count')
    list_filter = ('role',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'role', 'description')
    ordering = ('user__first_name',)
    list_per_page = 20
    autocomplete_fields = ['user']

    def member_info(self, obj):
        if obj.user.profile_picture:
            img = f'<img src="{obj.user.profile_picture.url}" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover; margin-right: 10px; vertical-align: middle;" />'
        else:
            img = '<div style="width: 35px; height: 35px; border-radius: 50%; background: #007bff; display: inline-flex; align-items: center; justify-content: center; color: white; margin-right: 10px; vertical-align: middle; font-size: 14px;">👤</div>'
        return format_html(
            '{}<strong>{} {}</strong><br><small style="color: #666;">{}</small>',
            img, obj.user.first_name, obj.user.last_name, obj.user.email
        )
    member_info.short_description = 'Team Member'

    def role_badge(self, obj):
        colors = {
            'CEO': '#dc3545',
            'Manager': '#007bff',
            'Developer': '#28a745',
            'Designer': '#ffc107',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: 600;">{}</span>',
            color, obj.role
        )
    role_badge.short_description = 'Role'

    def social_links_preview(self, obj):
        links = []
        if obj.instagram:
            links.append('<a href="{}" target="_blank" style="margin-right: 8px; font-size: 16px;">📷</a>'.format(obj.instagram))
        if obj.twitter:
            links.append('<a href="{}" target="_blank" style="margin-right: 8px; font-size: 16px;">🐦</a>'.format(obj.twitter))
        if obj.facebook:
            links.append('<a href="{}" target="_blank" style="margin-right: 8px; font-size: 16px;">📘</a>'.format(obj.facebook))
        if obj.linkedin:
            links.append('<a href="{}" target="_blank" style="margin-right: 8px; font-size: 16px;">💼</a>'.format(obj.linkedin))
        if obj.youtube:
            links.append('<a href="{}" target="_blank" style="margin-right: 8px; font-size: 16px;">📹</a>'.format(obj.youtube))

        return format_html(''.join(links)) if links else format_html('<span style="color: #999;">No links</span>')
    social_links_preview.short_description = 'Social Media'

    def services_count(self, obj):
        count = obj.service_set.count()
        return format_html('<span style="background: #e7f3ff; color: #0066cc; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{} service(s)</span>', count)
    services_count.short_description = 'Assigned Services'

    fieldsets = (
        ('Member Details', {
            'fields': ('user', 'role', 'description')
        }),
        ('Social Media Links', {
            'fields': ('instagram', 'twitter', 'facebook', 'linkedin', 'youtube'),
            'classes': ('collapse',),
            'description': 'Add social media profile URLs for this team member'
        }),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Enhanced Service Admin with member management"""
    list_display = ('name', 'description_preview', 'members_count', 'created_at_badge')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    list_per_page = 20
    filter_horizontal = ('members',)
    date_hierarchy = 'created_at'

    def description_preview(self, obj):
        if obj.description and len(obj.description) > 60:
            return obj.description[:60] + '...'
        return obj.description or format_html('<span style="color: #999;">No description</span>')
    description_preview.short_description = 'Description'

    def members_count(self, obj):
        count = obj.members.count()
        if count == 0:
            return format_html('<span style="color: #dc3545;">⚠️ No members</span>')
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">👥 {} member(s)</span>',
            count
        )
    members_count.short_description = 'Team Members'

    def created_at_badge(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_badge.short_description = 'Created On'
    created_at_badge.admin_order_field = 'created_at'

    fieldsets = (
        ('Service Information', {
            'fields': ('name', 'description'),
            'description': 'Basic information about the service'
        }),
        ('Team Assignment', {
            'fields': ('members',),
            'description': 'Select team members who will handle this service'
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Enhanced Comment/Testimonial Admin"""
    list_display = ('user_info', 'content_preview', 'has_image', 'created_at_formatted')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'content')
    ordering = ('-created_at',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'image_preview')

    def user_info(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_info.short_description = 'User'

    def content_preview(self, obj):
        if len(obj.content) > 80:
            return obj.content[:80] + '...'
        return obj.content
    content_preview.short_description = 'Comment'

    def has_image(self, obj):
        if obj.image:
            return format_html('<span style="color: #28a745;">✓ Yes</span>')
        return format_html('<span style="color: #999;">✗ No</span>')
    has_image.short_description = 'Has Image'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_formatted.short_description = 'Posted On'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 300px; border-radius: 8px;" />', obj.image.url)
        return format_html('<span style="color: #999;">No image uploaded</span>')
    image_preview.short_description = 'Image Preview'

    fieldsets = (
        ('Comment Details', {
            'fields': ('user', 'content')
        }),
        ('Media', {
            'fields': ('image', 'image_preview'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Enhanced Conversation Admin"""
    list_display = ('user', 'staff_member', 'has_file', 'created_at_formatted')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'staff__user__email')
    ordering = ('-created_at',)
    list_per_page = 25
    readonly_fields = ('created_at',)

    def staff_member(self, obj):
        if obj.staff:
            return f"{obj.staff.user.first_name} {obj.staff.user.last_name}"
        return format_html('<span style="color: #999;">Not assigned</span>')
    staff_member.short_description = 'Assigned Staff'

    def has_file(self, obj):
        if obj.conversation_file:
            return format_html('<a href="{}" target="_blank">📎 View File</a>', obj.conversation_file.url)
        return format_html('<span style="color: #999;">No file</span>')
    has_file.short_description = 'Attachment'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%b %d, %Y %I:%M %p')
    created_at_formatted.short_description = 'Created On'


@admin.register(BlogPost)
class BlogAdmin(admin.ModelAdmin):
    """Enhanced Blog Post Admin"""
    list_display = ('theme', 'content_preview', 'has_file', 'created_at_badge')
    list_filter = ('created_at',)
    search_fields = ('theme', 'content')
    ordering = ('-created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'file_preview')

    def content_preview(self, obj):
        if obj.content and len(obj.content) > 100:
            return obj.content[:100] + '...'
        return obj.content or format_html('<span style="color: #999;">No content</span>')
    content_preview.short_description = 'Content Preview'

    def has_file(self, obj):
        if obj.file:
            return format_html('<span style="color: #28a745;">✓ Has file</span>')
        return format_html('<span style="color: #999;">✗ No file</span>')
    has_file.short_description = 'Media'

    def created_at_badge(self, obj):
        return obj.created_at.strftime('%b %d, %Y')
    created_at_badge.short_description = 'Published On'

    def file_preview(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank" class="button">View File</a>', obj.file.url)
        return format_html('<span style="color: #999;">No file uploaded</span>')
    file_preview.short_description = 'File'

    fieldsets = (
        ('Blog Post', {
            'fields': ('theme', 'content')
        }),
        ('Media', {
            'fields': ('file', 'file_preview'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Register additional models if needed
@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    """Chat Request Admin"""
    list_display = ('user_info', 'status_badge', 'staff_assigned', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('username', 'reason')
    ordering = ('-created_at',)

    def user_info(self, obj):
        return f"{obj.username} ({obj.chat_id})"
    user_info.short_description = 'User'

    def status_badge(self, obj):
        colors = {'open': '#ffc107', 'assigned': '#28a745', 'closed': '#6c757d'}
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'

    def staff_assigned(self, obj):
        if obj.assigned_staff:
            return f"{obj.assigned_staff.user.first_name} {obj.assigned_staff.user.last_name}"
        return format_html('<span style="color: #999;">Not assigned</span>')
    staff_assigned.short_description = 'Assigned To'


# Custom admin CSS
class CustomAdminSite(admin.AdminSite):
    """Custom admin site with enhanced styling"""
    site_header = "Eric's Consulting Administration"
    site_title = "Eric's Consulting Admin"
    index_title = "Dashboard"
