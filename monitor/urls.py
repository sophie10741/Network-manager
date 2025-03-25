from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path, include
from monitor.views import home, calculator, useful, useful_detail
from django.urls import path
from .views import calculators, subnet_calculator, server_calculator, storage_calculator
from .views import network_topology_data, device_list, network_topology_view
from .views import notes_list, note_detail, add_note, edit_note, delete_note
from .views import register_step_one, register_step_two
from .views import start_scan, scan_progress, scan_status

urlpatterns = [
    path('devices/', device_list, name='device_list'),
    path('devices/<int:pk>/ssh/', views.ssh_command_view, name='ssh_command'),
    path('devices/<int:pk>/template/', views.execute_template_view, name='execute_template'),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('calculator/', calculator, name='calculator'),
    path('useful/', useful, name='useful'),
    path('useful/<int:utility_id>', views.useful_detail, name='useful_detail'),
    path('accounts/', include('django.contrib.auth.urls')),  # Вход/выход
    path('calculators/', calculators, name='calculators'),
    path('calculators/subnet/', subnet_calculator, name='subnet_calculator'),
    path('calculators/server/', server_calculator, name='server_calculator'),
    path('calculators/storage/', storage_calculator, name='storage_calculator'),
    path('network_topology/', network_topology_view, name='network_topology'),
    path('api/network_topology/', network_topology_data, name='network_topology_data'),
    path('notes/', notes_list, name='notes_list'),
    path('notes/<int:pk>/', note_detail, name='note_detail'),
    path('notes/add/', add_note, name='add_note'),
    path('notes/<int:pk>/edit/', edit_note, name='edit_note'),
    path('notes/<int:pk>/delete/', delete_note, name='delete_note'),
    path('register/step-one/', register_step_one, name='register_step_one'),
    path('register/step-two/', register_step_two, name='register_step_two'),
    path('scan/start/', start_scan, name='start_scan'),
    path('scan/progress/', scan_progress, name='scan_progress'),
    path('scan/status/', scan_status, name='scan_status'),
]
