# mBot IoT Gateway - Web Application

🤖 Gateway IoT local pentru monitorizare și colectare date în timp real de la robotul mBot.

## 📋 Caracteristici

- ✅ **Comunicare Serială** cu Arduino prin USB
- ✅ **REST API** pentru acces la date
- ✅ **Dashboard Web** cu vizualizare în timp real
- ✅ **Grafice Interactive** (Chart.js) pentru toate semnalele
- ✅ **Bază de Date SQLite** pentru arhivare
- ✅ **Export CSV** pentru analiză offline
- ✅ **Statistici** în timp real

## 🏗️ Arhitectură

```
mBot (Arduino) ──[USB Serial]──> Python Gateway ──[REST API]──> Web Dashboard
                                         │
                                         └──> SQLite Database
```

## 📦 Instalare

### 1. Instalează Python 3.8+

```bash
python3 --version  # Verifică versiunea Python
```

### 2. Creează Virtual Environment (Recomandat)

```bash
cd web_app
python3 -m venv venv

# Activează virtual environment:
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Instalează Dependențe

```bash
pip install -r requirements.txt
```

## ⚙️ Configurare

### 1. Configurează Portul Serial

Editează `backend/config.py`:

```python
# Pentru Linux:
SERIAL_PORT = '/dev/ttyUSB0'  # sau /dev/ttyACM0

# Pentru Windows:
SERIAL_PORT = 'COM3'  # verifică în Device Manager

# Pentru Mac:
SERIAL_PORT = '/dev/tty.usbserial-XXX'
```

### 2. Verifică Portul Disponibil

**Linux:**
```bash
ls /dev/tty* | grep USB
# sau
dmesg | grep tty
```

**Windows:**
- Device Manager → Ports (COM & LPT)

**Python (orice platformă):**
```bash
python -m serial.tools.list_ports
```

## 🚀 Pornire

### 1. Conectează Arduino

- Conectează mBot-ul la PC prin USB
- Asigură-te că firmware-ul este încărcat pe Arduino (`main.cpp`)

### 2. Pornește Gateway-ul

```bash
cd web_app/backend
python app.py
```

Output așteptat:
```
INFO - Starting mBot IoT Gateway...
INFO - Connected to Arduino on /dev/ttyUSB0 at 115200 baud
INFO - Serial parser started
 * Running on http://0.0.0.0:5000
```

### 3. Deschide Dashboard-ul

Accesează în browser:
```
http://localhost:5000
```

## 🎮 Utilizare

### 1. Start Experiment

1. Apasă butonul **"Start Experiment"** din dashboard
2. Arduino va primi comanda `S` (START)
3. Va începe secvența de teste:
   - **Phase 1 (0-30s)**: Motor open-loop test (ridică robotul!)
   - **Phase 2 (30-60s)**: Balance test cu PRBS (pune robotul jos)

### 2. Monitorizare Timp Real

Dashboard-ul afișează:
- 📊 **Valori Curente**: PWM, viteze, unghi, gyro
- 📈 **Grafice Live**: actualizare la 1 Hz
- 📉 **Faza Curentă**: status test
- 🔌 **Status Conexiune**: Connected/Disconnected

### 3. Export Date

- Apasă **"Export CSV"** pentru a descărca toate datele
- Fișierul include: `time_s, phase, pwm_left, pwm_right, speed_1, speed_2, angle_x, gyro_y, timestamp`

## 🔌 REST API Endpoints

### Status Sistem
```http
GET /api/status
```
Răspuns:
```json
{
  "status": "online",
  "serial_connected": true,
  "serial_port": "/dev/ttyUSB0",
  "buffer_size": 150,
  "timestamp": "2025-01-06T15:30:00"
}
```

### Date Timp Real (Buffer)
```http
GET /api/data/buffer?limit=100
```
Răspuns:
```json
{
  "success": true,
  "count": 100,
  "data": [...]
}
```

### Ultimul Punct de Date
```http
GET /api/data/latest
```

### Date Istorice
```http
GET /api/data/history?start=2025-01-06T10:00:00&end=2025-01-06T12:00:00&limit=10000
```

### Start Experiment
```http
POST /api/control/start
```

### Export CSV
```http
GET /api/data/export
```

### Statistici
```http
GET /api/statistics
```

### Configurație
```http
GET /api/config
```

## 📊 Format Date

### CSV din Arduino:
```csv
time,phase,pwm_left,pwm_right,speed_1,speed_2,angleX,gyroY
0.10,1,150,150,45.23,44.89,-1.23,2.45
0.20,1,150,150,48.12,47.56,-1.18,2.51
```

### JSON în API:
```json
{
  "time_s": 0.10,
  "phase": 1,
  "pwm_left": 150,
  "pwm_right": 150,
  "speed_1": 45.23,
  "speed_2": 44.89,
  "angle_x": -1.23,
  "gyro_y": 2.45,
  "timestamp": "2025-01-06T15:30:00.123456"
}
```

## 🗄️ Bază de Date

SQLite database: `web_app/data/mbot_data.db`

### Schema:

**Tabel: measurements**
- `id`: INTEGER PRIMARY KEY
- `timestamp`: DATETIME
- `time_s`: REAL (timpul de la începutul experimentului)
- `phase`: INTEGER (0=Idle, 1=Motor Test, 2=Balance Test, 3=Complete)
- `pwm_left`: INTEGER
- `pwm_right`: INTEGER
- `speed_1`: REAL
- `speed_2`: REAL
- `angle_x`: REAL
- `gyro_y`: REAL
- `created_at`: DATETIME

**Tabel: system_log**
- `id`: INTEGER PRIMARY KEY
- `timestamp`: DATETIME
- `level`: VARCHAR(10)
- `message`: TEXT

### Interogare Manuală

```bash
cd web_app/data
sqlite3 mbot_data.db

