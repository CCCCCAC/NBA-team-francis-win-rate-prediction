
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error
import warnings

warnings.filterwarnings('ignore')

# 读取数据
df = pd.read_excel('indicators.xlsx')


# 定义对数线性拟合函数：ln(TEAM_VALUE) = α + β * RWIN + θ * PLAYER_EXPENSES
def log_valuation_model(X, alpha, beta, theta):
    """Log-linear team valuation model: ln(V) = α + β*RWIN + θ*PE"""
    rwin, player_exp = X
    return alpha + beta * rwin + theta * player_exp


# 为每个球队进行拟合
team_results = []

# 设置图形 - 简化到只显示重要部分
plt.figure(figsize=(16, 12))
n_rows = 6
n_cols = 5

for i, team in enumerate(sorted(df['TEAM'].unique())):
    team_data = df[df['TEAM'] == team].copy()

    # 确保有足够的数据点
    if len(team_data) < 3:
        continue

    # 准备数据 - 使用RWIN而不是WINPCT
    X = (team_data['RWIN'].values, team_data['PLAYER_EXPENSES'].values)
    y = np.log(team_data['TEAM_VALUE'].values)  # 对数变换

    # 尝试拟合模型
    try:
        # 初始参数猜测
        p0 = [np.mean(y), 1.0, 0.01]

        # 拟合模型
        params, cov = curve_fit(log_valuation_model, X, y, p0=p0, maxfev=5000)

        # 提取参数
        alpha, beta, theta = params

        # 计算预测值（对数值）
        y_pred_log = log_valuation_model(X, alpha, beta, theta)

        # 转换回原始尺度用于评估
        y_actual = team_data['TEAM_VALUE'].values
        y_pred = np.exp(y_pred_log)

        # 计算拟合指标（在原始尺度上）
        r2 = r2_score(y_actual, y_pred)
        rmse = np.sqrt(mean_squared_error(y_actual, y_pred))

        # 添加到结果列表
        team_results.append({
            'TEAM': team,
            'Alpha': alpha,
            'Beta': beta,
            'Theta': theta,
            'R2': r2,
            'RMSE': rmse,
            'Samples': len(y_actual)
        })

        # 绘制子图 - 简化为实际vs预测对比
        ax = plt.subplot(n_rows, n_cols, i + 1)

        # 绘制实际值和预测值
        seasons = team_data['SEASON'].astype(str).values
        x_pos = np.arange(len(seasons))

        ax.plot(x_pos, y_actual, 'o-', label='Actual', color='blue', linewidth=2, markersize=5)
        ax.plot(x_pos, y_pred, 's--', label='Predicted', color='red', linewidth=1.5, markersize=4)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(seasons, rotation=45, fontsize=7)
        ax.set_title(f'{team}\nR²={r2:.3f}', fontsize=9)
        ax.grid(True, alpha=0.3, linestyle=':')
        ax.legend(fontsize=6, loc='best')

    except Exception as e:
        print(f"Team {team} fitting failed: {e}")
        team_results.append({
            'TEAM': team,
            'Alpha': np.nan,
            'Beta': np.nan,
            'Theta': np.nan,
            'R2': np.nan,
            'RMSE': np.nan,
            'Samples': len(team_data)
        })

plt.tight_layout()
plt.suptitle('Team Valuation Model: ln(V) = α + β·RWIN + θ·PE', fontsize=14, y=1.02)
plt.show()

# 创建结果数据框
results_df = pd.DataFrame(team_results)

# 显示拟合结果汇总
print("=" * 80)
print("TEAM VALUATION MODEL FITTING RESULTS")
print("Model: ln(TEAM_VALUE) = α + β × RWIN + θ × PLAYER_EXPENSES")
print("=" * 80)

# 显示最佳拟合的球队
best_fits = results_df.sort_values('R2', ascending=False).head(10)
print("\nTop 10 Teams with Best Fit:")
print(best_fits[['TEAM', 'Alpha', 'Beta', 'Theta', 'R2', 'RMSE', 'Samples']].to_string(index=False))

