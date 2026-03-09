import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_excel('indicators.xlsx')


# 定义模型: ln(TEAM_VALUE) = α + β * RWIN + θ * PLAYER_EXPENSES
def log_valuation_model(X, alpha, beta, theta):
    rwin, player_exp = X
    return alpha + beta * rwin + theta * player_exp


print("=" * 80)
print("TEAM VALUATION MODEL - Parameter Fitting and Prediction")
print("Model: ln(TEAM_VALUE) = α + β × RWIN + θ × PLAYER_EXPENSES")
print("=" * 80)

# ============================================================================
# PART 1: 用2021-2024年数据拟合参数
# ============================================================================
print("\n" + "=" * 80)
print("PART 1: Parameter Fitting using 2021-2024 data")
print("=" * 80)

df_2021_2024 = df[(df['SEASON'] >= 2021) & (df['SEASON'] <= 2024)].copy()
team_params = {}

for team in sorted(df_2021_2024['TEAM'].unique()):
    team_data = df_2021_2024[df_2021_2024['TEAM'] == team].copy()
    team_data = team_data.sort_values('SEASON')

    if len(team_data) < 3:
        print(f"  Skipping {team}: Insufficient data ({len(team_data)} seasons)")
        continue

    try:
        X = (team_data['RWIN'].values, team_data['PLAYER_EXPENSES'].values)
        y = np.log(team_data['TEAM_VALUE'].values)

        params, _ = curve_fit(log_valuation_model, X, y, p0=[np.mean(y), 1.0, 0.01], maxfev=5000)
        alpha, beta, theta = params

        team_params[team] = {
            'Alpha': alpha,
            'Beta': beta,
            'Theta': theta,
            'Samples': len(y),
            'Mean_TV_2021_2024': team_data['TEAM_VALUE'].mean()
        }
        print(f"  {team}: α={alpha:.3f}, β={beta:.3f}, θ={theta:.4f} (n={len(y)})")
    except Exception as e:
        print(f"  Failed for {team}: {str(e)}")

print(f"\nTotal teams successfully fitted: {len(team_params)}")

# ============================================================================
# PART 2: 使用拟合参数预测2025年TV
# ============================================================================
print("\n" + "=" * 80)
print("PART 2: Predicting 2025 TEAM_VALUE using fitted parameters")
print("=" * 80)

# 获取2025年数据
df_2025 = df[df['SEASON'] == 2025].copy()

predictions = []
for team in team_params.keys():
    if team in df_2025['TEAM'].values:
        team_2025 = df_2025[df_2025['TEAM'] == team].iloc[0]
        params = team_params[team]

        # 预测ln(TV)
        ln_predicted = params['Alpha'] + params['Beta'] * team_2025['RWIN'] + params['Theta'] * team_2025[
            'PLAYER_EXPENSES']


        # 转换为实际TV值
        # *k=1.1调节因子
        predicted_tv = np.exp(ln_predicted)*1.10
        actual_tv = team_2025['TEAM_VALUE']

        # 计算预测误差
        error = predicted_tv - actual_tv
        error_percent = (error / actual_tv) * 100

        predictions.append({
            'TEAM': team,
            'Predicted_TV': predicted_tv,
            'Actual_TV': actual_tv,
            'Error': error,
            'Error_Percent': error_percent,
            'Alpha': params['Alpha'],
            'Beta': params['Beta'],
            'Theta': params['Theta'],
            'RWIN_2025': team_2025['RWIN'],
            'PE_2025': team_2025['PLAYER_EXPENSES']
        })

        print(f"  {team}: Predicted={predicted_tv:,.1f}, Actual={actual_tv:,.1f}, Error={error_percent:+.1f}%")

predictions_df = pd.DataFrame(predictions)

# ============================================================================
# PART 3: 计算模型性能指标
# ============================================================================
print("\n" + "=" * 80)
print("PART 3: Model Performance Metrics for 2025 Prediction")
print("=" * 80)

