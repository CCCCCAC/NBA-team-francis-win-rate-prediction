import math

# 2526球队价值数据
# team_values = {
#     'SAS': 1059.77, 'NYK': 1058.23, 'DET': 1047.37, 'CHI': 1046.47, 'MIL': 1045.99,
#     'CHO': 1026.16, 'ORL': 1023.17, 'UTA': 1021.50, 'HOU': 1019.59, 'MIN': 1012.17,
#     'PHX': 1008.79, 'LAC': 999.83, 'PHI': 999.30, 'LAL': 979.31, 'TOR': 964.88,
#     'DEN': 963.96, 'WSD': 963.80, 'NOP': 962.61, 'SAC': 960.57, 'ATL': 957.60,
#     'BOS': 929.88, 'GSW': 918.85, 'POR': 911.94, 'IND': 911.75, 'CLE': 909.66,
#     'MEM': 901.23, 'MIA': 890.65, 'BRK': 873.18, 'OCK': 856.99, 'DAL': 854.57
# }
# #2425
# team_values = {
#     '2TM': 1837.78, 'NYK': 1615.39, 'PHI': 1613.14, 'MIL': 1572.06, 'SAC': 1556.74,
#     'LAC': 1542.56, 'CLE': 1445.58, 'LAL': 1438.96, 'WAS': 1434.26, 'DAL': 1427.51,
#     'CHI': 1423.33, 'CHO': 1409.66, 'NOP': 1400.39, 'IND': 1391.61, 'MEM': 1389.10,
#     'TOR': 1383.14, 'BOS': 1379.64, 'PHO': 1376.65, 'SAS': 1363.41, 'DET': 1353.94,
#     'ATL': 1353.41, 'MIA': 1343.40, 'POR': 1328.28, 'MIN': 1310.73, 'HOU': 1299.09,
#     'DEN': 1294.75, 'GSW': 1285.31, 'UTA': 1271.22, 'OKC': 1271.14, 'BRK': 1246.23,
#     'ORL': 1049.71, '3TM': 335.90
# }
#2324
team_values = {
    'DET': 1779.45, '2TM': 1729.58, 'MEM': 1649.05, 'NYK': 1581.53, 'OKC': 1564.49,
    'TOR': 1529.52, 'PHI': 1503.86, 'LAC': 1370.55, 'PHO': 1482.29, 'BOS': 1467.40,
    'LAL': 1452.57, 'SAS': 1437.84, 'DAL': 1429.29, 'SAC': 1409.23, 'BRK': 1394.33,
    'ATL': 1390.11, 'CHO': 1387.30, 'POR': 1386.20, 'WAS': 1383.04, 'MIA': 1375.72,
    'MIN': 1353.86, 'UTA': 1351.48, 'IND': 1332.45, 'CLE': 1308.95, 'MIL': 1302.96,
    'DEN': 1291.01, 'CHI': 1271.10, 'GSW': 1262.66, 'NOP': 1246.32, 'HOU': 1243.52,
    'ORL': 1154.59, '3TM': 576.51
}
#LAC：1487.70--->1370.55


# # 2223
# team_values = {
#     '2TM': 1801.12, 'POR': 1575.55, 'LAL': 1525.46, 'WAS': 1453.24, 'IND': 1435.98,
#     'MIA': 1428.64, 'UTA': 1420.22, 'DAL': 1416.21, 'MIL': 1410.16, 'ATL': 1398.73,
#     'SAC': 1376.66, 'SAS': 1362.41, 'BRK': 1358.83, 'TOR': 1351.34, 'BOS': 1338.48,
#     'LAC': 1332.13, 'ORL': 1316.26, 'MEM': 1310.33, 'MIN': 1295.00, 'PHI': 1290.39,
#     'GSW': 1287.23, 'PHO': 1285.83, 'HOU': 1279.62, 'DET': 1279.57, 'CHI': 1267.02,
#     'OKC': 1261.57, 'DEN': 1259.20, 'CLE': 1253.73, 'NYK': 1189.57, 'CHO': 1185.83,
#     'NOP': 1133.09
# }

# # 2122
# team_values = {
#     '2TM': 2122.66, 'MIL': 1729.96, 'WAS': 1662.04, 'LAL': 1651.92, 'DET': 1643.15,
#     'UTA': 1626.34, 'DAL': 1620.39, 'ATL': 1615.23, 'MIA': 1597.67, 'CLE': 1573.56,
#     'BOS': 1560.82, 'TOR': 1514.32, 'PHO': 1494.26, 'SAC': 1484.59, 'ORL': 1471.40,
#     'LAC': 1465.95, 'SAS': 1437.35, 'PHI': 1410.14, 'CHI': 1408.41, 'OKC': 1403.48,
#     'DEN': 1379.49, 'NOP': 1346.79, 'POR': 1333.53, 'NYK': 1317.92, 'BRK': 1289.42,
#     'HOU': 1288.54, 'MEM': 1263.36, 'CHO': 1261.12, 'IND': 1249.50, 'MIN': 1237.66,
#     'GSW': 1119.83, '3TM': 872.37, '4TM': 86.68
# }


# 计算联盟平均价值
league_avg = sum(team_values.values()) / len(team_values)
print(f"联盟平均球队价值 (S_league): {league_avg:.2f}")
print("="*50)

# Elo公式参数
# D值通常设为400（国际象棋标准），但可以根据需要调整
D = 400

# 计算每个队伍的胜率
team_win_rates = {}
for team, value in team_values.items():
    # 使用Elo公式计算胜率
    win_rate = 1 / (1 + 10 ** (-(value - league_avg) / D))
    team_win_rates[team] = win_rate

# 按胜率从高到低排序
sorted_teams = sorted(team_win_rates.items(), key=lambda x: x[1], reverse=True)

# 输出结果
print("球队胜率排名 (基于Elo公式):")
print("="*50)
for i, (team, win_rate) in enumerate(sorted_teams, 1):
    print(f"{i:2d}. {team}: 胜率 = {win_rate:.3f} ({win_rate*100:.1f}%)")
    print(f"    球队价值: {team_values[team]:.2f}")

print("\n" + "="*50)
print("详细统计数据:")
print("="*50)
print(f"最高胜率: {sorted_teams[0][1]:.3f} ({sorted_teams[0][0]})")
print(f"最低胜率: {sorted_teams[-1][1]:.3f} ({sorted_teams[-1][0]})")
print(f"平均胜率: {sum(team_win_rates.values())/len(team_win_rates):.3f}")

# 输出为可复制的格式
print("\n" + "="*50)
print("简洁格式 (球队: 胜率):")
print("="*50)
for team, win_rate in sorted_teams:
    print(f"{team}: {win_rate:.3f}")