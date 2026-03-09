# # import pandas as pd
# # import numpy as np
# # import matplotlib.pyplot as plt
# # import seaborn as sns
# #
# # # 读取数据
# # df = pd.read_excel('indicators.xlsx')
# #
# # # 按球队和赛季排序
# # df = df.sort_values(['TEAM', 'SEASON']).reset_index(drop=True)
# #
# # # 对齐数据：每个赛季的WINPCT与下一个赛季的RWIN比较
# # df_aligned = []
# #
# # for team in df['TEAM'].unique():
# #     team_data = df[df['TEAM'] == team].sort_values('SEASON')
# #
# #     for i in range(len(team_data) - 1):
# #         current_row = team_data.iloc[i]
# #         next_row = team_data.iloc[i + 1]
# #
# #         aligned_row = {
# #             'TEAM': team,
# #             'SEASON_PRED': current_row['SEASON'],  # 预测赛季
# #             'SEASON_ACTUAL': next_row['SEASON'],  # 实际赛季
# #             'WINPCT': current_row['WINPCT'],  # 预测值
# #             'RWIN': next_row['RWIN']  # 实际值（下一个赛季）
# #         }
# #         df_aligned.append(aligned_row)
# #
# # # 创建对齐后的数据框
# # df_aligned = pd.DataFrame(df_aligned)
# #
# # # 计算误差
# # df_aligned['ERROR'] = df_aligned['RWIN'] - df_aligned['WINPCT']
# # df_aligned['ABS_ERROR'] = abs(df_aligned['ERROR'])
# #
# # print("=" * 50)
# # print("ALIGNED MODEL PERFORMANCE (WINPCT_{t} vs RWIN_{t+1}):")
# # print("=" * 50)
# # print(f"数据量: {len(df_aligned)} 个预测-实际配对")
# # print(f"MSE:  {np.mean(df_aligned['ERROR'] ** 2):.6f}")
# # print(f"MAE:  {np.mean(df_aligned['ABS_ERROR']):.6f}")
# # print(f"RMSE: {np.sqrt(np.mean(df_aligned['ERROR'] ** 2)):.6f}")
# #
# # print("\n" + "=" * 50)
# # print("AVERAGE ABSOLUTE ERROR BY TEAM:")
# # print("=" * 50)
# #
# # team_error = df_aligned.groupby('TEAM')['ABS_ERROR'].mean().sort_values()
# # for team, error in team_error.items():
# #     print(f"{team}: {error:.6f}")
# #
# # print("\n" + "=" * 50)
# # print("AVERAGE ABSOLUTE ERROR BY PREDICTION SEASON:")
# # print("=" * 50)
# #
# # season_error = df_aligned.groupby('SEASON_PRED')['ABS_ERROR'].mean()
# # for season, error in season_error.items():
# #     print(f"{season}: {error:.6f}")
# #
# # print("\n" + "=" * 50)
# # print("TEAM BIAS ANALYSIS (RWIN_{t+1} - WINPCT_{t}):")
# # print("=" * 50)
# # print("Positive = Model UNDERESTIMATES team (predicts too low)")
# # print("Negative = Model OVERESTIMATES team (predicts too high)")
# # print()
# #
# # team_biases = df_aligned.groupby('TEAM')['ERROR'].mean().sort_values()
# # for team, bias in team_biases.items():
# #     direction = "持续低估" if bias > 0 else "持续高估"
# #     print(f"{team}: {bias:+.4f} ({direction})")
# #
# # # 简单可视化
# # plt.figure(figsize=(15, 10))
# #
# # # 1. 误差分布
# # plt.subplot(2, 2, 1)
# # sns.histplot(df_aligned['ERROR'], kde=True, bins=20)
# # plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
# # plt.title('Error Distribution (RWIN_{t+1} - WINPCT_{t})')
# # plt.xlabel('Error')
# # plt.ylabel('Frequency')
# #
# # # 2. 按球队的误差箱线图
# # plt.subplot(2, 2, 2)
# # team_order = team_error.index.tolist()
# # sns.boxplot(data=df_aligned, x='TEAM', y='ERROR', order=team_order)
# # plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# # plt.xticks(rotation=90)
# # plt.title('Errors by Team')
# # plt.xlabel('Team')
# # plt.ylabel('Error')
# #
# # # 3. 预测赛季的趋势
# # plt.subplot(2, 2, 3)
# # season_avg = df_aligned.groupby('SEASON_PRED')['ERROR'].mean()
# # sns.lineplot(x=season_avg.index, y=season_avg.values, marker='o')
# # plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# # plt.title('Error Trend by Prediction Season')
# # plt.xlabel('Prediction Season')
# # plt.ylabel('Average Error')
# #
# # # 4. 误差 vs 预测值
# # plt.subplot(2, 2, 4)
# # plt.scatter(df_aligned['WINPCT'], df_aligned['ERROR'], alpha=0.6)
# # plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# # plt.xlabel('Predicted Win Rate (WINPCT)')
# # plt.ylabel('Error')
# # plt.title('Errors vs Predicted Values')
# #
# # plt.tight_layout()
# # plt.savefig('aligned_model_analysis.png', dpi=300, bbox_inches='tight')
# # plt.show()
# #
# # print("\n" + "=" * 50)
# # print("SUMMARY:")
# # print("=" * 50)
# # print(f"总预测-实际配对数量: {len(df_aligned)}")
# # print(f"平均绝对误差 (MAE): {np.mean(df_aligned['ABS_ERROR']):.4f}")
# # print(f"均方根误差 (RMSE): {np.sqrt(np.mean(df_aligned['ERROR'] ** 2)):.4f}")
# #
# # # 保存对齐后的数据（可选）
# # df_aligned.to_excel('aligned_data.xlsx', index=False)
# # print(f"\n对齐后的数据已保存为 'aligned_data.xlsx'")
# # print("可视化已保存为 'aligned_model_analysis.png'")
#
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
#
# # 读取对齐后的数据
# df = pd.read_excel('aligned_data.xlsx')
#
# # 计算原始误差
# df['ERROR'] = df['RWIN'] - df['WINPCT']
# df['ABS_ERROR'] = abs(df['ERROR'])
#
# print("=" * 50)
# print("ORIGINAL MODEL PERFORMANCE:")
# print("=" * 50)
# print(f"MAE:  {np.mean(df['ABS_ERROR']):.4f}")
# print(f"RMSE: {np.sqrt(np.mean(df['ERROR'] ** 2)):.4f}")
#
#
# # ============ 离群因子修正 ============
#
# def calculate_outlier_factor(team_errors):
#     """计算离群因子：基于持续偏差程度"""
#     n = len(team_errors)
#     if n < 2:
#         return 0  # 数据不足
#
#     # 1. 计算平均偏差
#     avg_bias = np.mean(team_errors)
#
#     # 2. 计算偏差方向一致性（最近3个赛季）
#     recent_errors = team_errors[-min(3, n):]
#     direction_consistency = sum(1 for e in recent_errors if e * avg_bias > 0) / len(recent_errors)
#
#     # 3. 计算离群因子
#     # 基础因子：偏差的绝对值
#     base_factor = min(abs(avg_bias) * 2, 1.0)  # 限制在0-1之间
#
#     # 方向一致性加成
#     if direction_consistency >= 2 / 3:  # 最近3季有2季以上同方向
#         consistency_bonus = 0.2 * direction_consistency
#     else:
#         consistency_bonus = 0
#
#     # 最终离群因子
#     outlier_factor = base_factor + consistency_bonus
#     return min(outlier_factor, 1.0)
#
#
# # 计算每个球队的离群因子
# team_factors = {}
# for team in df['TEAM'].unique():
#     team_data = df[df['TEAM'] == team].sort_values('SEASON_PRED')
#     errors = team_data['ERROR'].values
#     factor = calculate_outlier_factor(errors)
#     team_factors[team] = factor
#
# # 应用修正
# corrected_preds = []
# for idx, row in df.iterrows():
#     team = row['TEAM']
#     original_pred = row['WINPCT']
#
#     # 获取该球队的平均历史偏差
#     team_data = df[df['TEAM'] == team]
#     avg_bias = team_data['ERROR'].mean()
#
#     # 应用修正：修正幅度 = 离群因子 * 平均偏差
#     correction = team_factors[team] * avg_bias
#     corrected_pred = original_pred + correction
#
#     # 确保在合理范围内
#     corrected_pred = max(0.05, min(0.95, corrected_pred))
#     corrected_preds.append(corrected_pred)
#
# df['CORRECTED_PRED'] = corrected_preds
# df['OUTLIER_FACTOR'] = df['TEAM'].map(team_factors)
#
# # 计算修正后误差
# df['CORRECTED_ERROR'] = df['RWIN'] - df['CORRECTED_PRED']
# df['ABS_CORRECTED_ERROR'] = abs(df['CORRECTED_ERROR'])
#
# print("\n" + "=" * 50)
# print("CORRECTED MODEL PERFORMANCE:")
# print("=" * 50)
# print(f"MAE:  {np.mean(df['ABS_CORRECTED_ERROR']):.4f}")
# print(f"RMSE: {np.sqrt(np.mean(df['CORRECTED_ERROR'] ** 2)):.4f}")
#
# # 计算改进
# mae_imp = (np.mean(df['ABS_ERROR']) - np.mean(df['ABS_CORRECTED_ERROR'])) / np.mean(df['ABS_ERROR']) * 100
# print(f"\nMAE改进: {mae_imp:+.1f}%")
#
# # ============ 球队分析 ============
# print("\n" + "=" * 50)
# print("TEAM ANALYSIS:")
# print("=" * 50)
#
# # 按离群因子排序
# sorted_teams = sorted(team_factors.items(), key=lambda x: x[1], reverse=True)
#
# print("\n高离群因子球队（前10）：")
# print(f"{'球队':<15} {'离群因子':<12} {'平均偏差':<12} {'原始MAE':<12} {'修正MAE':<12} {'改进':<10}")
# print("-" * 75)
#
# team_results = []
# for team, factor in sorted_teams[:10]:
#     team_data = df[df['TEAM'] == team]
#     orig_mae = team_data['ABS_ERROR'].mean()
#     corr_mae = team_data['ABS_CORRECTED_ERROR'].mean()
#     avg_bias = team_data['ERROR'].mean()
#     imp = (orig_mae - corr_mae) / orig_mae * 100 if orig_mae > 0 else 0
#     team_results.append((team, factor, avg_bias, orig_mae, corr_mae, imp))
#     print(f"{team:<15} {factor:.3f}        {avg_bias:+.4f}     {orig_mae:.4f}      {corr_mae:.4f}      {imp:+.1f}%")
#
# # 所有球队改进统计
# all_team_results = []
# for team in df['TEAM'].unique():
#     team_data = df[df['TEAM'] == team]
#     orig_mae = team_data['ABS_ERROR'].mean()
#     corr_mae = team_data['ABS_CORRECTED_ERROR'].mean()
#     imp = (orig_mae - corr_mae) / orig_mae * 100 if orig_mae > 0 else 0
#     all_team_results.append(imp)
#
# improved = sum(1 for imp in all_team_results if imp > 0)
# total = len(all_team_results)
#
# print(f"\n球队改进统计：{improved}/{total} 支球队有改进 ({improved / total * 100:.1f}%)")
#
# # ============ 可视化 ============
# plt.figure(figsize=(15, 8))
#
# # 1. 修正前后误差对比（箱线图）
# plt.subplot(2, 3, 1)
# error_data = [df['ERROR'], df['CORRECTED_ERROR']]
# box = plt.boxplot(error_data, patch_artist=True, widths=0.6)
# colors = ['lightblue', 'lightgreen']
# for patch, color in zip(box['boxes'], colors):
#     patch.set_facecolor(color)
# plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# plt.xticks([1, 2], ['Original', 'Corrected'])
# plt.title('Error Distribution Comparison')
# plt.ylabel('Error')
# plt.grid(True, alpha=0.3)
#
# # 2. 绝对误差对比（箱线图）
# plt.subplot(2, 3, 2)
# abs_error_data = [df['ABS_ERROR'], df['ABS_CORRECTED_ERROR']]
# box = plt.boxplot(abs_error_data, patch_artist=True, widths=0.6)
# for patch, color in zip(box['boxes'], colors):
#     patch.set_facecolor(color)
# plt.xticks([1, 2], ['Original', 'Corrected'])
# plt.title('Absolute Error Comparison')
# plt.ylabel('Absolute Error')
# plt.grid(True, alpha=0.3)
#
# # 3. 离群因子分布
# plt.subplot(2, 3, 3)
# plt.hist(df['OUTLIER_FACTOR'], bins=15, alpha=0.7, color='purple', edgecolor='black')
# plt.axvline(x=np.mean(df['OUTLIER_FACTOR']), color='red', linestyle='--',
#             label=f'Mean: {np.mean(df["OUTLIER_FACTOR"]):.3f}')
# plt.title('Outlier Factor Distribution')
# plt.xlabel('Outlier Factor')
# plt.ylabel('Frequency')
# plt.legend()
# plt.grid(True, alpha=0.3)
#
# # 4. 球队改进幅度
# plt.subplot(2, 3, 4)
# teams = [r[0] for r in team_results]
# improvements = [r[5] for r in team_results]
# colors = ['green' if imp > 0 else 'red' for imp in improvements]
# plt.bar(range(len(teams)), improvements, color=colors, alpha=0.7)
# plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
# plt.xticks(range(len(teams)), teams, rotation=45, ha='right')
# plt.ylabel('MAE Improvement (%)')
# plt.title('Top Outlier Teams Improvement')
# plt.grid(True, alpha=0.3)
#
# # 5. 离群因子 vs 平均偏差
# plt.subplot(2, 3, 5)
# teams_scatter = []
# factors_scatter = []
# biases_scatter = []
# for team in df['TEAM'].unique():
#     team_data = df[df['TEAM'] == team]
#     teams_scatter.append(team)
#     factors_scatter.append(team_data['OUTLIER_FACTOR'].iloc[0])
#     biases_scatter.append(team_data['ERROR'].mean())
#
# colors_scatter = ['red' if b < 0 else 'green' for b in biases_scatter]
# plt.scatter(factors_scatter, biases_scatter, c=colors_scatter, alpha=0.6, s=50)
# plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
# plt.xlabel('Outlier Factor')
# plt.ylabel('Average Bias')
# plt.title('Outlier Factor vs Average Bias')
# plt.grid(True, alpha=0.3)
#
# # 6. 误差分布密度图
# plt.subplot(2, 3, 6)
# import seaborn as sns
# sns.kdeplot(df['ERROR'], label='Original Error', fill=True, alpha=0.3, color='blue')
# sns.kdeplot(df['CORRECTED_ERROR'], label='Corrected Error', fill=True, alpha=0.3, color='green')
# plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
# plt.xlabel('Error Value')
# plt.ylabel('Density')
# plt.title('Error Distribution Density Comparison')
# plt.legend()
# plt.grid(True, alpha=0.3)
#
# plt.tight_layout()
# plt.savefig('outlier_correction_results.png', dpi=300, bbox_inches='tight')
# plt.show()
#
# # ============ 总结 ============
# print("\n" + "=" * 50)
# print("SUMMARY:")
# print("=" * 50)
# print(f"平均离群因子: {np.mean(df['OUTLIER_FACTOR']):.3f}")
# print(f"高离群因子(>0.3)球队数: {sum(1 for f in team_factors.values() if f > 0.3)}")
# print(f"整体MAE改进: {mae_imp:+.1f}%")
# print(f"\n可视化已保存为 'outlier_correction_results.png'")
#
# # 保存修正结果
# df[['TEAM', 'SEASON_PRED', 'SEASON_ACTUAL', 'WINPCT', 'RWIN',
#     'ERROR', 'CORRECTED_PRED', 'CORRECTED_ERROR', 'OUTLIER_FACTOR']].to_excel(
#     'outlier_corrected_results.xlsx', index=False)
# print("修正结果已保存为 'outlier_corrected_results.xlsx'")



