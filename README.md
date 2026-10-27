# ZiUPX Ultimate Scanner 🛡️

Профессиональный OSINT-инструмент и сканер портов, написанный с нуля на Python.

## 🚀 Возможности:
- **WHOIS-разведка:** Получение данных о владельце домена без сторонних утилит.
- **DNS Enumeration:** Поиск скрытых поддоменов.
- **OS Fingerprinting:** Определение операционной системы сервера по TTL.
- **Геолокация IP:** Определение местоположения сервера.
- **Глубокое сканирование портов:** Многопоточный анализ открытых портов и баннеров.
- **Генерация HTML-отчетов:** Создание красивых отчетов для аудита.

## 📱 Termux Android:
'''bash
pkg update && pkg upgrade -y
pkg install python -y
pip install requests rich
git clone https://github.com/kobey405-stack/ZiUPX_Scan.git
cd ZiUPX_Scan
python ziupx_ultimate.py


## 🛠 Установка на Linux:
```bash
sudo apt update
sudo apt install git -y
git clone https://github.com/ZiUPX/ZiUPX_Scan.git
cd ZiUPX_Scan
pip install requests rich
python ZiUPXscan.py

