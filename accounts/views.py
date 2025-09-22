from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            error = "Usuario o contraseña incorrectos"
    return render(request, 'accounts/login.html', {'error': error})

# Vista de confirmación de logout (GET muestra la página, POST confirma y cierra sesión)
def logout_view(request):
    if request.method == "POST":  # Si el usuario confirma
        logout(request)
        return redirect("login")
    return render(request, "accounts/confirm_logout.html")  # Muestra la confirmación

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/registro.html', {'form': form})

@login_required
def home(request):
    return render(request, 'accounts/home.html')
# Vista protegida que requiere login