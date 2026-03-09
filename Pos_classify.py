# # Classification
# import pandas as pd
#
# # 读取原始数据
# file_path = "Pose2526total.xlsx"  # 修改为你的文件路径
# df = pd.read_excel(file_path)
#
# # 确保数据按Rk列排序（保持原有排名顺序）
# df = df.sort_values('Rk').reset_index(drop=True)
#
# # 获取所有不同的Pos值
# pos_values = df['Pos'].unique()
#
# print("开始分类处理...")
# print(f"原始数据行数: {len(df)}")
# print(f"发现 {len(pos_values)} 种不同的Pos: {pos_values}")
#
# # 创建每个Pos的分类文件
# for pos in pos_values:
#     # 筛选该Pos的所有行
#     filtered_df = df[df['Pos'] == pos].copy()
#
#     # 确保保持原有顺序（已经按Rk排序）
#     filtered_df = filtered_df.sort_values('Rk')
#
#     # 生成文件名
#     filename = f"Pos_{pos}2526.xlsx"
#
#     # 保存到Excel，保持所有原有列名和顺序
#     filtered_df.to_excel(filename, index=False)
#
#     print(f"\n✓ 已保存: {filename}")
#     print(f"  包含 {len(filtered_df)} 条记录")
#     print(f"  列数: {len(filtered_df.columns)}")
#     print(f"  数据形状: {filtered_df.shape}")
#
# print("\n✅ 所有分类文件已生成完成！")
#
# # 验证数据完整性
# total_rows = 0
# for pos in pos_values:
#     temp_df = pd.read_excel(f"Pos_{pos}2526.xlsx")
#     total_rows += len(temp_df)
#     print(f"{pos}: {len(temp_df)} 行")
#
# print(f"\n数据完整性检查:")
# print(f"原始数据总行数: {len(df)}")
# print(f"分类后总行数: {total_rows}")
# print(f"数据是否一致: {'是' if len(df) == total_rows else '否'}")




#data diagnose rk-指标分布散点图
import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
pos_files = ['Pos_PG2526.xlsx', 'Pos_SG2526.xlsx', 'Pos_SF2526.xlsx', 'Pos_PF2526.xlsx', 'Pos_C2526.xlsx']
colors = ['red', 'blue', 'green', 'orange', 'purple']

# 创建图表 - 每个指标一个图表
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

# 选择4个关键指标
metrics = ['MP', 'G', 'FG', 'FGA']

for i, metric in enumerate(metrics):
    ax = axes[i]

    for j, file in enumerate(pos_files):
        df = pd.read_excel(file)
        ax.scatter(df[metric], df['Rk'],
                   alpha=0.7, s=20,
                   color=colors[j],
                   label=file.replace('Pos_', '').replace('.xlsx', ''))

    ax.set_xlabel(metric, fontsize=12)
    ax.set_ylabel('Rk', fontsize=12)
    ax.set_title(f'{metric} vs Rk', fontsize=14)
    ax.invert_yaxis()  # 排名越高（数值越小）越靠上
    ax.legend(fontsize=9)

plt.tight_layout()
plt.show()



