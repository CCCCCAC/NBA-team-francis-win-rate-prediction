# import pandas as pd
# import numpy as np
# import seaborn as sns
# import matplotlib.pyplot as plt
# from scipy import stats
#
# # 1. 读取数据
# df = pd.read_excel('indicators.xlsx')
#
# # 2. 从league summary中提取MVP和总冠军信息
# mvp_champions_data = {
#     'SEASON': [2021, 2022, 2023, 2024],
#     'CHAMPION_TEAM': ['GSW', 'DEN', 'BOS', 'OKC'],
#     'MVP_TEAM': ['DEN', 'PHI', 'DEN', 'OKC']
# }
#
# # 3. 创建指标列
# # 3.1 总冠军指标 (Champion: 1, 其他: 0)
# df['IS_CHAMPION'] = 0
# for idx, row in enumerate(mvp_champions_data['SEASON']):
#     season = row
#     champion_team = mvp_champions_data['CHAMPION_TEAM'][idx]
#     df.loc[(df['SEASON'] == season) & (df['TEAM'] == champion_team), 'IS_CHAMPION'] = 1
#
# # 3.2 MVP指标 (MVP所在球队: 1, 其他: 0)
# df['IS_MVP_TEAM'] = 0
# for idx, row in enumerate(mvp_champions_data['SEASON']):
#     season = row
#     mvp_team = mvp_champions_data['MVP_TEAM'][idx]
#     df.loc[(df['SEASON'] == season) & (df['TEAM'] == mvp_team), 'IS_MVP_TEAM'] = 1
#
# # 4. 计算相关性矩阵
# # 只选择需要的列
# corr_columns = ['TEAM_VALUE', 'IS_CHAMPION', 'IS_MVP_TEAM', 'RWIN', 'PLAYER_EXPENSES']
# corr_df = df[corr_columns].copy()
#
# # 重命名列以在热力图中显示
# corr_df.columns = ['TEAM_VALUE', 'CHAMPION', 'MVP_TEAM', 'RWIN', 'PLAYER_EXP']
#
# # 计算相关性矩阵（皮尔逊相关系数）
# correlation_matrix = corr_df.corr(method='pearson')
#
# # 5. 创建只显示上三角的热力图（不包括对角线）
# mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
#
# plt.figure(figsize=(8, 6))
#
# # 创建热力图，添加数值
# heatmap = sns.heatmap(correlation_matrix,
#                       mask=mask,  # 应用遮罩，只显示上三角
#                       annot=True,
#                       fmt='.3f',
#                       cmap='coolwarm',
#                       center=0,
#                       square=True,
#                       linewidths=0.5,
#                       cbar_kws={'label': 'Correlation Coefficient'})
#
# plt.title('Correlation Heatmap: Team Value vs Performance Indicators',
#           fontsize=14, fontweight='bold', pad=20)
#
# # 调整布局
# plt.tight_layout()
# plt.show()
#
# # 6. 打印关键相关性结果
# print("CORRELATION WITH TEAM_VALUE:")
# print("=" * 50)
# for column in ['CHAMPION', 'MVP_TEAM', 'RWIN', 'PLAYER_EXP']:
#     if column != 'TEAM_VALUE':
#         corr_value = correlation_matrix.loc['TEAM_VALUE', column]
#         print(f"{column}: {corr_value:.4f}")
#
#         # 判断相关性强度
#         abs_corr = abs(corr_value)
#         if abs_corr > 0.7:
#             strength = "Strong"
#         elif abs_corr > 0.3:
#             strength = "Moderate"
#         elif abs_corr > 0.1:
#             strength = "Weak"
#         else:
#             strength = "Very weak/None"
#
#         # 判断方向
#         direction = "Positive" if corr_value > 0 else "Negative"
#
#         print(f"  → {strength} {direction} correlation")
#         print(
#             f"  → {direction} relationship: Higher TEAM_VALUE associated with {'higher' if corr_value > 0 else 'lower'} {column}")
# print("=" * 50)
#
# # 7. 保存相关性矩阵
# correlation_matrix.to_csv('team_value_correlation_matrix.csv')
# print("\nCorrelation matrix saved to 'team_value_correlation_matrix.csv'")


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# 1. 读取数据
df = pd.read_excel('indicators_with_attendance.xlsx')

# 2. 筛选2021-2024年的数据
df = df[df['SEASON'].between(2021, 2024)]

# 3. 选择连续变量指标（新增GDP）
analysis_columns = [
    'TEAM_VALUE',        # 球队价值
    'RWIN',              # 胜率相关指标
    'PLAYER_EXPENSES',   # 球员支出
    'FACEBOOK_FANS',     # 脸书粉丝数
    'ATTENDANCE',        # 上座人数
    'GDP'                # 新增：GDP
]

# 4. 计算相关性矩阵
corr_df = df[analysis_columns].copy()

# 重命名列名以便在热力图中显示
corr_df.columns = [
    'TEAM_VALUE',
    'RWIN',
    'PLAYER_EXP',
    'FB_FANS',
    'ATTENDANCE',
    'GDP'
]

# 计算皮尔逊相关性矩阵
correlation_matrix = corr_df.corr(method='pearson')

# 5. 创建遮罩 - 只显示上三角（不包括对角线）
mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=0)

plt.figure(figsize=(9, 7))
sns.heatmap(correlation_matrix,
           mask=mask,
           annot=True,
           fmt='.3f',
           cmap='coolwarm',
           center=0,
           square=True,
           linewidths=0.5,
           cbar_kws={'label': 'Correlation Coefficient'})

plt.title('Correlation Heatmap: Team Value vs Performance Indicators (2021-2024)',
          fontsize=14, fontweight='bold', pad=20)
plt.tight_layout()
plt.show()

# 6. 打印TEAM_VALUE与其他指标的相关性
print("CORRELATION WITH TEAM_VALUE:")
print("=" * 40)
for column in correlation_matrix.columns[1:]:
    corr_value = correlation_matrix.loc['TEAM_VALUE', column]
    print(f"{column}: {corr_value:.4f}")
print("=" * 40)