# 统计整体拟合效果
print(f"\nOverall Statistics:")
print(f"Average R²: {results_df['R2'].mean():.3f}")
print(f"Median R²: {results_df['R2'].median():.3f}")
print(f"Teams with R² > 0.9: {(results_df['R2'] > 0.9).sum()}")
print(f"Teams with R² > 0.8: {(results_df['R2'] > 0.8).sum()}")
print(f"Teams with R² > 0.7: {(results_df['R2'] > 0.7).sum()}")
print(f"Teams with R² < 0.3: {(results_df['R2'] < 0.3).sum()}")

# 保存结果到Excel
output_file = '../TV_fitting.xlsx'
results_df.to_excel(output_file, index=False)
print(f"\nDetailed results saved to: {output_file}")

# 关键可视化：R²分布和参数关系
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. R²分布
r2_values = results_df['R2'].dropna()
axes[0, 0].hist(r2_values, bins=12, edgecolor='black', alpha=0.7, color='green')
axes[0, 0].axvline(r2_values.mean(), color='red', linestyle='--',
                   label=f'Mean R²: {r2_values.mean():.3f}', linewidth=2)
axes[0, 0].set_xlabel('R² (Goodness of Fit)', fontsize=11)
axes[0, 0].set_ylabel('Number of Teams', fontsize=11)
axes[0, 0].set_title('R² Distribution Across Teams', fontsize=12, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# 2. Beta (RWIN系数) vs R²
valid_data = results_df.dropna(subset=['Beta', 'R2'])
axes[0, 1].scatter(valid_data['Beta'], valid_data['R2'], alpha=0.6, edgecolors='black', s=80)
axes[0, 1].set_xlabel('Beta (RWIN Coefficient)', fontsize=11)
axes[0, 1].set_ylabel('R²', fontsize=11)
axes[0, 1].set_title('Impact of RWIN Coefficient on Model Fit', fontsize=12, fontweight='bold')
axes[0, 1].grid(True, alpha=0.3)

# 3. Theta (PE系数) vs R²
valid_data = results_df.dropna(subset=['Theta', 'R2'])
axes[1, 0].scatter(valid_data['Theta'], valid_data['R2'], alpha=0.6, edgecolors='black', s=80, color='orange')
axes[1, 0].set_xlabel('Theta (Player Expenses Coefficient)', fontsize=11)
axes[1, 0].set_ylabel('R²', fontsize=11)
axes[1, 0].set_title('Impact of Player Expenses Coefficient on Model Fit', fontsize=12, fontweight='bold')
axes[1, 0].grid(True, alpha=0.3)

# 4. Beta vs Theta
valid_data = results_df.dropna(subset=['Beta', 'Theta'])
scatter = axes[1, 1].scatter(valid_data['Beta'], valid_data['Theta'],
                             c=valid_data['R2'], cmap='viridis', alpha=0.7,
                             edgecolors='black', s=80)
axes[1, 1].set_xlabel('Beta (RWIN Coefficient)', fontsize=11)
axes[1, 1].set_ylabel('Theta (Player Expenses Coefficient)', fontsize=11)
axes[1, 1].set_title('Parameter Relationship (color = R²)', fontsize=12, fontweight='bold')
plt.colorbar(scatter, ax=axes[1, 1], label='R²')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# 显示参数统计
print("\nParameter Statistics:")
print(f"Alpha (Intercept) - Mean: {results_df['Alpha'].mean():.3f}, Std: {results_df['Alpha'].std():.3f}")
print(f"Beta (RWIN Coefficient) - Mean: {results_df['Beta'].mean():.3f}, Std: {results_df['Beta'].std():.3f}")
print(
    f"Theta (Player Expenses Coefficient) - Mean: {results_df['Theta'].mean():.4f}, Std: {results_df['Theta'].std():.4f}")

# 显示前3个最佳和最差拟合的球队对比
print("\n" + "=" * 80)
print("TOP 3 BEST FITTING TEAMS:")
top3 = results_df.sort_values('R2', ascending=False).head(3)
for idx, row in top3.iterrows():
    print(f"{row['TEAM']}: R²={row['R2']:.4f}, α={row['Alpha']:.3f}, β={row['Beta']:.3f}, θ={row['Theta']:.4f}")

print("\nTOP 3 WORST FITTING TEAMS:")
bottom3 = results_df.sort_values('R2', ascending=True).head(3)
for idx, row in bottom3.iterrows():
    print(f"{row['TEAM']}: R²={row['R2']:.4f}, α={row['Alpha']:.3f}, β={row['Beta']:.3f}, θ={row['Theta']:.4f}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETED!")
print("=" * 80)
#


# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.optimize import curve_fit
# from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
# import warnings
#
# warnings.filterwarnings('ignore')
#
# # 读取数据
# df = pd.read_excel('indicators.xlsx')
#
# # 按赛季排序
# df = df.sort_values(['TEAM', 'SEASON'])
#
#
# def train_predict_team(team_data):
#     """训练和预测单个球队"""
#     # 前4年作为训练集，第5年作为测试集
#     train_data = team_data[team_data['SEASON'] < 2025]
#     test_data = team_data[team_data['SEASON'] == 2025]
#
#     if len(train_data) < 3 or len(test_data) == 0:
#         return None
#
#     try:
#         # 数据标准化：对数值变量进行标准化
#         # 对TV取对数
#         train_tv_log = np.log(train_data['TEAM_VALUE'].values)
#
#         # 对RWIN进行z-score标准化
#         train_rwin_mean = train_data['RWIN'].mean()
#         train_rwin_std = train_data['RWIN'].std()
#
#         # 对PE进行z-score标准化
#         train_pe_mean = train_data['PLAYER_EXPENSES'].mean()
#         train_pe_std = train_data['PLAYER_EXPENSES'].std()
#
#         # 标准化训练数据
#         X1_train = (train_data['RWIN'].values - train_rwin_mean) / train_rwin_std
#         X2_train = (train_data['PLAYER_EXPENSES'].values - train_pe_mean) / train_pe_std
#
#         # 定义模型
#         def model(X, alpha, beta, theta):
#             rwin_norm, pe_norm = X
#             return alpha + beta * rwin_norm + theta * pe_norm
#
#         # 拟合模型
#         p0 = [np.mean(train_tv_log), 0.1, 0.1]
#         params, _ = curve_fit(model, (X1_train, X2_train), train_tv_log, p0=p0, maxfev=5000)
#         alpha, beta, theta = params
#
#         # 预测第5年
#         # 标准化测试数据（使用训练集的均值和标准差）
#         winpct_pred = test_data['WINPCT'].values[0]
#         winpct_norm = (winpct_pred - train_rwin_mean) / train_rwin_std
#
#         pe_pred = test_data['PLAYER_EXPENSES'].values[0]
#         pe_norm = (pe_pred - train_pe_mean) / train_pe_std
#
#         # 预测对数TV
#         tv_log_pred = alpha + beta * winpct_norm + theta * pe_norm
#
#         # 转换回原始尺度
#         tv_pred = np.exp(tv_log_pred)
#         tv_actual = test_data['TEAM_VALUE'].values[0]
#
#         # 计算相对误差
#         error_abs = abs(tv_pred - tv_actual)
#         error_rel = error_abs / tv_actual * 100
#
#         return {
#             'team': team_data['TEAM'].iloc[0],
#             'alpha': alpha,
#             'beta': beta,
#             'theta': theta,
#             'tv_actual': tv_actual,
#             'tv_pred': tv_pred,
#             'error_abs': error_abs,
#             'error_rel': error_rel,
#             'winpct_pred': winpct_pred,
#             'winpct_norm': winpct_norm,
#             'pe_pred': pe_pred,
#             'pe_norm': pe_norm,
#             'train_rwin_mean': train_rwin_mean,
#             'train_rwin_std': train_rwin_std,
#             'train_pe_mean': train_pe_mean,
#             'train_pe_std': train_pe_std,
#             'train_samples': len(train_data)
#         }
#
#     except Exception as e:
#         print(f"Team {team_data['TEAM'].iloc[0]} failed: {e}")
#         return None
#
#
# # 为所有球队进行训练和预测
# results = []
# for team in df['TEAM'].unique():
#     team_data = df[df['TEAM'] == team]
#     if len(team_data) >= 5:  # 需要至少5年数据
#         result = train_predict_team(team_data)
#         if result:
#             results.append(result)
#
# results_df = pd.DataFrame(results)
#
# # ==================== 可视化 ====================
#
# fig, axes = plt.subplots(2, 2, figsize=(14, 10))
#
# # 1. 预测值 vs 实际值散点图
# ax1 = axes[0, 0]
# if len(results_df) > 0:
#     ax1.scatter(results_df['tv_actual'], results_df['tv_pred'], alpha=0.7, s=80, edgecolors='black')
#     # 添加对角线（完美预测线）
#     min_val = min(results_df['tv_actual'].min(), results_df['tv_pred'].min())
#     max_val = max(results_df['tv_actual'].max(), results_df['tv_pred'].max())
#     ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.7, label='Perfect Prediction')
#     ax1.set_xlabel('Actual TV ($M)', fontsize=11)
#     ax1.set_ylabel('Predicted TV ($M)', fontsize=11)
#     ax1.set_title('Actual vs Predicted Team Values (2025)', fontsize=12, fontweight='bold')
#     ax1.legend()
#     ax1.grid(True, alpha=0.3)
#
#     # 计算R²
#     r2 = r2_score(results_df['tv_actual'], results_df['tv_pred'])
#     rmse = np.sqrt(mean_squared_error(results_df['tv_actual'], results_df['tv_pred']))
#     mae = mean_absolute_error(results_df['tv_actual'], results_df['tv_pred'])
#
#     # 在图中添加指标
#     textstr = f'R² = {r2:.3f}\nRMSE = {rmse:.0f}M\nMAE = {mae:.0f}M'
#     ax1.text(0.05, 0.95, textstr, transform=ax1.transAxes, fontsize=10,
#              verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
#
# # 2. 相对误差分布
# ax2 = axes[0, 1]
# if len(results_df) > 0:
#     errors = results_df['error_rel']
#     ax2.hist(errors, bins=15, edgecolor='black', alpha=0.7, color='orange')
#     ax2.axvline(errors.mean(), color='red', linestyle='--',
#                 label=f'Mean: {errors.mean():.1f}%')
#     ax2.axvline(errors.median(), color='blue', linestyle='--',
#                 label=f'Median: {errors.median():.1f}%')
#     ax2.set_xlabel('Prediction Error (%)', fontsize=11)
#     ax2.set_ylabel('Number of Teams', fontsize=11)
#     ax2.set_title('Prediction Error Distribution', fontsize=12, fontweight='bold')
#     ax2.legend()
#     ax2.grid(True, alpha=0.3)
#
# # 3. 预测精度排名
# ax3 = axes[1, 0]
# if len(results_df) > 0:
#     # 按误差排序
#     sorted_results = results_df.sort_values('error_rel').reset_index(drop=True)
#     teams = sorted_results['team']
#     errors = sorted_results['error_rel']
#
#     bars = ax3.barh(range(len(teams)), errors, color='steelblue', alpha=0.7)
#     ax3.set_yticks(range(len(teams)))
#     ax3.set_yticklabels(teams, fontsize=8)
#     ax3.set_xlabel('Prediction Error (%)', fontsize=11)
#     ax3.set_title('Prediction Accuracy by Team (Sorted)', fontsize=12, fontweight='bold')
#     ax3.grid(True, alpha=0.3, axis='x')
#
#     # 标注最小和最大误差
#     min_error_idx = errors.idxmin()
#     max_error_idx = errors.idxmax()
#
#     if min_error_idx < len(bars):
#         bars[min_error_idx].set_color('green')
#         ax3.text(errors[min_error_idx], min_error_idx, f' {errors[min_error_idx]:.1f}%',
#                  va='center', color='green', fontweight='bold')
#
#     if max_error_idx < len(bars):
#         bars[max_error_idx].set_color('red')
#         ax3.text(errors[max_error_idx], max_error_idx, f' {errors[max_error_idx]:.1f}%',
#                  va='center', color='red', fontweight='bold')
#
# # 4. 模型参数分布
# ax4 = axes[1, 1]
# if len(results_df) > 0:
#     # 创建参数分布箱线图
#     param_data = [results_df['beta'].dropna(), results_df['theta'].dropna()]
#     param_labels = ['Beta (RWIN/WINPCT)', 'Theta (PE)']
#
#     bp = ax4.boxplot(param_data, tick_labels=param_labels, patch_artist=True, showmeans=True,
#                      meanprops={'marker': 'o', 'markerfacecolor': 'white', 'markeredgecolor': 'black'})
#
#     # 设置颜色
#     colors_box = ['lightblue', 'lightgreen']
#     for patch, color in zip(bp['boxes'], colors_box):
#         patch.set_facecolor(color)
#         patch.set_alpha(0.7)
#
#     ax4.set_ylabel('Parameter Value', fontsize=11)
#     ax4.set_title('Model Parameter Distribution', fontsize=12, fontweight='bold')
#     ax4.grid(True, alpha=0.3, axis='y')
#
# plt.tight_layout()
# plt.suptitle('TV Prediction Model Validation (2021-2024 → 2025)', fontsize=14, fontweight='bold', y=1.02)
# plt.show()
#
# # ==================== 终端报告 ====================
# print("=" * 80)
# print("TV PREDICTION MODEL VALIDATION REPORT")
# print("=" * 80)
# print(f"Model: ln(TV) = α + β × (WINPCT_norm) + θ × (PE_norm)")
# print(f"Training: 2021-2024 seasons")
# print(f"Testing: 2025 season predictions")
# print("=" * 80)
#
# if len(results_df) > 0:
#     print(f"\nOVERALL PERFORMANCE:")
#     print(f"Teams evaluated: {len(results_df)}")
#     print(f"R² on 2025 predictions: {r2:.4f}")
#     print(f"RMSE: ${rmse:.0f}M")
#     print(f"MAE: ${mae:.0f}M")
#     print(f"Mean absolute error: {errors.mean():.1f}%")
#     print(f"Median absolute error: {errors.median():.1f}%")
#
#     print(f"\nERROR DISTRIBUTION:")
#     print(f"Teams with error < 5%: {(errors < 5).sum()} ({((errors < 5).sum() / len(errors) * 100):.1f}%)")
#     print(f"Teams with error < 10%: {(errors < 10).sum()} ({((errors < 10).sum() / len(errors) * 100):.1f}%)")
#     print(f"Teams with error < 20%: {(errors < 20).sum()} ({((errors < 20).sum() / len(errors) * 100):.1f}%)")
#     print(f"Teams with error > 30%: {(errors > 30).sum()} ({((errors > 30).sum() / len(errors) * 100):.1f}%)")
#
#     print(f"\nMODEL PARAMETERS (averaged across teams):")
#     print(f"Alpha (intercept): {results_df['alpha'].mean():.3f}")
#     print(f"Beta (WINPCT coefficient): {results_df['beta'].mean():.3f} ± {results_df['beta'].std():.3f}")
#     print(f"Theta (PE coefficient): {results_df['theta'].mean():.4f} ± {results_df['theta'].std():.4f}")
#
#     # 分析误差来源
#     print(f"\nERROR ANALYSIS:")
#     print(f"Average WINPCT prediction used: {results_df['winpct_pred'].mean():.3f}")
#     print(f"Average PE used: ${results_df['pe_pred'].mean():.0f}M")
#
#     # 分析Beta系数的符号
#     beta_positive = (results_df['beta'] > 0).sum()
#     beta_negative = (results_df['beta'] < 0).sum()
#     print(f"\nBETA COEFFICIENT ANALYSIS:")
#     print(f"Positive beta (WINPCT增加→TV增加): {beta_positive} teams ({beta_positive / len(results_df) * 100:.1f}%)")
#     print(f"Negative beta (WINPCT增加→TV减少): {beta_negative} teams ({beta_negative / len(results_df) * 100:.1f}%)")
#
#     print(f"\nBEST PREDICTIONS (error < 10%):")
#     best = results_df[results_df['error_rel'] < 10].sort_values('error_rel')
#     for _, row in best.head(10).iterrows():
#         print(
#             f"  {row['team']}: Actual=${row['tv_actual']:.0f}M, Pred=${row['tv_pred']:.0f}M, Error={row['error_rel']:.1f}%")
#
#     print(f"\nWORST PREDICTIONS (error > 30%):")
#     worst = results_df[results_df['error_rel'] > 30].sort_values('error_rel', ascending=False)
#     for _, row in worst.iterrows():
#         print(
#             f"  {row['team']}: Actual=${row['tv_actual']:.0f}M, Pred=${row['tv_pred']:.0f}M, Error={row['error_rel']:.1f}%")
#
#     print(f"\nSAMPLE PREDICTION DETAILS:")
#     sample = results_df.iloc[0]
#     print(f"  Team: {sample['team']}")
#     print(
#         f"  Model: ln(TV) = {sample['alpha']:.3f} + {sample['beta']:.3f}×(WINPCT_norm) + {sample['theta']:.4f}×(PE_norm)")
#     print(f"  Training stats: RWIN_mean={sample['train_rwin_mean']:.3f}, RWIN_std={sample['train_rwin_std']:.3f}")
#     print(f"                   PE_mean=${sample['train_pe_mean']:.0f}M, PE_std=${sample['train_pe_std']:.0f}M")
#     print(f"  2025 WINPCT: {sample['winpct_pred']:.3f} → normalized: {sample['winpct_norm']:.3f}")
#     print(f"  2025 PE: ${sample['pe_pred']:.0f}M → normalized: {sample['pe_norm']:.3f}")
#     print(
#         f"  Predicted TV: exp({sample['alpha']:.3f} + {sample['beta']:.3f}×{sample['winpct_norm']:.3f} + {sample['theta']:.4f}×{sample['pe_norm']:.3f})")
#     print(
#         f"              = exp({sample['alpha'] + sample['beta'] * sample['winpct_norm'] + sample['theta'] * sample['pe_norm']:.3f})")
#     print(
#         f"              = ${sample['tv_pred']:.0f}M (Actual: ${sample['tv_actual']:.0f}M, Error: {sample['error_rel']:.1f}%)")
#
#     # 模型诊断
#     print(f"\nMODEL DIAGNOSTICS:")
#     if r2 < 0:
#         print("  WARNING: Negative R² indicates model predictions are worse than using the mean.")
#         print("  Possible reasons:")
#         print("  1. Overfitting on training data")
#         print("  2. WINPCT predictions not accurate enough")
#         print("  3. Model form may not be appropriate")
#         print("  4. Significant outliers in the data")
#         print("  Suggestion: Consider adding more variables or using ensemble methods.")
#
# else:
#     print("\nNo teams with complete 5-year data available for validation.")
#
# print("=" * 80)
# print("VALIDATION COMPLETED")
# print("=" * 80)
#
# # 保存详细结果
# if len(results_df) > 0:
#     output_file = 'tv_prediction_validation_results.xlsx'
#     results_df.to_excel(output_file, index=False)
#     print(f"\nDetailed results saved to: {output_file}")