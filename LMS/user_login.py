from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from app.EmailBackend import EmailBackend
from django.contrib.auth import authenticate, login, logout
from app.models import Categories

def REGISTER(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(email=email).exists():
            messages.warning(request, 'Email is already in use')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.warning(request, 'Username is already in use')
            return redirect('register')

        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()
        return redirect('login')
        
        print('-------------------------')
        print(username, email, password)
        print('-------------------------')
    return render(request, 'registration/register.html')

def DO_LOGIN(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = EmailBackend.authenticate(request, username=email, password=password)

        if user != None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login')
        
        print('-------------------------')
        print(email, password)
        print('-------------------------')
    return None

def PROFILE(request):
    category = Categories.objects.all().order_by('id')[0:5]
    context = {
        'category': category,
    }
    return render(request, 'registration/profile.html', context)

def PROFILE_UPDATE(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        user_id = request.user.id
        user = User.objects.get(id=user_id)
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        
        if password != None and password != "":
            user.set_password(password)
        
        user.save()
        messages.success(request, 'Profile updated successfully!!')
        return redirect('profile')
    
def DO_LOGOUT(request):
    logout(request)
    return redirect('home')