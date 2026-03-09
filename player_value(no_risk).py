# import pandas as pd
# import numpy as np
#
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
#
# def calculate_pca_score(player):
#     """计算PCA效率分（0-100分）"""
#     pos = player['Pos']
#     weights = POSITION_WEIGHTS.get(pos, {})
#     return sum(player[ind] * (weight / 100) for ind, weight in weights.items())
#
#
# def calculate_player_value(player):
#     """
#     计算球员综合价值
#
#     公式：
#     球员价值 = PCA评分 × [0.2 + 0.8 × sqrt(MP / 2870)]
#     2870 = 82场 × 35分钟/场（合理最大值）
#     """
#     # PCA效率分
#     pca_score = calculate_pca_score(player)
#
#     # MP因子（基于理论最大值）
#     REASONABLE_MAX_MP = 82 * 35  # 2870分钟
#     mp_ratio = min(1.0, player['MP'] / REASONABLE_MAX_MP)
#     mp_factor = 0+ 1 * (mp_ratio ** 0.5)
#
#     # 最终价值
#     return pca_score * mp_factor
#
#
# def calculate_all_players(df):
#     """批量计算所有球员价值"""
#     return df.apply(calculate_player_value, axis=1)
#
#
# def calculate_team_value(df, team_name):
#     """计算球队总价值"""
#     team_players = df[df['Team'] == team_name]
#     return team_players.apply(calculate_player_value, axis=1).sum()
#
#
# # ====== 使用示例 ======
# if __name__ == "__main__":
#     # 读取数据
#     df = pd.read_excel("Pose2526total.xlsx")
#
#     # 计算所有球员价值
#     df['player_value'] = calculate_all_players(df)
#
#     # 归一化到0-100分（可选）
#     df['player_value_norm'] = 100 * (df['player_value'] - df['player_value'].min()) / (
#                 df['player_value'].max() - df['player_value'].min())
#
#     # 按位置输出排名
#     for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
#         pos_df = df[df['Pos'] == pos].copy()
#         pos_df = pos_df.sort_values('player_value', ascending=False)
#         pos_df['pos_rank'] = range(1, len(pos_df) + 1)
#
#         print(f"\n{pos}位置前5名:")
#         print(pos_df[['Player', 'MP', 'player_value', 'player_value_norm', 'pos_rank']].head().to_string(index=False))
#
#     # 保存结果
#     df.to_excel('player_values.xlsx', index=False)
#     print(f"\n结果已保存到: player_values.xlsx")

import pandas as pd
import numpy as np

# 位置权重（百分制）
POSITION_WEIGHTS = {
    "PG": {"FGA": 20.64, "G": 20.03, "PF": 19.72, "DRtg": 19.42, "ORtg": 18.96},
    "SG": {"PF": 21.86, "eFG": 21.55, "FGA": 20.60, "TOV": 19.81, "ORtg": 19.18},
    "SF": {"eFG": 20.90, "ORtg": 20.44, "FGA": 19.70, "FG": 19.26, "DRtg": 19.11},
    "PF": {"TOV": 21.17, "FGA": 20.86, "eFG": 19.48, "G": 19.02, "ORtg": 18.87},
    "C": {"eFG": 20.62, "FGA": 20.47, "PF": 20.00, "FG": 19.84, "G": 19.53}
}

# MP-RK回归方程系数
MP_RK_COEF = {
    'intercept': 1485.9,
    'slope': -3.24
}


def calculate_predicted_mp(rank):
    """
    根据排名计算预测的MP
    回归方程: MP = 1485.9 + -3.24 × Rank
    """
    return MP_RK_COEF['intercept'] + MP_RK_COEF['slope'] * rank


def calculate_normalized_mp(player_mp, player_rank):
    """
    计算归一化的MP，基于预测MP
    """
    # 计算预测MP
    predicted_mp = calculate_predicted_mp(player_rank)

    # 使用预测MP作为基准进行归一化
    # 如果实际MP高于预测MP，给予适当奖励；如果低于，给予适当惩罚
    # 使用1 + ln(实际MP/预测MP)作为调整因子
    if predicted_mp > 0:
        ratio = player_mp / predicted_mp
        # 使用对数调整，避免极端值影响过大
        normalized_factor = 1 + np.log(ratio) if ratio > 0 else 0.5
        # 限制调整因子在合理范围内
        normalized_factor = max(0.5, min(2.0, normalized_factor))
        return predicted_mp * normalized_factor
    return player_mp


def calculate_pca_score(player):
    """计算PCA效率分（0-100分）"""
    pos = player['Pos']
    weights = POSITION_WEIGHTS.get(pos, {})
    return sum(player[ind] * (weight / 100) for ind, weight in weights.items())


