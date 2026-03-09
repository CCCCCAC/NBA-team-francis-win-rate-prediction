import pandas as pd
import numpy as np
import json

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

# 伤病风险函数参数（使用你调整好的参数）
INJURY_PARAMS = {
    'a0': -2.0,  # 截距项
    'a1_youth': 0.03,  # 青年组年龄系数
    'a1_mid':0.04,
    'a1_veteran': 0.06,  # 老将组年龄系数 0.09
    'a2': 0.6,  # 负荷系数
    'a3': 0.2  # 位置惩罚系数
}

# 风险折扣系数
RISK_DISCOUNT_FACTOR = 0.2


def calculate_injury_risk(player):
    """
    计算球员伤病风险
    公式：risk = 1 / (1 + exp(-z))
    z = a0 + a1×AgeEffect + a2×LoadEffect + a3×PositionPenalty
    """
    # 1. 年龄因子（分段处理）
    age = player['Age']
    age_base = age - 27  # 以27岁为基准

    if age <= 27:
        age_effect = age_base * INJURY_PARAMS['a1_youth']
    elif age <=31:
        age_effect = age_base * INJURY_PARAMS['a1_mid']
    else:
        age_effect = age_base * INJURY_PARAMS['a1_veteran']

    # 2. 负荷因子（对数归一化）
    mp = player['MP']
    load_effect = np.log(mp / 677 + 1) * INJURY_PARAMS['a2']

    # 3. 位置因子
    position_penalty = INJURY_PARAMS['a3'] if player['Pos'] in ['C', 'PF'] else 0

    # 4. 计算z值
    z = (INJURY_PARAMS['a0'] + age_effect + load_effect + position_penalty)

    # 5. 计算风险
    risk = 1 / (1 + np.exp(-z))

    return risk


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
    if predicted_mp > 0:
        ratio = player_mp / predicted_mp
        # 使用对数调整，避免极端值影响过大
        normalized_factor = 1 + np.log(ratio) if ratio > 0 else 0.5
        # 限制调整因子在合理范围内
        normalized_factor = max(0.5, min(2.0, normalized_factor))
        return predicted_mp * normalized_factor
    return player_mp


def calculate_pca_score(player, zscore_params):
    """
    计算PCA效率分（使用全联盟Z-score参数标准化，每个指标20分，总分100分）
    """
    pos = player['Pos']
    weights = POSITION_WEIGHTS.get(pos, {})

    if pos not in zscore_params:
        # 如果没有该位置的参数，使用简单计算
        return sum(player[ind] * (weight / 100) for ind, weight in weights.items())

    params = zscore_params[pos]
    total_score = 0

    for ind, weight in weights.items():
        if ind in params['means'] and ind in params['stds']:
            # 获取该指标在全联盟的均值和标准差
            mean_val = params['means'][ind]
            std_val = params['stds'][ind]

            # Z-score标准化
            if std_val > 0:
                z_score = (player[ind] - mean_val) / std_val
            else:
                z_score = 0

            # 使用sigmoid将Z-score转换到0-1范围
            normalized_score = 1 / (1 + np.exp(-z_score))

            # 每个指标贡献20分
            total_score += normalized_score * 20

    return total_score



def calculate_player_value_with_risk(player, zscore_params):
    """
    计算球员综合价值（使用归一化MP和风险折扣）
    """
    # PCA效率分（使用Z-score参数）
    pca_score = calculate_pca_score(player, zscore_params)

    # 获取球员排名（假设数据中有'Rk'列）
    if 'Rk' not in player.index:
        raise ValueError("数据中缺少'Rk'列，无法进行MP归一化")

    # 计算归一化MP
    normalized_mp = calculate_normalized_mp(player['MP'], player['Rk'])

    # MP因子（基于理论最大值）
    REASONABLE_MAX_MP = 82 * 35  # 2870分钟
    mp_ratio = min(1.0, normalized_mp / REASONABLE_MAX_MP)
    # mp_factor = 0.2 + 0.8 * (mp_ratio ** 0.5)
    mp_factor = 0.2 + 0.8 * (mp_ratio ** 0.5)

    # 计算伤病风险
    injury_risk = calculate_injury_risk(player)

    # 计算风险折扣
    risk_discount = 1 - (injury_risk * RISK_DISCOUNT_FACTOR)

    # 最终价值（应用风险折扣）
    player_value_without_risk = pca_score * mp_factor
    player_value_with_risk = player_value_without_risk * risk_discount

    return player_value_without_risk, injury_risk, risk_discount, player_value_with_risk


