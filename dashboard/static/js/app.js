const formatter = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });

async function getJSON(url) {
	const res = await fetch(url);
	if (!res.ok) throw new Error(await res.text());
	return res.json();
}

function setCard(id, value, digits = 2) {
	const el = document.getElementById(id);
	if (!el) return;
	if (value === null || value === undefined || Number.isNaN(value)) {
		el.textContent = '—';
		return;
	}
	el.textContent = Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : String(value);
}

function isoToLocalString(iso) {
	try {
		const d = new Date(iso.replace(' ', 'T') + 'Z');
		return d.toLocaleString();
	} catch (_) {
		return iso || '—';
	}
}

let charts = {};

function ensureCharts(ctx) {
	if (charts.power) return charts;
	charts.power = new Chart(document.getElementById('chart-power').getContext('2d'), {
		type: 'line',
		data: { labels: [], datasets: [{ label: 'Total Active Power (W)', data: [], borderColor: '#1f77b4', tension: 0.2 }]},
		options: { responsive: true, scales: { x: { ticks: { autoSkip: true } }, y: { beginAtZero: false } } }
	});
	charts.frequency = new Chart(document.getElementById('chart-frequency').getContext('2d'), {
		type: 'line',
		data: { labels: [], datasets: [{ label: 'Frequency (Hz)', data: [], borderColor: '#ff7f0e', tension: 0.2 }]},
		options: { responsive: true, scales: { x: { ticks: { autoSkip: true } }, y: { beginAtZero: false } } }
	});
	charts.voltage = new Chart(document.getElementById('chart-voltage').getContext('2d'), {
		type: 'line',
		data: { labels: [], datasets: [
			{ label: 'V1-N (V)', data: [], borderColor: '#2ca02c', tension: 0.2 },
			{ label: 'V2-N (V)', data: [], borderColor: '#d62728', tension: 0.2 },
			{ label: 'V3-N (V)', data: [], borderColor: '#9467bd', tension: 0.2 },
		]},
		options: { responsive: true, scales: { x: { ticks: { autoSkip: true } }, y: { beginAtZero: false } } }
	});
	charts.current = new Chart(document.getElementById('chart-current').getContext('2d'), {
		type: 'line',
		data: { labels: [], datasets: [
			{ label: 'L1 (A)', data: [], borderColor: '#8c564b', tension: 0.2 },
			{ label: 'L2 (A)', data: [], borderColor: '#e377c2', tension: 0.2 },
			{ label: 'L3 (A)', data: [], borderColor: '#7f7f7f', tension: 0.2 },
		]},
		options: { responsive: true, scales: { x: { ticks: { autoSkip: true } }, y: { beginAtZero: false } } }
	});
	return charts;
}

function updateCharts(rows) {
	const labels = rows.map(r => r.timestamp);
	const power = rows.map(r => r.Total_Active_Power ?? null);
	const freq = rows.map(r => r.Frequency ?? null);
	const v1 = rows.map(r => r.V1_N_Voltage ?? null);
	const v2 = rows.map(r => r.V2_N_Voltage ?? null);
	const v3 = rows.map(r => r.V3_N_Voltage ?? null);
	const i1 = rows.map(r => r.L1_Current ?? null);
	const i2 = rows.map(r => r.L2_Current ?? null);
	const i3 = rows.map(r => r.L3_Current ?? null);

	const c = ensureCharts();
	c.power.data.labels = labels;
	c.power.data.datasets[0].data = power;
	c.power.update('none');

	c.frequency.data.labels = labels;
	c.frequency.data.datasets[0].data = freq;
	c.frequency.update('none');

	c.voltage.data.labels = labels;
	c.voltage.data.datasets[0].data = v1;
	c.voltage.data.datasets[1].data = v2;
	c.voltage.data.datasets[2].data = v3;
	c.voltage.update('none');

	c.current.data.labels = labels;
	c.current.data.datasets[0].data = i1;
	c.current.data.datasets[1].data = i2;
	c.current.data.datasets[2].data = i3;
	c.current.update('none');
}

async function refresh() {
	try {
		const health = await getJSON('/api/health');
		const statusEl = document.getElementById('db-status');
		if (health.exists) {
			statusEl.textContent = `DB: OK (${health.record_count} records)`;
			statusEl.className = 'ok';
		} else {
			statusEl.textContent = 'DB: not found';
			statusEl.className = 'bad';
		}
	} catch (e) {
		document.getElementById('db-status').textContent = 'DB: error';
	}

	try {
		const latest = await getJSON('/api/summary');
		setCard('card-timestamp', isoToLocalString(latest.timestamp), 0);
		setCard('card-power', latest.Total_Active_Power);
		setCard('card-frequency', latest.Frequency);
		setCard('card-v1', latest.V1_N_Voltage);
		setCard('card-v2', latest.V2_N_Voltage);
		setCard('card-v3', latest.V3_N_Voltage);
		setCard('card-i1', latest.L1_Current);
		setCard('card-i2', latest.L2_Current);
		setCard('card-i3', latest.L3_Current);
	} catch (_) {}

	try {
		const rows = await getJSON('/api/latest?limit=200');
		if (Array.isArray(rows) && rows.length) {
			updateCharts(rows);
		}
	} catch (e) {
		console.error(e);
	}
}

window.addEventListener('load', () => {
	ensureCharts();
	refresh();
	setInterval(refresh, 5000);
});