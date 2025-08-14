# atreus

PAC3200 Dashboard

Quick start:

1) Install deps

    pip install -r requirements.txt

2) Start the dashboard (default uses pac3200_readings.db in workspace root)

    python dashboard/app.py

3) If your DB lives elsewhere, point the app to it

    PAC3200_DB_PATH=/absolute/path/to/pac3200_readings.db python dashboard/app.py

4) Run logger (optional, if you want to collect data)

    python pac3200_logger.py

Open http://localhost:8000 in your browser.