def calculate_player_value(player):
    """
    计算球员综合价值（使用归一化MP）

    公式：
    球员价值 = PCA评分 × [0.2 + 0.8 × sqrt(归一化MP / 2870)]
    2870 = 82场 × 35分钟/场（合理最大值）
    """
    # PCA效率分
    pca_score = calculate_pca_score(player)

    # 获取球员排名（假设数据中有'Rk'列）
    if 'Rk' not in player.index:
        raise ValueError("数据中缺少'Rk'列，无法进行MP归一化")

    # 计算归一化MP
    normalized_mp = calculate_normalized_mp(player['MP'], player['Rk'])

    # MP因子（基于理论最大值）
    REASONABLE_MAX_MP = 82 * 35  # 2870分钟
    mp_ratio = min(1.0, normalized_mp / REASONABLE_MAX_MP)
    mp_factor = 0.2 + 0.8 * (mp_ratio ** 0.5)  # 修正了公式中的错误

    # 最终价值
    return pca_score * mp_factor


def calculate_all_players(df):
    """批量计算所有球员价值（使用归一化MP）"""
    # 确保数据中有Rk列
    if 'Rk' not in df.columns:
        print("警告：数据中没有'Rk'列，将使用原始MP计算")
        # 如果没有Rk列，回退到使用原始MP
        df['normalized_mp'] = df['MP']

        # 创建一个临时的calculate_player_value_simple函数
        def calculate_player_value_simple(player):
            pca_score = calculate_pca_score(player)
            mp_ratio = min(1.0, player['MP'] / (82 * 35))
            mp_factor = 0.2 + 0.8 * (mp_ratio ** 0.5)
            return pca_score * mp_factor

        return df.apply(calculate_player_value_simple, axis=1)

    # 计算所有球员的归一化MP
    df['predicted_mp'] = df['Rk'].apply(calculate_predicted_mp)
    df['normalized_mp'] = df.apply(
        lambda row: calculate_normalized_mp(row['MP'], row['Rk']),
        axis=1
    )

    return df.apply(calculate_player_value, axis=1)


def calculate_team_value(df, team_name):
    """计算球队总价值（使用归一化MP）"""
    team_players = df[df['Team'] == team_name]
    return team_players.apply(calculate_player_value, axis=1).sum()


# ====== 使用示例 ======
if __name__ == "__main__":
    # 读取数据
    # df = pd.read_excel("Pose2526total.xlsx")
    df = pd.read_excel("players_by_team/GSWplayers.xlsx")

    # 确保Rk列存在
    if 'Rk' not in df.columns:
        print("警告：数据中没有'Rk'列，将使用原始MP计算")
        # 添加默认排名（按MP降序）
        df['Rk'] = range(1, len(df) + 1)

    # 计算所有球员价值（使用归一化MP）
    df['player_value'] = calculate_all_players(df)

    # 计算基于预测MP的球员价值（用于对比）
    df['predicted_mp'] = df['Rk'].apply(calculate_predicted_mp)
    df['mp_adjustment'] = df['normalized_mp'] / df['MP'].clip(lower=1)

    # # 归一化到0-100分（可选）
    # if df['player_value'].max() > df['player_value'].min():
    #     df['player_value_norm'] = 100 * (df['player_value'] - df['player_value'].min()) / (
    #             df['player_value'].max() - df['player_value'].min())
    # else:
    #     df['player_value_norm'] = 50  # 如果所有值相等，设为中间值
    #
    # # 按位置输出排名
    # for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
    #     pos_df = df[df['Pos'] == pos].copy()
    #     if len(pos_df) > 0:
    #         pos_df = pos_df.sort_values('player_value', ascending=False)
    #         pos_df['pos_rank'] = range(1, len(pos_df) + 1)
    #
    #         print(f"\n{pos}位置前5名:")
    #         print(pos_df[['Player', 'Rk', 'MP', 'predicted_mp', 'normalized_mp',
    #                       'player_value', 'player_value_norm', 'pos_rank']].head().to_string(index=False))
    #
    # # 输出MP调整统计信息
    # print("\nMP调整统计:")
    # print(f"平均实际MP: {df['MP'].mean():.1f}")
    # print(f"平均预测MP: {df['predicted_mp'].mean():.1f}")
    # print(f"平均归一化MP: {df['normalized_mp'].mean():.1f}")
    # print(f"平均调整系数: {df['mp_adjustment'].mean():.3f}")

    # 保存结果
    # df.to_excel('player_values_normalized.xlsx', index=False)
    # print(f"\n结果已保存到: player_values_normalized.xlsx")
    df.to_excel('players_by_team/GSW_player_values.xlsx', index=False)
    print(f"\n结果已保存到: GSW_player_values.xlsx")