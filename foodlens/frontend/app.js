// FoodWatch India — Dashboard JS
// Loads data.json + charts_b64.json and renders all sections

let DATA = null;
let CHARTS = null;
let predictionLineChart = null;

const COLORS = ['#C8521A','#2A6B4F','#C8860A','#B03A3A','#4A7FB5',
                '#7B5EA7','#3A8A7A','#D4763B','#5A8A40','#8A5A40'];

// ── Boot ──────────────────────────────────────────────────────────────────
async function boot() {
  try {
    const [d, c] = await Promise.all([
      fetch('data.json').then(r => r.json()),
      fetch('charts_b64.json').then(r => r.json()).catch(() => null)
    ]);
    DATA = d;
    CHARTS = c;
    renderAll();
  } catch (e) {
    document.body.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:center;height:80vh;text-align:center;font-family:sans-serif;color:#7A7068;">
        <div>
          <p style="font-size:2rem;margin-bottom:1rem">⚠️</p>
          <p><strong>data.json not found.</strong></p>
          <p style="margin-top:0.5rem;font-size:0.85rem">Run <code>python analysis/analyze.py</code> then open this file via a local server.</p>
        </div>
      </div>`;
  }
}

function renderAll() {
  renderKPIs();
  renderOverviewCharts();
  renderPyCharts();
  renderCpiTable();
  renderPredictions();
}

// ── Navigation ─────────────────────────────────────────────────────────────
function go(id, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('pg-' + id).classList.add('active');
  btn.classList.add('active');
}

// ── KPI Cards ──────────────────────────────────────────────────────────────
function renderKPIs() {
  const s = DATA.summary;
  const items = [
    { label: 'Market Records',    value: s.total_records.toLocaleString(),      note: `${s.unique_states} states covered`,        cls: 'orange' },
    { label: 'Food Inflation',    value: s.food_inflation_combined + '%',        note: 'CPI Combined — March 2026',                cls: 'red'    },
    { label: 'All India CPI',     value: s.all_india_inflation + '%',            note: 'Overall inflation rate',                   cls: 'orange' },
    { label: 'Food CPI Index',    value: s.cpi_food_index,                       note: 'Base year = 100',                          cls: 'green'  },
  ];
  document.getElementById('kpi-row').innerHTML = items.map(k => `
    <div class="kpi-card ${k.cls}">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value">${k.value}</div>
      <div class="kpi-note">${k.note}</div>
    </div>`).join('');
}

// ── Overview Charts (Chart.js) ─────────────────────────────────────────────
function renderOverviewCharts() {
  // Commodity bar
  const comms = Object.entries(DATA.commodity_prices)
    .filter(([k]) => !['Pepper ungarbled','Black pepper','Ghee','Raibel','Betal Leaves'].includes(k))
    .slice(0, 10);
  makeBar('chart-comms', comms.map(([k]) => k), comms.map(([,v]) => v), '₹/Qtl', true);

  // CPI inflation grouped bar
  const cpi = DATA.cpi_data.slice(0, 10);
  new Chart(document.getElementById('chart-cpi'), {
    type: 'bar',
    data: {
      labels: cpi.map(r => r.Division_Name.split(',')[0].slice(0, 16)),
      datasets: [
        { label: 'Rural',    data: cpi.map(r => r.Inflation_Rural),    backgroundColor: '#C8521A99', borderColor: '#C8521A', borderWidth: 1 },
        { label: 'Urban',    data: cpi.map(r => r.Inflation_Urban),    backgroundColor: '#2A6B4F99', borderColor: '#2A6B4F', borderWidth: 1 },
        { label: 'Combined', data: cpi.map(r => r.Inflation_Combined), backgroundColor: '#C8860A99', borderColor: '#C8860A', borderWidth: 1 },
      ]
    },
    options: chartOpts({ stacked: false, horizontal: false, yLabel: 'Inflation (%)' })
  });

  // State prices
  const states = Object.entries(DATA.state_prices).sort((a,b) => b[1]-a[1]).slice(0, 12);
  makeBar('chart-states', states.map(([k]) => k.replace('NCT of ','')), states.map(([,v]) => v), '₹/Qtl', false);
}

function makeBar(id, labels, data, yLabel, horizontal) {
  new Chart(document.getElementById(id), {
    type: 'bar',
    data: {
      labels,
      datasets: [{ data, backgroundColor: COLORS.map(c => c + 'CC'), borderColor: COLORS, borderWidth: 1, borderRadius: 4 }]
    },
    options: { ...chartOpts({ horizontal, yLabel }), plugins: { legend: { display: false } } }
  });
}

function chartOpts({ horizontal = false, yLabel = '', stacked = false } = {}) {
  return {
    responsive: true,
    indexAxis: horizontal ? 'y' : 'x',
    plugins: { legend: { labels: { font: { size: 10 }, color: '#7A7068' } } },
    scales: {
      x: { stacked, grid: { color: '#E4DDD4' }, ticks: { color: '#7A7068', font: { size: 9 }, maxRotation: 35 } },
      y: { stacked, grid: { color: '#E4DDD4' }, ticks: { color: '#7A7068', font: { size: 9 } },
           title: { display: !!yLabel, text: yLabel, color: '#7A7068', font: { size: 10 } } }
    }
  };
}

// ── Python Charts ──────────────────────────────────────────────────────────
function renderPyCharts() {
  if (!CHARTS) return;
  const list = [
    { key: 'top_commodities',  title: 'Top Commodities by Price',    sub: 'Average modal price — all markets' },
    { key: 'cpi_inflation',    title: 'CPI Inflation by Division',   sub: 'Rural vs Urban vs Combined' },
    { key: 'price_range',      title: 'Price Range — Key Items',     sub: 'Min, Max, Modal price bands' },
    { key: 'statewise_prices', title: 'State-wise Prices',           sub: 'Average food commodity prices' },
    { key: 'heatmap',          title: 'Price Heatmap',               sub: 'Commodity × State intensity' },
    { key: 'cpi_index',        title: 'CPI Index Comparison',        sub: 'Division-level CPI index' },
  ];
  document.getElementById('py-charts').innerHTML = list.map(m => `
    <div class="card">
      <div class="card-title">${m.title}</div>
      <div class="card-sub">${m.sub}</div>
      ${CHARTS[m.key]
        ? `<img src="data:image/png;base64,${CHARTS[m.key]}" alt="${m.title}" loading="lazy"/>`
        : `<p style="color:var(--muted);padding:2rem;text-align:center">Chart not available</p>`}
    </div>`).join('');
}

// ── CPI Table ────────────────────────────────────────────────────────────────
function renderCpiTable() {
  const wrap = document.getElementById('cpi-table-wrap');
  if (!wrap || !Array.isArray(DATA.cpi_data)) return;

  const rows = DATA.cpi_data.map((row, idx) => {
    const formatIndex = (value) => Number(value || 0).toFixed(2);
    const formatInflationCell = (value) => {
      const num = Number(value || 0);
      if (num > 0) return `<span class="infl up">▲ ${num.toFixed(2)}%</span>`;
      if (num < 0) return `<span class="infl down">▼ ${Math.abs(num).toFixed(2)}%</span>`;
      return `<span class="infl flat">${num.toFixed(2)}%</span>`;
    };

    return `
      <tr>
        <td>${idx + 1}</td>
        <td>${row.Division_Name}</td>
        <td>${formatIndex(row.Index_Rural)}</td>
        <td>${formatIndex(row.Index_Urban)}</td>
        <td>${formatIndex(row.Index_Combined)}</td>
        <td>${formatInflationCell(row.Inflation_Rural)}</td>
        <td>${formatInflationCell(row.Inflation_Urban)}</td>
        <td>${formatInflationCell(row.Inflation_Combined)}</td>
      </tr>`;
  }).join('');

  wrap.innerHTML = `
    <div class="table-scroll">
      <table class="cpi-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Division</th>
            <th>Index Rural</th>
            <th>Index Urban</th>
            <th>Index Combined</th>
            <th>Infl. Rural</th>
            <th>Infl. Urban</th>
            <th>Infl. Combined</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// ── Predictions ─────────────────────────────────────────────────────────────
function renderPredictions() {
  const commodityInput = document.getElementById('pred-commodity');
  const dateInput = document.getElementById('pred-date');
  const resultEl = document.getElementById('pred-result');
  const datalist = document.getElementById('commodity-list');
  const form = document.getElementById('prediction-form');

  const commodityNames = DATA.predictions.map(p => p.commodity).sort((a, b) => a.localeCompare(b));
  datalist.innerHTML = commodityNames.map(name => `<option value="${name}"></option>`).join('');

  const now = new Date();
  dateInput.valueAsDate = now;
  dateInput.min = now.toISOString().split('T')[0];

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const commodity = commodityInput.value.trim();
    const predictionDate = dateInput.value ? new Date(dateInput.value) : null;

    if (!commodity || !predictionDate) {
      resultEl.textContent = 'Please enter both commodity and prediction date.';
      return;
    }

    const trendData = predictCommodityPrice(commodity, predictionDate);
    if (!trendData) {
      resultEl.textContent = `No trained prediction model found for "${commodity}". Please choose from the suggested commodities.`;
      renderPredictionChart(null);
      return;
    }

    resultEl.innerHTML = `
      <div class="pred-name">${trendData.commodity}</div>
      <div class="pred-row"><span class="lbl">Reference Date</span><span class="val">${trendData.date}</span></div>
      <div class="pred-row"><span class="lbl">Current Price</span><span class="val">₹${trendData.currentPrice.toLocaleString()} / quintal</span></div>
      <div class="pred-row"><span class="lbl">Predicted Price</span><span class="val">${trendData.predictedPriceText}</span></div>
      <div class="pred-row"><span class="lbl">Status</span><span class="val">${trendData.status}</span></div>
    `;

    renderPredictionChart(trendData);
  });
}