if len(predictions_df) > 0:
    # 基本统计
    mae = np.mean(np.abs(predictions_df['Error']))
    mape = np.mean(np.abs(predictions_df['Error_Percent']))
    rmse = np.sqrt(np.mean(predictions_df['Error'] ** 2))

    # R²计算
    ss_res = np.sum(predictions_df['Error'] ** 2)
    ss_tot = np.sum((predictions_df['Actual_TV'] - predictions_df['Actual_TV'].mean()) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    print(f"\nPrediction Performance Metrics:")
    print(f"  Number of predictions: {len(predictions_df)}")
    print(f"  R² Score: {r2:.4f}")
    print(f"  RMSE: {rmse:,.1f}")
    print(f"  MAE: {mae:,.1f}")
    print(f"  MAPE: {mape:.2f}%")

    # 预测准确度分布
    print(f"\nPrediction Accuracy Distribution:")
    for threshold in [5, 10, 15, 20]:
        within_threshold = np.sum(np.abs(predictions_df['Error_Percent']) <= threshold)
        percentage = (within_threshold / len(predictions_df)) * 100
        print(f"  Within ±{threshold}%: {within_threshold} teams ({percentage:.1f}%)")

    # 最佳和最差预测
    print(f"\nTop 5 Best Predictions:")
    for i, row in predictions_df.reindex(predictions_df['Error_Percent'].abs().nsmallest(5).index).iterrows():
        print(
            f"  {row['TEAM']}: Error={row['Error_Percent']:+.1f}% (Pred={row['Predicted_TV']:,.0f}, Act={row['Actual_TV']:,.0f})")

    print(f"\nTop 5 Worst Predictions:")
    for i, row in predictions_df.reindex(predictions_df['Error_Percent'].abs().nlargest(5).index).iterrows():
        print(
            f"  {row['TEAM']}: Error={row['Error_Percent']:+.1f}% (Pred={row['Predicted_TV']:,.0f}, Act={row['Actual_TV']:,.0f})")

# ============================================================================
# PART 4: 可视化
# ============================================================================
print("\n" + "=" * 80)
print("PART 4: Generating Visualization Plots")
print("=" * 80)

if len(predictions_df) > 0:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 图1: 预测值 vs 实际值散点图
    ax1 = axes[0, 0]
    min_val = min(predictions_df['Predicted_TV'].min(), predictions_df['Actual_TV'].min())
    max_val = max(predictions_df['Predicted_TV'].max(), predictions_df['Actual_TV'].max())

    ax1.scatter(predictions_df['Actual_TV'], predictions_df['Predicted_TV'],
                alpha=0.7, s=80, edgecolors='black', linewidth=0.5)
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Prediction')

    # 为每个点添加球队标签（只标注误差最大的5个）
    largest_errors = predictions_df.nlargest(5, 'Error_Percent', keep='all')
    for _, row in largest_errors.iterrows():
        ax1.annotate(row['TEAM'],
                     (row['Actual_TV'], row['Predicted_TV']),
                     textcoords="offset points",
                     xytext=(0, 10),
                     ha='center',
                     fontsize=9)

    ax1.set_xlabel('Actual TEAM_VALUE 2025', fontsize=12)
    ax1.set_ylabel('Predicted TEAM_VALUE 2025', fontsize=12)
    ax1.set_title('Predicted vs Actual TEAM_VALUE (2025)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 图2: 预测误差分布
    ax2 = axes[0, 1]
    errors = predictions_df['Error_Percent'].values
    ax2.hist(errors, bins=15, edgecolor='black', alpha=0.7)
    ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    ax2.set_xlabel('Prediction Error (%)', fontsize=12)
    ax2.set_ylabel('Number of Teams', fontsize=12)
    ax2.set_title('Distribution of Prediction Errors', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # 添加统计信息
    mean_error = np.mean(errors)
    std_error = np.std(errors)
    ax2.text(0.05, 0.95, f'Mean: {mean_error:.1f}%\nStd: {std_error:.1f}%',
             transform=ax2.transAxes, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 图3: 误差与参数的关系
    ax3 = axes[1, 0]
    scatter = ax3.scatter(predictions_df['Beta'], predictions_df['Error_Percent'],
                          c=predictions_df['Theta'], cmap='viridis', s=80,
                          edgecolors='black', linewidth=0.5)

    ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
    ax3.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    ax3.set_xlabel('Beta Coefficient (RWIN)', fontsize=12)
    ax3.set_ylabel('Prediction Error (%)', fontsize=12)
    ax3.set_title('Prediction Error vs Beta Coefficient', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # 添加颜色条
    plt.colorbar(scatter, ax=ax3, label='Theta Coefficient (PE)')

    # 图4: 预测准确性排名
    ax4 = axes[1, 1]
    sorted_df = predictions_df.copy()
    sorted_df['Abs_Error'] = sorted_df['Error_Percent'].abs()
    sorted_df = sorted_df.sort_values('Abs_Error')

    x_pos = range(len(sorted_df))
    colors = ['green' if err < 10 else 'orange' if err < 20 else 'red'
              for err in sorted_df['Abs_Error']]

    bars = ax4.bar(x_pos, sorted_df['Error_Percent'], color=colors, alpha=0.7)
    ax4.axhline(y=0, color='black', linestyle='-', alpha=0.3)

    # 添加数值标签（每3个球队显示一个）
    for i, (x, row) in enumerate(zip(x_pos, sorted_df.iterrows())):
        if i % 3 == 0:  # 每3个显示一个
            ax4.text(x, sorted_df.iloc[i]['Error_Percent'] + (1 if sorted_df.iloc[i]['Error_Percent'] >= 0 else -3),
                     sorted_df.iloc[i]['TEAM'], rotation=90, ha='center', fontsize=8)

    ax4.set_xlabel('Teams (sorted by prediction accuracy)', fontsize=12)
    ax4.set_ylabel('Prediction Error (%)', fontsize=12)
    ax4.set_title('Prediction Accuracy by Team', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('prediction_performance_2025.png', dpi=300, bbox_inches='tight')
    print(f"  Visualization saved as 'prediction_performance_2025.png'")

    # 保存预测结果到Excel
    predictions_df.to_excel('team_value_predictions_2025.xlsx', index=False)
    print(f"  Detailed predictions saved as 'team_value_predictions_2025.xlsx'")

    # 显示关键统计摘要
    print(f"\n  KEY PERFORMANCE SUMMARY:")
    print(f"  • R² Score: {r2:.4f}")
    print(f"  • Average Error: {mape:.2f}%")
    print(f"  • Best Prediction: {predictions_df['Error_Percent'].abs().min():.1f}%")
    print(f"  • Worst Prediction: {predictions_df['Error_Percent'].abs().max():.1f}%")
    print(f"  • Teams within ±10% error: {np.sum(np.abs(predictions_df['Error_Percent']) <= 10)}/{len(predictions_df)}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)