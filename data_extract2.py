# import pandas as pd
# import glob
# import os
#
# # 读取所有球队文件
# team_data = {}
#
# # 使用正确的路径，排除临时文件
# files_found = [f for f in glob.glob("Fprediction/player_expense/*_PE.xlsx")
#                if not f.startswith("Fprediction/player_expense/~$")]
#
# print(f"找到 {len(files_found)} 个有效文件")
#
# # 使用通配符读取所有value文件
# for file in files_found:
#     # 从文件名提取球队缩写
#     file_name = os.path.basename(file)
#     parts = file_name.split("_")
#
#     if len(parts) >= 2:
#         team_abbr = parts[1]  # 第二个部分是球队缩写
#     else:
#         continue
#
#     print(f"处理 {team_abbr}...")
#
#     try:
#         # 读取第二个sheet
#         df = pd.read_excel(file, sheet_name=1)
#
#         # 调试：查看数据形状
#         print(f"  {team_abbr} 原始数据形状: {df.shape}")
#         print(f"  {team_abbr} 原始列名: {df.columns.tolist()}")
#
#         # 方法1：直接定位年份和数值列
#         # 从你的数据看，年份在第二列(Unnamed: 1)，数值在第三列(Unnamed: 2)
#         # 我们需要跳过前几行空行
#
#         # 找到第一行有数值的数据
#         # 寻找第二列是数字（年份）的行
#         for i in range(len(df)):
#             cell_value = df.iloc[i, 1]  # 第二列
#             try:
#                 year = int(float(cell_value))
#                 if 2000 <= year <= 2030:  # 合理的年份范围
#                     # 从这一行开始提取数据
#                     data_start = i
#                     break
#             except:
#                 continue
#
#         print(f"  {team_abbr} 数据从第 {data_start} 行开始")
#
#         # 提取数据
#         df_data = df.iloc[data_start:, [1, 2]].copy()  # 提取第二列和第三列
#         df_data.columns = ["Year", "Value"]
#
#         # 清理数据
#         df_data["Year"] = pd.to_numeric(df_data["Year"], errors='coerce')
#         df_data["Value"] = pd.to_numeric(df_data["Value"], errors='coerce')
#         df_data = df_data.dropna(subset=["Year", "Value"])
#         df_data["Year"] = df_data["Year"].astype(int)
#
#         print(f"  {team_abbr} 清理后数据形状: {df_data.shape}")
#         print(f"  {team_abbr} 年份范围: {df_data['Year'].min()} - {df_data['Year'].max()}")
#
#         # 提取2021-2025数据
#         df_2021_25 = df_data[(df_data["Year"] >= 2021) & (df_data["Year"] <= 2025)]
#
#         print(f"  {team_abbr} 2021-2025数据行数: {len(df_2021_25)}")
#
#         if not df_2021_25.empty:
#             # 创建字典，年份为键，估值为值
#             values_dict = dict(zip(df_2021_25["Year"], df_2021_25["Value"]))
#             print(f"  {team_abbr} 提取的数据: {values_dict}")
#             team_data[team_abbr] = values_dict
#         else:
#             print(f"  {team_abbr} 没有2021-2025年数据")
#
#     except Exception as e:
#         print(f"  处理 {file} 时出错: {e}")
#
# print(f"\n成功提取数据的球队数: {len(team_data)}")
#
# # 转换为DataFrame并保存
# if team_data:
#     df_result = pd.DataFrame(team_data).T
#
#     # 显示所有列
#     print(f"\nDataFrame所有列: {df_result.columns.tolist()}")
#
#     # 选择2021-2025年的列（如果存在）
#     # 注意：有些球队可能缺少某些年份的数据
#     all_years = []
#     for data_dict in team_data.values():
#         all_years.extend(data_dict.keys())
#
#     unique_years = sorted(set(all_years), reverse=True)
#     print(f"所有存在的年份: {unique_years}")
#
#     # 创建一个包含所有年份的DataFrame
#     all_teams_df = pd.DataFrame(index=team_data.keys())
#
#     for year in unique_years:
#         year_data = {}
#         for team, data_dict in team_data.items():
#             if year in data_dict:
#                 year_data[team] = data_dict[year]
#
#         all_teams_df[str(year)] = pd.Series(year_data)
#
#     # 确保列顺序：2025, 2024, 2023, 2022, 2021
#     year_cols = [str(year) for year in [2025, 2024, 2023, 2022, 2021] if str(year) in all_teams_df.columns]
#     all_teams_df = all_teams_df[year_cols]
#
#     # 保存
#     all_teams_df.to_excel("PE21_25.xlsx")
#     print(f"\n成功保存 {len(all_teams_df)} 支球队的数据到 value21_25.xlsx")
#     print("\n数据预览:")
#     print(all_teams_df)
#
#     # 保存详细信息到另一个文件
#     with pd.ExcelWriter("PE21_25_detailed.xlsx") as writer:
#         all_teams_df.to_excel(writer, sheet_name='汇总')
#
#         # 添加每个球队的详细数据
#         for team, data_dict in team_data.items():
#             team_df = pd.DataFrame(list(data_dict.items()), columns=['Year', 'Value'])
#             team_df = team_df.sort_values('Year', ascending=False)
#             team_df.to_excel(writer, sheet_name=f'{team}_value', index=False)
#
#     print(f"\n详细数据已保存到 PE21_25_detailed.xlsx")
#
# else:
#     print("没有成功提取到任何数据")


