# FoodWatch India: Food Price & Inflation Analysis

A data pipeline and dashboard that cleans Indian food-market price data and CPI inflation data, forecasts commodity prices, and shows the results visually.

## Problem
Food prices rise suddenly because of inflation and supply issues. This makes monthly budgeting hard for middle-class households and causes losses for small vendors facing unstable prices. FoodWatch turns raw price data into insights people can act on.

## Data
- **Market prices:** daily mandi (APMC) prices by state, district, market and commodity (min, max and modal price in ₹/quintal) from [data.gov.in](https://data.gov.in). The current snapshot has 5,947 records covering 205 commodities across 26 states (April 2026).
- **Inflation:** Consumer Price Index (CPI) by division, rural, urban and combined, from MoSPI (March 2026, provisional).

## What it does
1. **Cleans the data** with Pandas and NumPy: fixes column names, parses day-first dates, drops rows with no price, and extracts the CPI table from an irregular Excel sheet.
2. **Analyzes** prices by commodity, by state and by CPI division.
3. **Forecasts prices** for key commodities (tomato, onion, potato, wheat and others) using per-commodity polynomial regression from scikit-learn, with MAE and R² reported for each.
4. **Visualizes** the results with Matplotlib and Seaborn charts, and exports a JSON file that powers a Chart.js web dashboard.

## How to run
```bash
pip install -r requirements.txt
python analysis/analyze.py
```
This regenerates the charts in `charts/` and the data file `frontend/data.json`.

To view the dashboard, serve the `frontend` folder (the page loads JSON files, so opening the HTML file directly won't work):
```bash
cd frontend
python -m http.server 8000
```
Then open http://localhost:8000 in your browser.

## Tech stack
Python, Pandas, NumPy, scikit-learn, Matplotlib, Seaborn, Chart.js

## Project structure
```
analysis/analyze.py   data cleaning, charts, forecasting
data/                 market prices (CSV) and CPI (Excel)
charts/               generated charts
frontend/             dashboard (HTML, CSS, JS, JSON)
```

## Limitations
- The price data is mostly a single-period snapshot with few distinct dates, so the forecasts are illustrative, not production-grade.
- Model fit (MAE, R²) is measured on the training data. A proper train/test split on a longer price history is the next step.

## Team
- Pragya Sumbly
- Pranjal
- Akshita Garg

Built as a college project at Jaypee Institute of Information Technology (JIIT), Noida.
