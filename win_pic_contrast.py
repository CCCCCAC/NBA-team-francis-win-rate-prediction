import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 配色方案 - 蓝绿色系(原始) vs 红金色系(修正)
original_colors = ["#274753", "#297270", "#299d8f"]  # 蓝绿色系
corrected_colors = ["#e66d50", "#f3a361", "#e7c66b"]  # 红金色系

# 读取对齐后的数据
df = pd.read_excel('aligned_data.xlsx')

# 计算原始误差
df['ERROR'] = df['RWIN'] - df['WINPCT']
df['ABS_ERROR'] = abs(df['ERROR'])


# 计算每个球队的离群因子
def calculate_outlier_factor(team_errors):
    n = len(team_errors)
    if n < 2:
        return 0

    avg_bias = np.mean(team_errors)
    recent_errors = team_errors[-min(3, n):]
    direction_consistency = sum(1 for e in recent_errors if e * avg_bias > 0) / len(recent_errors)

    base_factor = min(abs(avg_bias) * 2, 1.0)

    if direction_consistency >= 2 / 3:
        consistency_bonus = 0.2 * direction_consistency
    else:
        consistency_bonus = 0

    return min(base_factor + consistency_bonus, 1.0)


# 计算离群因子
team_factors = {}
for team in df['TEAM'].unique():
    team_data = df[df['TEAM'] == team].sort_values('SEASON_PRED')
    factor = calculate_outlier_factor(team_data['ERROR'].values)
    team_factors[team] = factor

# 应用修正
corrected_preds = []
for _, row in df.iterrows():
    team = row['TEAM']
    original_pred = row['WINPCT']
    avg_bias = df[df['TEAM'] == team]['ERROR'].mean()
    correction = team_factors[team] * avg_bias
    corrected_pred = max(0.05, min(0.95, original_pred + correction))
    corrected_preds.append(corrected_pred)

df['CORRECTED_PRED'] = corrected_preds
df['CORRECTED_ERROR'] = df['RWIN'] - df['CORRECTED_PRED']

# 创建箱线图
plt.figure(figsize=(14, 6))

# 准备数据：为每个球队的原始和修正误差
teams = sorted(df['TEAM'].unique())
x_positions = np.arange(len(teams))
width = 0.35  # 箱线图宽度

# 收集数据
original_errors = []
corrected_errors = []
team_names = []

for team in teams:
    team_data = df[df['TEAM'] == team]
    original_errors.append(team_data['ERROR'].values)
    corrected_errors.append(team_data['CORRECTED_ERROR'].values)
    team_names.append(team)

# 创建箱线图
positions1 = x_positions - width / 2
positions2 = x_positions + width / 2

# 原始模型箱线图 (蓝绿色系)
bp1 = plt.boxplot(original_errors, positions=positions1, widths=width,
                  patch_artist=True, showfliers=False)
for box in bp1['boxes']:
    box.set_facecolor(original_colors[0])
    box.set_edgecolor(original_colors[1])
    box.set_linewidth(1.5)
for median in bp1['medians']:
    median.set_color(original_colors[2])
    median.set_linewidth(2)

# 修正模型箱线图 (红金色系)
bp2 = plt.boxplot(corrected_errors, positions=positions2, widths=width,
                  patch_artist=True, showfliers=False)
for box in bp2['boxes']:
    box.set_facecolor(corrected_colors[0])
    box.set_edgecolor(corrected_colors[1])
    box.set_linewidth(1.5)
for median in bp2['medians']:
    median.set_color(corrected_colors[2])
    median.set_linewidth(2)

# 添加零误差线
plt.axhline(y=0, color='black', linestyle='--', alpha=0.7, linewidth=1)

# 设置x轴标签
plt.xticks(x_positions, team_names, rotation=45, ha='right')
plt.xlim(-0.5, len(teams) - 0.5)

# 添加标签和标题
plt.ylabel('Prediction Error', fontsize=12)
plt.title('Team-wise Prediction Errors: Original vs Corrected Models', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3, axis='y')

# 添加图例
import matplotlib.patches as mpatches

legend_elements = [
    mpatches.Patch(facecolor=original_colors[0], edgecolor=original_colors[1],
                   label='Original Model (No Correction)'),
    mpatches.Patch(facecolor=corrected_colors[0], edgecolor=corrected_colors[1],
                   label='Corrected Model (Outlier Factor)')
]
plt.legend(handles=legend_elements, loc='upper right')

plt.tight_layout()
plt.savefig('teamwise_comparison_boxplot.png', dpi=300, bbox_inches='tight')
plt.show()

# 计算总体改进
orig_mae = np.mean(abs(df['ERROR']))
corr_mae = np.mean(abs(df['CORRECTED_ERROR']))
improvement = (orig_mae - corr_mae) / orig_mae * 100

print(f"Overall MAE: {orig_mae:.4f} → {corr_mae:.4f}")
print(f"Improvement: {improvement:+.1f}%")
print(f"Plot saved as 'teamwise_comparison_boxplot.png'")