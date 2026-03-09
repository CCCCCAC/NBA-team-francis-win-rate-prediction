# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
#
# # 读取数据
# df = pd.read_excel('indicators.xlsx')
#
# # 计算误差
# df['ERROR'] = df['RWIN'] - df['WINPCT']
# df['ABS_ERROR'] = abs(df['ERROR'])
#
# print("=" * 50)
# print("Overall Error Metrics:")
# print(f"MSE: {np.mean(df['ERROR']**2):.6f}")
# print(f"MAE: {np.mean(df['ABS_ERROR']):.6f}")
# print(f"RMSE: {np.sqrt(np.mean(df['ERROR']**2)):.6f}")
# print("=" * 50)
#
# print("\nAverage Absolute Error by Team:")
# team_error = df.groupby('TEAM')['ABS_ERROR'].mean().sort_values()
# for team, error in team_error.items():
#     print(f"{team}: {error:.6f}")
#
# print("\nAverage Absolute Error by Season:")
# season_error = df.groupby('SEASON')['ABS_ERROR'].mean()
# for season, error in season_error.items():
#     print(f"{season}: {error:.6f}")
#
# # 残差分布可视化
# plt.figure(figsize=(15, 10))
#
# # 1. Overall residual distribution
# plt.subplot(2, 2, 1)
# sns.histplot(df['ERROR'], kde=True, bins=20)
# plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
# plt.title('Residual Distribution')
# plt.xlabel('Residual (RWIN - WINPCT)')
# plt.ylabel('Frequency')
#
# # 2. Residuals by team
# plt.subplot(2, 2, 2)
# team_order = team_error.index.tolist()
# sns.boxplot(data=df, x='TEAM', y='ERROR', order=team_order)
# plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# plt.xticks(rotation=90)
# plt.title('Residuals by Team')
# plt.xlabel('Team')
# plt.ylabel('Residual')
#
# # 3. Residual trend by season
# plt.subplot(2, 2, 3)
# season_avg = df.groupby('SEASON')['ERROR'].mean()
# sns.lineplot(x=season_avg.index, y=season_avg.values, marker='o')
# plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# plt.title('Residual Trend by Season')
# plt.xlabel('Season')
# plt.ylabel('Average Residual')
#
# # 4. Residuals vs predicted values
# plt.subplot(2, 2, 4)
# plt.scatter(df['WINPCT'], df['ERROR'], alpha=0.6)
# plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# plt.xlabel('Predicted Win Rate (WINPCT)')
# plt.ylabel('Residual')
# plt.title('Residuals vs Predicted Values')
#
# plt.tight_layout()
# plt.savefig('residual_analysis.png', dpi=300, bbox_inches='tight')
# plt.show()
#
# print("\nVisualization saved as 'residual_analysis.png'")


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 读取数据
df = pd.read_excel('indicators.xlsx')

# 计算原始误差
df['ERROR'] = df['RWIN'] - df['WINPCT']
df['ABS_ERROR'] = abs(df['ERROR'])

print("=" * 50)
print("ORIGINAL MODEL PERFORMANCE:")
print("=" * 50)
print(f"MSE:  {np.mean(df['ERROR'] ** 2):.6f}")
print(f"MAE:  {np.mean(df['ABS_ERROR']):.6f}")
print(f"RMSE: {np.sqrt(np.mean(df['ERROR'] ** 2)):.6f}")


# 方法1：平均偏差修正法
def simple_correction(df, team, original_pred, current_season, correction_factor=0.6):
    """
    最简单的修正方法：使用球队历史平均偏差
    correction_factor: 修正幅度（0-1），默认60%
    """
    # 获取历史数据（不包括当前赛季）
    history = df[(df['TEAM'] == team) & (df['SEASON'] < current_season)]

    if len(history) < 2:  # 历史数据不足，不修正
        return original_pred

    # 计算历史平均偏差
    avg_bias = history['ERROR'].mean()

    # 应用修正
    corrected = original_pred + avg_bias * correction_factor

    # 确保在合理范围内
    return np.clip(corrected, 0.05, 0.95)


# 应用修正
df['CORRECTED_PRED'] = df.apply(
    lambda row: simple_correction(df, row['TEAM'], row['WINPCT'], row['SEASON'], 0.6),
    axis=1
)

# 计算修正后误差
df['CORRECTED_ERROR'] = df['RWIN'] - df['CORRECTED_PRED']
df['ABS_CORRECTED_ERROR'] = abs(df['CORRECTED_ERROR'])

print("\n" + "=" * 50)
print("CORRECTED MODEL PERFORMANCE:")
print("=" * 50)
print(f"MSE:  {np.mean(df['CORRECTED_ERROR'] ** 2):.6f}")
print(f"MAE:  {np.mean(df['ABS_CORRECTED_ERROR']):.6f}")
print(f"RMSE: {np.sqrt(np.mean(df['CORRECTED_ERROR'] ** 2)):.6f}")

# 计算改进
mse_imp = (np.mean(df['ERROR'] ** 2) - np.mean(df['CORRECTED_ERROR'] ** 2)) / np.mean(df['ERROR'] ** 2) * 100
mae_imp = (np.mean(df['ABS_ERROR']) - np.mean(df['ABS_CORRECTED_ERROR'])) / np.mean(df['ABS_ERROR']) * 100