# Exemple comenzi:
sqlite> SELECT COUNT(*) FROM measurements;
sqlite> SELECT * FROM measurements ORDER BY timestamp DESC LIMIT 10;
sqlite> SELECT AVG(angle_x), AVG(speed_1) FROM measurements WHERE phase=2;
```

## 🐛 Troubleshooting

### Eroare: "Permission denied" (Linux)

```bash
# Adaugă user-ul la grupul dialout
sudo usermod -a -G dialout $USER

# Sau schimbă permisiunile direct
sudo chmod 666 /dev/ttyUSB0
```

### Eroare: "Port already in use"

```bash
# Verifică ce proces folosește portul
lsof -i :5000

# Omoară procesul
kill -9 <PID>
```

### Arduino nu răspunde

1. Verifică conexiunea USB
2. Verifică că firmware-ul (`main.cpp`) este încărcat
3. Resetează Arduino (buton reset)
4. Verifică baudrate-ul (115200 în ambele părți)
5. Testează cu Arduino Serial Monitor

### Browser nu se actualizează

1. Șterge cache browser (Ctrl+Shift+Delete)
2. Verifică Console (F12) pentru erori
3. Verifică că API-ul răspunde: http://localhost:5000/api/status

## 📈 Performanță

- **Sampling Rate Arduino**: 10 Hz (100ms)
- **Update Rate Dashboard**: 1 Hz (1000ms)
- **Buffer Size**: 100 puncte (ultimele 10 secunde)
- **Database Retention**: 30 zile (configurabil)
- **Latență End-to-End**: ~20-80ms

## 🔧 Dezvoltare

### Structură Fișiere

```
web_app/
├── backend/
│   ├── app.py              # Flask application + REST API
│   ├── serial_parser.py    # Serial communication cu Arduino
│   ├── database.py         # SQLite operations
│   └── config.py           # Configuration
├── frontend/
│   ├── index.html          # Dashboard HTML
│   ├── style.css           # Stiluri CSS
│   └── app.js              # JavaScript + Chart.js logic
├── data/
│   ├── mbot_data.db        # SQLite database (generat automat)
│   └── gateway.log         # Log file
├── requirements.txt        # Python dependencies
└── README.md              # Acest fișier
```

### Adaugă Endpoint Nou

1. Editează `backend/app.py`:
```python
@app.route(f'{config.API_PREFIX}/new-endpoint', methods=['GET'])
def new_endpoint():
    return jsonify({'message': 'Hello'})
```

2. Testează cu curl:
```bash
curl http://localhost:5000/api/new-endpoint
```

### Modifică Dashboard

1. Editează `frontend/index.html` pentru HTML
2. Editează `frontend/style.css` pentru stiluri
3. Editează `frontend/app.js` pentru logică

## 📝 Logs

**Gateway log:**
```bash
tail -f web_app/data/gateway.log
```

**Flask console:**
```
INFO - Starting mBot IoT Gateway...
INFO - Connected to Arduino on /dev/ttyUSB0
INFO - Serial parser started
127.0.0.1 - - [06/Jan/2025 15:30:00] "GET /api/status HTTP/1.1" 200 -
```

## 🔐 Securitate

⚠️ **Notă**: Această aplicație rulează LOCAL și nu este designed pentru expunere pe internet.

Dacă vrei să expui API-ul:
- Adaugă autentificare (token-based)
- Folosește HTTPS
- Validează toate input-urile
- Rate limiting pentru API

## 🚢 Deploy Producție

Pentru un deployment mai robust:

```bash
# Folosește Gunicorn în loc de Flask dev server
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🤝 Contribuții

Dezvoltat pentru proiectul de identificare sistem mBot Ranger.

## 📄 Licență

MIT License - free to use and modify.

---

**🎉 Gateway-ul tău IoT este gata! Să începem testele!**
