# ============================================================
# Parameter Sensitivity Analysis for TV Valuation Model
# Three parameters: RWIN, PLAYER_EXPENSES, MARKET_SCORE
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy import stats

# Custom color scheme
hex_colors = ["#274753", "#297270", "#299d8f", "#8ab07c", "#e7c66b", "#f3a361", "#e66d50"]
rgb_colors = [(39 / 255, 71 / 255, 83 / 255), (41 / 255, 114 / 255, 112 / 255), (41 / 255, 157 / 255, 143 / 255),
              (138 / 255, 176 / 255, 124 / 255), (231 / 255, 198 / 255, 107 / 255), (243 / 255, 163 / 255, 97 / 255),
              (230 / 255, 109 / 255, 80 / 255)]

# Create gradient colormap
custom_cmap = mpl.colors.LinearSegmentedColormap.from_list("custom_gradient", hex_colors, N=256)

# ============================================================
# 1. Load and prepare data
# ============================================================

print("Loading data...")
# Read data
df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
df_2425 = pd.read_excel('indicators_noMIA.xlsx')

# 2024 actual TV values
tv_2024_actual = {
    'ATL': 3800, 'BOS': 6000, 'BRK': 4800, 'CHA': 3300, 'CHI': 5000,
    'CLE': 3950, 'DAL': 4700, 'DEN': 3900, 'DET': 3400, 'GSW': 8800,
    'HOU': 4900, 'IND': 3600, 'LAC': 5500, 'LAL': 7100, 'MEM': 3000,
    'MIA': 4250, 'MIL': 4000, 'MIN': 3100, 'NOP': 3050, 'NYK': 7500,
    'OKC': 3650, 'ORL': 3200, 'PHI': 4600, 'PHX': 4300, 'POR': 3500,
    'SAC': 3700, 'SAS': 3850, 'UTA': 3550, 'WAS': 4100
}

# Calculate market features
market_features = {}
for team in df_2123['TEAM'].unique():
    team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')
    latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[
        -1]

    gdp_norm = latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0
    fans_norm = latest['FANS']
    attend_norm = latest['ATTENDANCE'] / 100000
    market_score = gdp_norm * 0.24 + fans_norm * 0.22 + attend_norm * 0.54

    market_features[team] = {'MARKET_SCORE': market_score}

features_df = pd.DataFrame.from_dict(market_features, orient='index').reset_index()
features_df.columns = ['TEAM', 'MARKET_SCORE']

