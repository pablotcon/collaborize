from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile, Experience, Proyecto, Application, Modalidad, Categoria
from .forms import UserProfileForm, UsuarioForm, ExperienceForm, ContactoForm, CustomUserCreationForm, ProyectoForm, ProyectoSearchForm, ApplicationForm
from django.core.mail import send_mail
from djmoney.money import Money

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def chat(request):
    return render(request, 'chat.html')

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    experiences = Experience.objects.filter(user_profile=user_profile)
    default_avatar = 'static/img/default-avatar.png'

    context = {
        'user_profile': user_profile,
        'experiences': experiences,
        'default_avatar': default_avatar,
    }

    return render(request, 'perfil/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    profile = user.userprofile

    if request.method == 'POST':
        user_form = UsuarioForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')  # Reemplaza 'profile' con la URL de la página de perfil
    else:
        if isinstance(profile.hourly_rate, (int, float)):
            profile.hourly_rate = Money(profile.hourly_rate, 'USD')
        user_form = UsuarioForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'perfil/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'experience_form': ExperienceForm()
    })

@login_required
def add_experience(request, experience_id=None):
    if experience_id:
        experience = get_object_or_404(Experience, id=experience_id, user_profile__user=request.user)
    else:
        experience = Experience(user_profile=request.user.userprofile)

    if request.method == 'POST':
        experience_form = ExperienceForm(request.POST, instance=experience)
        if experience_form.is_valid():
            experience_form.save()
            messages.success(request, "Experiencia actualizada correctamente")
            return redirect('profile')
    else:
        experience_form = ExperienceForm(instance=experience)

    return render(request, 'perfil/edit_experience.html', {'experience_form': experience_form})

def projects(request):
    form = ProyectoSearchForm(request.GET or None)
    proyectos = Proyecto.objects.all()

    if request.method == 'GET' and form.is_valid():
        nombre = form.cleaned_data.get('nombre')
        modalidad = form.cleaned_data.get('modalidad')
        categoria = form.cleaned_data.get('categoria')
        salario = form.cleaned_data.get('salario')

        if nombre:
            proyectos = proyectos.filter(nombre__icontains=nombre)
        if modalidad:
            proyectos = proyectos.filter(modalidad=modalidad)
        if categoria:
            proyectos = proyectos.filter(categoria=categoria)
        if salario:
            proyectos = proyectos.filter(salario__gte=salario)

    return render(request, 'projects.html', {'proyectos': proyectos, 'form': form})

def project_detail(request, project_id):
    proyecto = get_object_or_404(Proyecto, id=project_id)
    return render(request, 'project_detail.html', {'proyecto': proyecto})

@login_required
def agregar_proyecto(request):
    if request.method == 'POST':
        form = ProyectoForm(request.POST, request.FILES)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.usuario = request.user  # Asocia el proyecto con el usuario actual
            proyecto.save()
            print(f"Proyecto creado: {proyecto.nombre}, Usuario: {proyecto.usuario.username}")  # Log para verificar
            messages.success(request, "Proyecto guardado correctamente")
            return redirect('mis_proyectos')
    else:
        form = ProyectoForm()
    
    return render(request, 'proyecto/agregar.html', {'form': form})

@login_required
def mis_proyectos(request):
    proyectos = Proyecto.objects.filter(usuario=request.user)
    return render(request, 'proyecto/mis_proyectos.html', {'proyectos': proyectos})

@login_required
def listar_proyecto(request):
    proyectos = Proyecto.objects.all()
    return render(request, 'proyecto/listar.html', {'proyectos': proyectos})

@login_required
def apply_to_project(request, project_id):
    project = get_object_or_404(Proyecto, id=project_id)
    user = request.user

    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application, created = Application.objects.get_or_create(user=user, project=project)
            if created:
                application.save()
                messages.success(request, "Te has postulado correctamente al proyecto.")
                
                # Enviar notificación al creador del proyecto
                creator = project.usuario
                send_mail(
                    'Nueva solicitud de aplicación',
                    f'{user.username} se ha postulado a tu proyecto: {project.nombre}.',
                    'pablotcon@outlook.com',
                    [creator.email],
                    fail_silently=False,
                )
                messages.info(request, "El creador del proyecto ha sido notificado.")
            else:
                messages.warning(request, "Ya te has postulado a este proyecto.")
            return render(request, 'apply_to_project.html', {'form': form, 'project': project})
    else:
        form = ApplicationForm(initial={'project': project})

    return render(request, 'apply_to_project.html', {'form': form, 'project': project})

@login_required
def manage_applications(request):
    projects = Proyecto.objects.filter(usuario=request.user)
    applications = Application.objects.filter(project__in=projects)
    return render(request, 'perfil/manage_applications.html', {'applications': applications})

@login_required
def update_application_status(request, application_id, status):
    application = get_object_or_404(Application, id=application_id)
    if application.project.usuario != request.user:
        messages.error(request, "No tienes permiso para actualizar esta aplicación.")
    else:
        application.status = status
        application.save()
        messages.success(request, f"El estado de la aplicación ha sido actualizado a {application.get_status_display()}.")
    return redirect('manage_applications')

@login_required
def my_applications(request):
    applications = Application.objects.filter(user=request.user)
    return render(request, 'perfil/my_applications.html', {'applications': applications})

def contact(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Formulario enviado correctamente")
            return redirect('contact')
    else:
        form = ContactoForm()

    return render(request, 'contact.html', {'form': form})

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, "Te has registrado correctamente")
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/registro.html', {'form': form})
