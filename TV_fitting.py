# import pandas as pd
# import numpy as np
# from scipy.optimize import curve_fit
#
# # 读取数据
# df = pd.read_excel('indicators.xlsx')
#
#
# # 定义模型: ln(TEAM_VALUE) = α + β * RWIN + θ * PLAYER_EXPENSES
# def log_valuation_model(X, alpha, beta, theta):
#     rwin, player_exp = X
#     return alpha + beta * rwin + theta * player_exp
#
#
# print("=" * 60)
# print("TEAM VALUATION MODEL - PARAMETER FITTING ONLY")
# print("Model: ln(TEAM_VALUE) = α + β × RWIN + θ × PLAYER_EXPENSES")
# print("=" * 60)
#
# # 第一种拟合：使用2021-2025年数据
# print("\n[FIT 1] Using 2022-2025 data")
# print("-" * 40)
#
# # df_2022_2025 = df[df['SEASON'] >= 2021].copy()
# df_2021_2023 = df[(df['SEASON'] >= 2021) & (df['SEASON'] <= 2023)].copy()
# team_results_1 = {}
#
# for team in sorted(df_2021_2023['TEAM'].unique()):
#     team_data = df_2021_2023[df_2021_2023['TEAM'] == team].copy()
#     team_data = team_data.sort_values('SEASON')
#
#     if len(team_data) < 3:
#         continue
#
#     try:
#         X = (team_data['RWIN'].values, team_data['PLAYER_EXPENSES'].values)
#         y = np.log(team_data['TEAM_VALUE'].values)
#
#         params, _ = curve_fit(log_valuation_model, X, y, p0=[np.mean(y), 1.0, 0.01], maxfev=5000)
#         alpha, beta, theta = params
#
#         team_results_1[team] = {
#             'Alpha': alpha,
#             'Beta': beta,
#             'Theta': theta,
#             'Samples': len(y)
#         }
#     except:
#         continue
#
# print(f"Successfully fitted: {len(team_results_1)} teams")
#
# # 第二种拟合：使用2021-2024年数据
# print("\n[FIT 2] Using 2022-2024 data")
# print("-" * 40)
#
# df_2021_2024 = df[(df['SEASON'] >= 2021) & (df['SEASON'] <= 2024)].copy()
# team_results_2 = {}
#
# for team in sorted(df_2021_2024['TEAM'].unique()):
#     team_data = df_2021_2024[df_2021_2024['TEAM'] == team].copy()
#     team_data = team_data.sort_values('SEASON')
#
#     if len(team_data) < 3:
#         continue
#
#     try:
#         X = (team_data['RWIN'].values, team_data['PLAYER_EXPENSES'].values)
#         y = np.log(team_data['TEAM_VALUE'].values)
#
#         params, _ = curve_fit(log_valuation_model, X, y, p0=[np.mean(y), 1.0, 0.01], maxfev=5000)
#         alpha, beta, theta = params
#
#         team_results_2[team] = {
#             'Alpha': alpha,
#             'Beta': beta,
#             'Theta': theta,
#             'Samples': len(y)
#         }
#     except:
#         continue
#
# print(f"Successfully fitted: {len(team_results_2)} teams")
#
# # 获取两个数据集中都有的球队（交集）
# common_teams = sorted(set(team_results_1.keys()).intersection(set(team_results_2.keys())))
#
# print("\n" + "=" * 80)
# print("INDIVIDUAL TEAM PARAMETER COMPARISON")
# print("=" * 80)
# print(
#     "Team           |  Alpha (2021-2024) |  Alpha (2021-2023) |  Beta (2021-2024) |  Beta (2021-2023) |  Theta (2021-2024) |  Theta (2021-2023) |  Samples")
# print("-" * 120)
#
# for team in common_teams:
#     r1 = team_results_1[team]
#     r2 = team_results_2[team]
#
#     print(
#         f"{team:<12} | {r1['Alpha']:>18.3f} | {r2['Alpha']:>18.3f} | {r1['Beta']:>17.3f} | {r2['Beta']:>17.3f} | {r1['Theta']:>18.4f} | {r2['Theta']:>18.4f} | {r1['Samples']}/{r2['Samples']}")
#
# # 显示参数差异最大的球队
# print("\n" + "=" * 80)
# print("TEAMS WITH LARGEST PARAMETER CHANGES")
# print("=" * 80)
#
# # 计算每个球队的参数变化
# changes = []
# for team in common_teams:
#     r1 = team_results_1[team]
#     r2 = team_results_2[team]
#
#     alpha_change = r2['Alpha'] - r1['Alpha']
#     beta_change = r2['Beta'] - r1['Beta']
#     theta_change = r2['Theta'] - r1['Theta']
#     total_change = abs(alpha_change) + abs(beta_change) + abs(theta_change)
#
#     changes.append({
#         'TEAM': team,
#         'Alpha_change': alpha_change,
#         'Beta_change': beta_change,
#         'Theta_change': theta_change,
#         'Total_change': total_change
#     })

