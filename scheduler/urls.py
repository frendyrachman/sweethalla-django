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
    path('app/', views.home, name='home'), # Titik masuk setelah login
    path('app/list/', views.schedule_list, name='schedule_list'),
    path('app/create/', views.create_schedule, name='create_schedule'),
    path('app/preview/<int:schedule_id>/', views.schedule_preview, name='schedule_preview'),
    path('app/ai-preview/<int:schedule_id>/', views.ai_preview, name='ai_preview'),
    path('app/confirm-ai/<int:schedule_id>/', views.confirm_ai_result, name='confirm_ai_result'),
    path('app/process/<int:schedule_id>/', views.process_schedule, name='process_schedule'),
    path('app/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
]