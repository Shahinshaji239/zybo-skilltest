from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_list_view, name='user_list'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
]