def calculate_all_players(df, zscore_params):
    """批量计算所有球员价值（使用归一化MP和风险折扣）"""
    results = []

    for idx, row in df.iterrows():
        try:
            player_value_without_risk, injury_risk, risk_discount, player_value_with_risk = calculate_player_value_with_risk(
                row, zscore_params)
            results.append({
                'player_value': player_value_with_risk,  # 这个将作为最终价值
                'player_value_without_risk': player_value_without_risk,
                'injury_risk': injury_risk,
                'risk_discount': risk_discount,
            })
        except Exception as e:
            print(f"计算球员 {row.get('Player', idx)} 时出错: {e}")
            results.append({
                'player_value': np.nan,
                'player_value_without_risk': np.nan,
                'injury_risk': np.nan,
                'risk_discount': np.nan,
                'player_contribution': np.nan
            })

    return pd.DataFrame(results)


# ====== 使用示例 ======
if __name__ == "__main__":
    # 1. 加载Z-score参数
    with open('global_zscore_params.json', 'r', encoding='utf-8') as f:
        zscore_params = json.load(f)

    # 2. 读取数据
    df = pd.read_excel("players_by_team/ORLplayers.xlsx")

    # 确保Rk列存在
    if 'Rk' not in df.columns:
        print("警告：数据中没有'Rk'列，将使用原始MP计算")
        # 添加默认排名（按MP降序）
        df['Rk'] = range(1, len(df) + 1)

    # 计算所有球员价值（使用归一化MP和风险折扣）
    results_df = calculate_all_players(df, zscore_params)

    # 合并结果到原数据框
    df = pd.concat([df, results_df], axis=1)

    # 计算基于预测MP的球员价值（用于对比）
    df['predicted_mp'] = df['Rk'].apply(calculate_predicted_mp)
    df['normalized_mp'] = df.apply(
        lambda row: calculate_normalized_mp(row['MP'], row['Rk']),
        axis=1
    )

    # 计算MP调整系数
    df['mp_adjustment'] = df['normalized_mp'] / df['MP'].clip(lower=1)

    # # 按位置输出前5名球员
    # positions = ['PG', 'SG', 'SF', 'PF', 'C']

    # for pos in positions:
    #     print(f"\n{'=' * 80}")
    #     print(f"{pos}位置评分前5名球员（包含风险折扣）")
    #     print(f"{'=' * 80}")
    #
    #     # 筛选该位置球员并按最终评分排序
    #     pos_df = df[df['Pos'] == pos].copy()
    #
    #     if len(pos_df) == 0:
    #         print(f"没有找到{pos}位置的球员")
    #         continue
    #
    #     pos_df = pos_df.sort_values('player_value', ascending=False).head(5).reset_index(drop=True)
    #
    #     for i, row in pos_df.iterrows():
    #         print(f"{i + 1:2d}. {row['Player']:<25} 年龄: {row['Age']:>2}岁  MP: {row['MP']:>5}分钟")
    #         print(f"    原始评分: {row['player_value_without_risk']:7.2f}  伤病风险: {row['injury_risk']:.3f}")
    #         print(f"    风险折扣: {row['risk_discount']:.3f}  最终评分: {row['player_value']:7.2f}")
    #         print(f"    排名(Rk): {row['Rk']:>3}  归一化MP: {row['normalized_mp']:>7.1f}")
    #         print("-" * 80)
    print(f"\n{'=' * 80}")
    print("整体统计信息")
    print(f"{'=' * 80}")

    print("\nMP调整统计:")
    print(f"平均实际MP: {df['MP'].mean():.1f}")
    print(f"平均预测MP: {df['predicted_mp'].mean():.1f}")
    print(f"平均归一化MP: {df['normalized_mp'].mean():.1f}")
    print(f"平均调整系数: {df['mp_adjustment'].mean():.3f}")

    print("\n风险折扣统计:")
    print(f"平均伤病风险: {df['injury_risk'].mean():.3f}")
    print(f"平均风险折扣: {df['risk_discount'].mean():.3f}")
    print(f"最高风险折扣: {df['risk_discount'].max():.3f}")
    print(f"最低风险折扣: {df['risk_discount'].min():.3f}")

    print(f"\n评分统计:")
    print(f"平均原始评分: {df['player_value_without_risk'].mean():.2f}")
    print(f"平均最终评分: {df['player_value'].mean():.2f}")
    print(
        f"风险影响幅度: {((df['player_value_without_risk'].mean() - df['player_value'].mean()) / df['player_value_without_risk'].mean() * 100):.1f}%")

    # 保存结果
    df.to_excel('players_by_team/ORL_player_values.xlsx', index=False)
    print(f"\n结果已保存到: players_by_team/ORL_player_values.xlsx")