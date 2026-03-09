# import pandas as pd
# import numpy as np
# from collections import Counter
#
# # 读取数据
# df = pd.read_excel("player_final_pca_score_byteam/WAS_final_pca_scores.xlsx")
#
# # 参数设置
# alpha = 0.02  # 可调参数
#
#
# # 计算协同系数
# def calculate_lambda(pos_list):
#     standard_positions = ['C', 'PG', 'SG', 'SF', 'PF']
#     pos_counter = Counter(pos_list)
#     current_dist = np.array([pos_counter.get(pos, 0) for pos in standard_positions])
#     # ideal_dist = np.array([3, 3, 3, 3, 3])
#     ideal_dist = np.array([2, 3, 3, 4, 3])
#
#     # 当前分布与理想分布的欧氏距离
#     current_distance = np.linalg.norm(current_dist - ideal_dist)
#
#     # 计算最差情况：所有球员集中在一个位置
#     worst_distances = []
#     for i in range(5):
#         worst_dist = np.zeros(5)
#         worst_dist[i] = len(pos_list)  # 使用实际球员数
#         distance = np.linalg.norm(worst_dist - ideal_dist)
#         worst_distances.append(distance)
#
#     worst_distance = max(worst_distances)
#
#     return max(0, 1 - current_distance / worst_distance)
#
#
#
#
# # 计算球员价值总和
# total_player_value = df['final_pca_score'].sum()
#
#
# # 获取位置列表
# pos_list = df['Pos'].tolist()
#
# # 计算协同系数
# lambda_syn = calculate_lambda(pos_list)
#
# # 计算球队价值
# team_value = total_player_value * (1 + alpha * lambda_syn)
#
# # 输出结果
# print(f"球员数量: {len(df)}")
# print(f"球员价值总和 ΣS_i: {total_player_value:.2f}")
# print(f"协同系数 λ_syn: {lambda_syn:.4f}")
# print(f"参数 α: {alpha}")
# print(f"球队价值 E_team: {team_value:.2f}")
# print(f"协同加成: {(alpha * lambda_syn * 100):.1f}%")
# print(f"\n位置分布统计:")
# pos_counter = Counter(pos_list)
# standard_positions = ['C', 'PG', 'SG', 'SF', 'PF']
# for pos in standard_positions:
#     count = pos_counter.get(pos, 0)
#     print(f"  {pos}: {count}人")

import pandas as pd
import numpy as np
from collections import Counter
import glob
import os

# 参数设置
alpha = 0.02  # 可调参数

# 球队缩写映射（用于输出格式）
# team_abbr_mapping = {
#     'ATL': 'ATL', 'BOS': 'BOS', 'BRK': 'BRK', 'CHO': 'CHO', 'CLE': 'CLE',
#     'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'IND': 'IND', 'LAC': 'LAC',
#     'LAL': 'LAL', 'MEM': 'MEM', 'MIA': 'MIA', 'MIL': 'MIL', 'MIN': 'MIN',
#     'NOP': 'NOP', 'NYK': 'NYK', 'OCK': 'OCK', 'ORL': 'ORL', 'PHI': 'PHI',
#     'PHX': 'PHX', 'POR': 'POR', 'SAC': 'SAC', 'SAS': 'SAS', 'TOR': 'TOR',
#     'UTA': 'UTA', 'WAS': 'WSD', 'GSW': 'GSW'
# }
team_abbr_mapping = {
    '2TM': '2TM', '3TM': '3TM', 'ATL': 'ATL', 'BOS': 'BOS', 'BRK': 'BRK',
    'CHI': 'CHI', 'CHO': 'CHO', 'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN',
    'DET': 'DET', 'GSW': 'GSW', 'HOU': 'HOU', 'IND': 'IND', 'LAC': 'LAC',
    'LAL': 'LAL', 'MEM': 'MEM', 'MIA': 'MIA', 'MIL': 'MIL', 'MIN': 'MIN',
    'NOP': 'NOP', 'NYK': 'NYK', 'OKC': 'OKC', 'ORL': 'ORL', 'PHI': 'PHI',
    'PHO': 'PHO', 'POR': 'POR', 'SAC': 'SAC', 'SAS': 'SAS', 'TOR': 'TOR',
    'UTA': 'UTA', 'WAS': 'WAS'
}


