import os
from flask import Flask, jsonify, send_from_directory, request
from pac3200_logger import create_logger_from_env

app = Flask(__name__, static_folder='static', static_url_path='/static')
logger = create_logger_from_env()

# Attempt initial connection (non-fatal)
try:
    logger.connect()
except Exception:
    pass


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health')
def health():
    return jsonify({
        'device_host': logger.host,
        'device_port': logger.port,
        'unit_id': logger.unit_id,
        'connected': bool(logger.client is not None),
        'is_logging': logger.is_logging,
        'db_name': logger.db_name,
    })


@app.route('/api/parameters')
def parameters():
    df = logger.get_parameter_summary()
    rows = [] if df is None else df.to_dict(orient='records')
    return jsonify(rows)


@app.route('/api/latest')
def latest():
    try:
        limit = int(request.args.get('limit', '50'))
    except ValueError:
        limit = 50
    df = logger.query_latest_readings(limit=limit)
    rows = [] if df is None else df.fillna(value=None).to_dict(orient='records')
    return jsonify(rows)


@app.route('/api/range')
def range_query():
    start_time = request.args.get('start')
    end_time = request.args.get('end')
    if not start_time or not end_time:
        return jsonify({'error': 'start and end query parameters are required (YYYY-MM-DD HH:MM:SS)'}), 400
    df = logger.query_readings_by_timerange(start_time, end_time)
    rows = [] if df is None else df.fillna(value=None).to_dict(orient='records')
    return jsonify(rows)


@app.route('/api/collect', methods=['POST'])
def collect():
    if logger.client is None:
        logger.connect()
    record_id = logger.collect_and_store_data()
    return jsonify({'record_id': record_id}), (200 if record_id else 500)


@app.route('/api/logging/start', methods=['POST'])
def start_logging():
    body = request.get_json(silent=True) or {}
    interval = int(body.get('interval', 60))
    logger.start_background_logging(interval_seconds=interval)
    return jsonify({'is_logging': logger.is_logging, 'interval': interval})


@app.route('/api/logging/stop', methods=['POST'])
def stop_logging():
    logger.stop_background_logging()
    return jsonify({'is_logging': logger.is_logging})


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '0.0.0.0')
    app.run(host=host, port=port, debug=False)