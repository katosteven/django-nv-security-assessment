"""Views - hardened against vulnerabilities listed in report.txt.

Security-relevant changes (each marked with `# SECURITY:` inline):
  * upload(): SQL injection (B608) replaced by Django ORM
  * profile_by_id / change_password / forgot_password / reset_password:
    @csrf_exempt removed - CSRF protection re-enabled (CWE-352)
  * reset_password(): hardcoded "" reset_token replaced with None (B105)
  * Updated `is_authenticated()` -> `is_authenticated` (Django 5 property)
  * Replaced removed `render_to_response` / `RequestContext` with `render`
  * `users_assigned = [...]` (set assignment) replaced by `.set([...])`
"""
import datetime
import mimetypes
import os
import secrets
from pathlib import Path

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout
from django.contrib.auth.models import Group, User
from django.db import connection
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from taskManager.forms import ProfileForm, ProjectFileForm, UserForm
from taskManager.misc import store_uploaded_file
from taskManager.models import File, Notes, Project, Task, UserProfile


def manage_tasks(request, project_id):
    user = request.user
    proj = Project.objects.get(pk=project_id)

    if user.is_authenticated:
        if user.has_perm('can_change_task'):
            if request.method == 'POST':
                userid = request.POST.get("userid")
                taskid = request.POST.get("taskid")
                u = User.objects.get(pk=userid)
                task = Task.objects.get(pk=taskid)
                task.users_assigned.add(u)
                return redirect('/taskManager/')
            return render(request, 'taskManager/manage_tasks.html', {
                'tasks': Task.objects.filter(project=proj).order_by('title'),
                'users': User.objects.order_by('date_joined'),
            })
        return redirect('/taskManager/', {'permission': False})
    return redirect('/taskManager/', {'logged_in': False})


def manage_projects(request):
    user = request.user
    if user.is_authenticated:
        if user.has_perm('can_change_group'):
            if request.method == 'POST':
                userid = request.POST.get("userid")
                projectid = request.POST.get("projectid")
                u = User.objects.get(pk=userid)
                project = Project.objects.get(pk=projectid)
                project.users_assigned.add(u)
                return redirect('/taskManager/')
            return render(request, 'taskManager/manage_projects.html', {
                'projects': Project.objects.order_by('title'),
                'users': User.objects.order_by('date_joined'),
                'logged_in': True,
            })
        return redirect('/taskManager/', {'permission': False})
    return redirect('/taskManager/', {'logged_in': False})