function predictCommodityPrice(commodityName, targetDate) {
  const predictionModel = DATA.predictions.find(
    (p) => p.commodity.toLowerCase() === commodityName.toLowerCase()
  );
  if (!predictionModel || !predictionModel.historical_series?.length) return null;

  const selectedDate = new Date(targetDate);
  selectedDate.setHours(0, 0, 0, 0);

  const historicalPoints = predictionModel.historical_series.map((p) => ({
    date: p.date,
    price: Math.round(p.price)
  }));
  const lastObserved = historicalPoints[historicalPoints.length - 1];
  let status = 'Stable';
  let predictedPriceText = 'Not available';
  let predictedPrice = null;

  if (predictionModel.forecast_series?.length) {
    const forecastSeries = predictionModel.forecast_series
      .map((point) => ({ ...point, ts: new Date(point.date).getTime() }))
      .sort((a, b) => a.ts - b.ts);

    const selectedTs = selectedDate.getTime();
    let selectedForecast = forecastSeries.find((point) => point.ts >= selectedTs);
    if (!selectedForecast) {
      selectedForecast = forecastSeries[forecastSeries.length - 1];
    }

    predictedPrice = Math.round(selectedForecast.price);
    predictedPriceText = `₹${predictedPrice.toLocaleString()} / quintal`;

    const delta = predictedPrice - lastObserved.price;
    status = delta > 0 ? 'Rising' : delta < 0 ? 'Falling' : 'Stable';
  }

  return {
    commodity: predictionModel.commodity,
    date: selectedDate.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }),
    currentPrice: lastObserved.price,
    predictedPrice,
    predictedPriceText,
    status,
    historicalPoints
  };
}