import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 使用您提供的配色方案
hex_colors = [
    "#274753",  # 深蓝绿 - 原始模型主色
    "#297270",  # 蓝绿 - 原始模型辅助色
    "#299d8f",  # 青绿
    "#8ab07c",  # 浅绿
    "#e7c66b",  # 金黄
    "#f3a361",  # 橙黄
    "#e66d50"   # 橙红 - 修正模型主色
]

# 读取对齐后的数据
df = pd.read_excel('aligned_data.xlsx')

# 计算原始误差
df['ERROR'] = df['RWIN'] - df['WINPCT']
df['ABS_ERROR'] = abs(df['ERROR'])

print("=" * 50)
print("ORIGINAL MODEL PERFORMANCE:")
print("=" * 50)
print(f"MAE:  {np.mean(df['ABS_ERROR']):.4f}")
print(f"RMSE: {np.sqrt(np.mean(df['ERROR'] ** 2)):.4f}")

# ============ 离群因子修正 ============

def calculate_outlier_factor(team_errors):
    """计算离群因子：基于持续偏差程度"""
    n = len(team_errors)
    if n < 2:
        return 0  # 数据不足

    # 1. 计算平均偏差
    avg_bias = np.mean(team_errors)

    # 2. 计算偏差方向一致性（最近3个赛季）
    recent_errors = team_errors[-min(3, n):]
    direction_consistency = sum(1 for e in recent_errors if e * avg_bias > 0) / len(recent_errors)

    # 3. 计算离群因子
    # 基础因子：偏差的绝对值
    base_factor = min(abs(avg_bias) * 2, 1.0)  # 限制在0-1之间

    # 方向一致性加成
    if direction_consistency >= 2 / 3:  # 最近3季有2季以上同方向
        consistency_bonus = 0.2 * direction_consistency
    else:
        consistency_bonus = 0

    # 最终离群因子
    outlier_factor = base_factor + consistency_bonus
    return min(outlier_factor, 1.0)

