import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 定义配色方案
BLUE_GREEN_GOLD = [
    '#274753',  # 深蓝绿
    '#297270',  # 蓝绿
    '#299d8f',  # 青绿
    '#8ab07c',  # 黄绿
    '#E7C66B',  # 金黄色
    '#F3A361',  # 橙黄色
    '#E66D50'  # 橙红色
]

plt.style.use('default')
sns.set_palette("husl")

# 读取数据
df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
df_2425 = pd.read_excel('indicators_noMIA.xlsx')

# 2024实际TV值
tv_2024_actual = {
    'ATL': 3800, 'BOS': 6000, 'BRK': 4800, 'CHA': 3300, 'CHI': 5000,
    'CLE': 3950, 'DAL': 4700, 'DEN': 3900, 'DET': 3400, 'GSW': 8800,
    'HOU': 4900, 'IND': 3600, 'LAC': 5500, 'LAL': 7100, 'MEM': 3000,
    'MIA': 4250, 'MIL': 4000, 'MIN': 3100, 'NOP': 3050, 'NYK': 7500,
    'OKC': 3650, 'ORL': 3200, 'PHI': 4600, 'PHX': 4300, 'POR': 3500,
    'SAC': 3700, 'SAS': 3850, 'UTA': 3550, 'WAS': 4100
}

# ============================================================
# 1. 计算市场特征
# ============================================================
market_features = {}
for team in df_2123['TEAM'].unique():
    team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')
    latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[-1]

    gdp_norm = latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0
    fans_norm = latest['FANS']
    attend_norm = latest['ATTENDANCE'] / 100000
    market_score = gdp_norm * 0.57 + fans_norm * 0.49 + attend_norm * 0.40

    market_features[team] = {'MARKET_SCORE': market_score}

features_df = pd.DataFrame.from_dict(market_features, orient='index').reset_index()
features_df.columns = ['TEAM', 'MARKET_SCORE']

# ============================================================
# 2. 训练模型
# ============================================================
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

# 计算训练集残差
train_df['LOG_PREDICTED'] = alpha + beta * train_df['RWIN'] + theta * train_df['PLAYER_EXPENSES'] + gamma * train_df['MARKET_SCORE']
residuals = train_df['LOG_TV'] - train_df['LOG_PREDICTED']
residual_std = residuals.std()
dof = len(X_train) - X_train_with_intercept.shape[1]  # 自由度

print("=" * 60)
print("MODEL TRAINING SUMMARY")
print("=" * 60)
print(f"Coefficients: α={alpha:.4f}, β={beta:.4f}, θ={theta:.4f}, γ={gamma:.4f}")
print(f"Residual std: {residual_std:.4f}, Degrees of freedom: {dof}")

