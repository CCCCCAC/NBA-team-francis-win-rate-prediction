import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from scipy import stats

# 读取数据
df = pd.read_excel("Pose2526total.xlsx")

# 1. 基础线性回归
model = LinearRegression()
model.fit(df[['Rk']], df['MP'])
df['MP_expected'] = model.predict(df[['Rk']])
df['MP_residual'] = df['MP'] - df['MP_expected']

# 2. 蒙特卡洛模拟：估计位置调整因子
print("=== 蒙特卡洛模拟：位置调整因子 ===")

# 设置模拟参数
n_simulations = 10000
pos_factors = {pos: [] for pos in df['Pos'].unique()}

for sim in range(n_simulations):
    # 随机重排位置标签（保持数据不变）
    shuffled_pos = np.random.permutation(df['Pos'].values)
    temp_df = df.copy()
    temp_df['Pos_shuffled'] = shuffled_pos

    # 对每个位置计算平均残差
    for pos in temp_df['Pos_shuffled'].unique():
        pos_mask = temp_df['Pos_shuffled'] == pos
        avg_residual = temp_df.loc[pos_mask, 'MP_residual'].mean()
        pos_factors[pos].append(avg_residual)

# 3. 计算统计量
print("\n位置调整因子统计（蒙特卡洛模拟）：")
results = []
for pos in df['Pos'].unique():
    factors = pos_factors[pos]
    mean_factor = np.mean(factors)
    std_factor = np.std(factors)

    # 计算95%置信区间
    ci_lower = np.percentile(factors, 2.5)
    ci_upper = np.percentile(factors, 97.5)

    # 实际观察值
    actual_residual = df[df['Pos'] == pos]['MP_residual'].mean()

    # 计算z-score（实际值偏离随机期望的程度）
    z_score = (actual_residual - mean_factor) / std_factor if std_factor > 0 else 0

    results.append({
        'Pos': pos,
        '球员数': len(df[df['Pos'] == pos]),
        '实际残差均值': actual_residual,
        '随机期望均值': mean_factor,
        '随机标准差': std_factor,
        '95%CI下限': ci_lower,
        '95%CI上限': ci_upper,
        'z_score': z_score,
        'p_value': 2 * (1 - stats.norm.cdf(abs(z_score))) if std_factor > 0 else 1
    })

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

# 4. 确定调整因子
print("\n=== 位置调整因子计算 ===")
print("调整因子 = (实际残差 - 随机期望) / 随机标准差")
print("调整后的MP = MP_expected + 调整因子 × 随机标准差")

adjustments = []
for _, row in results_df.iterrows():
    # 如果显著偏离随机期望（|z| > 1.96，p < 0.05），则应用调整
    if abs(row['z_score']) > 1.96:
        adjustment_factor = row['z_score']  # 标准化调整量
        adjustment_minutes = row['实际残差均值'] - row['随机期望均值']  # 实际分钟调整
    else:
        adjustment_factor = 0
        adjustment_minutes = 0

    adjustments.append({
        'Pos': row['Pos'],
        '是否显著': '是' if abs(row['z_score']) > 1.96 else '否',
        'z_score': row['z_score'],
        '调整因子': adjustment_factor,
        '调整分钟数': adjustment_minutes,
        '建议权重': 1 + adjustment_factor * 0.1  # 缩放因子
    })

adjustments_df = pd.DataFrame(adjustments)
print(adjustments_df.to_string(index=False))

# 5. 应用调整
print("\n=== 应用位置调整 ===")
df['pos_adjustment'] = 0
for _, adj in adjustments_df.iterrows():
    pos_mask = df['Pos'] == adj['Pos']
    df.loc[pos_mask, 'pos_adjustment'] = adj['调整分钟数']

# 修正后的预期MP
df['MP_expected_adj'] = df['MP_expected'] + df['pos_adjustment']
df['MP_residual_adj'] = df['MP'] - df['MP_expected_adj']

# 检查调整效果
print("\n调整效果：")
print(f"原始残差标准差: {df['MP_residual'].std():.1f}")
print(f"调整后残差标准差: {df['MP_residual_adj'].std():.1f}")
print(f"残差减少: {(1 - df['MP_residual_adj'].std() / df['MP_residual'].std()) * 100:.1f}%")

# 6. 可视化
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1：原始残差分布
axes[0, 0].scatter(df['Rk'], df['MP_residual'], alpha=0.5, s=10, c='blue')
axes[0, 0].axhline(y=0, color='red', linestyle='--')
axes[0, 0].set_xlabel('Rk')
axes[0, 0].set_ylabel('原始残差')
axes[0, 0].set_title('原始MP残差分布')
axes[0, 0].grid(True, alpha=0.3)

# 图2：调整后残差分布
axes[0, 1].scatter(df['Rk'], df['MP_residual_adj'], alpha=0.5, s=10, c='green')
axes[0, 1].axhline(y=0, color='red', linestyle='--')
axes[0, 1].set_xlabel('Rk')
axes[0, 1].set_ylabel('调整后残差')
axes[0, 1].set_title('调整后MP残差分布')
axes[0, 1].grid(True, alpha=0.3)

# 图3：位置调整因子
colors = ['red', 'blue', 'green', 'orange', 'purple']
for i, (pos, adj) in enumerate(zip(adjustments_df['Pos'], adjustments_df['调整分钟数'])):
    axes[1, 0].bar(i, adj, color=colors[i], alpha=0.7)
axes[1, 0].set_xticks(range(len(adjustments_df)))
axes[1, 0].set_xticklabels(adjustments_df['Pos'])
axes[1, 0].set_ylabel('调整分钟数')
axes[1, 0].set_title('位置调整量')
axes[1, 0].axhline(y=0, color='black', linewidth=0.5)

# 图4：残差分布对比
axes[1, 1].boxplot([df['MP_residual'], df['MP_residual_adj']])
axes[1, 1].set_xticklabels(['原始残差', '调整后残差'])
axes[1, 1].set_ylabel('残差值')
axes[1, 1].set_title('残差分布对比')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# 7. 简化输出：实际应用公式
print("\n=== 实际应用公式 ===")
print("对于每个球员，计算修正后的预期MP：")
print("MP_expected_corrected = MP_expected + pos_adjustment")
print("\n位置调整值：")
for _, adj in adjustments_df.iterrows():
    if adj['调整分钟数'] != 0:
        print(f"  {adj['Pos']}: {'+' if adj['调整分钟数'] > 0 else ''}{adj['调整分钟数']:.0f}分钟")

# 保存结果
df[['Rk', 'Player', 'Pos', 'MP', 'MP_expected', 'pos_adjustment', 'MP_expected_adj', 'MP_residual',
    'MP_residual_adj']].to_excel('MP_adjusted_monte_carlo.xlsx', index=False)
print(f"\n详细结果已保存到: MP_adjusted_monte_carlo.xlsx")