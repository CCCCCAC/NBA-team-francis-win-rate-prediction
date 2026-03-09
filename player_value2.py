# import pandas as pd
# import numpy as np
# import json
#
# # 位置权重（百分制）
# POSITION_WEIGHTS = {
#     "PG": {"FGA": 20.64, "G": 20.03, "PF": 19.72, "DRtg": 19.42, "ORtg": 18.96},
#     "SG": {"PF": 21.86, "eFG": 21.55, "FGA": 20.60, "TOV": 19.81, "ORtg": 19.18},
#     "SF": {"eFG": 20.90, "ORtg": 20.44, "FGA": 19.70, "FG": 19.26, "DRtg": 19.11},
#     "PF": {"TOV": 21.17, "FGA": 20.86, "eFG": 19.48, "G": 19.02, "ORtg": 18.87},
#     "C": {"eFG": 20.62, "FGA": 20.47, "PF": 20.00, "FG": 19.84, "G": 19.53}
# }
#
# # 伤病风险函数参数
# INJURY_PARAMS = {
#     'a0': -2.0,  # 截距项
#     'a1_youth': 0.03,  # 青年组年龄系数
#     'a1_mid': 0.04,
#     'a1_veteran': 0.06,  # 老将组年龄系数
#     'a2': 0.6,  # 负荷系数
#     'a3': 0.2  # 位置惩罚系数
# }
#
# # 风险折扣系数
# RISK_DISCOUNT_FACTOR = 0.2
#
#
# def calculate_injury_risk(player):
#     """
#     计算球员伤病风险
#     公式：risk = 1 / (1 + exp(-z))
#     z = a0 + a1×AgeEffect + a2×LoadEffect + a3×PositionPenalty
#     """
#     # 1. 年龄因子（分段处理）
#     age = player['Age']
#     age_base = age - 27  # 以27岁为基准
#
#     if age <= 27:
#         age_effect = age_base * INJURY_PARAMS['a1_youth']
#     elif age <= 31:
#         age_effect = age_base * INJURY_PARAMS['a1_mid']
#     else:
#         age_effect = age_base * INJURY_PARAMS['a1_veteran']
#
#     # 2. 负荷因子（对数归一化）
#     mp = player['MP']
#     load_effect = np.log(mp / 677 + 1) * INJURY_PARAMS['a2']
#
#     # 3. 位置因子
#     position_penalty = INJURY_PARAMS['a3'] if player['Pos'] in ['C', 'PF'] else 0
#
#     # 4. 计算z值
#     z = (INJURY_PARAMS['a0'] + age_effect + load_effect + position_penalty)
#
#     # 5. 计算风险
#     risk = 1 / (1 + np.exp(-z))
#
#     return risk
#
#
# def calculate_pca_score(player, zscore_params):
#     """
#     计算PCA效率分（使用全联盟Z-score参数标准化，每个指标20分，总分100分）
#     """
#     pos = player['Pos']
#     weights = POSITION_WEIGHTS.get(pos, {})
#
#     if pos not in zscore_params:
#         return sum(player.get(ind, 0) * (weight / 100) for ind, weight in weights.items())
#
#     params = zscore_params[pos]
#     total_score = 0
#
#     for ind, weight in weights.items():
#         if ind in params['means'] and ind in params['stds']:
#             mean_val = params['means'][ind]
#             std_val = params['stds'][ind]
#             player_value = player.get(ind, mean_val)
#
#             if std_val > 0:
#                 z_score = (player_value - mean_val) / std_val
#             else:
#                 z_score = 0
#
#             normalized_score = 1 / (1 + np.exp(-z_score))
#             total_score += normalized_score * 20
#
#     return total_score
#
#
# if __name__ == "__main__":
#     # 1. 加载Z-score参数
#     with open('global_zscore_params.json', 'r', encoding='utf-8') as f:
#         zscore_params = json.load(f)
#
#     # 2. 读取数据
#     df = pd.read_excel("players_by_team/OCKplayers.xlsx")
#
#     # 3. 计算PCA得分
#     df['pca_score'] = df.apply(lambda row: calculate_pca_score(row, zscore_params), axis=1)
#
#     # 4. 计算时间贡献率（归一化，平均值为1）
#     total_mp = df['MP'].sum()
#     num_players = len(df)
#     df['time_contribution'] = (df['MP'] / total_mp) * num_players
#
#     # 5. 计算PCA×时间贡献得分
#     df['pca_time_score'] = df['pca_score'] * df['time_contribution']
#
#     # 6. 计算伤病风险
#     df['injury_risk'] = df.apply(calculate_injury_risk, axis=1)
#
#     # 7. 计算风险折扣
#     df['risk_discount'] = 1 - (df['injury_risk'] * RISK_DISCOUNT_FACTOR)
#
#     # 8. 计算最终评分 = PCA×时间贡献得分 × 风险折扣
#     df['final_pca_score'] = df['pca_time_score'] * df['risk_discount']
#
#     # 9. 输出结果
#     print("最终PCA评分（包含时间贡献和风险折扣）:")
#     print("=" * 100)
#
#     # 按最终评分排序
#     df_sorted = df.sort_values('final_pca_score', ascending=False).reset_index(drop=True)
#
#     for i, row in df_sorted.iterrows():
#         print(f"{i + 1:2d}. {row['Player']:<25} 年龄: {row['Age']:>2}岁 位置: {row['Pos']:<2}")
#         print(f"    原始PCA: {row['pca_score']:6.2f} 时间贡献: {row['time_contribution']:.3f}")
#         print(f"    PCA×时间: {row['pca_time_score']:6.2f} 伤病风险: {row['injury_risk']:.3f}")
#         print(f"    风险折扣: {row['risk_discount']:.3f} 最终评分: {row['final_pca_score']:6.2f}")
#         print("-" * 80)
#
#     # 10. 统计信息
#     print("\n统计信息:")
#     print(f"球队总MP: {df['MP'].sum():.0f}分钟")
#     print(f"球员数量: {num_players}人")
#     print(f"平均原始PCA得分: {df['pca_score'].mean():.2f}")
#     print(f"平均时间贡献: {df['time_contribution'].mean():.3f}")
#     print(f"平均PCA×时间得分: {df['pca_time_score'].mean():.2f}")
#     print(f"平均伤病风险: {df['injury_risk'].mean():.3f}")
#     print(f"平均风险折扣: {df['risk_discount'].mean():.3f}")
#     print(f"平均最终评分: {df['final_pca_score'].mean():.2f}")
#
#     # 11. 按位置统计
#     positions = ['PG', 'SG', 'SF', 'PF', 'C']
#     print(f"\n按位置统计（前3名）:")
#
#     for pos in positions:
#         pos_df = df[df['Pos'] == pos]
#         if len(pos_df) > 0:
#             print(f"\n{pos}位置 ({len(pos_df)}人):")
#             pos_sorted = pos_df.sort_values('final_pca_score', ascending=False).head(3)
#             for j, (_, player_row) in enumerate(pos_sorted.iterrows(), 1):
#                 print(
#                     f"  {j}. {player_row['Player']:<20} 最终评分: {player_row['final_pca_score']:6.2f} 风险: {player_row['injury_risk']:.3f}")
#
#     # 12. 保存结果
#     df.to_excel('Pose2526total_pcascore.xlsx', index=False)