print(f"\nImprovement:")
print(f"MSE improvement:  {mse_imp:+.2f}%")
print(f"MAE improvement:  {mae_imp:+.2f}%")

# 按球队分析
print("\n" + "=" * 50)
print("TEAM-BY-TEAM IMPROVEMENT:")
print("=" * 50)

team_results = []
for team in sorted(df['TEAM'].unique()):
    team_data = df[df['TEAM'] == team]
    orig_mae = team_data['ABS_ERROR'].mean()
    corr_mae = team_data['ABS_CORRECTED_ERROR'].mean()
    imp = (orig_mae - corr_mae) / orig_mae * 100 if orig_mae > 0 else 0
    team_results.append((team, orig_mae, corr_mae, imp))

# 按改进幅度排序
team_results.sort(key=lambda x: x[3], reverse=True)

print("\nTop 10 Most Improved Teams:")
for team, orig, corr, imp in team_results[:10]:
    print(f"{team}: {imp:+.1f}% ({orig:.4f} → {corr:.4f})")

print("\nTop 10 Most Worsened Teams:")
for team, orig, corr, imp in team_results[-10:]:
    print(f"{team}: {imp:+.1f}% ({orig:.4f} → {corr:.4f})")

# 查看每个球队的历史偏差
print("\n" + "=" * 50)
print("TEAM BIAS ANALYSIS (Avg Error = RWIN - WINPCT):")
print("=" * 50)
print("Positive = Model UNDERESTIMATES team (predicts too low)")
print("Negative = Model OVERESTIMATES team (predicts too high)")
print("")

team_biases = {}
for team in sorted(df['TEAM'].unique()):
    team_data = df[df['TEAM'] == team]
    bias = team_data['ERROR'].mean()
    team_biases[team] = bias
    trend = "↑ consistently high" if all(e > 0 for e in team_data['ERROR'].tail(3)) else \
        "↓ consistently low" if all(e < 0 for e in team_data['ERROR'].tail(3)) else "↔ mixed"

    print(f"{team}: {bias:+.4f} {trend}")

# 简单可视化：误差对比
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. 整体误差对比
ax1 = axes[0, 0]
categories = ['MSE', 'MAE', 'RMSE']
original = [np.mean(df['ERROR'] ** 2), np.mean(df['ABS_ERROR']), np.sqrt(np.mean(df['ERROR'] ** 2))]
corrected = [np.mean(df['CORRECTED_ERROR'] ** 2), np.mean(df['ABS_CORRECTED_ERROR']),
             np.sqrt(np.mean(df['CORRECTED_ERROR'] ** 2))]

x = np.arange(len(categories))
ax1.bar(x - 0.2, original, 0.4, label='Original', alpha=0.8)
ax1.bar(x + 0.2, corrected, 0.4, label='Corrected', alpha=0.8)
ax1.set_xticks(x)
ax1.set_xticklabels(categories)
ax1.set_ylabel('Error Value')
ax1.set_title('Overall Error Metrics Comparison')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 球队改进幅度
ax2 = axes[0, 1]
teams = [r[0] for r in team_results]
improvements = [r[3] for r in team_results]
colors = ['green' if imp > 0 else 'red' for imp in improvements]

ax2.bar(range(len(teams)), improvements, color=colors, alpha=0.7)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
ax2.set_xticks(range(0, len(teams), 3))
ax2.set_xticklabels([teams[i] for i in range(0, len(teams), 3)], rotation=45)
ax2.set_ylabel('Improvement (%)')
ax2.set_title('Improvement by Team')
ax2.set_ylim(-50, 50)

# 3. 残差分布对比
ax3 = axes[1, 0]
sns.histplot(df['ERROR'], bins=20, kde=True, label='Original', alpha=0.5, ax=ax3)
sns.histplot(df['CORRECTED_ERROR'], bins=20, kde=True, label='Corrected', alpha=0.5, ax=ax3)
ax3.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax3.set_xlabel('Residual (Actual - Predicted)')
ax3.set_ylabel('Frequency')
ax3.set_title('Residual Distribution Comparison')
ax3.legend()

# 4. 偏差最大的球队
ax4 = axes[1, 1]
top_teams = sorted(team_biases.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
top_teams.sort(key=lambda x: x[1])  # 按偏差值排序
teams_names = [t[0] for t in top_teams]
biases = [t[1] for t in top_teams]
colors = ['red' if b < 0 else 'green' for b in biases]

ax4.barh(teams_names, biases, color=colors, alpha=0.7)
ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
ax4.set_xlabel('Average Bias (Positive = Underestimated)')
ax4.set_title('Teams with Largest Historical Bias')

plt.tight_layout()
plt.savefig('simple_correction_results.png', dpi=150, bbox_inches='tight')
plt.show()

print("\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)
print(f"Teams improved: {sum(1 for _, _, _, imp in team_results if imp > 0)}/{len(team_results)}")
print(f"Teams worsened: {sum(1 for _, _, _, imp in team_results if imp < 0)}/{len(team_results)}")
print(f"Teams unchanged: {sum(1 for _, _, _, imp in team_results if imp == 0)}/{len(team_results)}")
print("\nVisualization saved as 'simple_correction_results.png'")