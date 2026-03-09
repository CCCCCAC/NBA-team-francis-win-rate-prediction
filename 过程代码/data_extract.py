# import pandas as pd
#
# # 读取文件
# file_path = "Per100Poss2526.xls"  # 修改为你的文件路径
# df = pd.read_excel(file_path)  # 如果报错，尝试添加 engine='openpyxl' 或 engine='xlrd'
#
# # 查看基本信息
# print("数据形状（行, 列）:", df.shape)
# print("\n列名列表:")
# for i, col in enumerate(df.columns, 1):
#     print(f"{i}. {col}")
#
# print("\n前几行数据:")
# print(df.head())
#
# print("\n数据类型:")
# print(df.dtypes)

import pandas as pd

# # 读取Excel文件（修改为你的文件路径）
# file_path = 'Per100Poss2526.xls'  # 请将your_file.xls替换为你的实际文件名
# df = pd.read_excel(file_path)

# print("=== 文件基本信息 ===")
# print(f"数据集形状: {df.shape}")  # (行数, 列数)
# print(f"总共有 {df.size} 个数据点")
#
# print("\n=== 缺失值统计 ===")
# # 每列的缺失值数量
# missing_per_column = df.isnull().sum()
# print("各列的缺失值数量:")
# print(missing_per_column)
#
# # 有缺失值的列
# columns_with_missing = missing_per_column[missing_per_column > 0]
# if len(columns_with_missing) > 0:
#     print(f"\n有缺失值的列 ({len(columns_with_missing)}个):")
#     for col, count in columns_with_missing.items():
#         percentage = (count / len(df)) * 100
#         print(f"  {col}: {count}个缺失值 ({percentage:.2f}%)")
# else:
#     print("没有发现缺失值！")
#
# print("\n=== 缺失值所在位置 ===")
# # 找到缺失值的具体位置
# missing_positions = df.isnull()
#
# # 显示每个缺失值的行列位置
# missing_cells = []
# for col in df.columns:
#     rows_with_missing = df[df[col].isnull()].index.tolist()
#     if rows_with_missing:
#         for row in rows_with_missing:
#             missing_cells.append((row, col, df.loc[row, col]))
#
# if missing_cells:
#     print("缺失值具体位置（行号从0开始）:")
#     for row_idx, col_name, value in missing_cells:
#         # 显示Excel实际行号（从1开始）
#         excel_row = row_idx + 1
#         print(f"  第{excel_row}行, 列'{col_name}'")
# else:
#     print("没有发现缺失值！")

# # 使用value_counts找出有重复的值
# rank_counts = df['Rk'].value_counts()
# repeated_ranks = rank_counts[rank_counts > 1].index.tolist()
# repeated_ranks.sort()
# import pandas as pd
#
# # 读取.xls文件（必须安装xlrd）
# df = pd.read_excel('Per100Poss2526.xls', engine='xlrd')
#
# # 填充缺失值为0
# df = df.fillna(0)
#
# # 保存为新文件（建议保存为xlsx格式）
# df.to_excel('Per100PossFilled.xlsx', index=False)
# print("✅ 完成！缺失值已填充为0")
# # print(f"重复的排名值: {repeated_ranks}")


#
import pandas as pd

# 读取 Excel 文件
df = pd.read_excel('PerFilledclean.xlsx')

# 定义要保留的列
columns_to_keep = ['Rk','Player', 'Age', 'Pos','G', 'MP','FG', 'FGA', 'eFG','TOV', 'PF','ORtg', 'DRtg']

# 只保留这些列
df_filtered = df[columns_to_keep]

# 保存到新文件（可选）
df_filtered.to_excel('Pose2526total.xlsx', index=False)

# 或者直接覆盖原文件（如果你想要）
# df_filtered.to_excel('Per100PossFilled.xlsx', index=False)

print("列已筛选完成，只保留了：", columns_to_keep)