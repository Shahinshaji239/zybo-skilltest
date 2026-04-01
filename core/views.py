from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import User, Message
from django.db.models import Q, Count
from django.contrib import messages
from .forms import UserRegisterForm, UserLoginForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('user_list')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('user_list')
    else:
        form = UserRegisterForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('user_list')
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('user_list')
    else:
        form = UserLoginForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        request.user.is_online = False
        request.user.save()
        logout(request)
    return redirect('login')

@login_required
def user_list_view(request):
    users = User.objects.exclude(id=request.user.id).annotate(
        unread_count=Count('sent_messages', filter=Q(sent_messages__receiver=request.user, sent_messages__is_read=False))
    )
    return render(request, 'core/user_list.html', {'users': users})

@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    # Get all previous messages between the two
    messages_history = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | 
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    
    # Mark messages as read
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    context = {
        'other_user': other_user,
        'messages_history': messages_history,
    }
    return render(request, 'core/chat.html', context)

@login_required
def delete_user_view(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' has been deleted.")
        return redirect('user_list')

    # GET: show confirmation page
    return render(request, 'core/confirm_delete_user.html', {'target_user': target_user})
