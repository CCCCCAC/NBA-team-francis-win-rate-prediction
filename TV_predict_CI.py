import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import seaborn as sns

# 设置英文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_excel('indicators.xlsx')

print("=" * 80)
print("TEAM VALUATION MODEL with Confidence Intervals")
print("=" * 80)

# ============================================================================
# STEP 1: 统一单位 - 确保所有货币值以十亿美元为单位
# ============================================================================
print("\nConverting values to Billions of Dollars...")

# 转换TEAM_VALUE到十亿美元
df['TEAM_VALUE_BILLIONS'] = df['TEAM_VALUE'] / 1000.0  # 从百万转换为十亿

# 转换PLAYER_EXPENSES到十亿美元
df['PLAYER_EXPENSES_BILLIONS'] = df['PLAYER_EXPENSES'] / 1000.0  # 从百万转换为十亿

print("Unit conversion complete. All values now in Billions ($B).")


# ============================================================================
# STEP 2: 用2021-2024年数据拟合参数 + 简单置信区间
# ============================================================================
def log_valuation_model(X, alpha, beta, theta):
    rwin, player_exp = X
    return alpha + beta * rwin + theta * player_exp


df_2021_2024 = df[(df['SEASON'] >= 2021) & (df['SEASON'] <= 2024)].copy()
team_params = {}

np.random.seed(42)  # 可重复结果

for team in sorted(df_2021_2024['TEAM'].unique()):
    team_data = df_2021_2024[df_2021_2024['TEAM'] == team].copy()
    team_data = team_data.sort_values('SEASON')

    if len(team_data) < 3:
        print(f"  Skipping {team}: Insufficient data")
        continue

    try:
        # 使用统一单位后的变量
        X = (team_data['RWIN'].values, team_data['PLAYER_EXPENSES_BILLIONS'].values)
        y = np.log(team_data['TEAM_VALUE_BILLIONS'].values)

        # 简单拟合
        params, _ = curve_fit(log_valuation_model, X, y, p0=[np.mean(y), 1.0, 0.01], maxfev=5000)
        alpha, beta, theta = params

        # 计算标准误差（简化版）
        n = len(y)
        if n > 3:  # 有足够数据计算标准误差
            residuals = y - log_valuation_model(X, alpha, beta, theta)
            mse = np.sum(residuals ** 2) / (n - 3)

            # 参数协方差矩阵的简化估计
            param_se = np.sqrt(mse / n)

            team_params[team] = {
                'Alpha': alpha, 'Beta': beta, 'Theta': theta,
                'Alpha_SE': param_se, 'Beta_SE': param_se * 0.5, 'Theta_SE': param_se,
                'Samples': n
            }
        else:
            team_params[team] = {
                'Alpha': alpha, 'Beta': beta, 'Theta': theta,
                'Alpha_SE': 0.1, 'Beta_SE': 0.05, 'Theta_SE': 0.1,
                'Samples': n
            }

        print(f"  {team}: α={alpha:.3f}, β={beta:.3f}, θ={theta:.3f}")

    except Exception as e:
        print(f"  Failed for {team}: {str(e)}")

print(f"\nTotal teams fitted: {len(team_params)}")

# ============================================================================
# STEP 3: 预测2025年TV + 简化置信区间
# ============================================================================
print("\n" + "=" * 80)
print("PREDICTIONS FOR 2025 with Simplified Confidence Intervals")
print("=" * 80)

df_2025 = df[df['SEASON'] == 2025].copy()
predictions = []

for team in team_params.keys():
    if team in df_2025['TEAM'].values:
        team_2025 = df_2025[df_2025['TEAM'] == team].iloc[0]
        params = team_params[team]

        # 点预测（用原始参数）
        ln_pred = params['Alpha'] + params['Beta'] * team_2025['RWIN'] + params['Theta'] * team_2025[
            'PLAYER_EXPENSES_BILLIONS']
        pred_point = np.exp(ln_pred)
        actual_tv = team_2025['TEAM_VALUE_BILLIONS']

        # 简化置信区间：使用参数标准误差
        se_total = np.sqrt(
            params['Alpha_SE'] ** 2 +
            (params['Beta_SE'] * team_2025['RWIN']) ** 2 +
            (params['Theta_SE'] * team_2025['PLAYER_EXPENSES_BILLIONS']) ** 2
        )

        # 95% 置信区间
        ci_multiplier = 1.96  # 95% 置信度
        ln_ci_lower = ln_pred - ci_multiplier * se_total
        ln_ci_upper = ln_pred + ci_multiplier * se_total

        # 转换回原始尺度
        pred_ci_lower = np.exp(ln_ci_lower)
        pred_ci_upper = np.exp(ln_ci_upper)

        # 计算误差和CI宽度
        error_percent = ((pred_point - actual_tv) / actual_tv) * 100
        ci_width_percent = ((pred_ci_upper - pred_ci_lower) / pred_point) * 100

        predictions.append({
            'TEAM': team,
            'Predicted_TV_B': pred_point,
            'CI_Lower_B': pred_ci_lower,
            'CI_Upper_B': pred_ci_upper,
            'CI_Width_Pct': ci_width_percent,
            'Actual_TV_B': actual_tv,
            'Error_Percent': error_percent,
            'In_CI': pred_ci_lower <= actual_tv <= pred_ci_upper,
            'RWIN_2025': team_2025['RWIN'],
            'PE_2025_B': team_2025['PLAYER_EXPENSES_BILLIONS']
        })

        print(f"  {team:3s}: ${pred_point:.2f}B [{pred_ci_lower:.2f}, {pred_ci_upper:.2f}]B | "
              f"Actual: ${actual_tv:.2f}B | CI Width: {ci_width_percent:.1f}% | "
              f"In CI: {'✓' if pred_ci_lower <= actual_tv <= pred_ci_upper else '✗'}")

