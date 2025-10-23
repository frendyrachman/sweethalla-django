from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_schedule, name='create_schedule'),
    path('list/', views.schedule_list, name='schedule_list'),
    path('delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
