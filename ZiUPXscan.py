import os
import sys
import time
import socket
import json
import datetime
import concurrent.futures
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.align import Align
from rich.layout import Layout
from rich.columns import Columns

console = Console()

# Словарь портов
PORT_INFO = {
    21: {"service": "FTP", "risk": "HIGH", "desc": "Передача файлов"},
    22: {"service": "SSH", "risk": "MEDIUM", "desc": "Удаленный доступ"},
    80: {"service": "HTTP", "risk": "LOW", "desc": "Веб-сервер"},
    443: {"service": "HTTPS", "risk": "LOW", "desc": "Безопасный веб"},
    3306: {"service": "MySQL", "risk": "CRITICAL", "desc": "База данных"},
    3389: {"service": "RDP", "risk": "CRITICAL", "desc": "Удаленный рабочий стол"}
}

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    banner = """
[bold cyan]
███████╗██╗██╗   ██╗██████╗ ██╗  ██╗
╚══███╔╝██║██║   ██║██╔══██╗╚██╗██╔╝
  ███╔╝ ██║██║   ██║██████╔╝ ╚███╔╝ 
 ███╔╝  ██║██║   ██║██╔═══╝  ██╔██╗ 
███████╗██║╚██████╔╝██║     ██╔╝ ██╗
╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝
[/bold cyan]
[bold green]   [+] ZiUPX Ultimate Scanner[/bold green]
[bold white]   [+] OSINT + Port Scan + DNS Recon[/bold white]
[bold red]   [!] v4.0 - The Full Power[/bold red]
    """
    console.print(Align.center(banner))
    console.print("[bold yellow]═══════════════════════════════════════════════════════════[/bold yellow]\n")

# ================= МОДУЛЬ 1: WHOIS С НУЛЯ =================
def raw_whois(domain, server="whois.iana.org"):
    """Подключается к WHOIS-серверу напрямую и забирает данные"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((server, 43))
        s.send((domain + "\r\n").encode())
        
        response = b""
        while True:
            data = s.recv(4096)
            if not data: break
            response += data
        s.close()
        
        # Ищем нужные нам поля
        result = {}
        for line in response.decode(errors='ignore').split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                if key in ['registrar', 'creation date', 'name server', 'registrant organization']:
                    result[key] = value.strip()
        return result
    except:
        return {}

# ================= МОДУЛЬ 2: DNS ПОДДОМЕНЫ =================
def scan_subdomains(domain):
    """Ищет популярные поддомены"""
    subs = ['www', 'mail', 'ftp', 'admin', 'dev', 'api', 'test', 'portal', 'vpn', 'ns1', 'ns2']
    found = []
    
    def check_sub(sub):
        target = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(target)
            return (target, ip)
        except:
            return None

    with Progress(SpinnerColumn(), TextColumn("[cyan]Поиск поддоменов..."), transient=True) as progress:
        progress.add_task("", total=None)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(check_sub, subs)
            for res in results:
                if res: found.append(res)
    return found

# ================= МОДУЛЬ 3: ОПРЕДЕЛЕНИЕ ОС =================
def detect_os(ip):
    """Определяет ОС по TTL (Time To Live)"""
    try:
        # Пытаемся отправить ICMP-пакет (пинг) через сокет
        # В Windows это работает по-другому, но для Kali сойдет
        import subprocess
        output = subprocess.check_output(f"ping -c 1 {ip}", shell=True, text=True)
        if "ttl=" in output.lower():
            ttl = int(output.lower().split("ttl=")[1].split()[0])
            if ttl <= 64:
                return "Linux / Unix (TTL <= 64)"
            elif ttl <= 128:
                return "Windows (TTL <= 128)"
            else:
                return "Network Device (Router/Switch)"
    except:
        pass
    return "Неизвестно"

# ================= МОДУЛЬ 4: ГЕОЛОКАЦИЯ IP =================
def get_ip_info(ip):
    """Запрашивает данные о IP через бесплатный API"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        data = response.json()
        if data['status'] == 'success':
            return f"{data['country']}, {data['city']} (ISP: {data['isp']})"
    except:
        pass
    return "Данные недоступны"