# 计算每个球队的离群因子
team_factors = {}
for team in df['TEAM'].unique():
    team_data = df[df['TEAM'] == team].sort_values('SEASON_PRED')
    errors = team_data['ERROR'].values
    factor = calculate_outlier_factor(errors)
    team_factors[team] = factor

# 应用修正
corrected_preds = []
for idx, row in df.iterrows():
    team = row['TEAM']
    original_pred = row['WINPCT']

    # 获取该球队的平均历史偏差
    team_data = df[df['TEAM'] == team]
    avg_bias = team_data['ERROR'].mean()

    # 应用修正：修正幅度 = 离群因子 * 平均偏差
    correction = team_factors[team] * avg_bias
    corrected_pred = original_pred + correction

    # 确保在合理范围内
    corrected_pred = max(0.05, min(0.95, corrected_pred))
    corrected_preds.append(corrected_pred)

df['CORRECTED_PRED'] = corrected_preds
df['OUTLIER_FACTOR'] = df['TEAM'].map(team_factors)

# 计算修正后误差
df['CORRECTED_ERROR'] = df['RWIN'] - df['CORRECTED_PRED']
df['ABS_CORRECTED_ERROR'] = abs(df['CORRECTED_ERROR'])

print("\n" + "=" * 50)
print("CORRECTED MODEL PERFORMANCE:")
print("=" * 50)
print(f"MAE:  {np.mean(df['ABS_CORRECTED_ERROR']):.4f}")
print(f"RMSE: {np.sqrt(np.mean(df['CORRECTED_ERROR'] ** 2)):.4f}")