# ============================================================
# 3. 预测2024年数据
# ============================================================
df_2024 = df_2425[df_2425['SEASON'] == 2024].copy()
df_2024 = pd.merge(df_2024, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
df_2024['ACTUAL_TV'] = df_2024['TEAM'].map(tv_2024_actual)

# 预测值
df_2024['LOG_PREDICTED'] = (alpha + beta * df_2024['RWIN'] +
                            theta * df_2024['PLAYER_EXPENSES'] +
                            gamma * df_2024['MARKET_SCORE'])
df_2024['PREDICTED_TV'] = np.exp(df_2024['LOG_PREDICTED']) * 1.084

# ============================================================
# 4. 计算预测区间
# ============================================================
confidence_level = 0.95
t_value = stats.t.ppf((1 + confidence_level) / 2, dof)

# 计算预测区间标准差
n = len(X_train)
pred_std = residual_std * np.sqrt(1 + 1 / n)  # 简化计算

df_2024['LOG_PRED_LOWER'] = df_2024['LOG_PREDICTED'] - t_value * pred_std
df_2024['LOG_PRED_UPPER'] = df_2024['LOG_PREDICTED'] + t_value * pred_std

# 转换为原始尺度
df_2024['PRED_LOWER'] = np.exp(df_2024['LOG_PRED_LOWER']) * 1.084
df_2024['PRED_UPPER'] = np.exp(df_2024['LOG_PRED_UPPER']) * 1.084

# 检查实际值是否在预测区间内
df_2024['IN_PI'] = (df_2024['ACTUAL_TV'] >= df_2024['PRED_LOWER']) & (df_2024['ACTUAL_TV'] <= df_2024['PRED_UPPER'])

# 预测区间统计
pi_coverage = df_2024['IN_PI'].mean() * 100
avg_pi_width = (df_2024['PRED_UPPER'] - df_2024['PRED_LOWER']).mean()

print("\n" + "=" * 60)
print("PREDICTION INTERVAL VALIDATION")
print("=" * 60)
print(f"\nPrediction Level: {confidence_level * 100:.0f}%")
print(f"Teams within PI: {df_2024['IN_PI'].sum()}/{len(df_2024)} ({pi_coverage:.1f}%)")
print(f"Average PI Width: ${avg_pi_width:,.0f}")
print(f"PI Width Range: ${(df_2024['PRED_UPPER'] - df_2024['PRED_LOWER']).min():,.0f} - ${(df_2024['PRED_UPPER'] - df_2024['PRED_LOWER']).max():,.0f}")

# 显示超出预测区间的球队
outside_pi = df_2024[~df_2024['IN_PI']]
if len(outside_pi) > 0:
    print(f"\nTeams outside prediction interval ({len(outside_pi)}):")
    for _, row in outside_pi.iterrows():
        if row['ACTUAL_TV'] < row['PRED_LOWER']:
            position = "below"
            distance_pct = (row['PRED_LOWER'] - row['ACTUAL_TV']) / row['ACTUAL_TV'] * 100
        else:
            position = "above"
            distance_pct = (row['ACTUAL_TV'] - row['PRED_UPPER']) / row['ACTUAL_TV'] * 100
        print(f"  {row['TEAM']}: {position} PI by {distance_pct:.1f}%")
else:
    print(f"\nAll teams within prediction interval!")

# ============================================================
# 5. 可视化1：预测值 vs 实际值 + 预测区间
# ============================================================
plt.figure(figsize=(14, 8))

# 按预测值排序
df_sorted = df_2024.sort_values('PREDICTED_TV')

# 绘制预测区间
plt.fill_between(range(len(df_sorted)),
                 df_sorted['PRED_LOWER'],
                 df_sorted['PRED_UPPER'],
                 alpha=0.15, color=BLUE_GREEN_GOLD[1],
                 label=f'{confidence_level * 100:.0f}% Prediction Interval')

# 绘制预测值线
plt.plot(range(len(df_sorted)), df_sorted['PREDICTED_TV'],
         color=BLUE_GREEN_GOLD[0], linewidth=3,
         marker='o', markersize=10, markeredgecolor='white', markeredgewidth=1.5,
         label='Predicted Value')

# 绘制实际值
for i, (idx, row) in enumerate(df_sorted.iterrows()):
    if row['IN_PI']:
        # 在预测区间内的点
        plt.scatter(i, row['ACTUAL_TV'], color=BLUE_GREEN_GOLD[4], s=120,
                    edgecolor='black', linewidth=1.5, zorder=5, marker='o')
    else:
        # 超出预测区间的点
        plt.scatter(i, row['ACTUAL_TV'], color=BLUE_GREEN_GOLD[6], s=150,
                    edgecolor='black', linewidth=2, zorder=6, marker='s')
        # 添加标签
        va_pos = 'bottom' if row['ACTUAL_TV'] > row['PRED_UPPER'] else 'top'
        plt.text(i, row['ACTUAL_TV'], row['TEAM'],
                 fontsize=10, ha='center', va=va_pos,
                 fontweight='bold', color=BLUE_GREEN_GOLD[6])

plt.xlabel('Teams (Sorted by Predicted Value)', fontsize=13, fontweight='bold')
plt.ylabel('Team Value ($M)', fontsize=13, fontweight='bold')
plt.title(f'NBA Team Value Prediction with {confidence_level * 100:.0f}% Prediction Intervals\n'
          f'Coverage: {df_2024["IN_PI"].sum()}/{len(df_2024)} teams within interval',
          fontsize=16, fontweight='bold', pad=20)

# 添加完美预测线
min_val = min(df_sorted['PRED_LOWER'].min(), df_sorted['ACTUAL_TV'].min())
max_val = max(df_sorted['PRED_UPPER'].max(), df_sorted['ACTUAL_TV'].max())
plt.plot([0, len(df_sorted) - 1], [min_val, max_val], 'k--', alpha=0.3, linewidth=1, label='Perfect Prediction')

# 自定义图例
from matplotlib.patches import Patch

legend_elements = [
    Patch(facecolor=BLUE_GREEN_GOLD[1], alpha=0.15, label=f'{confidence_level * 100:.0f}% Prediction Interval'),
    plt.Line2D([0], [0], color=BLUE_GREEN_GOLD[0], marker='o', markersize=10, linewidth=3,
               markeredgecolor='white', markeredgewidth=1.5, label='Predicted Value'),
    plt.Line2D([0], [0], color=BLUE_GREEN_GOLD[4], marker='o', markersize=10, linewidth=0,
               label='Actual Value (in PI)', markeredgecolor='black'),
    plt.Line2D([0], [0], color=BLUE_GREEN_GOLD[6], marker='s', markersize=10, linewidth=0,
               label='Actual Value (outside PI)', markeredgecolor='black'),
    plt.Line2D([0], [0], color='black', linestyle='--', linewidth=1, alpha=0.3, label='Perfect Prediction')
]
plt.legend(handles=legend_elements, loc='upper left', fontsize=11, framealpha=0.9)

plt.grid(True, alpha=0.2, linestyle='--')
plt.xticks(range(len(df_sorted)), df_sorted['TEAM'], rotation=45, ha='right', fontsize=10)
plt.ylim(min_val * 0.95, max_val * 1.05)
plt.tight_layout()
plt.savefig('prediction_with_intervals.png', dpi=300, bbox_inches='tight')
print("\n✓ Chart 1 saved as 'prediction_with_intervals.png'")

# ============================================================
# 6. 可视化2：预测误差分析
# ============================================================
plt.figure(figsize=(14, 8))

# 计算百分比误差
df_2024['ERROR_PCT'] = (df_2024['PREDICTED_TV'] - df_2024['ACTUAL_TV']) / df_2024['ACTUAL_TV'] * 100

# 按误差排序
df_sorted_error = df_2024.sort_values('ERROR_PCT')

# 创建条形图
bars = plt.bar(range(len(df_sorted_error)), df_sorted_error['ERROR_PCT'],
               color=[BLUE_GREEN_GOLD[4] if in_pi else BLUE_GREEN_GOLD[6]
                      for in_pi in df_sorted_error['IN_PI']],
               edgecolor='black', linewidth=1.2, alpha=0.8)

# 计算预测区间边界（使用t_value * pred_std转换回百分比）
# 平均百分比边界
avg_bound_pct = t_value * pred_std * 100  # 近似转换

plt.axhline(y=-avg_bound_pct, color=BLUE_GREEN_GOLD[1], linestyle='--', linewidth=2.5, alpha=0.8,
            label=f'PI Lower bound ({-avg_bound_pct:.1f}%)')
plt.axhline(y=avg_bound_pct, color=BLUE_GREEN_GOLD[1], linestyle='--', linewidth=2.5, alpha=0.8,
            label=f'PI Upper bound ({avg_bound_pct:.1f}%)')
plt.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)

