from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from accounts.models import (
    User, TeamMembership, Service, Comment, ContactMessage,
    BlogPost, Conversation, ChatRequest
)


def is_admin(user):
    """Check if user is staff or superuser"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Custom Admin Dashboard"""
    context = {
        'active_page': 'admin_dashboard',
        'total_users': User.objects.count(),
        'total_team_members': TeamMembership.objects.count(),
        'total_services': Service.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_messages': ContactMessage.objects.count(),
        'total_blogs': BlogPost.objects.count(),
        'recent_users': User.objects.order_by('-join_date')[:5],
        'recent_messages': ContactMessage.objects.order_by('-created_at')[:5],
        'recent_comments': Comment.objects.order_by('-created_at')[:5],
    }
    return render(request, 'admin/dashboard.html', context)


# ==================== TEAM MEMBER MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def team_member_list(request):
    """List all team members"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    members = TeamMembership.objects.select_related('user').all()

    if search_query:
        members = members.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(role__icontains=search_query)
        )

    if role_filter:
        members = members.filter(role__icontains=role_filter)

    members = members.order_by('user__first_name')

    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'admin_team',
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'admin/team_list.html', context)


@login_required
@user_passes_test(is_admin)
def team_member_add(request):
    """Add new team member"""
    if request.method == 'POST':
        user_id = request.POST.get('user')
        role = request.POST.get('role')
        description = request.POST.get('description', '')
        instagram = request.POST.get('instagram', '')
        twitter = request.POST.get('twitter', '')
        facebook = request.POST.get('facebook', '')
        linkedin = request.POST.get('linkedin', '')
        youtube = request.POST.get('youtube', '')

        try:
            user = User.objects.get(id=user_id)

            # Check if already a team member
            if TeamMembership.objects.filter(user=user).exists():
                messages.error(request, 'This user is already a team member!')
                return redirect('team_member_add')

            TeamMembership.objects.create(
                user=user,
                role=role,
                description=description,
                instagram=instagram,
                twitter=twitter,
                facebook=facebook,
                linkedin=linkedin,
                youtube=youtube
            )

            messages.success(request, 'Team member added successfully!')
            return redirect('team_member_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    users = User.objects.exclude(
        id__in=TeamMembership.objects.values_list('user_id', flat=True)
    ).order_by('first_name')

    context = {
        'active_page': 'admin_team',
        'users': users,
    }
    return render(request, 'admin/team_form.html', context)


@login_required
@user_passes_test(is_admin)
def team_member_edit(request, pk):
    """Edit team member"""
    member = get_object_or_404(TeamMembership, pk=pk)

    if request.method == 'POST':
        member.role = request.POST.get('role')
        member.description = request.POST.get('description', '')
        member.instagram = request.POST.get('instagram', '')
        member.twitter = request.POST.get('twitter', '')
        member.facebook = request.POST.get('facebook', '')
        member.linkedin = request.POST.get('linkedin', '')
        member.youtube = request.POST.get('youtube', '')

        try:
            member.save()
            messages.success(request, 'Team member updated successfully!')
            return redirect('team_member_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context = {
        'active_page': 'admin_team',
        'member': member,
        'is_edit': True,
    }
    return render(request, 'admin/team_form.html', context)


@login_required
@user_passes_test(is_admin)
def team_member_delete(request, pk):
    """Delete team member"""
    member = get_object_or_404(TeamMembership, pk=pk)

    if request.method == 'POST':
        try:
            member.delete()
            messages.success(request, 'Team member deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('team_member_list')


# ==================== SERVICE MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def service_list(request):
    """List all services"""
    search_query = request.GET.get('search', '')

    services = Service.objects.prefetch_related('members').all()

    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    services = services.order_by('-created_at')

    paginator = Paginator(services, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'admin_services',
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin/service_list.html', context)


@login_required
@user_passes_test(is_admin)
def service_add(request):
    """Add new service"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        member_ids = request.POST.getlist('members')

        try:
            service = Service.objects.create(
                name=name,
                description=description
            )

            if member_ids:
                service.members.set(member_ids)

            messages.success(request, 'Service added successfully!')
            return redirect('service_list_admin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    team_members = TeamMembership.objects.select_related('user').order_by('user__first_name')

    context = {
        'active_page': 'admin_services',
        'team_members': team_members,
    }
    return render(request, 'admin/service_form.html', context)


@login_required
@user_passes_test(is_admin)
def service_edit(request, pk):
    """Edit service"""
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.description = request.POST.get('description', '')
        member_ids = request.POST.getlist('members')

        try:
            service.save()
            service.members.set(member_ids)
            messages.success(request, 'Service updated successfully!')
            return redirect('service_list_admin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    team_members = TeamMembership.objects.select_related('user').order_by('user__first_name')

    context = {
        'active_page': 'admin_services',
        'service': service,
        'team_members': team_members,
        'is_edit': True,
    }
    return render(request, 'admin/service_form.html', context)


@login_required
@user_passes_test(is_admin)
def service_delete(request, pk):
    """Delete service"""
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        try:
            service.delete()
            messages.success(request, 'Service deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('service_list_admin')


# ==================== USER MANAGEMENT ====================

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """List all users"""
    search_query = request.GET.get('search', '')
    filter_type = request.GET.get('filter', '')

    users = User.objects.all()

    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if filter_type == 'staff':
        users = users.filter(is_staff=True)
    elif filter_type == 'superuser':
        users = users.filter(is_superuser=True)
    elif filter_type == 'regular':
        users = users.filter(is_staff=False, is_superuser=False)

    users = users.order_by('-join_date')

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'admin_users',
        'page_obj': page_obj,
        'search_query': search_query,
        'filter_type': filter_type,
    }
    return render(request, 'admin/user_list.html', context)


# ==================== CONTACT MESSAGES ====================

@login_required
@user_passes_test(is_admin)
def message_list(request):
    """List all contact messages"""
    search_query = request.GET.get('search', '')

    messages_query = ContactMessage.objects.all()

    if search_query:
        messages_query = messages_query.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )

    messages_query = messages_query.order_by('-created_at')

    paginator = Paginator(messages_query, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'admin_messages',
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin/message_list.html', context)


@login_required
@user_passes_test(is_admin)
def message_delete(request, pk):
    """Delete contact message"""
    message = get_object_or_404(ContactMessage, pk=pk)

    if request.method == 'POST':
        try:
            message.delete()
            messages.success(request, 'Message deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('message_list_admin')


# ==================== COMMENTS/TESTIMONIALS ====================

@login_required
@user_passes_test(is_admin)
def comment_list(request):
    """List all comments"""
    search_query = request.GET.get('search', '')

    comments = Comment.objects.select_related('user').all()

    if search_query:
        comments = comments.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    comments = comments.order_by('-created_at')

    paginator = Paginator(comments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'admin_comments',
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin/comment_list.html', context)


@login_required
@user_passes_test(is_admin)
def comment_delete(request, pk):
    """Delete comment"""
    comment = get_object_or_404(Comment, pk=pk)

    if request.method == 'POST':
        try:
            comment.delete()
            messages.success(request, 'Comment deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('comment_list_admin')


# ==================== BLOG POSTS ====================

@login_required
@user_passes_test(is_admin)
def blog_list(request):
    """List all blog posts"""
    search_query = request.GET.get('search', '')

    blogs = BlogPost.objects.all()

    if search_query:
        blogs = blogs.filter(
            Q(theme__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    blogs = blogs.order_by('-created_at')

    paginator = Paginator(blogs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'active_page': 'admin_blogs',
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin/blog_list.html', context)


@login_required
@user_passes_test(is_admin)
def blog_add(request):
    """Add new blog post"""
    if request.method == 'POST':
        theme = request.POST.get('theme')
        content = request.POST.get('content', '')
        blog_file = request.FILES.get('file')

        try:
            BlogPost.objects.create(
                theme=theme,
                content=content,
                file=blog_file
            )
            messages.success(request, 'Blog post added successfully!')
            return redirect('blog_list_admin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context = {
        'active_page': 'admin_blogs',
    }
    return render(request, 'admin/blog_form.html', context)


@login_required
@user_passes_test(is_admin)
def blog_edit(request, pk):
    """Edit blog post"""
    blog = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        blog.theme = request.POST.get('theme')
        blog.content = request.POST.get('content', '')

        if request.FILES.get('file'):
            blog.file = request.FILES.get('file')

        try:
            blog.save()
            messages.success(request, 'Blog post updated successfully!')
            return redirect('blog_list_admin')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context = {
        'active_page': 'admin_blogs',
        'blog': blog,
        'is_edit': True,
    }
    return render(request, 'admin/blog_form.html', context)


@login_required
@user_passes_test(is_admin)
def blog_delete(request, pk):
    """Delete blog post"""
    blog = get_object_or_404(BlogPost, pk=pk)

    if request.method == 'POST':
        try:
            blog.delete()
            messages.success(request, 'Blog post deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return redirect('blog_list_admin')