# 计算改进
mae_imp = (np.mean(df['ABS_ERROR']) - np.mean(df['ABS_CORRECTED_ERROR'])) / np.mean(df['ABS_ERROR']) * 100
print(f"\nMAE Improvement: {mae_imp:+.1f}%")

# ============ 可视化 ============
plt.figure(figsize=(10, 6))

# 误差分布密度图
sns.kdeplot(df['ERROR'], label='Original Model (No Correction)',
            fill=True, alpha=0.5, color=hex_colors[0], linewidth=2)
sns.kdeplot(df['CORRECTED_ERROR'], label='Corrected Model (Outlier Factor)',
            fill=True, alpha=0.5, color=hex_colors[6], linewidth=2)

plt.axvline(x=0, color='black', linestyle='--', alpha=0.7, linewidth=1)
plt.xlabel('Prediction Error (RWIN - Prediction)', fontsize=12)
plt.ylabel('Density', fontsize=12)
plt.title('Win Rate Prediction Error Distribution Density Comparison\nOriginal vs Corrected Models', fontsize=14, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('error_density_comparison.png', dpi=300, bbox_inches='tight')
plt.show()

# ============ 总结 ============
print("\n" + "=" * 50)
print("SUMMARY:")
print("=" * 50)
print(f"Average Outlier Factor: {np.mean(df['OUTLIER_FACTOR']):.3f}")
print(f"Teams with High Outlier Factor (>0.3): {sum(1 for f in team_factors.values() if f > 0.3)}")
print(f"Overall MAE Improvement: {mae_imp:+.1f}%")
print(f"\nError density plot saved as 'error_density_comparison.png'")

# 保存修正结果
df[['TEAM', 'SEASON_PRED', 'SEASON_ACTUAL', 'WINPCT', 'RWIN',
    'ERROR', 'CORRECTED_PRED', 'CORRECTED_ERROR', 'OUTLIER_FACTOR']].to_excel(
    'outlier_corrected_results.xlsx', index=False)
print("Corrected results saved as 'outlier_corrected_results.xlsx'")