predictions_df = pd.DataFrame(predictions)

# ============================================================================
# STEP 4: 性能评估
# ============================================================================
print("\n" + "=" * 80)
print("PERFORMANCE SUMMARY")
print("=" * 80)

if len(predictions_df) > 0:
    # 基础指标
    mape = np.mean(np.abs(predictions_df['Error_Percent']))
    ci_coverage = np.mean(predictions_df['In_CI']) * 100
    avg_ci_width = np.mean(predictions_df['CI_Width_Pct'])

    print(f"\nModel Performance:")
    print(f"  • MAPE: {mape:.2f}%")
    print(f"  • 95% CI Coverage: {ci_coverage:.1f}% of teams")
    print(f"  • Average CI Width: {avg_ci_width:.1f}% of predicted value")
    print(f"  • Teams inside CI: {sum(predictions_df['In_CI'])}/{len(predictions_df)}")

    # 最佳预测
    print(f"\nTop 3 Most Accurate Predictions:")
    for _, row in predictions_df.nsmallest(3, 'Error_Percent').iterrows():
        print(
            f"  {row['TEAM']}: Pred=${row['Predicted_TV_B']:.2f}B, Actual=${row['Actual_TV_B']:.2f}B, Error={row['Error_Percent']:.1f}%")

# ============================================================================
# STEP 5: 简单可视化
# ============================================================================
print("\n" + "=" * 80)
print("GENERATING VISUALIZATIONS")
print("=" * 80)

if len(predictions_df) > 0:
    # 图1: 预测vs实际值
    plt.figure(figsize=(12, 6))

    # 按字母顺序排序
    predictions_df = predictions_df.sort_values('TEAM')

    teams = predictions_df['TEAM'].values
    x_pos = range(len(teams))

    plt.errorbar(x_pos, predictions_df['Predicted_TV_B'],
                 yerr=[predictions_df['Predicted_TV_B'] - predictions_df['CI_Lower_B'],
                       predictions_df['CI_Upper_B'] - predictions_df['Predicted_TV_B']],
                 fmt='o', capsize=5, label='Prediction ±95% CI', alpha=0.7)

    plt.scatter(x_pos, predictions_df['Actual_TV_B'],
                color='red', s=80, label='Actual Value', zorder=5)

    plt.xlabel('Teams')
    plt.ylabel('Team Value (Billion $)')
    plt.title('NBA Team Value Predictions for 2025 with 95% Confidence Intervals')
    plt.xticks(x_pos, teams, rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig('nba_valuations_2025.png', dpi=300, bbox_inches='tight')
    print("  Chart saved as 'nba_valuations_2025.png'")

    # 图2: 预测误差分布
    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.hist(predictions_df['Error_Percent'], bins=10, edgecolor='black', alpha=0.7)
    plt.axvline(x=0, color='red', linestyle='--', alpha=0.5)
    plt.xlabel('Prediction Error (%)')
    plt.ylabel('Number of Teams')
    plt.title('Distribution of Prediction Errors')
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.scatter(predictions_df['Predicted_TV_B'], predictions_df['Actual_TV_B'], alpha=0.7)

    # 添加对角线
    min_val = min(predictions_df['Predicted_TV_B'].min(), predictions_df['Actual_TV_B'].min())
    max_val = max(predictions_df['Predicted_TV_B'].max(), predictions_df['Actual_TV_B'].max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Prediction')

    plt.xlabel('Predicted Value ($B)')
    plt.ylabel('Actual Value ($B)')
    plt.title('Predicted vs Actual Values')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('nba_prediction_analysis.png', dpi=300, bbox_inches='tight')
    print("  Chart saved as 'nba_prediction_analysis.png'")

    # 保存结果到CSV
    predictions_df.to_csv('nba_team_predictions_2025.csv', index=False)
    print("  Predictions saved as 'nba_team_predictions_2025.csv'")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)