def manage_groups(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('/taskManager/', {'logged_in': False})

    user_list = User.objects.order_by('date_joined')

    if request.method == 'POST':
        post_data = request.POST.dict()
        accesslevel = post_data.get("accesslevel", "").strip()
        if accesslevel in ['admin_g', 'project_managers', 'team_member']:
            grp, _ = Group.objects.get_or_create(name=accesslevel)
            try:
                specified_user = User.objects.get(pk=post_data.get("userid"))
            except (User.DoesNotExist, ValueError):
                return redirect('/taskManager/', {'permission': False})
            specified_user.groups.add(grp)
            specified_user.save()
            return render(request, 'taskManager/manage_groups.html',
                          {'users': user_list, 'groups_changed': True, 'logged_in': True})
        return render(request, 'taskManager/manage_groups.html',
                      {'users': user_list, 'logged_in': True})

    if user.has_perm('can_change_group'):
        return render(request, 'taskManager/manage_groups.html',
                      {'users': user_list, 'logged_in': True})
    return redirect('/taskManager/', {'permission': False})


def upload(request, project_id):
    if request.method == 'POST':
        proj = Project.objects.get(pk=project_id)
        form = ProjectFileForm(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            upload_path = store_uploaded_file(name, request.FILES['file'])

            # SECURITY: replaced raw string-formatted SQL (B608 / CWE-89)
            # with parameterised Django ORM call.
            File.objects.create(name=name, path=upload_path, project=proj)

            return redirect(f'/taskManager/{project_id}/',
                            {'new_file_added': True})
    form = ProjectFileForm()
    return render(request, 'taskManager/upload.html', {'form': form})


def download(request, file_id):
    f = File.objects.get(pk=file_id)
    # SECURITY: prevent path traversal - only serve files under uploads dir
    base = Path(__file__).resolve().parent
    target = (base / f.path.lstrip('/')).resolve()
    uploads_root = (base / 'static' / 'taskManager' / 'uploads').resolve()
    if not str(target).startswith(str(uploads_root)):
        raise Http404
    with open(target, 'rb') as fh:
        response = HttpResponse(content=fh.read())
    response['Content-Type'] = mimetypes.guess_type(f.path)[0] or 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{Path(f.name).name}"'
    return response


def download_profile_pic(request, user_id):
    user = User.objects.get(pk=user_id)
    filepath = user.userprofile.image
    if filepath and len(filepath) > 1:
        return redirect(filepath)
    return redirect('/static/taskManager/uploads/default.png')


def task_create(request, project_id):
    if request.method == 'POST':
        proj = Project.objects.get(pk=project_id)
        text = request.POST.get('text', '')
        task_title = request.POST.get('task_title', '')
        now = timezone.now()
        task_duedate = now + datetime.timedelta(weeks=1)
        if request.POST.get('task_duedate'):
            task_duedate = timezone.make_aware(datetime.datetime.fromtimestamp(
                int(request.POST.get('task_duedate'))))

        task = Task.objects.create(
            text=text, title=task_title,
            start_date=now, due_date=task_duedate, project=proj,
        )
        task.users_assigned.set([request.user])
        return redirect(f'/taskManager/{project_id}/', {'new_task_added': True})
    return render(request, 'taskManager/task_create.html', {'proj_id': project_id})


def task_edit(request, project_id, task_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    if request.method == 'POST':
        if task.project == proj:
            task.title = request.POST.get('task_title', '')
            task.text = request.POST.get('text', '')
            task.completed = request.POST.get('task_completed', '') == "1"
            task.save()
        return redirect(f'/taskManager/{project_id}/{task_id}')
    return render(request, 'taskManager/task_edit.html', {'task': task})


def task_delete(request, project_id, task_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    if task.project == proj:
        task.delete()
    return redirect(f'/taskManager/{project_id}/')


def task_complete(request, project_id, task_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    if task.project == proj:
        task.completed = not task.completed
        task.save()
    return redirect(f'/taskManager/{project_id}')


def project_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '')
        text = request.POST.get('text', '')
        project_priority = int(request.POST.get('project_priority') or 1)
        now = timezone.now()
        project_duedate = timezone.make_aware(datetime.datetime.fromtimestamp(
            int(request.POST.get('project_duedate'))))

        project = Project.objects.create(
            title=title, text=text, priority=project_priority,
            due_date=project_duedate, start_date=now,
        )
        project.users_assigned.set([request.user])
        return redirect('/taskManager/', {'new_project_added': True})
    return render(request, 'taskManager/project_create.html', {})


def project_edit(request, project_id):
    proj = Project.objects.get(pk=project_id)
    if request.method == 'POST':
        proj.title = request.POST.get('title', '')
        proj.text = request.POST.get('text', '')
        proj.priority = int(request.POST.get('project_priority') or 1)
        proj.due_date = timezone.make_aware(datetime.datetime.fromtimestamp(
            int(request.POST.get('project_duedate'))))
        proj.save()
        return redirect(f'/taskManager/{project_id}/')
    return render(request, 'taskManager/project_edit.html', {'proj': proj})


def project_delete(request, project_id):
    Project.objects.get(pk=project_id).delete()
    return redirect('/taskManager/dashboard')


def logout_view(request):
    logout(request)
    return redirect('/taskManager/')


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if User.objects.filter(username=username).exists():
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                auth_login(request, user)
                return redirect('/taskManager/')
            if user is not None:
                return redirect('/taskManager/', {'disabled_user': True})
            return render(request, 'taskManager/login.html', {'failed_login': False})
        return render(request, 'taskManager/login.html', {'invalid_username': False})
    return render(request, 'taskManager/login.html', {})


def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        if user_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            UserProfile.objects.create(user=user)
            registered = True
        else:
            print(user_form.errors)
    else:
        user_form = UserForm()
    return render(request, 'taskManager/register.html',
                  {'user_form': user_form, 'registered': registered})


def index(request):
    sorted_projects = Project.objects.order_by('-start_date')
    admin_level = request.user.is_authenticated and \
        request.user.groups.filter(name='admin_g').exists()

    if request.user.is_authenticated:
        return redirect('/taskManager/dashboard')
    return render(request, 'taskManager/index.html',
                  {'project_list': sorted_projects,
                   'user': request.user,
                   'admin_level': admin_level})


def profile_view(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('/taskManager/dashboard')

    if request.user.groups.filter(name='admin_g').exists():
        role = "Admin"
    elif request.user.groups.filter(name='project_managers').exists():
        role = "Project Manager"
    else:
        role = "Team Member"

    sorted_projects = Project.objects.filter(
        users_assigned=request.user.id).order_by('title')
    return render(request, 'taskManager/profile_view.html',
                  {'user': user, 'role': role, 'project_list': sorted_projects})


def project_details(request, project_id):
    proj = Project.objects.filter(
        users_assigned=request.user.id, pk=project_id)
    if not proj:
        messages.warning(request, 'You are not authorized to view this project')
        return redirect('/taskManager/dashboard')
    proj = Project.objects.get(pk=project_id)
    return render(request, 'taskManager/project_details.html',
                  {'proj': proj,
                   'user_can_edit': request.user.has_perm('project_edit')})


def note_create(request, project_id, task_id):
    if request.method == 'POST':
        parent_task = Task.objects.get(pk=task_id)
        Notes.objects.create(
            title=request.POST.get('note_title', ''),
            text=request.POST.get('text', ''),
            user=str(request.user),
            task=parent_task,
        )
        return redirect(f'/taskManager/{project_id}/{task_id}',
                        {'new_note_added': True})
    return render(request, 'taskManager/note_create.html', {'task_id': task_id})


def note_edit(request, project_id, task_id, note_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    note = Notes.objects.get(pk=note_id)
    if request.method == 'POST':
        if task.project == proj and note.task == task:
            note.title = request.POST.get('note_title', '')
            note.text = request.POST.get('text', '')
            note.save()
        return redirect(f'/taskManager/{project_id}/{task_id}')
    return render(request, 'taskManager/note_edit.html', {'note': note})


def note_delete(request, project_id, task_id, note_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    note = Notes.objects.get(pk=note_id)
    if task.project == proj and note.task == task:
        note.delete()
    return redirect(f'/taskManager/{project_id}/{task_id}')


def task_details(request, project_id, task_id):
    task = Task.objects.get(pk=task_id)
    logged_in = request.user.is_authenticated
    admin_level = logged_in and request.user.groups.filter(name='admin_g').exists()
    pmanager_level = logged_in and request.user.groups.filter(name='project_managers').exists()

    assigned_to = False
    if logged_in and task.users_assigned.filter(username=request.user.username).exists():
        assigned_to = True
    elif admin_level:
        assigned_to = True
    elif pmanager_level:
        assigned_to = task.project.users_assigned.filter(
            username=request.user.username).exists()

    return render(request, 'taskManager/task_details.html',
                  {'task': task,
                   'assigned_to': assigned_to,
                   'logged_in': logged_in,
                   'completed_task': "Yes" if task.completed else "No"})


def dashboard(request):
    return render(request, 'taskManager/dashboard.html', {
        'project_list': Project.objects.filter(
            users_assigned=request.user.id).order_by('title'),
        'task_list': Task.objects.filter(
            users_assigned=request.user.id).order_by('title'),
        'user': request.user,
    })


def project_list(request):
    return render(request, 'taskManager/project_list.html', {
        'project_list': Project.objects.filter(
            users_assigned=request.user.id).order_by('title'),
        'user': request.user,
        'user_can_edit': request.user.has_perm('project_edit'),
        'user_can_delete': request.user.has_perm('project_delete'),
        'user_can_add': request.user.has_perm('project_add'),
    })


def task_list(request):
    return render(request, 'taskManager/task_list.html', {
        'task_list': Task.objects.filter(users_assigned=request.user.id),
        'user': request.user,
    })


def search(request):
    query = request.GET.get('q', '')
    return render(request, 'taskManager/search.html', {
        'q': query,
        'task_list': Task.objects.filter(users_assigned=request.user.id)
                                  .filter(title__icontains=query).order_by('title'),
        'project_list': Project.objects.filter(users_assigned=request.user.id)
                                        .filter(title__icontains=query).order_by('title'),
        'user': request.user,
    })


def tutorials(request):
    return render(request, 'taskManager/tutorials.html', {'user': request.user})


def show_tutorial(request, vuln_id):
    allowed = {"injection", "brokenauth", "xss", "idor", "misconfig",
               "exposure", "access", "csrf", "components", "redirects"}
    if vuln_id in allowed:
        return render(request, f'taskManager/tutorials/{vuln_id}.html')
    return render(request, 'taskManager/tutorials.html', {'user': request.user})


def profile(request):
    return render(request, 'taskManager/profile.html', {'user': request.user})


# SECURITY: @csrf_exempt removed - CSRF protection now enforced (CWE-352)
def profile_by_id(request, user_id):
    user = User.objects.get(pk=user_id)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            for field in ('username', 'first_name', 'last_name', 'email'):
                val = request.POST.get(field)
                if val and getattr(user, field) != val:
                    setattr(user, field, val)
            if request.POST.get('password'):
                user.set_password(request.POST.get('password'))
            if request.FILES.get('picture'):
                pic = request.FILES['picture']
                fname = f"{user.username}.{Path(pic.name).suffix.lstrip('.')}"
                user.userprofile.image = store_uploaded_file(fname, pic)
                user.userprofile.save()
            user.save()
            messages.info(request, "User Updated")
    return render(request, 'taskManager/profile.html', {'user': user})


# SECURITY: @csrf_exempt removed (CWE-352). reset_token cleared with None (B105).
def reset_password(request):
    if request.method == 'POST':
        reset_token = request.POST.get('reset_token')
        try:
            userprofile = UserProfile.objects.get(reset_token=reset_token)
        except UserProfile.DoesNotExist:
            messages.warning(request, 'Invalid password reset token')
            return render(request, 'taskManager/reset_password.html')

        if timezone.now() > userprofile.reset_token_expiration:
            userprofile.reset_token_expiration = timezone.now()
            userprofile.reset_token = None  # SECURITY: explicit NULL (report 2.4)
            userprofile.save()
            return redirect('/taskManager/')

        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.warning(request, 'Passwords do not match')
            return render(request, 'taskManager/reset_password.html')

        userprofile.user.set_password(new_password)
        userprofile.reset_token = None  # SECURITY: explicit NULL (report 2.4)
        userprofile.reset_token_expiration = timezone.now()
        userprofile.user.save()
        userprofile.save()
        messages.success(request, 'Password has been successfully reset')
        return redirect('/taskManager/login')
    return render(request, 'taskManager/reset_password.html')


# SECURITY: @csrf_exempt removed (CWE-352)
def forgot_password(request):
    if request.method == 'POST':
        t_email = request.POST.get('email')
        try:
            reset_user = User.objects.get(email=t_email)
            # Cryptographically strong 6-digit token
            reset_token = f"{secrets.randbelow(1_000_000):06d}"
            reset_user.userprofile.reset_token = reset_token
            reset_user.userprofile.reset_token_expiration = (
                timezone.now() + datetime.timedelta(minutes=10))
            reset_user.userprofile.save()
            reset_user.email_user(
                "Reset your password",
                f"Use \"{reset_token}\" as your token at /taskManager/reset_password/. "
                "This token expires in 10 minutes.",
            )
        except User.DoesNotExist:
            # Same response prevents user enumeration
            pass
        messages.success(request, 'Check your email for a reset token')
        return redirect('/taskManager/reset_password')
    return render(request, 'taskManager/forgot_password.html')


# SECURITY: @csrf_exempt removed (CWE-352)
def change_password(request):
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if authenticate(username=user.username, password=old_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password Updated')
            else:
                messages.warning(request, 'Passwords do not match')
        else:
            messages.warning(request, 'Invalid Password')
    return render(request, 'taskManager/change_password.html', {'user': request.user})


def tm_settings(request):
    return render(request, 'taskManager/settings.html',
                  {'settings': request.META})