# 计算协同系数
def calculate_lambda(pos_list):
    standard_positions = ['C', 'PG', 'SG', 'SF', 'PF']
    pos_counter = Counter(pos_list)
    current_dist = np.array([pos_counter.get(pos, 0) for pos in standard_positions])
    ideal_dist = np.array([2, 3, 3, 4, 3])

    # 当前分布与理想分布的欧氏距离
    current_distance = np.linalg.norm(current_dist - ideal_dist)

    # 计算最差情况：所有球员集中在一个位置
    worst_distances = []
    for i in range(5):
        worst_dist = np.zeros(5)
        worst_dist[i] = len(pos_list)  # 使用实际球员数
        distance = np.linalg.norm(worst_dist - ideal_dist)
        worst_distances.append(distance)

    worst_distance = max(worst_distances)

    return max(0, 1 - current_distance / worst_distance)


# 处理单个球队文件的函数
def process_team_file(file_path):
    try:
        # 从文件名提取球队缩写
        file_name = os.path.basename(file_path)
        # 假设文件名格式为: WAS_final_pca_scores.xlsx
        team_abbr = file_name.split('_')[0].upper()

        # 读取数据
        df = pd.read_excel(file_path)

        # 按final_pca_score降序排序，取前10名
        df_sorted = df.sort_values('final_pca_score', ascending=False)
        df_top10 = df_sorted.head(10)

        # 计算前10名球员的价值总和
        total_player_value = df_top10['final_pca_score'].sum()

        # 获取全队球员的位置列表（用于计算协同系数）
        pos_list_all = df['Pos'].tolist()

        # 计算协同系数（基于全队所有球员的位置分布）
        lambda_syn = calculate_lambda(pos_list_all)

        # 计算球队价值（基于前10名球员的价值总和）
        team_value = total_player_value * (1 + alpha * lambda_syn)

        # 输出球队缩写映射
        output_abbr = team_abbr_mapping.get(team_abbr, team_abbr)

        return {
            'team': output_abbr,
            'value': team_value,
            'total_players': len(df),
            'top10_value': total_player_value,
            'lambda_syn': lambda_syn
        }

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return None


# 主程序
def main():
    # 获取所有球队文件
    # 假设所有文件都在当前目录的 player_final_pca_score_byteam 文件夹下
    # file_pattern = "player_final_pca_score_byteam/*_final_pca_scores.xlsx"
    file_pattern = "2324/*_final_pca_scores.xlsx"
    team_files = glob.glob(file_pattern)

    if not team_files:
        print(f"未找到匹配的文件: {file_pattern}")
        # 尝试其他可能的路径
        file_pattern = "*_final_pca_scores.xlsx"
        team_files = glob.glob(file_pattern)

        if not team_files:
            print("未找到球队数据文件，请检查文件路径")
            return

    print(f"找到 {len(team_files)} 个球队数据文件")

    # 处理所有球队
    team_results = []
    for file_path in team_files:
        result = process_team_file(file_path)
        if result:
            team_results.append(result)
            print(f"已处理: {result['team']} - 球队价值: {result['value']:.2f}")

    # 按球队价值降序排序
    team_results.sort(key=lambda x: x['value'], reverse=True)

    print("\n" + "=" * 50)
    print("球队价值排名（基于前10名球员价值 + 全队位置协同）")
    print("=" * 50)

    # 输出排序结果
    for i, team_data in enumerate(team_results, 1):
        print(f"{team_data['team']}: {team_data['value']:.2f}")

    print("\n" + "=" * 50)
    print("详细信息:")
    print("=" * 50)

    # 输出详细信息
    for team_data in team_results:
        print(f"\n{team_data['team']}:")
        print(f"  球队价值 E_team: {team_data['value']:.2f}")
        print(f"  前10名球员价值总和: {team_data['top10_value']:.2f}")
        print(f"  协同系数 λ_syn: {team_data['lambda_syn']:.4f}")
        print(f"  协同加成: {(alpha * team_data['lambda_syn'] * 100):.1f}%")
        print(f"  全队球员数: {team_data['total_players']}人")


# 执行主程序
if __name__ == "__main__":
    main()