import pandas as pd
import glob
import os
import re

# 更简单的方法：直接读取数据行
team_data = {}
files_found = glob.glob("Fprediction/player_expense/*_PE.xlsx")

print(f"找到 {len(files_found)} 个球员开支文件")

for file in files_found:
    file_name = os.path.basename(file)
    team_abbr = file_name.split("_")[1]
    print(f"处理 {team_abbr}...")

    try:
        # 读取Excel，不指定header
        df = pd.read_excel(file, sheet_name=1, header=None)

        # 查找包含年份和数值的行
        data_rows = []
        for i in range(len(df)):
            for j in range(len(df.columns)):
                cell = str(df.iloc[i, j]).strip()
                # 寻找 '2001/02' 格式
                if '/' in cell and cell.replace('/', '').isdigit():
                    # 提取年份部分
                    year_part = cell.split('/')[0]
                    try:
                        year = int(year_part)
                        if 2000 <= year <= 2024:
                            # 尝试获取数值（可能在下一列或同一行的其他列）
                            for k in range(j + 1, len(df.columns)):
                                try:
                                    value = float(df.iloc[i, k])
                                    if value > 10:  # 合理的球员开支（百万美元）
                                        data_rows.append((year, value))
                                        break
                                except:
                                    continue
                    except:
                        pass

        if data_rows:
            # 去重并排序
            data_dict = {}
            for year, value in data_rows:
                if year not in data_dict or value > data_dict[year]:  # 取较大值
                    data_dict[year] = value

            # 转换为DataFrame并排序
            df_data = pd.DataFrame(list(data_dict.items()), columns=['Year', 'Value'])
            df_data = df_data.sort_values('Year')

            print(f"  找到 {len(df_data)} 年数据: {list(data_dict.keys())}")

            # 提取并转换年份
            values_dict = {}
            for year in [2020, 2021, 2022, 2023, 2024]:  # 原始年份
                if year in data_dict:
                    season_year = year + 1  # 转换为赛季年
                    if 2021 <= season_year <= 2025:
                        values_dict[season_year] = data_dict[year]

            if values_dict:
                team_data[team_abbr] = values_dict
                print(f"  ✓ 提取到 {len(values_dict)} 年数据")
            else:
                print(f"  ✗ 没有2021-2025赛季数据")
        else:
            print(f"  ✗ 未找到数据")

    except Exception as e:
        print(f"  错误: {e}")

# 创建汇总表
if team_data:
    all_teams = sorted(team_data.keys())
    df_result = pd.DataFrame(index=all_teams, columns=['2025', '2024', '2023', '2022', '2021'])

    for team in all_teams:
        for year in [2021, 2022, 2023, 2024, 2025]:
            if year in team_data[team]:
                df_result.loc[team, str(year)] = team_data[team][year]

    df_result.to_excel("player_expenses_2021-2025.xlsx")
    print(f"\n保存了 {len(df_result)} 支球队的数据")
    print(df_result)