# #密度图
# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
#
# # 读取数据
# pos_files = ['Pos_PG2526.xlsx', 'Pos_SG2526.xlsx', 'Pos_SF2526.xlsx', 'Pos_PF2526.xlsx', 'Pos_C2526.xlsx']
# pos_labels = ['PG', 'SG', 'SF', 'PF', 'C']
# colors = ['red', 'blue', 'green', 'orange', 'purple']
#
# # 选择关键指标 - 调整为实际存在的列名
# metrics = ['PF', 'PTS', 'ORtg', 'DRtg']
#
# # 创建图表
# fig, axes = plt.subplots(2, 2, figsize=(14, 10))
# axes = axes.flatten()
#
# for i, metric in enumerate(metrics):
#     ax = axes[i]
#
#     # 收集所有位置的数据用于统一x轴范围
#     all_data = []
#
#     for j, (file, label) in enumerate(zip(pos_files, pos_labels)):
#         try:
#             df = pd.read_excel(file)
#
#             # 确保该列存在且为数值型
#             if metric in df.columns and pd.api.types.is_numeric_dtype(df[metric]):
#                 data = df[metric].dropna().values
#
#                 if len(data) > 0:
#                     # 绘制分布曲线（核密度估计）
#                     from scipy.stats import gaussian_kde
#
#                     # 创建平滑的分布曲线
#                     kde = gaussian_kde(data)
#                     x_range = np.linspace(data.min(), data.max(), 200)
#                     y_values = kde(x_range)
#
#                     # 标准化y值以便更好显示
#                     y_values_normalized = y_values / y_values.max()
#
#                     # 绘制曲线
#                     ax.plot(x_range, y_values_normalized,
#                             color=colors[j],
#                             linewidth=2.5,
#                             label=f'{label} ({len(data)}people)',
#                             alpha=0.8)
#
#                     # 填充曲线下方区域
#                     ax.fill_between(x_range, 0, y_values_normalized,
#                                     color=colors[j], alpha=0.2)
#
#                     all_data.extend(data)
#                 else:
#                     print(f"警告: {label} 的 {metric} 数据为空")
#             else:
#                 print(f"警告: {label} 中不存在 {metric} 列或不是数值型")
#
#         except Exception as e:
#             print(f"读取文件 {file} 时出错: {e}")
#             continue
#
#     # 设置图表属性
#     ax.set_xlabel(metric, fontsize=12)
#     ax.set_ylabel('density', fontsize=12)
#
#     # 根据指标含义设置标题 - 修复这里：使用字典而不是集合
#     metric_names = {
#         'FG.1': 'Field Goal % Distribution',
#         '3PP': '3-Point % Distribution',
#         '2PP': '2-Point % Distribution',
#         'FT.1': 'Free Throw % Distribution'
#     }
#     # 使用字典的get方法，如果metric不在字典中则使用默认值
#     title = metric_names.get(metric, f'{metric} Distribution')
#     ax.set_title(title, fontsize=14, fontweight='bold')
#
#     # 设置图例
#     ax.legend(fontsize=9, loc='upper left')
#
#     # 添加网格
#     ax.grid(True, alpha=0.3, linestyle='--')
#
#     # 如果所有位置的数据都有效，设置统一的x轴范围
#     if all_data:
#         min_val = min(all_data)
#         max_val = max(all_data)
#         buffer = (max_val - min_val) * 0.1
#         ax.set_xlim(min_val - buffer, max_val + buffer)
#
#     # 添加均值线
#     for j, (file, label) in enumerate(zip(pos_files, pos_labels)):
#         try:
#             df = pd.read_excel(file)
#             if metric in df.columns:
#                 mean_val = df[metric].mean()
#                 ax.axvline(x=mean_val, color=colors[j], linestyle=':',
#                            alpha=0.5, linewidth=1.5)
#
#                 # 标注均值
#                 ax.text(mean_val, 0.95 - j * 0.05, f'{mean_val:.3f}',
#                         color=colors[j], fontsize=8,
#                         transform=ax.get_xaxis_transform(),
#                         ha='center', va='bottom')
#         except:
#             continue
#
# plt.tight_layout()
# plt.suptitle('Position Difference Analysis', fontsize=16, fontweight='bold', y=1.02)
# plt.show()
#
# # 额外的统计摘要
# print("\n" + "=" * 60)
# print("各位置关键指标统计摘要")
# print("=" * 60)
#
# for file, label in zip(pos_files, pos_labels):
#     try:
#         df = pd.read_excel(file)
#         print(f"\n{label}位置 ({len(df)}人):")
#
#         for metric in metrics:
#             if metric in df.columns:
#                 data = df[metric].dropna()
#                 if len(data) > 0:
#                     print(f"  {metric}: {data.mean():.3f} ± {data.std():.3f} "
#                           f"(range: {data.min():.3f} - {data.max():.3f})")
#     except:
#         print(f"\n{label}: 读取文件失败")
#         continue