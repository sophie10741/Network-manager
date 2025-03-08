from django.urls import path
from . import views
from .views import scan_network_view
from django.contrib import admin
from django.urls import path, include
from monitor.views import home, calculator, useful, useful_detail, notes
from django.urls import path
from .views import calculators, subnet_calculator, server_calculator, storage_calculator

urlpatterns = [
	path('devices/', views.device_list, name='device_list'),
	path('devices/<int:pk>/ssh/', views.ssh_command_view, name='ssh_command'),
	path('devices/<int:pk>/template/', views.execute_template_view, name='execute_template'),
	path('scan/', scan_network_view, name='scan_network'),
        path('admin/', admin.site.urls),
        path('', home, name='home'),
        path('calculator/', calculator, name='calculator'),
        path('useful/', useful, name='useful'),
        path('useful/<int:utility_id>', views.useful_detail, name='useful_detail'),
        path('notes/', notes, name='notes'),
        path('accounts/', include('django.contrib.auth.urls')),  # Вход/выход
        path('calculators/', calculators, name='calculators'),
        path('calculators/subnet/', subnet_calculator, name='subnet_calculator'),
        path('calculators/server/', server_calculator, name='server_calculator'),
        path('calculators/storage/', storage_calculator, name='storage_calculator'),
#        path('utilities/', views.utilities_list, name='utilities_list'),
#        path('utilities/<int:utility_id>/', views.utility_detail, name='utility_detail'),
]
