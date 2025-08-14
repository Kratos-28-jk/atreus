import os
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder="templates", static_folder="static")

DB_PATH = os.environ.get("PAC3200_DB_PATH", os.path.join(os.getcwd(), "pac3200_readings.db"))


def get_connection():
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
	cur = conn.execute(
		"SELECT name FROM sqlite_master WHERE type='table' AND name=\u003f", (table_name,)
	)
	return cur.fetchone() is not None


@app.get("/")
def index():
	db_exists = os.path.exists(DB_PATH)
	return render_template("index.html", db_exists=db_exists, db_path=DB_PATH)


@app.get("/api/health")
def api_health():
	exists = os.path.exists(DB_PATH)
	status = {"db_path": DB_PATH, "exists": exists, "record_count": 0}
	if not exists:
		return jsonify(status)
	try:
		with get_connection() as conn:
			if table_exists(conn, "pac3200_readings"):
				count = conn.execute("SELECT COUNT(*) FROM pac3200_readings").fetchone()[0]
				status["record_count"] = count
	except Exception as exc:
		status["error"] = str(exc)
	return jsonify(status)


@app.get("/api/columns")
def api_columns():
	if not os.path.exists(DB_PATH):
		return jsonify({"columns": []})
	try:
		with get_connection() as conn:
			if not table_exists(conn, "pac3200_readings"):
				return jsonify({"columns": []})
			cols = conn.execute("PRAGMA table_info(pac3200_readings)").fetchall()
			names = [row[1] for row in cols]
			return jsonify({"columns": names})
	except Exception as exc:
		return jsonify({"error": str(exc)}), 500


@app.get("/api/latest")
def api_latest():
	if not os.path.exists(DB_PATH):
		return jsonify([])
	limit = request.args.get("limit", default=200, type=int)
	try:
		with get_connection() as conn:
			if not table_exists(conn, "pac3200_readings"):
				return jsonify([])
			cur = conn.execute(
				"SELECT * FROM pac3200_readings ORDER BY timestamp DESC LIMIT ?",
				(limit,),
			)
			rows = cur.fetchall()
			# Reverse to ascending time for charts
			records = [dict(r) for r in rows][::-1]
			# Convert None-safe types to plain python (sqlite3.Row is already fine)
			return jsonify(records)
	except Exception as exc:
		return jsonify({"error": str(exc)}), 500


@app.get("/api/summary")
def api_summary():
	keys = [
		"V1_N_Voltage",
		"V2_N_Voltage",
		"V3_N_Voltage",
		"L1_Current",
		"L2_Current",
		"L3_Current",
		"Total_Active_Power",
		"Frequency",
		"timestamp",
	]
	if not os.path.exists(DB_PATH):
		return jsonify({})
	try:
		with get_connection() as conn:
			if not table_exists(conn, "pac3200_readings"):
				return jsonify({})
			cols = conn.execute("PRAGMA table_info(pac3200_readings)").fetchall()
			available = {row[1] for row in cols}
			use_cols = [c for c in keys if c in available]
			if not use_cols:
				return jsonify({})
			query = "SELECT " + ", ".join(use_cols) + " FROM pac3200_readings ORDER BY timestamp DESC LIMIT 1"
			row = conn.execute(query).fetchone()
			if not row:
				return jsonify({})
			return jsonify(dict(row))
	except Exception as exc:
		return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
	port = int(os.environ.get("PORT", 8000))
	app.run(host="0.0.0.0", port=port, debug=True)