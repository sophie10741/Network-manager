import subprocess
import paramiko
from queue import Queue
from monitor.models import NetworkDevice, NetworkInterface, Connection
import re

SSH_USERNAME = "root"
SSH_PASSWORD = "toor"

client = paramiko.SSHClient()


def connect_via_ssh(ip):

    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(ip, username=SSH_USERNAME, password=SSH_PASSWORD, timeout=2)


def disconnect_from_ssh():
    client.close()


def get_hostname_via_ssh():
    try:

        stdin, stdout, stderr = client.exec_command("hostname")
        hostname = stdout.read().decode().strip()

        return hostname if hostname else "Unknown"

    except Exception as e:
        print(f"⚠️ Ошибка команды hostname: {e}")
        return "Unknown"


def determine_device_type(hostname, server_type, router_type, switch_type, client_type):
    hostname_lower = hostname.lower()

    if any(pattern.lower() in hostname_lower for pattern in server_type):
        return "server"
    elif any(pattern.lower() in hostname_lower for pattern in router_type):
        return "router"
    elif any(pattern.lower() in hostname_lower for pattern in switch_type):
        return "switch"
    elif any(pattern.lower() in hostname_lower for pattern in client_type):
        return "client"

    return "unknown"


def get_interfaces_via_ssh():
    current_interface = ''
    mac = ''
    interfaces = []

    try:

        stdin, stdout, stderr = client.exec_command("ip a")
        output_ip_a = stdout.read().decode().strip()

        for line in output_ip_a.split("\n"):
            if re.match(r"\d+: (\S+):", line):  # Найден новый интерфейс
                current_interface = str(re.match(r"\d+: (\S+):", line).group(1))
            elif "link/ether" in line and current_interface:
                mac = re.search(r"link/ether ([\da-fA-F:]+)", line).group(1)
            elif "inet " in line and current_interface:  # Найден IP-адрес
                match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/\d+", line)
                if match:
                    ip_addr = match.group(1)
                    interfaces.append({"interface": current_interface, "ip": ip_addr, "mac": mac})

        print(interfaces)
        return interfaces if interfaces else "Unknown"
    except Exception as e:
        print(f"⚠️ Ошибка команды 'ip a': {e}")
    return "Unknown"


def get_arp_via_ssh():
    neighbors = []

    try:
        stdin, stdout, stderr = client.exec_command("arp -a")
        output_arp = stdout.read().decode()

        print(f"📋 Вывод arp -a:\n{output_arp}")

        # Разбираем вывод `arp -a`
        for line in output_arp.split("\n"):
            match = re.search(r"(\S+) \(([\d.]+)\) at ([\w:<>]+) \[.*\] on (\S+)", line)
            if match:
                neighbor_hostname, neighbor_ip, neighbor_mac, neighbor_interface = match.groups()

                # Пропускаем, если MAC-адрес отсутствует (`<incomplete>`)
                if neighbor_mac == "<incomplete>":
                    continue

                neighbors.append({
                    "ip": neighbor_ip,
                    "mac": neighbor_mac,
                    "hostname": neighbor_hostname,
                    "interface": neighbor_interface
                })

    except Exception as e:
        print(f"⚠️ Ошибка выполнения 'arp -a': {e}")

    return neighbors


def add_to_db_device(hostname, device_type):
    """ Добавляет устройство в БД, если его там еще нет, и записывает интерфейсы. """
    NetworkDevice.objects.get_or_create(
        name=hostname,
        defaults={"device_type": device_type, "status": "unknown", "ssh_username": "root"}
    )


def add_to_db_interface(ip, mac, name_device, interface_name):
    device = NetworkDevice.objects.get(name=f"{name_device}")

    interface = NetworkInterface.objects.filter(ip_address=ip).first()

    #TODO обработка существующих записей (актуализация)

    # Добавляем интерфейс, если он еще не записан
    if not interface:
        NetworkInterface.objects.create(
            device=device,
            interface_name=interface_name,
            ip_address=ip,
            mac_address=mac
        )
        print(f"✅ Добавлен интерфейс {interface_name} для {name_device} ({ip})")


def add_to_db_connection(source_device_name, target_ip, target_mac):
    """ Добавляет связь между двумя устройствами, если они напрямую связаны (по MAC). """

    # Проверяем, есть ли устройство-источник в БД
    source_device = NetworkDevice.objects.filter(name=source_device_name).first()
    if not source_device:
        print(f"⚠️ Ошибка: устройство {source_device_name} не найдено в БД!")
        return

    # Проверяем, есть ли целевое устройство в БД
    target_interface = NetworkInterface.objects.filter(ip_address=target_ip, mac_address=target_mac).first()
    if not target_interface:
        print(f"⚠️ Ошибка: интерфейс {target_ip} с MAC {target_mac} не найден в БД!")
        return

    target_device = target_interface.device

    # Проверяем, что мы не соединяем устройство само с собой
    if source_device == target_device:
        print(f"⚠️ Пропускаем: {source_device.name} уже связан с самим собой.")
        return

    # Проверяем, что связь не дублируется
    if not Connection.objects.filter(source=source_device, target=target_device).exists():
        Connection.objects.create(source=source_device, target=target_device)
        print(f"🔗 Добавлена связь: {source_device.name} → {target_device.name}")
    else:
        print(f"⚠️ Связь {source_device.name} → {target_device.name} уже существует")


def scan_full_network(start_ip, server_type, router_type, switch_type, client_type):
    """ Запускает полное сканирование сети с BFS. """
    print("🌍 Запускаем полное сканирование сети...")

    queue = Queue()
    scanned_ips = set()

    queue.put(start_ip)

    while not queue.empty():
        ip = queue.get()

        if ip in scanned_ips:
            continue

        try:
            connect_via_ssh(ip)
        except Exception as e:
            print(f"⚠️ Ошибка подключения к {ip}: {e}")
            scanned_ips.add(str(ip))
            continue

        scanned_ips.add(str(ip))
        print(f"🚀 Сканируем с устройства {ip}")

        # Получаем имя хоста
        current_hostname = get_hostname_via_ssh()
        device_type = determine_device_type(current_hostname, server_type, router_type, switch_type, client_type)
        add_to_db_device(current_hostname, device_type)

        # Добавляем интерфейсы устройства
        for current_interface in get_interfaces_via_ssh():
            if current_interface["ip"] not in scanned_ips and current_interface["interface"] != "lo":
                add_to_db_interface(
                    current_interface["ip"],
                    current_interface["mac"],
                    current_hostname,
                    current_interface["interface"]
                )

        # Запрашиваем соседей по SSH или через локальный ARP
        neighbors = get_arp_via_ssh()

        for neighbor in neighbors:
            if neighbor["ip"] not in scanned_ips:
                queue.put(neighbor["ip"])
                add_to_db_device(neighbor["hostname"], device_type)
                add_to_db_interface(neighbor["ip"], neighbor["mac"], neighbor["hostname"], neighbor["interface"])
                add_to_db_connection(current_hostname, neighbor["ip"], neighbor["mac"])  # 🔥 ДОБАВЛЯЕМ СВЯЗИ

        disconnect_from_ssh()

    print("✅ Сканирование завершено!")


