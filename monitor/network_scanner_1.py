import subprocess
import paramiko
from queue import Queue
from monitor.models import NetworkDevice, NetworkInterface, Connection
import re

SSH_USERNAME = "root"
SSH_PASSWORD = "toor"

def get_hostname_via_ssh(ip):
    """ Подключается по SSH и получает hostname. """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=SSH_USERNAME, password=SSH_PASSWORD, timeout=2)

        stdin, stdout, stderr = client.exec_command("hostname")
        hostname = stdout.read().decode().strip()

        client.close()
        return hostname if hostname else "Unknown"

    except Exception as e:
        print(f"⚠️ Ошибка подключения к {ip}: {e}")
        return "Unknown"

def get_neighbors_arp():
    """ Выполняет arp -a и возвращает список найденных IP, MAC и hostname. """
    neighbors = []
    try:
        output = subprocess.check_output(["arp", "-a"]).decode()
        print(f"📋 Вывод arp -a:\n{output}")
    except Exception as e:
        print(f"❌ Ошибка выполнения arp -a: {e}")
        return neighbors

    for line in output.split("\n"):
        match = re.search(r"(\S+) \(([\d.]+)\) at ([\w:]+) \[.*\] on (\S+)", line)
        if match:
            hostname, ip, mac, interface = match.groups()
            neighbors.append({"ip": ip, "mac": mac, "hostname": hostname, "interface": interface})

    print(f"✅ Найденные устройства: {neighbors}")
    return neighbors

def ssh_get_arp(ip):
    """ Подключается по SSH и получает список соседей через arp -a + hostname. """
    neighbors = []
    hostname = "Unknown"

    try:
        print(f"🔍 Подключаемся по SSH к {ip} для получения ARP-таблицы и имени хоста...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=SSH_USERNAME, password=SSH_PASSWORD, timeout=5)

        # Получаем ARP-таблицу
        stdin, stdout, stderr = client.exec_command("arp -a")
        output_arp = stdout.read().decode()

        # Получаем имя хоста
        stdin, stdout, stderr = client.exec_command("hostname")
        output_hostname = stdout.read().decode().strip()
        if output_hostname:
            hostname = output_hostname

        client.close()

        print(f"📋 Вывод arp -a с {ip}:\n{output_arp}")
        print(f"🏷 Имя устройства: {hostname}")

        # arp
        for line in output_arp.split("\n"):
            match = re.search(r"(\S+) \(([\d.]+)\) at ([\w:]+) \[.*\] on (\S+)", line)
            if match:
                neighbor_hostname, neighbor_ip, neighbor_mac, neighbor_interface = match.groups()
                neighbors.append({"ip": neighbor_ip, "mac": neighbor_mac, "hostname": neighbor_hostname, "interface": neighbor_interface})

    except Exception as e:
        print(f"⚠️ Ошибка подключения к {ip}: {e}")

    return neighbors, hostname

"""def add_device_to_db(ip, mac, hostname):
    # Добавляет устройство в БД, если оно там еще не записано.
    if not NetworkDevice.objects.filter(ip_address=ip).exists():
        device = NetworkDevice(
            name=hostname,
            ip_address=ip,
            mac_address=mac,
            device_type="Unknown",
            status="online",
            ssh_username="root"
        )
        device.save()
        print(f"✅ Добавлено в БД: {hostname} ({ip})")
    else:
        print(f"⚠️ Устройство {hostname} ({ip}) уже в БД.")"""


def add_device_to_db(ip, mac, hostname, interface_name="unknown"):
    """ Добавляет устройство в БД, если его там еще нет, и записывает интерфейсы. """
    device, created = NetworkDevice.objects.get_or_create(
        name=hostname,
        defaults={"device_type": "unknown", "status": "unknown", "ssh_username": "root"}
    )

    interface = NetworkInterface.objects.filter(ip_address=ip).first()

        # Добавляем интерфейс, если он еще не записан
    if not interface:
       NetworkInterface.objects.create(
            device=device,
            interface_name=interface_name,
            ip_address=ip,
            mac_address=mac
       )
       print(f"✅ Добавлен интерфейс {interface_name} для {hostname} ({ip})")
def add_connection(source_ip, target_ip):
    """ Добавляет связь между двумя устройствами, если ее еще нет. """
    source_interface = NetworkInterface.objects.filter(ip_address=source_ip).first()
    target_interface = NetworkInterface.objects.filter(ip_address=target_ip).first()
    
    if source_interface and target_interface:
        source = source_interface.device
        target = target_interface.device
        if not Connection.objects.filter(source=source, target=target).exists():
            Connection.objects.create(source=source, target=target)
            print(f"🔗 Добавлена связь: {source.name} → {target.name}")
def scan_full_network(start_ip):
    """ Запускает полное сканирование сети с BFS. """
    print("🌍 Запускаем полное сканирование сети...")

    queue = Queue()
    scanned_ips = set()

    # Добавляем стартовый IP в БД, если его там нет
    add_device_to_db(start_ip, "unknown_mac", str(get_hostname_via_ssh(start_ip)))

    queue.put(start_ip)

    while not queue.empty():
        ip = queue.get()

        if ip in scanned_ips:
            continue
        scanned_ips.add(ip)
        print(f"🚀 Сканируем с устройства {ip}")
# Запрашиваем соседей по SSH или через локальный ARP
        if ip == start_ip:
            neighbors = get_neighbors_arp()
            hostname = "this"
        else:
            neighbors, hostname = ssh_get_arp(ip)  # 🔥 Теперь корректно обрабатываем

        # Добавляем устройство в БД
        add_device_to_db(ip, "unknown_mac", hostname)

        for neighbor in neighbors:
            if neighbor["ip"] not in scanned_ips:
                queue.put(neighbor["ip"])
                add_device_to_db(neighbor["ip"], neighbor["mac"], neighbor["hostname"], neighbor["interface"])
                add_connection(ip, neighbor["ip"])
    print("✅ Сканирование завершено!")
