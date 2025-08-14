const statusEl = document.getElementById('status');
const dbEl = document.getElementById('dbName');
const deviceEl = document.getElementById('device');
const loggingEl = document.getElementById('logging');
const btnCollect = document.getElementById('collectBtn');
const btnToggle = document.getElementById('toggleLoggingBtn');

const v1El = document.getElementById('v1');
const v2El = document.getElementById('v2');
const v3El = document.getElementById('v3');
const pTotalEl = document.getElementById('p_total');
const freqEl = document.getElementById('freq');

let isLogging = false;
let voltChart, currChart;

async function fetchJSON(url, options) {
	const res = await fetch(url, options);
	if (!res.ok) {
		throw new Error(`HTTP ${res.status}`);
	}
	return res.json();
}

async function refreshHealth() {
	try {
		const h = await fetchJSON('/api/health');
		statusEl.textContent = h.connected ? 'Connected' : 'Disconnected';
		statusEl.className = `status ${h.connected ? 'ok' : 'bad'}`;
		dbEl.textContent = h.db_name;
		deviceEl.textContent = `${h.device_host}:${h.device_port} (Unit ${h.unit_id})`;
		loggingEl.textContent = h.is_logging ? 'ON' : 'OFF';
		isLogging = h.is_logging;
		btnToggle.textContent = isLogging ? 'Stop Logging' : 'Start Logging';
	} catch (e) {
		statusEl.textContent = 'API error';
		statusEl.className = 'status bad';
	}
}

function setCardValue(el, value, digits = 2) {
	if (value === null || value === undefined || Number.isNaN(value)) {
		el.textContent = '--';
		return;
	}
	el.textContent = Number(value).toFixed(digits);
}

function buildTimeSeries(rows) {
	const labels = rows.map(r => r.timestamp).reverse();
	const v1 = rows.map(r => r.V1_N_Voltage).reverse();
	const v2 = rows.map(r => r.V2_N_Voltage).reverse();
	const v3 = rows.map(r => r.V3_N_Voltage).reverse();
	const c1 = rows.map(r => r.L1_Current).reverse();
	const c2 = rows.map(r => r.L2_Current).reverse();
	const c3 = rows.map(r => r.L3_Current).reverse();
	return { labels, v1, v2, v3, c1, c2, c3 };
}

function ensureCharts(ctx1, ctx2) {
	if (!window.Chart) return { volt: null, curr: null };
	if (!voltChart) {
		voltChart = new Chart(ctx1, {
			type: 'line',
			data: { labels: [], datasets: [
				{ label: 'V1-N', data: [], borderColor: '#1f77b4', tension: 0.2 },
				{ label: 'V2-N', data: [], borderColor: '#ff7f0e', tension: 0.2 },
				{ label: 'V3-N', data: [], borderColor: '#2ca02c', tension: 0.2 },
			]},
			options: { scales: { y: { beginAtZero: false } } }
		});
	}
	if (!currChart) {
		currChart = new Chart(ctx2, {
			type: 'line',
			data: { labels: [], datasets: [
				{ label: 'L1', data: [], borderColor: '#9467bd', tension: 0.2 },
				{ label: 'L2', data: [], borderColor: '#8c564b', tension: 0.2 },
				{ label: 'L3', data: [], borderColor: '#e377c2', tension: 0.2 },
			]},
			options: { scales: { y: { beginAtZero: true } } }
		});
	}
	return { volt: voltChart, curr: currChart };
}

async function refreshData() {
	const rows = await fetchJSON('/api/latest?limit=100');
	if (!rows.length) return;

	const latest = rows[0];
	setCardValue(v1El, latest.V1_N_Voltage);
	setCardValue(v2El, latest.V2_N_Voltage);
	setCardValue(v3El, latest.V3_N_Voltage);
	setCardValue(pTotalEl, latest.Total_Active_Power, 0);
	setCardValue(freqEl, latest.Frequency);

	const series = buildTimeSeries(rows);
	const ctxV = document.getElementById('voltChart');
	const ctxC = document.getElementById('currChart');
	const charts = ensureCharts(ctxV, ctxC);
	if (charts.volt) {
		charts.volt.data.labels = series.labels;
		charts.volt.data.datasets[0].data = series.v1;
		charts.volt.data.datasets[1].data = series.v2;
		charts.volt.data.datasets[2].data = series.v3;
		charts.volt.update();
	}
	if (charts.curr) {
		charts.curr.data.labels = series.labels;
		charts.curr.data.datasets[0].data = series.c1;
		charts.curr.data.datasets[1].data = series.c2;
		charts.curr.data.datasets[2].data = series.c3;
		charts.curr.update();
	}
}

btnCollect.addEventListener('click', async () => {
	btnCollect.disabled = true;
	try {
		await fetchJSON('/api/collect', { method: 'POST' });
		await refreshData();
	} catch (e) {
		alert('Collect failed');
	} finally {
		btnCollect.disabled = false;
	}
});

btnToggle.addEventListener('click', async () => {
	try {
		if (isLogging) {
			await fetchJSON('/api/logging/stop', { method: 'POST' });
			isLogging = false;
			btnToggle.textContent = 'Start Logging';
		} else {
			await fetchJSON('/api/logging/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ interval: 60 }) });
			isLogging = true;
			btnToggle.textContent = 'Stop Logging';
		}
		await refreshHealth();
	} catch (e) {
		alert('Action failed');
	}
});

(async function boot() {
	await refreshHealth();
	await refreshData();
	setInterval(refreshHealth, 5000);
	setInterval(refreshData, 5000);
})();