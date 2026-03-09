import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# 读取数据
df = pd.read_excel("Pose2526total.xlsx")

# 1. 计算RK-MP的线性关系（整体）
print("=== RK-MP线性关系分析 ===")
X = df[['Rk']].values
y = df['MP'].values

# 线性回归
model = LinearRegression()
model.fit(X, y)

# 回归系数
slope = model.coef_[0]  # 斜率：每增加1个RK，MP的变化
intercept = model.intercept_  # 截距

print(f"回归方程: MP = {intercept:.1f} + {slope:.2f} × Rk")
print(f"R² = {model.score(X, y):.4f}")

# 预测MP
df['MP_expected'] = model.predict(X)
df['MP_residual'] = df['MP'] - df['MP_expected']

print(f"平均MP: {df['MP'].mean():.1f}")
print(f"平均预期MP: {df['MP_expected'].mean():.1f}")
print(f"平均残差: {df['MP_residual'].mean():.1f}")

# 2. 按位置分析
print("\n=== 按位置分析 ===")
positions = df['Pos'].unique()
pos_stats = []

for pos in positions:
    pos_df = df[df['Pos'] == pos]
    pos_model = LinearRegression()
    pos_model.fit(pos_df[['Rk']], pos_df['MP'])

    pos_stats.append({
        'Pos': pos,
        '数量': len(pos_df),
        '平均MP': pos_df['MP'].mean(),
        '平均残差': pos_df['MP_residual'].mean(),
        '残差标准差': pos_df['MP_residual'].std(),
        '斜率': pos_model.coef_[0]
    })

pos_stats_df = pd.DataFrame(pos_stats)
print(pos_stats_df.to_string(index=False))

# 3. 可视化
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 散点图：RK vs MP
axes[0].scatter(df['Rk'], df['MP'], alpha=0.5, s=10)
axes[0].plot(df['Rk'], df['MP_expected'], color='red', linewidth=2, label='fit line')
axes[0].set_xlabel('Rk')
axes[0].set_ylabel('MP ')
axes[0].set_title('RK-MP')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 箱线图：位置残差分布
df.boxplot(column='MP_residual', by='Pos', ax=axes[1])
axes[1].set_xlabel('Pos')
axes[1].set_ylabel('MP residual')
axes[1].set_title('MP residual distribution')
axes[1].axhline(y=0, color='red', linestyle='--', alpha=0.5)

plt.suptitle('')
plt.tight_layout()
plt.show()

# 4. 简洁版结果
print("\n=== 精简结论 ===")
print(f"1. RK每增加1位，MP平均减少 {abs(slope):.1f} 分钟")
print(f"2. 第1名预期MP: {intercept:.0f}分钟")
print(f"3. 第250名预期MP: {intercept + slope * 250:.0f}分钟")
print("\n4. 各位置特点:")
for _, row in pos_stats_df.iterrows():
    if row['平均残差'] > 20:
        print(f"   {row['Pos']}: 上场时间偏多 (平均+{row['平均残差']:.0f}分钟)")
    elif row['平均残差'] < -20:
        print(f"   {row['Pos']}: 上场时间偏少 (平均{row['平均残差']:.0f}分钟)")
    else:
        print(f"   {row['Pos']}: 上场时间正常 (平均{row['平均残差']:.0f}分钟)")

# 5. 保存结果
df[['Rk', 'Player', 'Pos', 'MP', 'MP_expected', 'MP_residual']].to_excel('RK_MP_analysis.xlsx', index=False)
print(f"\n详细结果已保存到: RK_MP_analysis.xlsx")