# # 按总变化量排序
# changes_df = pd.DataFrame(changes)
#
# print("\nTop 5 teams with largest TOTAL parameter changes:")
# for i, row in changes_df.nlargest(5, 'Total_change').iterrows():
#     print(
#         f"{row['TEAM']:>12}: Alpha Δ={row['Alpha_change']:7.3f}, Beta Δ={row['Beta_change']:7.3f}, Theta Δ={row['Theta_change']:7.4f}, Total={row['Total_change']:7.3f}")
#
# print("\nTop 5 teams with largest ALPHA changes:")
# for i, row in changes_df.reindex(changes_df['Alpha_change'].abs().nlargest(5).index).iterrows():
#     print(
#         f"{row['TEAM']:>12}: Alpha Δ={row['Alpha_change']:7.3f} (2022-2024={team_results_2[row['TEAM']]['Alpha']:.3f} vs 2022-2025={team_results_1[row['TEAM']]['Alpha']:.3f})")
#
# print("\nTop 5 teams with largest BETA changes:")
# for i, row in changes_df.reindex(changes_df['Beta_change'].abs().nlargest(5).index).iterrows():
#     print(
#         f"{row['TEAM']:>12}: Beta Δ={row['Beta_change']:7.3f} (2022-2024={team_results_2[row['TEAM']]['Beta']:.3f} vs 2022-2025={team_results_1[row['TEAM']]['Beta']:.3f})")
#
# print("\nTop 5 teams with largest THETA changes:")
# for i, row in changes_df.reindex(changes_df['Theta_change'].abs().nlargest(5).index).iterrows():
#     print(
#         f"{row['TEAM']:>12}: Theta Δ={row['Theta_change']:7.4f} (2022-2024={team_results_2[row['TEAM']]['Theta']:.4f} vs 2022-2025={team_results_1[row['TEAM']]['Theta']:.4f})")
#
# # 统计参数变化方向
# alpha_increased = sum(1 for team in common_teams if team_results_2[team]['Alpha'] > team_results_1[team]['Alpha'])
# beta_increased = sum(1 for team in common_teams if team_results_2[team]['Beta'] > team_results_1[team]['Beta'])
# theta_increased = sum(1 for team in common_teams if team_results_2[team]['Theta'] > team_results_1[team]['Theta'])
#
# print("\n" + "=" * 80)
# print("PARAMETER CHANGE DIRECTION SUMMARY")
# print("=" * 80)
# print(f"Alpha increased in {alpha_increased} teams, decreased in {len(common_teams) - alpha_increased} teams")
# print(f"Beta increased in {beta_increased} teams, decreased in {len(common_teams) - beta_increased} teams")
# print(f"Theta increased in {theta_increased} teams, decreased in {len(common_teams) - theta_increased} teams")
#
# print("\n" + "=" * 60)
# print("ANALYSIS COMPLETE")
# print("=" * 60)


import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

# 读取数据
df = pd.read_excel('indicators_all.xlsx')

# 只使用2021-2023年的数据
df_filtered = df[(df['SEASON'] >= 2021) & (df['SEASON'] <= 2023)].copy()


# 定义模型: ln(TEAM_VALUE) = α + β * RWIN + θ * PLAYER_EXPENSES + γ * GDP
def log_valuation_model_with_atten(X, alpha, beta, theta, gamma):
    rwin, player_exp, atten = X
    return alpha + beta * rwin + theta * player_exp + gamma * atten


print("=" * 80)
print("TEAM VALUATION MODEL WITH ATTEN - PARAMETER FITTING")
print("Model: ln(TEAM_VALUE) = α + β × RWIN + θ × PLAYER_EXPENSES + γ × ATTENDANCE")
print("Using 2021-2023 data only")
print("=" * 80)

# 对每个球队进行拟合
team_results = {}

for team in sorted(df_filtered['TEAM'].unique()):
    team_data = df_filtered[df_filtered['TEAM'] == team].copy()
    team_data = team_data.sort_values('SEASON')

    # 移除有空值的行
    team_data = team_data.dropna(subset=['RWIN', 'PLAYER_EXPENSES', 'ATTENDANCE', 'TEAM_VALUE'])

    if len(team_data) < 3:  # 需要3个完整年份的数据点
        continue

    try:
        X = (team_data['RWIN'].values, team_data['PLAYER_EXPENSES'].values, team_data['ATTENDANCE'].values)
        y = np.log(team_data['TEAM_VALUE'].values)

        params, _ = curve_fit(log_valuation_model_with_atten, X, y,
                              p0=[np.mean(y), 1.0, 0.01, 0.001],
                              maxfev=5000)
        alpha, beta, theta, gamma = params

        team_results[team] = {
            'Alpha': alpha,
            'Beta': beta,
            'Theta': theta,
            'Gamma': gamma,
            'Samples': len(y)
        }
    except:
        continue

# 输出每个队伍的参数
print("\n" + "=" * 100)
print("INDIVIDUAL TEAM PARAMETER ESTIMATES (2021-2023)")
print("=" * 100)
print(f"{'Team':<12} | {'Alpha':>10} | {'Beta (RWIN)':>12} | {'Theta (PE)':>12} | {'Gamma (atten)':>12} | {'Samples':>8}")
print("-" * 90)

for team, results in sorted(team_results.items()):
    print(f"{team:<12} | {results['Alpha']:>10.3f} | {results['Beta']:>12.4f} | "
          f"{results['Theta']:>12.4f} | {results['Gamma']:>12.6f} | {results['Samples']:>8}")

print(f"\nTotal teams fitted: {len(team_results)}")
print("=" * 60)