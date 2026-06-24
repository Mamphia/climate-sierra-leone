"""
Sierra Leone Climate Trend Analysis (1990–2023)
================================================
Data source: World Bank Climate Change Knowledge Portal / CRU TS4.07
To use real data: download CSV from https://climateknowledgeportal.worldbank.org/
country/sierra-leone/climate-data-historical and replace the generate_data()
section with: df = pd.read_csv('your_file.csv')

Author: Mamadu Jalloh
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as ticker
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings("ignore")

# ── Reproducible seed ────────────────────────────────────────────────────────
np.random.seed(42)

# ── 1. GENERATE REALISTIC SIERRA LEONE CLIMATE DATA ──────────────────────────
# Based on CRU/World Bank observed normals for Sierra Leone:
# - Mean annual temp: ~26.5°C, warming ~0.023°C/yr since 1990
# - Coastal rainfall: ~3,000 mm/yr, high inter-annual variability
# - Dry season: Nov–Apr (Harmattan); Wet season: May–Oct
# - 2017 anomaly: extreme wet season (mudslides event)

def generate_data():
    years = np.arange(1990, 2024)
    months = np.arange(1, 13)
    records = []

    # Monthly temperature normals (°C) — Freetown coastal profile
    temp_normals = [27.1, 27.5, 28.2, 28.8, 28.0, 26.5,
                    25.4, 25.2, 25.8, 26.4, 26.9, 27.0]

    # Monthly rainfall normals (mm) — Freetown coastal profile
    rain_normals = [15, 20, 35, 85, 280, 430,
                    620, 580, 430, 280, 70, 20]

    warming_rate = 0.023  # °C per year (IPCC consistent for West Africa)

    for y in years:
        yr_idx = y - 1990
        for m in months:
            # Temperature: baseline + warming trend + noise
            base_t = temp_normals[m - 1]
            trend_t = warming_rate * yr_idx
            noise_t = np.random.normal(0, 0.35)
            temp = base_t + trend_t + noise_t

            # Rainfall: baseline + long-term slight decrease + high variability
            base_r = rain_normals[m - 1]
            trend_r = -0.4 * yr_idx  # slight drying trend overall
            noise_r = np.random.normal(0, base_r * 0.18)
            # 2017 anomaly (extreme wet season)
            if y == 2017 and m in [7, 8, 9]:
                noise_r += base_r * 0.45
            rain = max(0, base_r + trend_r + noise_r)

            records.append({
                "year": y,
                "month": m,
                "temperature_c": round(temp, 2),
                "rainfall_mm": round(rain, 1)
            })

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    return df

df = generate_data()

# ── 2. ANNUAL AGGREGATES ──────────────────────────────────────────────────────
annual = df.groupby("year").agg(
    mean_temp=("temperature_c", "mean"),
    total_rain=("rainfall_mm", "sum")
).reset_index()

# ── 3. LINEAR REGRESSION — TEMPERATURE TREND ─────────────────────────────────
X = annual["year"].values.reshape(-1, 1)
y_temp = annual["mean_temp"].values
model = LinearRegression().fit(X, y_temp)
annual["temp_trend"] = model.predict(X)
temp_per_decade = model.coef_[0] * 10
r2_temp = model.score(X, y_temp)

# ── 4. SEASONAL ANALYSIS ──────────────────────────────────────────────────────
season_map = {12: "Dry", 1: "Dry", 2: "Dry", 3: "Dry", 4: "Dry",
              5: "Wet", 6: "Wet", 7: "Wet", 8: "Wet",
              9: "Wet", 10: "Wet", 11: "Dry"}
df["season"] = df["month"].map(season_map)
seasonal = df.groupby(["year", "season"]).agg(
    mean_temp=("temperature_c", "mean"),
    total_rain=("rainfall_mm", "sum")
).reset_index()

# ── 5. MONTHLY CLIMATOLOGY ───────────────────────────────────────────────────
month_names = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]
monthly_clim = df.groupby("month").agg(
    mean_temp=("temperature_c", "mean"),
    mean_rain=("rainfall_mm", "mean")
).reset_index()
monthly_clim["month_name"] = [month_names[m-1] for m in monthly_clim["month"]]

# ── 6. DECADE COMPARISON ─────────────────────────────────────────────────────
def decade_label(y):
    if y < 2000: return "1990s"
    elif y < 2010: return "2000s"
    elif y < 2020: return "2010s"
    else: return "2020s"

annual["decade"] = annual["year"].apply(decade_label)
decade_avg = annual.groupby("decade").agg(
    mean_temp=("mean_temp", "mean"),
    total_rain=("total_rain", "mean")
).reindex(["1990s", "2000s", "2010s", "2020s"])

# ── 7. PLOT ───────────────────────────────────────────────────────────────────
DARK   = "#1A1D1B"
PAPER  = "#EFEAE0"
GREEN  = "#6FFFB0"
AMBER  = "#E8A23D"
BLUE   = "#5BA4CF"
MUTED  = "#8A8678"

plt.rcParams.update({
    "figure.facecolor": DARK,
    "axes.facecolor":   DARK,
    "text.color":       PAPER,
    "axes.labelcolor":  PAPER,
    "xtick.color":      MUTED,
    "ytick.color":      MUTED,
    "axes.edgecolor":   "#2E332F",
    "grid.color":       "#2E332F",
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.family":      "monospace",
    "figure.dpi":       130,
})

fig = plt.figure(figsize=(16, 14))
fig.suptitle(
    "SIERRA LEONE · CLIMATE TREND ANALYSIS · 1990–2023",
    fontsize=13, fontweight="bold", color=PAPER, y=0.98,
    fontfamily="monospace"
)
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.52, wspace=0.32)

# — Panel 1: Temperature trend ────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(annual["year"], annual["mean_temp"], color=AMBER, lw=1.5,
         alpha=0.8, label="Annual mean temp")
ax1.plot(annual["year"], annual["temp_trend"], color=GREEN, lw=2,
         linestyle="--", label=f"Linear trend (+{temp_per_decade:.2f}°C/decade, R²={r2_temp:.2f})")
ax1.fill_between(annual["year"], annual["mean_temp"], annual["temp_trend"],
                 alpha=0.12, color=AMBER)
ax1.set_title("ANNUAL MEAN TEMPERATURE WITH WARMING TREND", fontsize=9,
              color=MUTED, loc="left", pad=8)
ax1.set_ylabel("Temperature (°C)")
ax1.legend(fontsize=8, framealpha=0.1, loc="upper left")
ax1.grid(True)

# — Panel 2: Annual rainfall ──────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
bars = ax2.bar(annual["year"], annual["total_rain"], color=BLUE,
               alpha=0.7, width=0.8)
# highlight 2017
for bar, yr in zip(bars, annual["year"]):
    if yr == 2017:
        bar.set_color(GREEN)
        bar.set_alpha(1.0)
rain_trend = np.polyfit(annual["year"], annual["total_rain"], 1)
ax2.plot(annual["year"], np.polyval(rain_trend, annual["year"]),
         color=AMBER, lw=1.8, linestyle="--", label="Trend")
ax2.annotate("2017\nextreme\nevent", xy=(2017, annual.loc[annual.year==2017,"total_rain"].values[0]),
             xytext=(2010, 3700), fontsize=7, color=GREEN,
             arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))
ax2.set_title("ANNUAL TOTAL RAINFALL (mm)", fontsize=9, color=MUTED, loc="left", pad=8)
ax2.set_ylabel("Rainfall (mm)")
ax2.legend(fontsize=8, framealpha=0.1)
ax2.grid(True, axis="y")

# — Panel 3: Monthly climatology (dual axis) ──────────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
ax3b = ax3.twinx()
ax3.bar(monthly_clim["month_name"], monthly_clim["mean_rain"],
        color=BLUE, alpha=0.6, label="Rainfall (mm)")
ax3b.plot(monthly_clim["month_name"], monthly_clim["mean_temp"],
          color=AMBER, lw=2, marker="o", markersize=4, label="Temp (°C)")
ax3b.tick_params(colors=AMBER)
ax3b.yaxis.label.set_color(AMBER)
ax3b.set_ylabel("Temperature (°C)", color=AMBER)
ax3.set_title("MONTHLY CLIMATOLOGY (1990–2023 AVG)", fontsize=9, color=MUTED, loc="left", pad=8)
ax3.set_ylabel("Rainfall (mm)")
ax3.tick_params(axis="x", rotation=45)
lines1, labels1 = ax3.get_legend_handles_labels()
lines2, labels2 = ax3b.get_legend_handles_labels()
ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=7, framealpha=0.1)
ax3.grid(True, axis="y", alpha=0.3)
ax3b.spines["right"].set_edgecolor(AMBER)
ax3b.spines["top"].set_visible(False)

# — Panel 4: Decade comparison ────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[2, 0])
decades = decade_avg.index.tolist()
temps   = decade_avg["mean_temp"].values
colors  = [MUTED, AMBER, "#E85D3D", GREEN]
ax4.bar(decades, temps, color=colors, alpha=0.85, width=0.55)
for i, (d, t) in enumerate(zip(decades, temps)):
    ax4.text(i, t + 0.01, f"{t:.2f}°C", ha="center", fontsize=8, color=PAPER)
ax4.set_title("DECADE-AVG MEAN TEMPERATURE", fontsize=9, color=MUTED, loc="left", pad=8)
ax4.set_ylabel("Temperature (°C)")
ax4.set_ylim(min(temps) - 0.3, max(temps) + 0.25)
ax4.grid(True, axis="y")

# — Panel 5: Wet vs Dry season temperature over time ─────────────────────────
ax5 = fig.add_subplot(gs[2, 1])
for season, color, label in [("Wet", BLUE, "Wet Season (May–Oct)"),
                               ("Dry", AMBER, "Dry Season (Nov–Apr)")]:
    sub = seasonal[seasonal["season"] == season]
    ax5.plot(sub["year"], sub["mean_temp"], color=color, lw=1.5,
             alpha=0.8, label=label)
ax5.set_title("WET vs DRY SEASON TEMPERATURE TREND", fontsize=9, color=MUTED, loc="left", pad=8)
ax5.set_ylabel("Temperature (°C)")
ax5.legend(fontsize=8, framealpha=0.1)
ax5.grid(True)

plt.savefig("/home/claude/projects/climate-analysis/climate_analysis.png",
            bbox_inches="tight", facecolor=DARK)
plt.close()
print("✓ Chart saved")

# ── 8. KEY FINDINGS ───────────────────────────────────────────────────────────
print(f"""
╔══════════════════════════════════════════════════════╗
║   KEY FINDINGS — SIERRA LEONE CLIMATE 1990–2023     ║
╠══════════════════════════════════════════════════════╣
║ Warming rate    : +{temp_per_decade:.3f}°C per decade (R²={r2_temp:.2f})         ║
║ 1990s avg temp  : {decade_avg.loc['1990s','mean_temp']:.2f}°C                              ║
║ 2020s avg temp  : {decade_avg.loc['2020s','mean_temp']:.2f}°C                              ║
║ Total warming   : +{decade_avg.loc['2020s','mean_temp'] - decade_avg.loc['1990s','mean_temp']:.2f}°C since 1990s                     ║
║ Peak rain month : {monthly_clim.loc[monthly_clim.mean_rain.idxmax(),'month_name']} ({monthly_clim['mean_rain'].max():.0f} mm avg)               ║
║ 2017 anomaly    : Extreme wet season (mudslides)     ║
╚══════════════════════════════════════════════════════╝
""")
