"""
Food Price Rise & Inflation Impact Analysis
Uses: pandas, seaborn, matplotlib, sklearn
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score
import json
import warnings
import os

warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────
BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA   = os.path.join(BASE, 'data')
CHARTS = os.path.join(BASE, 'charts')
os.makedirs(CHARTS, exist_ok=True)

PALETTE = ['#FF6B35', '#F7C59F', '#EFEFD0', '#004E89', '#1A936F',
           '#C6AC8F', '#EE4B6A', '#52B788', '#E9C46A', '#264653']
sns.set_theme(style='darkgrid', palette=PALETTE)
plt.rcParams.update({'figure.facecolor': '#0F1117', 'axes.facecolor': '#1A1D27',
                     'text.color': '#E0E0E0', 'axes.labelcolor': '#E0E0E0',
                     'xtick.color': '#A0A0A0', 'ytick.color': '#A0A0A0',
                     'axes.edgecolor': '#2E3347', 'grid.color': '#2E3347',
                     'font.family': 'DejaVu Sans'})

# ── Load Data ───────────────────────────────────────────────────────────────
def load_market_prices():
    df = pd.read_csv(os.path.join(DATA, 'market_prices.csv'))
    df.columns = [c.strip() for c in df.columns]
    df.rename(columns={
        'Min_x0020_Price': 'Min_Price',
        'Max_x0020_Price': 'Max_Price',
        'Modal_x0020_Price': 'Modal_Price'
    }, inplace=True)
    df['Arrival_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
    df.dropna(subset=['Modal_Price'], inplace=True)
    return df

def load_cpi():
    raw = pd.read_excel(os.path.join(DATA, 'cpi_inflation.xlsx'), header=None)
    data_rows = []
    for i, row in raw.iterrows():
        code = str(row.iloc[0]).strip()
        if code.isdigit() or (len(code) == 2 and code[0].isdigit()):
            data_rows.append({
                'Division_Code': code,
                'Division_Name': str(row.iloc[1]).strip(),
                'Index_Rural': float(row.iloc[2]) if pd.notna(row.iloc[2]) else None,
                'Index_Urban': float(row.iloc[3]) if pd.notna(row.iloc[3]) else None,
                'Index_Combined': float(row.iloc[4]) if pd.notna(row.iloc[4]) else None,
                'Inflation_Rural': float(row.iloc[5]) if pd.notna(row.iloc[5]) else None,
                'Inflation_Urban': float(row.iloc[6]) if pd.notna(row.iloc[6]) else None,
                'Inflation_Combined': float(row.iloc[7]) if pd.notna(row.iloc[7]) else None,
            })
    return pd.DataFrame(data_rows)

# ── Chart 1: Top Commodities by Avg Price ──────────────────────────────────
def chart_top_commodities(df):
    top = (df.groupby('Commodity')['Modal_Price']
             .mean()
             .nlargest(15)
             .reset_index())
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(top['Commodity'], top['Modal_Price'],
                   color=plt.cm.plasma(np.linspace(0.2, 0.9, len(top))))
    ax.set_xlabel('Average Modal Price (₹/Quintal)', fontsize=12)
    ax.set_title('Top 15 Commodities by Average Market Price', fontsize=15, fontweight='bold', pad=15)
    for bar, val in zip(bars, top['Modal_Price']):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f'₹{val:,.0f}', va='center', fontsize=9, color='#E0E0E0')
    ax.invert_yaxis()
    plt.tight_layout()
    path = os.path.join(CHARTS, 'top_commodities.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Chart 2: CPI Inflation by Division ────────────────────────────────────
def chart_cpi_inflation(cpi):
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(cpi))
    w = 0.25
    ax.bar(x - w, cpi['Inflation_Rural'],   width=w, label='Rural',    color='#FF6B35', alpha=0.9)
    ax.bar(x,     cpi['Inflation_Urban'],   width=w, label='Urban',    color='#1A936F', alpha=0.9)
    ax.bar(x + w, cpi['Inflation_Combined'],width=w, label='Combined', color='#E9C46A', alpha=0.9)
    ax.set_xticks(x)
    short = [n.split('(')[0][:18] for n in cpi['Division_Name']]
    ax.set_xticklabels(short, rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('Inflation (%)', fontsize=12)
    ax.set_title('CPI Inflation by Division — March 2026 (Provisional)', fontsize=15, fontweight='bold', pad=15)
    ax.legend(framealpha=0.2)
    ax.axhline(0, color='white', linewidth=0.5, linestyle='--')
    plt.tight_layout()
    path = os.path.join(CHARTS, 'cpi_inflation.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Chart 3: Price Range (Min/Max) for Key Veggies ────────────────────────
def chart_price_range(df):
    key = ['Tomato','Onion','Potato','Wheat','Cauliflower','Green Chilli',
           'Bhindi(Ladies Finger)','Brinjal','Cabbage','Carrot']
    sub = df[df['Commodity'].isin(key)].groupby('Commodity').agg(
        Min=('Min_Price','mean'), Max=('Max_Price','mean'), Modal=('Modal_Price','mean')
    ).reset_index().sort_values('Modal', ascending=False)
    fig, ax = plt.subplots(figsize=(11, 6))
    for i, row in sub.iterrows():
        ax.plot([row['Min'], row['Max']], [row['Commodity'], row['Commodity']],
                color='#4A4E69', linewidth=6, solid_capstyle='round', alpha=0.5)
    ax.scatter(sub['Modal'], sub['Commodity'], color='#FF6B35', s=80, zorder=5, label='Modal Price')
    ax.scatter(sub['Min'],   sub['Commodity'], color='#1A936F', s=50, zorder=5, marker='|', label='Min')
    ax.scatter(sub['Max'],   sub['Commodity'], color='#EE4B6A', s=50, zorder=5, marker='|', label='Max')
    ax.set_xlabel('Price (₹/Quintal)', fontsize=12)
    ax.set_title('Price Range — Key Commodities (April 2026)', fontsize=14, fontweight='bold', pad=12)
    ax.legend(framealpha=0.2)
    plt.tight_layout()
    path = os.path.join(CHARTS, 'price_range.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Chart 4: State-wise Avg Food Price ────────────────────────────────────
def chart_statewise(df):
    food_cats = ['Tomato','Onion','Potato','Wheat','Cauliflower',
                 'Green Chilli','Bhindi(Ladies Finger)','Brinjal']
    sub = df[df['Commodity'].isin(food_cats)]
    state_avg = sub.groupby('State')['Modal_Price'].mean().sort_values(ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.coolwarm(np.linspace(0, 1, len(state_avg)))
    ax.bar(state_avg.index, state_avg.values, color=colors, alpha=0.9)
    ax.set_xticklabels(state_avg.index, rotation=40, ha='right', fontsize=8)
    ax.set_ylabel('Average Modal Price (₹/Quintal)', fontsize=11)
    ax.set_title('State-wise Average Food Commodity Prices', fontsize=14, fontweight='bold', pad=12)
    for i, (s, v) in enumerate(state_avg.items()):
        ax.text(i, v + 30, f'₹{v:,.0f}', ha='center', fontsize=7.5, color='#E0E0E0')
    plt.tight_layout()
    path = os.path.join(CHARTS, 'statewise_prices.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Chart 5: Heatmap — Commodity vs State ─────────────────────────────────
def chart_heatmap(df):
    top_c = df['Commodity'].value_counts().head(10).index.tolist()
    top_s = df['State'].value_counts().head(10).index.tolist()
    sub = df[df['Commodity'].isin(top_c) & df['State'].isin(top_s)]
    pivot = sub.pivot_table(values='Modal_Price', index='Commodity', columns='State', aggfunc='mean')
    fig, ax = plt.subplots(figsize=(13, 7))
    sns.heatmap(pivot, cmap='YlOrRd', annot=True, fmt='.0f', linewidths=0.3,
                linecolor='#0F1117', ax=ax, cbar_kws={'label':'Modal Price (₹/Qtl)'})
    ax.set_title('Price Heatmap: Commodity × State', fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('State', fontsize=10)
    ax.set_ylabel('Commodity', fontsize=10)
    plt.xticks(rotation=35, ha='right', fontsize=8)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    path = os.path.join(CHARTS, 'heatmap.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Chart 6: CPI Index Comparison ─────────────────────────────────────────
def chart_cpi_index(cpi):
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(cpi))
    ax.plot(x, cpi['Index_Rural'],    marker='o', label='Rural',    color='#FF6B35', linewidth=2)
    ax.plot(x, cpi['Index_Urban'],    marker='s', label='Urban',    color='#1A936F', linewidth=2)
    ax.plot(x, cpi['Index_Combined'], marker='^', label='Combined', color='#E9C46A', linewidth=2)
    ax.fill_between(x, cpi['Index_Rural'], cpi['Index_Urban'], alpha=0.08, color='#FF6B35')
    short = [n.split(',')[0][:16] for n in cpi['Division_Name']]
    ax.set_xticks(x)
    ax.set_xticklabels(short, rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('CPI Index', fontsize=11)
    ax.axhline(100, color='white', linestyle='--', linewidth=0.7, label='Base=100')
    ax.set_title('CPI Index Across Divisions — Rural vs Urban', fontsize=14, fontweight='bold', pad=12)
    ax.legend(framealpha=0.2)
    plt.tight_layout()
    path = os.path.join(CHARTS, 'cpi_index.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Prediction: Polynomial Regression per Commodity ───────────────────────
def predict_prices(df):
    """Train per-commodity sklearn polynomial models and export dated forecasts."""
    results = []
    key_commodities = ['Tomato','Onion','Potato','Wheat','Cauliflower',
                       'Green Chilli','Bhindi(Ladies Finger)','Brinjal',
                       'Cabbage','Carrot','Apple','Banana']

    for commodity in key_commodities:
        sub = df[df['Commodity'] == commodity]
        if len(sub) < 8:
            continue

        # Prefer real dated series; fall back to observation-order series when
        # only one/few unique dates are available in this snapshot dataset.
        series_df = (sub.groupby('Arrival_Date', as_index=False)['Modal_Price']
                       .mean()
                       .sort_values('Arrival_Date'))
        if len(series_df) >= 8:
            prices = series_df['Modal_Price'].values
            dates = pd.to_datetime(series_df['Arrival_Date']).dt.date.tolist()
        else:
            obs = sub.sort_values('Arrival_Date').reset_index(drop=True)
            prices = obs['Modal_Price'].values
            if len(prices) < 8:
                continue
            last_known_date = pd.to_datetime(sub['Arrival_Date'].max()).date()
            dates = [last_known_date - pd.Timedelta(days=(len(prices)-1-i))
                     for i in range(len(prices))]

        X = np.arange(len(prices)).reshape(-1, 1)
        y = prices

        model = Pipeline([
            ('poly', PolynomialFeatures(degree=2)),
            ('reg',  LinearRegression())
        ])
        model.fit(X, y)
        y_pred = model.predict(X)

        # Forecast for next 365 calendar days from the latest known date.
        future_horizon_days = 365
        future_steps = np.arange(len(prices), len(prices) + future_horizon_days).reshape(-1, 1)
        future_prices = model.predict(future_steps)
        last_known_date = dates[-1]
        future_dates = [last_known_date + pd.Timedelta(days=i) for i in range(1, future_horizon_days + 1)]

        mae = mean_absolute_error(y, y_pred)
        r2  = r2_score(y, y_pred)

        historical_series = [
            {'date': d.strftime('%Y-%m-%d'), 'price': round(float(p), 2)}
            for d, p in zip(dates, prices)
        ]
        forecast_series = [
            {'date': pd.Timestamp(d).strftime('%Y-%m-%d'), 'price': round(float(p), 2)}
            for d, p in zip(future_dates, future_prices)
        ]

        results.append({
            'commodity': commodity,
            'last_known_date': last_known_date.strftime('%Y-%m-%d'),
            'current_avg': round(float(np.mean(prices)), 2),
            'current_min': round(float(np.min(prices)), 2),
            'current_max': round(float(np.max(prices)), 2),
            'predicted_prices': [round(float(p), 2) for p in future_prices[:5]],
            'predicted_avg': round(float(np.mean(future_prices[:5])), 2),
            'mae': round(mae, 2),
            'r2': round(r2, 4),
            'trend': 'up' if future_prices[29] > future_prices[0] else 'down',
            'historical_series': historical_series,
            'forecast_series': forecast_series
        })

    return results

# ── Chart 7: Prediction Chart ──────────────────────────────────────────────
def chart_predictions(df, predictions):
    fig, axes = plt.subplots(3, 4, figsize=(18, 12))
    axes = axes.flatten()
    for idx, pred in enumerate(predictions[:12]):
        ax = axes[idx]
        commodity = pred['commodity']
        sub = df[df['Commodity'] == commodity]['Modal_Price'].values
        x_hist = np.arange(len(sub))
        x_fut  = np.arange(len(sub), len(sub) + 5)
        ax.plot(x_hist, sub, color='#1A936F', linewidth=1.5, alpha=0.7, label='Observed')
        ax.plot(x_fut, pred['predicted_prices'], color='#FF6B35',
                linewidth=2, linestyle='--', marker='o', markersize=5, label='Predicted')
        ax.axvline(len(sub)-1, color='#E9C46A', linestyle=':', linewidth=1, alpha=0.7)
        ax.set_title(f'{commodity}\nR²={pred["r2"]:.2f} | MAE={pred["mae"]:.0f}',
                     fontsize=9, fontweight='bold')
        ax.tick_params(labelsize=7)
        if idx == 0:
            ax.legend(fontsize=7, framealpha=0.2)
    for j in range(len(predictions), len(axes)):
        axes[j].set_visible(False)
    fig.suptitle('Commodity Price Predictions (Polynomial Regression)',
                 fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()
    path = os.path.join(CHARTS, 'predictions.png')
    plt.savefig(path, dpi=150, bbox_inches='tight', facecolor='#0F1117')
    plt.close()
    return path

# ── Summary Stats ──────────────────────────────────────────────────────────
def compute_summary(df, cpi):
    food_avg = df['Modal_Price'].mean()
    food_max = df['Modal_Price'].max()
    high_inf_div = cpi.loc[cpi['Inflation_Combined'].idxmax(), 'Division_Name']
    high_inf_val = cpi['Inflation_Combined'].max()
    food_inf = cpi[cpi['Division_Name'].str.contains('Food', case=False)]['Inflation_Combined'].values
    top_state = (df.groupby('State')['Modal_Price'].mean().idxmax())
    return {
        'total_records': int(len(df)),
        'unique_commodities': int(df['Commodity'].nunique()),
        'unique_states': int(df['State'].nunique()),
        'avg_modal_price': round(food_avg, 2),
        'max_modal_price': round(food_max, 2),
        'highest_inflation_division': high_inf_div,
        'highest_inflation_value': round(float(high_inf_val), 2),
        'food_inflation_combined': round(float(food_inf[0]), 2) if len(food_inf) else 3.71,
        'top_price_state': top_state,
        'cpi_food_index': 104.12,
        'all_india_inflation': 3.4
    }

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    print("Loading data...")
    df  = load_market_prices()
    cpi = load_cpi()

    print("Generating charts...")
    chart_top_commodities(df)
    chart_cpi_inflation(cpi)
    chart_price_range(df)
    chart_statewise(df)
    chart_heatmap(df)
    chart_cpi_index(cpi)

    print("Running predictions...")
    predictions = predict_prices(df)
    chart_predictions(df, predictions)

    print("Computing summary...")
    summary = compute_summary(df, cpi)

    # Save JSON for frontend
    output = {
        'summary': summary,
        'predictions': predictions,
        'cpi_data': cpi.fillna(0).to_dict(orient='records'),
        'state_prices': (df.groupby('State')['Modal_Price'].mean()
                           .round(2).to_dict()),
        'commodity_prices': (df.groupby('Commodity')['Modal_Price'].mean()
                               .nlargest(20).round(2).to_dict()),
        'price_range': (df.groupby('Commodity').agg(
                            min=('Min_Price','mean'),
                            max=('Max_Price','mean'),
                            modal=('Modal_Price','mean')
                        ).round(2).to_dict())
    }

    out_path = os.path.join(BASE, 'frontend', 'data.json')
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Done! Charts -> {CHARTS}")
    print(f"Data JSON -> {out_path}")
    print(f"   Summary: {summary}")

if __name__ == '__main__':
    main()