function renderPredictionChart(predictionData) {
  const canvas = document.getElementById('pred-line-chart');
  if (!canvas) return;

  if (predictionLineChart) {
    predictionLineChart.destroy();
    predictionLineChart = null;
  }

  if (!predictionData) return;

  const historical = predictionData.historicalPoints;
  const maxHistoryPoints = Math.min(60, historical.length);
  const chartPoints = historical.slice(historical.length - maxHistoryPoints);
  const labels = chartPoints.map((p, idx) => {
    if (idx % 6 === 0 || idx === chartPoints.length - 1) {
      return new Date(p.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
    }
    return '';
  });
  const historicalLine = chartPoints.map(p => p.price);

  predictionLineChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Observed Prices',
          data: historicalLine,
          borderColor: '#2A6B4F',
          backgroundColor: '#2A6B4F33',
          pointRadius: 2,
          tension: 0.25
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: '#7A7068', font: { size: 10 } } }
      },
      scales: {
        x: { grid: { color: '#E4DDD4' }, ticks: { color: '#7A7068', font: { size: 9 } } },
        y: {
          grid: { color: '#E4DDD4' },
          ticks: { color: '#7A7068', font: { size: 9 } },
          title: { display: true, text: 'Price (INR / quintal)', color: '#7A7068', font: { size: 10 } }
        }
      }
    }
  });
}

boot();