# ================= МОДУЛЬ 5: СКАНЕР ПОРТОВ =================
def grab_banner(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect((ip, port))
        if port == 80: s.send(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = s.recv(1024).decode(errors='ignore').strip()
        s.close()
        return banner.split('\n')[0][:50] if banner else "Скрыто"
    except:
        return "Скрыто"

def scan_port(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.8)
        result = s.connect_ex((ip, port))
        s.close()
        return port if result == 0 else None
    except:
        return None

def run_port_scan(ip, start_port, end_port):
    open_ports = []
    with Progress(SpinnerColumn(), TextColumn("[cyan]Сканирование портов..."), BarColumn(), TaskProgressColumn(), transient=True) as progress:
        task = progress.add_task("", total=(end_port - start_port + 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
            futures = [executor.submit(scan_port, ip, port) for port in range(start_port, end_port + 1)]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result: open_ports.append(result)
                progress.advance(task)
    return open_ports

# ================= ГЕНЕРАЦИЯ ОТЧЕТА =================
def generate_html_report(target, ip, whois_data, subdomains, os_info, geo_info, ports_data):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = f"""
    <html>
    <head>
        <title>ZiUPX Ultimate Report - {target}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0e17; color: #fff; padding: 30px; }}
            h1 {{ color: #a29bfe; border-bottom: 2px solid #6c5ce7; padding-bottom: 10px; }}
            .card {{ background: #131a26; border-radius: 10px; padding: 20px; margin-bottom: 20px; border: 1px solid #253044; }}
            .card h2 {{ color: #00b894; font-size: 18px; margin-top: 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 12px; border: 1px solid #253044; text-align: left; }}
            th {{ background: #1e2838; color: #6c5ce7; }}
            .critical {{ color: #e74c3c; font-weight: bold; }}
            .high {{ color: #e67e22; font-weight: bold; }}
            .low {{ color: #00b894; }}
        </style>
    </head>
    <body>
        <h1>ZiUPX Ultimate Security Report</h1>
        <p><b>Цель:</b> {target} ({ip})</p>
        <p><b>Дата:</b> {date_str}</p>

        <div class="card">
            <h2>🌐 Сетевая информация</h2>
            <p><b>ОС (Предположительно):</b> {os_info}</p>
            <p><b>Геолокация:</b> {geo_info}</p>
        </div>

        <div class="card">
            <h2>📝 WHOIS Информация</h2>
            <ul>
    """
    for k, v in whois_data.items():
        html += f"<li><b>{k.title()}:</b> {v}</li>"
    
    html += """
            </ul>
        </div>

        <div class="card">
            <h2>🔍 Найденные поддомены</h2>
            <ul>
    """
    for sub, sub_ip in subdomains:
        html += f"<li>{sub} -> {sub_ip}</li>"
        
    html += """
            </ul>
        </div>

        <div class="card">
            <h2>🚪 Открытые порты</h2>
            <table>
                <tr><th>Порт</th><th>Сервис</th><th>Баннер</th><th>Уровень риска</th></tr>
    """
    for item in ports_data:
        risk_class = item['risk'].lower()
        html += f"""
                <tr>
                    <td>{item['port']}</td>
                    <td>{item['service']}</td>
                    <td>{item['banner']}</td>
                    <td class="{risk_class}">{item['risk']}</td>
                </tr>
        """
    
    html += "</table></div></body></html>"
    
    filename = f"ZiUPX_ULTIMATE_{ip}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    return filename

# ================= ГЛАВНАЯ ФУНКЦИЯ =================
def main():
    print_banner()
    
    console.print("[bold cyan]Введите IP-адрес или домен (например, google.com):[/bold cyan]")
    target = input("> ").strip()
    if not target: return
        
    try:
        ip = socket.gethostbyname(target)
        console.print(f"[bold green][✓] IP-адрес: {ip}[/bold green]")
    except:
        console.print("[bold red][!] Ошибка разрешения DNS.[/bold red]")
        return

    # 1. OSINT Модули
    console.print("\n[bold yellow][*] Запуск OSINT-модулей...[/bold yellow]")
    
    with console.status("[cyan]Получение WHOIS...[/cyan]"):
        whois_data = raw_whois(target) if '.' in target else {}
        
    with console.status("[cyan]Геолокация IP...[/cyan]"):
        geo_info = get_ip_info(ip)
        
    with console.status("[cyan]Определение ОС...[/cyan]"):
        os_info = detect_os(ip)

    console.print("[bold green][✓] OSINT сбор завершен.[/bold green]")
    console.print(f"  - Геолокация: {geo_info}")
    console.print(f"  - ОС: {os_info}")

    # 2. Поддомены
    if '.' in target:
        console.print("\n[bold yellow][*] Поиск поддоменов...[/bold yellow]")
        subdomains = scan_subdomains(target)
        if subdomains:
            for sub, sub_ip in subdomains:
                console.print(f"  [green]Найден:[/green] {sub} -> {sub_ip}")
        else:
            console.print("  [red]Поддомены не найдены.[/red]")
    else:
        subdomains = []

    # 3. Сканирование портов
    console.print("\n[bold cyan]Введите диапазон портов (например, 1-1000):[/bold cyan]")
    port_range = input("> ").strip()
    try:
        start_port, end_port = map(int, port_range.split('-'))
    except:
        console.print("[bold red][!] Ошибка. Используйте 1-1000[/bold red]")
        return

    open_ports = run_port_scan(ip, start_port, end_port)

    # 4. Формирование отчета
    if open_ports:
        ports_data = []
        for port in sorted(open_ports):
            info = PORT_INFO.get(port, {"service": "Неизвестно", "risk": "UNKNOWN"})
            banner = grab_banner(ip, port)
            ports_data.append({
                'port': port,
                'service': info['service'],
                'banner': banner,
                'risk': info['risk']
            })

        html_file = generate_html_report(target, ip, whois_data, subdomains, os_info, geo_info, ports_data)
        console.print(Panel(f"[bold green]Сканирование завершено![/bold green]\n\n[cyan]HTML-отчет сохранен:[/cyan] {html_file}", title="[bold cyan]SUCCESS[/bold cyan]"))
    else:
        console.print("[bold red][!] Открытых портов не найдено.[/bold red]")

    console.print("\n[bold blue]Нажмите Enter для выхода...[/bold blue]")
    input()

if __name__ == "__main__":
    main()
