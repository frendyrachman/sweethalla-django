from django.urls import path
from . import views

# Nama aplikasi untuk namespacing URL, praktik yang baik
app_name = 'scheduler'

urlpatterns = [
    # URL Publik
    path('', views.landing_page_view, name='landing_page'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # URL Internal Aplikasi (untuk admin/ops) dengan prefix /app/
    path('app/list/', views.schedule_list, name='schedule_list'),
    path('app/create/', views.create_schedule, name='create_schedule'),
    path('app/confirmation/<int:schedule_id>/', views.schedule_confirmation, name='schedule_confirmation'),
    path('app/run-ai/<int:schedule_id>/', views.run_ai_and_confirm, name='run_ai_and_confirm'),
    path('app/process-confirmation/<int:schedule_id>/', views.process_confirmation, name='process_confirmation'),
    path('app/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('app/', views.home, name='home'), # Titik masuk setelah login, sekarang di posisi yang benar
]