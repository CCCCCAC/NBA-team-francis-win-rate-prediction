# # import pandas as pd
# #
# #
# # def add_GA_to_left(cleaned_file, source_file, output_file, match_columns):
# #     """
# #     专门用于添加GA列到左侧的函数
# #     """
# #     # 读取数据
# #     df_cleaned = pd.read_excel(cleaned_file)
# #     df_source = pd.read_excel(source_file)
# #
# #     print(f"清洗后文件行数: {len(df_cleaned)}")
# #     print(f"原始文件行数: {len(df_source)}")
# #     print(f"用于匹配的列: {match_columns}")
# #
# #     # 检查匹配列是否存在
# #     for col in match_columns:
# #         if col not in df_cleaned.columns:
# #             print(f"错误: 列 '{col}' 在清洗后文件中不存在")
# #             return None
# #         if col not in df_source.columns:
# #             print(f"错误: 列 '{col}' 在原始文件中不存在")
# #             return None
# #
# #     # 提取G列和匹配列
# #     ga_column = 'G'
# #     if ga_column not in df_source.columns:
# #         print(f"错误: 原始文件中没有 '{ga_column}' 列")
# #         print(f"原始文件中的列有: {list(df_source.columns)}")
# #         return None
# #
# #     # 合并数据
# #     merged_df = pd.merge(
# #         df_cleaned,
# #         df_source[match_columns + [ga_column]],
# #         on=match_columns,
# #         how='left'
# #     )
# #
# #     # 将GA列移动到最左侧
# #     cols = list(merged_df.columns)
# #     cols.remove(ga_column)
# #     cols = [ga_column] + cols
# #     merged_df = merged_df[cols]
# #
# #     # 保存结果
# #     merged_df.to_excel(output_file, index=False)
# #
# #     # 统计信息
# #     match_count = merged_df[ga_column].notna().sum()
# #     match_rate = match_count / len(merged_df)
# #
# #     print("\n" + "=" * 50)
# #     print("处理完成！")
# #     print(f"成功匹配: {match_count}/{len(merged_df)} 行")
# #     print(f"匹配率: {match_rate:.2%}")
# #     print(f"输出文件: {output_file}")
# #     print("=" * 50)
# #
# #     return merged_df
# #
# #
# # # ====== 实际调用 ======
# # if __name__ == "__main__":
# #     # 这里填写你的实际文件路径和匹配列
# #     cleaned_path = "PerFilledclean.xlsx"
# #     source_path = "Per100PossFilled.xlsx"
# #     output_path = "PerFilledclean.xlsx"
# #
# #     # 根据你的数据实际情况修改这里的匹配列
# #     # 重要：这些列必须在两个文件中都存在且数值一致
# #     match_cols = ['G', 'G']  # 修改为你实际的列名
# #
# #     # 执行
# #     result = add_GA_to_left(
# #         cleaned_file=cleaned_path,
# #         source_file=source_path,
# #         output_file=output_path,
# #         match_columns=match_cols
# #     )
# #
# #     if result is not None:
# #         # 显示前几行数据，确认GA列在左侧
# #         print("\n前几行数据预览:")
# #         print(result.head())
#
#
#
# import pandas as pd
#
# # 1. 先检查清洗后文件的列
# df_cleaned = pd.read_excel("PerFilledclean.xlsx")
# print("清洗后文件的列:")
# for i, col in enumerate(df_cleaned.columns):
#     print(f"第{i+1}列: {col}")
#
# # 2. 检查原始文件的列
# df_source = pd.read_excel("Per100PossFilled.xlsx")
# print("\n原始文件的列:")
# for i, col in enumerate(df_source.columns):
#     print(f"第{i+1}列: {col}")
#
# # 3. 检查重复列名
# def check_duplicates(columns, filename):
#     from collections import Counter
#     duplicates = [item for item, count in Counter(columns).items() if count > 1]
#     if duplicates:
#         print(f"\n⚠️ {filename} 中有重复列名: {duplicates}")
#     else:
#         print(f"\n✓ {filename} 列名都是唯一的")
#
# check_duplicates(df_cleaned.columns, "PerFilledclean.xlsx")
# check_duplicates(df_source.columns, "Per100PossFilled.xlsx")

import pandas as pd


def fill_G_column():
    # 读取文件
    df_cleaned = pd.read_excel("PerFilledclean.xlsx")
    df_source = pd.read_excel("Per100PossFilled.xlsx")

    print("处理前:")
    print(f"清洗后文件G列前5个值: {df_cleaned['G'].head().tolist()}")
    print(f"原始文件G列前5个值: {df_source['G'].head().tolist()}")

    # 使用Rk和Player匹配，填充G列
    # 创建匹配字典
    match_dict = {}
    for _, row in df_source.iterrows():
        key = (row['Rk'], row['Player'])
        match_dict[key] = row['G']

    # 填充G列
    df_cleaned['G'] = df_cleaned.apply(
        lambda row: match_dict.get((row['Rk'], row['Player']), row['G']),
        axis=1
    )

    print("\n处理后:")
    print(f"清洗后文件G列前5个值: {df_cleaned['G'].head().tolist()}")

    # 计算匹配成功率
    filled_count = df_cleaned['G'].notna().sum()
    total_count = len(df_cleaned)
    print(f"\n匹配结果:")
    print(f"成功填充: {filled_count}/{total_count} 行")
    print(f"填充率: {filled_count / total_count:.2%}")

    # 保存文件
    df_cleaned.to_excel("PerFilledclean_with_G.xlsx", index=False)
    print("\n文件已保存为: PerFilledclean_with_G.xlsx")

    return df_cleaned


# 运行
result = fill_G_column()