# 添加零误差参考区域
plt.axhspan(-5, 5, alpha=0.1, color=BLUE_GREEN_GOLD[2], label='±5% Error Zone')

# 添加数据标签（只显示显著误差或超出PI的球队）
for i, (idx, row) in enumerate(df_sorted_error.iterrows()):
    if not row['IN_PI'] or abs(row['ERROR_PCT']) > 15:
        # 在条形上方或下方添加标签
        offset = 3 if row['ERROR_PCT'] >= 0 else -8
        plt.text(i, row['ERROR_PCT'] + offset,
                 f"{row['TEAM']}\n({row['ERROR_PCT']:.1f}%)",
                 fontsize=9, ha='center', va='bottom' if row['ERROR_PCT'] >= 0 else 'top',
                 fontweight='bold', color=BLUE_GREEN_GOLD[0])

plt.xlabel('Teams (Sorted by Prediction Error)', fontsize=13, fontweight='bold')
plt.ylabel('Prediction Error (%)', fontsize=13, fontweight='bold')
plt.title(f'Prediction Error Distribution with {confidence_level * 100:.0f}% Prediction Interval Bounds\n'
          f'Mean Absolute Error: {df_2024["ERROR_PCT"].abs().mean():.1f}% | Coverage: {pi_coverage:.1f}%',
          fontsize=16, fontweight='bold', pad=20)

