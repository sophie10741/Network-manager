from django.shortcuts import render, get_object_or_404
from .models import NetworkDevice, Connection, NetworkInterface
from .forms import DeviceFilterForm
from .ssh_manager import execute_ssh_command
from .command_templates import command_templates
from django.http import JsonResponse
from .network_scanner_1 import scan_full_network
from .network_scanner_1 import get_neighbors_arp
import ipaddress
import math
from .models import Category, Utility

def device_list(request):
	devices = NetworkDevice.objects.all()
	form = DeviceFilterForm(request.GET)

	if form.is_valid():
		name = form.cleaned_data.get('name')
		device_type = form.cleaned_data.get('device_type')
		status = form.cleaned_data.get('status')

		if name:
			devices = devices.filter(name__icontains=name)
		if device_type:
			devices = devices = devices.filter(device_type=device_type)
		if status:
			if status == "online":
				devices = [device for device in devices if device.is_online()]
			elif status == "offline":
				devices = [device for device in devices if not device.is_online()]

	return render(request, 'monitor/device_list.html', {'devices': devices, 'form': form})

def ssh_command_view(request, pk):
	device = NetworkDevice.objects.get(pk=pk)
	result = None

	if request.method == "POST":
		command = request.POST.get("command")
		if command:
			result = execute_ssh_command(
				host=device.ip_address,
				username=device.ssh_username,
				command=command,
				private_key_path="/root/.ssh/id_rsa"
			)
	return render(request, "monitor/ssh_command.html", {
		"device": device,
		"result": result
	})

def execute_template_view(request, pk):
    """
    Представление для выполнения команд по шаблону.
    """
    device = get_object_or_404(NetworkDevice, pk=pk)
    result = None
    template_name = request.GET.get("template", None)
    template = command_templates.get(template_name, None)
    parameters = []
    if template:
        command = template["command"]
        parameters = [param.split("}")[0] for param in command.split("{")[1:]]

    if request.method == "POST" and template_name in command_templates:
        # Получаем параметры из POST-запроса
        input_parameters = {key: request.POST.get(key) for key in request.POST if key != "csrfmiddlewaretoken"}
        command = template["command"].format(**input_parameters)

        # Выполняем команду через SSH

        result = execute_ssh_command(
		host=device.ip_address,
		username=device.ssh_username,
		command=command,
		private_key_path="/root/.ssh/id_rsa"
        )
    return render(request, "monitor/execute_template.html", {
	"device": device,
	"template_name": template_name,
	"template": template,
	"parameters": parameters,
	"result": result
    })

def scan_network_view(request):
    if request.method == "POST":
        start_ip = request.POST.get("start_ip", "").strip()

        if not start_ip:
            return JsonResponse({"status": "error", "message": "Введите IP-адрес!"})

        # Добавляем стартовый IP в базу, если его там нет
#        network_interface = NetworkInterface.objects.filter(ip_address=start_ip).first()

#        if not network_interface:
#            device = NetworkDevice.objects.create(name="this", device_type="unknown", status="online")
#            NetworkInterface.objects.create(device=device, ip_address=start_ip, mac_address="unknown", interface_name="unknown")
#            print(f"{start_ip} added")
        # Запускаем сканирование
        scan_full_network(start_ip)

        return JsonResponse({"status": "success", "message": f"Сканирование началось с {start_ip}"})

    return render(request, "monitor/scan.html")  # Отображаем страницу сканирования
def home(request):
    return render(request, 'home.html')

def calculator(request):
    return render(request, 'calculator.html')

def useful(request):
    categories = Category.objects.all()
    utilities = Utility.objects.all()

    return render(request, 'monitor/useful/useful.html', {
        'categories': categories,
        'utilities': utilities,
    })

def useful_detail(request, utility_id):
    utility = Utility.objects.get(id=utility_id)
    return render(request, 'monitor/useful/useful_detail.html', {'utility': utility})

def notes(request):
    return render(request, 'notes.html')

def calculators(request):
    return render(request, 'monitor/calculators.html')

def subnet_calculator(request):
    result = None

    if request.method == "POST":
        ip_input = request.POST.get("ip")
        try:
            network = ipaddress.ip_network(ip_input, strict=False)
            result = {
                "network_address": str(network.network_address),
                "broadcast_address": str(network.broadcast_address),
                "netmask": str(network.netmask),
                "num_hosts": network.num_addresses - 2,  # Вычитаем сеть и broadcast
                "ip_range": f"{network.network_address + 1} - {network.broadcast_address - 1}"
            }
        except ValueError:
            result = {"error": "Неверный IP-адрес или маска!"}

    return render(request, "monitor/calculators/subnet_calculator.html", {"result": result})

def server_calculator(request):
    result = None

    if request.method == "POST":
        try:
            users = int(request.POST.get("users"))
            cpu_per_user = float(request.POST.get("cpu_per_user"))
            ram_per_user = float(request.POST.get("ram_per_user"))
            server_cpu = float(request.POST.get("server_cpu"))
            server_ram = float(request.POST.get("server_ram"))

            # Расчет минимального числа серверов
            total_cpu_needed = users * cpu_per_user
            total_ram_needed = users * ram_per_user

            servers_by_cpu = math.ceil(total_cpu_needed / server_cpu)
            servers_by_ram = math.ceil(total_ram_needed / server_ram)

            total_servers = max(servers_by_cpu, servers_by_ram)  # Берем большее из двух значений

            result = {
                "servers_by_cpu": servers_by_cpu,
                "servers_by_ram": servers_by_ram,
                "total_servers": total_servers
            }
        except (ValueError, TypeError):
            result = {"error": "Ошибка ввода данных!"}

    return render(request, "monitor/calculators/server_calculator.html", {"result": result})

def storage_calculator(request):
    result = None
    if request.method == 'POST':
        try:
            # Получаем данные с формы
            users = int(request.POST['users'])
            ram_per_user = float(request.POST['ram_per_user'])
            disk_per_user = float(request.POST['disk_per_user'])

            # Рассчитываем требуемые ресурсы
            total_ram = users * ram_per_user
            total_disk = users * disk_per_user

            result = {
                'total_ram': total_ram,
                'total_disk': total_disk,
            }
        except ValueError:
            result = {'error': 'Пожалуйста, введите корректные данные.'}
    return render(request, 'monitor/calculators/storage_calculator.html', {"result": result})