#批量处理代码
import pandas as pd
import numpy as np
import json
import glob

# 参数配置（与原代码相同）
POSITION_WEIGHTS = {
    "PG": {"FGA": 20.64, "G": 20.03, "PF": 19.72, "DRtg": 19.42, "ORtg": 18.96},
    "SG": {"PF": 21.86, "eFG": 21.55, "FGA": 20.60, "TOV": 19.81, "ORtg": 19.18},
    "SF": {"eFG": 20.90, "ORtg": 20.44, "FGA": 19.70, "FG": 19.26, "DRtg": 19.11},
    "PF": {"TOV": 21.17, "FGA": 20.86, "eFG": 19.48, "G": 19.02, "ORtg": 18.87},
    "C": {"eFG": 20.62, "FGA": 20.47, "PF": 20.00, "FG": 19.84, "G": 19.53}
}

INJURY_PARAMS = {
    'a0': -2.0, 'a1_youth': 0.03, 'a1_mid': 0.04,
    'a1_veteran': 0.06, 'a2': 0.6, 'a3': 0.2
}
RISK_DISCOUNT_FACTOR = 0.2


def calculate_injury_risk(player):
    age = player['Age']
    age_base = age - 27

    if age <= 27:
        age_effect = age_base * INJURY_PARAMS['a1_youth']
    elif age <= 31:
        age_effect = age_base * INJURY_PARAMS['a1_mid']
    else:
        age_effect = age_base * INJURY_PARAMS['a1_veteran']

    load_effect = np.log(player['MP'] / 677 + 1) * INJURY_PARAMS['a2']
    position_penalty = INJURY_PARAMS['a3'] if player['Pos'] in ['C', 'PF'] else 0

    z = INJURY_PARAMS['a0'] + age_effect + load_effect + position_penalty
    return 1 / (1 + np.exp(-z))


def calculate_pca_score(player, zscore_params):
    pos = player['Pos']
    weights = POSITION_WEIGHTS.get(pos, {})

    if pos not in zscore_params:
        return 0

    params = zscore_params[pos]
    total_score = 0

    for ind, weight in weights.items():
        if ind in params['means'] and ind in params['stds']:
            mean_val = params['means'][ind]
            std_val = params['stds'][ind]
            player_value = player.get(ind, mean_val)

            if std_val > 0:
                z_score = (player_value - mean_val) / std_val
            else:
                z_score = 0

            total_score += (1 / (1 + np.exp(-z_score))) * 20

    return total_score


# 批量处理
with open('global_zscore_params.json', 'r', encoding='utf-8') as f:
    zscore_params = json.load(f)




# 获取所有球队文件
files = glob.glob("2324/*players.xlsx")





for file in files:
    # 读取数据
    df = pd.read_excel(file)

    # 计算各项指标
    df['pca_score'] = df.apply(lambda row: calculate_pca_score(row, zscore_params), axis=1)
    total_mp = df['MP'].sum()
    df['time_contribution'] = (df['MP'] / total_mp) * len(df)
    df['pca_time_score'] = df['pca_score'] * df['time_contribution']
    df['injury_risk'] = df.apply(calculate_injury_risk, axis=1)
    df['risk_discount'] = 1 - (df['injury_risk'] * RISK_DISCOUNT_FACTOR)
    df['final_pca_score'] = df['pca_time_score'] * df['risk_discount']

    # 生成输出文件名
    team_name = file.replace('players.xlsx', '').replace('Players.xlsx', '')
    output_file = f"{team_name}_final_pca_scores.xlsx"

    # 保存结果
    df.to_excel(output_file, index=False)
    print(f"已处理: {file} -> {output_file}")