plt.legend(loc='upper right', fontsize=11, framealpha=0.9)
plt.grid(True, alpha=0.2, linestyle='--', axis='y')
plt.xticks([])  # 隐藏x轴刻度

# 设置y轴范围
y_max = max(df_sorted_error['ERROR_PCT'].max(), avg_bound_pct) * 1.2
y_min = min(df_sorted_error['ERROR_PCT'].min(), -avg_bound_pct) * 1.2
plt.ylim(y_min, y_max)

plt.tight_layout()
plt.savefig('error_analysis_with_intervals.png', dpi=300, bbox_inches='tight')
print("✓ Chart 2 saved as 'error_analysis_with_intervals.png'")

# ============================================================
# 7. 保存详细结果
# ============================================================
output_df = df_2024[['TEAM', 'PREDICTED_TV', 'ACTUAL_TV', 'PRED_LOWER', 'PRED_UPPER',
                     'IN_PI', 'ERROR_PCT', 'RWIN', 'PLAYER_EXPENSES', 'MARKET_SCORE']].copy()
output_df = output_df.sort_values('PREDICTED_TV', ascending=False)

# 计算PI宽度
output_df['PI_Width'] = output_df['PRED_UPPER'] - output_df['PRED_LOWER']

# 将PI_Width列复制回df_2024以便后续使用
df_2024['PI_Width'] = output_df['PI_Width'].values

# 添加预测状态
output_df['Prediction_Status'] = output_df['IN_PI'].apply(lambda x: 'Within PI' if x else 'Outside PI')

output_df.columns = ['Team', 'Predicted_Value', 'Actual_Value', 'PI_Lower', 'PI_Upper',
                     'In_Prediction_Interval', 'Error_Pct', 'RWIN', 'Player_Expenses',
                     'Market_Score', 'PI_Width', 'Prediction_Status']

output_df.to_excel('predictions_with_intervals_analysis.xlsx', index=False)

# ============================================================
# 8. 最终结果摘要
# ============================================================
print("\n" + "=" * 60)
print("FINAL RESULTS SUMMARY")
print("=" * 60)

# 计算MAE
mae = (df_2024['PREDICTED_TV'] - df_2024['ACTUAL_TV']).abs().mean()

print(f"\n📊 Model Performance Metrics:")
train_r2 = 1 - (residuals.var() / y_train.var())
print(f"  • Training R²: {train_r2:.4f}")
print(f"  • Residual Std Error: {residual_std:.4f}")
print(f"  • Mean Absolute Error: ${mae:,.0f}")

print(f"\n🎯 {confidence_level * 100:.0f}% Prediction Interval Analysis:")
print(f"  • Coverage Rate: {pi_coverage:.1f}% ({df_2024['IN_PI'].sum()}/{len(df_2024)} teams)")
print(f"  • Average PI Width: ${avg_pi_width:,.0f}")
print(f"  • Min PI Width: ${df_2024['PI_Width'].min():,.0f}")
print(f"  • Max PI Width: ${df_2024['PI_Width'].max():,.0f}")

print(f"\n📈 Prediction Accuracy:")
mape = df_2024['ERROR_PCT'].abs().mean()
print(f"  • MAPE: {mape:.2f}%")
print(f"  • Teams within ±10% error: {(df_2024['ERROR_PCT'].abs() <= 10).sum()}/{len(df_2024)}")
print(f"  • Teams within ±20% error: {(df_2024['ERROR_PCT'].abs() <= 20).sum()}/{len(df_2024)}")

# 重新获取超出预测区间的球队（确保包含ERROR_PCT列）
outside_pi_updated = df_2024[~df_2024['IN_PI']]
if len(outside_pi_updated) > 0:
    print(f"\n⚠️  Teams Outside Prediction Interval:")
    for _, row in outside_pi_updated.iterrows():
        print(f"  • {row['TEAM']}: Error = {row['ERROR_PCT']:.1f}%")

print(f"\n✅ Best Predictions (lowest error):")
best_3 = df_2024.nsmallest(3, df_2024['ERROR_PCT'].abs())
for _, row in best_3.iterrows():
    print(f"  • {row['TEAM']}: Error = {row['ERROR_PCT']:.1f}%")

print(f"\n📁 Detailed results saved to 'predictions_with_intervals_analysis.xlsx'")
print("=" * 60)