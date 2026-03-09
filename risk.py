import pandas as pd
import numpy as np


def calculate_injury_risk_simple(player):
    """
    简化版伤病风险函数（仅用于检查合理性）
    公式：risk = 1 / (1 + exp(-z))
    z = a0 + a1×AgeEffect + a2×LoadEffect + a3×PositionPenalty
    """
    # 参数设置（简化版）
    a0 = -2.0  # 截距项
    a1_youth = 0.03  # 青年组年龄系数
    a1_veteran = 0.09  # 老将组年龄系数
    a2 = 0.6  # 负荷系数
    a3 = 0.2  # 位置惩罚系数

    # 1. 提取球员基本信息
    name = player.get('Player', 'Unknown')
    age = player.get('Age', 25)
    mp = player.get('MP', 677)
    pos = player.get('Pos', 'SG')

    # 2. 年龄因子（分段处理）
    age_base = age - 27  # 以27岁为基准
    if age <= 27:
        age_effect = age_base * a1_youth
        age_group = "青年(≤27)"
    else:
        age_effect = age_base * a1_veteran
        age_group = "老将(>27)"

    # 3. 负荷因子（对数归一化）
    load_effect = np.log(mp / 677 + 1) * a2

    # 4. 位置因子
    position_penalty = a3 if pos in ['C', 'PF'] else 0

    # 5. 计算z值和风险
    z = a0 + age_effect + load_effect + position_penalty
    risk = 1 / (1 + np.exp(-z))

    return {
        'Player': name,
        'Age': age,
        'MP': mp,
        'Pos': pos,
        'age_group': age_group,
        'age_effect': age_effect,
        'load_effect': load_effect,
        'position_penalty': position_penalty,
        'z_value': z,
        'injury_risk': risk
    }


# ====== 使用你的真实数据 ======
if __name__ == "__main__":
    print("伤病风险函数合理性测试 - 使用真实数据")
    print("=" * 80)

    try:
        # 读取你的数据文件
        df = pd.read_excel("Pose2526total.xlsx")
        print(f"成功读取数据，共 {len(df)} 名球员")

        # 检查必要列是否存在
        required_cols = ['Player', 'Age', 'MP', 'Pos']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            print(f"错误：数据中缺少以下必要列: {missing_cols}")
            print("请确保数据文件包含以下列：Player, Age, MP, Pos")
            exit()

        # 计算每个球员的风险
        results = []
        for idx, row in df.iterrows():
            result = calculate_injury_risk_simple(row)
            results.append(result)

            # 每计算10名球员输出一次进度
            if (idx + 1) % 10 == 0:
                print(f"已计算 {idx + 1}/{len(df)} 名球员...")

        # 转换为DataFrame
        risk_df = pd.DataFrame(results)

        # 输出前20名球员的详细信息
        print("\n=== 前20名球员风险详情 ===")
        print("-" * 80)

        for i, row in risk_df.head(20).iterrows():
            print(f"{i + 1:2d}. {row['Player']:<25} 年龄: {row['Age']:>2}岁({row['age_group']:<8}) "
                  f"位置: {row['Pos']:>2} MP: {row['MP']:>5}分钟")
            print(f"    年龄因子: {row['age_effect']:6.3f} 负荷因子: {row['load_effect']:6.3f} "
                  f"位置惩罚: {row['position_penalty']:5.3f}")
            print(f"    z值: {row['z_value']:6.3f} 风险值: {row['injury_risk']:6.3f}")
            print("-" * 80)

        # 输出统计信息
        print("\n=== 整体风险分布统计 ===")
        print(f"总球员数: {len(risk_df)}")
        print(f"平均风险: {risk_df['injury_risk'].mean():.3f}")
        print(f"风险中位数: {risk_df['injury_risk'].median():.3f}")
        print(f"最低风险: {risk_df['injury_risk'].min():.3f}")
        print(f"最高风险: {risk_df['injury_risk'].max():.3f}")
        print(f"风险标准差: {risk_df['injury_risk'].std():.3f}")

        # 按类别分析
        print("\n=== 按类别风险统计 ===")

        # 按年龄组
        youth_df = risk_df[risk_df['age_group'] == '青年(≤27)']
        veteran_df = risk_df[risk_df['age_group'] == '老将(>27)']
        print(f"青年组(≤27岁): {len(youth_df)}人，平均风险: {youth_df['injury_risk'].mean():.3f}")
        print(f"老将组(>27岁): {len(veteran_df)}人，平均风险: {veteran_df['injury_risk'].mean():.3f}")

        # 按位置
        big_df = risk_df[risk_df['Pos'].isin(['C', 'PF'])]
        guard_df = risk_df[~risk_df['Pos'].isin(['C', 'PF'])]
        print(f"内线球员(C/PF): {len(big_df)}人，平均风险: {big_df['injury_risk'].mean():.3f}")
        print(f"外线球员: {len(guard_df)}人，平均风险: {guard_df['injury_risk'].mean():.3f}")

        # 按负荷（以1500分钟为界）
        high_mp_df = risk_df[risk_df['MP'] > 1500]
        low_mp_df = risk_df[risk_df['MP'] <= 1500]
        print(f"高负荷(>1500分钟): {len(high_mp_df)}人，平均风险: {high_mp_df['injury_risk'].mean():.3f}")
        print(f"低负荷(≤1500分钟): {len(low_mp_df)}人，平均风险: {low_mp_df['injury_risk'].mean():.3f}")

        # 输出风险最高的10名球员
        print("\n=== 风险最高的10名球员 ===")
        high_risk_df = risk_df.sort_values('injury_risk', ascending=False).head(10)
        for i, row in high_risk_df.iterrows():
            print(f"{i + 1:2d}. {row['Player']:<25} 风险: {row['injury_risk']:.3f} "
                  f"(年龄: {row['Age']}岁, 位置: {row['Pos']}, MP: {row['MP']})")

        # 输出风险最低的10名球员
        print("\n=== 风险最低的10名球员 ===")
        low_risk_df = risk_df.sort_values('injury_risk', ascending=True).head(10)
        for i, row in low_risk_df.iterrows():
            print(f"{i + 1:2d}. {row['Player']:<25} 风险: {row['injury_risk']:.3f} "
                  f"(年龄: {row['Age']}岁, 位置: {row['Pos']}, MP: {row['MP']})")

        # 保存结果到Excel
        output_file = 'player_risk_analysis.xlsx'
        risk_df.to_excel(output_file, index=False)
        print(f"\n结果已保存到: {output_file}")

    except FileNotFoundError:
        print("错误：找不到文件 'Pose2526total.xlsx'")
        print("请确保文件在当前目录下，或者提供正确的文件路径")
    except Exception as e:
        print(f"发生错误: {e}")