# Train model
train_df = pd.merge(df_2123, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
train_df['LOG_TV'] = np.log(train_df['TEAM_VALUE'])

X_train = np.column_stack([
    train_df['RWIN'].values,
    train_df['PLAYER_EXPENSES'].values,
    train_df['MARKET_SCORE'].values
])
y_train = train_df['LOG_TV'].values
X_train_with_intercept = np.column_stack([np.ones(len(X_train)), X_train])
coefficients = np.linalg.lstsq(X_train_with_intercept, y_train, rcond=None)[0]
alpha, beta, theta, gamma = coefficients

# Get 2024 data
df_2024 = df_2425[df_2425['SEASON'] == 2024].copy()
df_2024 = pd.merge(df_2024, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
df_2024['ACTUAL_TV'] = df_2024['TEAM'].map(tv_2024_actual)

# Calculate predictions and errors
df_2024['LOG_PREDICTED'] = alpha + beta * df_2024['RWIN'] + theta * df_2024['PLAYER_EXPENSES'] + gamma * df_2024[
    'MARKET_SCORE']
df_2024['PREDICTED_TV'] = np.exp(df_2024['LOG_PREDICTED']) * 1.084
df_2024['ERROR_PCT'] = (df_2024['PREDICTED_TV'] - df_2024['ACTUAL_TV']) / df_2024['ACTUAL_TV'] * 100
df_2024['ABS_ERROR_PCT'] = np.abs(df_2024['ERROR_PCT'])

print("Data preparation complete!")
print(f"Model coefficients: α={alpha:.4f}, β={beta:.4f}, θ={theta:.4f}, γ={gamma:.4f}")


# ============================================================
# 2. Parameter sensitivity analysis function
# ============================================================

def analyze_parameter_sensitivity(df, param_name, param_label, coefficient, ax, color_index):
    """
    Analyze the effect of a single parameter on prediction error

    Parameters:
    df: DataFrame containing data and prediction errors
    param_name: Parameter column name
    param_label: Parameter display name
    coefficient: Parameter coefficient in the model
    ax: Plot axis object
    color_index: Color index to use
    """

    # Prepare data
    x = df[param_name].values
    y = df['ERROR_PCT'].values

    # Calculate bin statistics
    n_bins = 8
    bins = np.linspace(x.min(), x.max(), n_bins + 1)
    bin_indices = np.digitize(x, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)

    bin_centers = []
    bin_means = []
    bin_stds = []
    bin_counts = []

    for i in range(n_bins):
        mask = bin_indices == i
        if np.sum(mask) > 0:
            bin_centers.append((bins[i] + bins[i + 1]) / 2)
            bin_means.append(np.mean(y[mask]))
            bin_stds.append(np.std(y[mask]))
            bin_counts.append(np.sum(mask))

    bin_centers = np.array(bin_centers)
    bin_means = np.array(bin_means)
    bin_stds = np.array(bin_stds)
    bin_counts = np.array(bin_counts)

    # Calculate correlation
    correlation, p_value = stats.pearsonr(x, y)

    # Plot scatter points
    scatter = ax.scatter(x, y, alpha=0.6, s=60,
                         color=hex_colors[color_index], edgecolor='white', linewidth=0.5)

    # Plot bin mean trend line
    ax.plot(bin_centers, bin_means, color=hex_colors[color_index + 2],
            linewidth=3, marker='o', markersize=8, label='Mean Trend')

    # Add error bars
    ax.errorbar(bin_centers, bin_means, yerr=bin_stds,
                fmt='none', color=hex_colors[color_index + 1], alpha=0.5, capsize=4)

    # Add zero error line
    ax.axhline(y=0, color='#666666', linestyle='--', linewidth=1.5, alpha=0.7, label='Zero Error')

    # Add linear regression line
    if len(x) > 1:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_range = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_range, p(x_range), color=hex_colors[min(color_index + 3, len(hex_colors) - 1)],
                linewidth=2, linestyle='--', label='Linear Trend')

    # Set labels
    coefficient_label = f"β" if param_name == 'RWIN' else f"θ" if param_name == 'PLAYER_EXPENSES' else f"γ"
    ax.set_xlabel(f'{param_label} ({coefficient_label}={coefficient:.4f})', fontsize=12)
    ax.set_ylabel('Prediction Error (%)', fontsize=12)

    # Add legend
    ax.legend(loc='best', fontsize=9)

    # Add grid
    ax.grid(True, alpha=0.2, linestyle='--')

    return correlation, p_value


# ============================================================
# 3. Create three subplots
# ============================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Analyze RWIN parameter
print("\nAnalyzing RWIN parameter...")
corr_rwin, p_rwin = analyze_parameter_sensitivity(
    df_2024, 'RWIN', 'RWIN', beta, axes[0], 0
)
axes[0].set_title(f'RWIN Parameter Sensitivity', fontsize=14, fontweight='bold', pad=15)

# Analyze PLAYER_EXPENSES parameter
print("Analyzing Player Expenses parameter...")
corr_pe, p_pe = analyze_parameter_sensitivity(
    df_2024, 'PLAYER_EXPENSES', 'Player Expenses', theta, axes[1], 2
)
axes[1].set_title(f'Player Expenses Parameter Sensitivity', fontsize=14, fontweight='bold', pad=15)

# Analyze MARKET_SCORE parameter
print("Analyzing Market Score parameter...")
corr_market, p_market = analyze_parameter_sensitivity(
    df_2024, 'MARKET_SCORE', 'Market Score', gamma, axes[2], 4
)
axes[2].set_title(f'Market Score Parameter Sensitivity', fontsize=14, fontweight='bold', pad=15)

# Set overall layout
plt.suptitle('TV Valuation Model: Parameter Sensitivity Analysis (2024 Validation)',
             fontsize=16, fontweight='bold', y=1.05)
plt.tight_layout()

# Save the figure
plt.savefig('parameter_sensitivity_analysis.png', dpi=300, bbox_inches='tight')
print("\n✓ Chart saved as 'parameter_sensitivity_analysis.png'")

# Show the figure
plt.show()

# ============================================================
# 4. Output statistical analysis report
# ============================================================

print("\n" + "=" * 60)
print("PARAMETER SENSITIVITY ANALYSIS REPORT")
print("=" * 60)

print(f"\n1. RWIN Parameter Analysis:")
print(f"   Coefficient (β): {beta:.4f}")
print(f"   Correlation with prediction error: {corr_rwin:.4f}")
print(f"   Significance (p-value): {p_rwin:.4f}")
print(f"   Conclusion: Parameter is {'significantly' if p_rwin < 0.05 else 'not significantly'} correlated with error")

print(f"\n2. Player Expenses Parameter Analysis:")
print(f"   Coefficient (θ): {theta:.4f}")
print(f"   Correlation with prediction error: {corr_pe:.4f}")
print(f"   Significance (p-value): {p_pe:.4f}")
print(f"   Conclusion: Parameter is {'significantly' if p_pe < 0.05 else 'not significantly'} correlated with error")

print(f"\n3. Market Score Parameter Analysis:")
print(f"   Coefficient (γ): {gamma:.4f}")
print(f"   Correlation with prediction error: {corr_market:.4f}")
print(f"   Significance (p-value): {p_market:.4f}")
print(
    f"   Conclusion: Parameter is {'significantly' if p_market < 0.05 else 'not significantly'} correlated with error")

print(f"\n4. Parameter Importance Comparison:")
# Calculate standardized contributions
rwin_contribution = abs(beta) * df_2024['RWIN'].std()
pe_contribution = abs(theta) * df_2024['PLAYER_EXPENSES'].std()
market_contribution = abs(gamma) * df_2024['MARKET_SCORE'].std()

total = rwin_contribution + pe_contribution + market_contribution
print(f"   RWIN relative contribution: {rwin_contribution / total * 100:.1f}%")
print(f"   Player Expenses relative contribution: {pe_contribution / total * 100:.1f}%")
print(f"   Market Score relative contribution: {market_contribution / total * 100:.1f}%")

print(f"\n5. Model Overall Performance:")
print(f"   Mean Absolute Error: {df_2024['ABS_ERROR_PCT'].mean():.2f}%")
print(f"   Maximum Positive Error: {df_2024['ERROR_PCT'].max():.2f}%")
print(f"   Maximum Negative Error: {df_2024['ERROR_PCT'].min():.2f}%")
print(f"   Error Standard Deviation: {df_2024['ERROR_PCT'].std():.2f}%")

print(f"\n6. Error Distribution:")
print(f"   Teams with error ≤ ±5%: {(df_2024['ABS_ERROR_PCT'] <= 5).sum()}/{len(df_2024)}")
print(f"   Teams with error ≤ ±10%: {(df_2024['ABS_ERROR_PCT'] <= 10).sum()}/{len(df_2024)}")
print(f"   Teams with error ≤ ±15%: {(df_2024['ABS_ERROR_PCT'] <= 15).sum()}/{len(df_2024)}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)