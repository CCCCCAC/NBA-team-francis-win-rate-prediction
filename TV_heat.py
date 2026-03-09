import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

# 设置样式
plt.style.use('default')
sns.set_palette("husl")

# 读取数据
df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
df_2425 = pd.read_excel('indicators_noMIA.xlsx')

# 2024实际球队价值
tv_2024_actual = {
    'ATL': 3800, 'BOS': 6000, 'BRK': 4800, 'CHA': 3300, 'CHI': 5000,
    'CLE': 3950, 'DAL': 4700, 'DEN': 3900, 'DET': 3400, 'GSW': 8800,
    'HOU': 4900, 'IND': 3600, 'LAC': 5500, 'LAL': 7100, 'MEM': 3000,
    'MIA': 4250, 'MIL': 4000, 'MIN': 3100, 'NOP': 3050, 'NYK': 7500,
    'OKC': 3650, 'ORL': 3200, 'PHI': 4600, 'PHX': 4300, 'POR': 3500,
    'SAC': 3700, 'SAS': 3850, 'UTA': 3550, 'WAS': 4100
}

print("=" * 60)
print("MARKET FACTOR SENSITIVITY HEATMAP ANALYSIS")
print("=" * 60)

# ============================================================
# 准备数据
# ============================================================
print("\n[1] Preparing data...")

# 计算每个球队的市场特征（基于2023年数据）
market_features = {}
for team in df_2123['TEAM'].unique():
    team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')
    latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[
        -1]

    market_features[team] = {
        'GDP_NORM': latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0,
        'FANS_NORM': latest['FANS'],
        'ATTEND_NORM': latest['ATTENDANCE'] / 100000
    }

features_df = pd.DataFrame.from_dict(market_features, orient='index')
features_df.index.name = 'TEAM'
features_df = features_df.reset_index()

# 获取2024年预测数据
df_2024 = df_2425[df_2425['SEASON'] == 2024].copy()
df_2024['ACTUAL_TV'] = df_2024['TEAM'].map(tv_2024_actual)

print(f"✓ Data prepared for {len(df_2024)} teams")

# ============================================================
# 训练基础模型（使用均匀权重作为基准）
# ============================================================
print("\n[2] Training base model...")

# 使用均匀权重计算市场分数
features_df['MARKET_SCORE_BASE'] = (
        features_df['GDP_NORM'] * 0.33 +
        features_df['FANS_NORM'] * 0.33 +
        features_df['ATTEND_NORM'] * 0.33
)

train_df = pd.merge(df_2123, features_df[['TEAM', 'MARKET_SCORE_BASE']], on='TEAM', how='left')
train_df['LOG_TV'] = np.log(train_df['TEAM_VALUE'])

X_train = np.column_stack([
    train_df['RWIN'].values,
    train_df['PLAYER_EXPENSES'].values,
    train_df['MARKET_SCORE_BASE'].values
])
y_train = train_df['LOG_TV'].values

X_train_with_intercept = np.column_stack([np.ones(len(X_train)), X_train])
coefficients = np.linalg.lstsq(X_train_with_intercept, y_train, rcond=None)[0]
alpha, beta, theta, gamma = coefficients

print(f"✓ Model trained: α={alpha:.4f}, β={beta:.4f}, θ={theta:.4f}, γ={gamma:.4f}")

# ============================================================
# 创建自定义色系
# ============================================================
hex_colors = ["#274753", "#297270", "#299d8f", "#8ab07c", "#e7c66b", "#f3a361", "#e66d50"]
custom_cmap = LinearSegmentedColormap.from_list("custom_gradient", hex_colors, N=256)

# ============================================================
# 高密度网格采样权重组合
# ============================================================
print("\n[3] High-density grid sampling...")

# 增加网格密度
n_points = 51  # 增加采样点数（从21增加到51）
w_gdp = np.linspace(0, 1, n_points)
w_fans = np.linspace(0, 1, n_points)

# 存储结果
results = []

# 使用向量化计算提高效率
print(f"  Sampling {n_points}×{n_points} grid points...", end="")

for i, w1 in enumerate(w_gdp):
    for j, w2 in enumerate(w_fans):
        # 计算第三个权重（保证和为1）
        w3 = 1 - w1 - w2

        # 跳过无效组合
        if w3 < 0 or w3 > 1:
            continue

        # 计算该权重下的市场分数
        market_score = (
                features_df['GDP_NORM'] * w1 +
                features_df['FANS_NORM'] * w2 +
                features_df['ATTEND_NORM'] * w3
        )

        # 合并数据
        market_score_df = pd.DataFrame({'TEAM': features_df['TEAM'], 'MARKET_SCORE': market_score})
        df_test = df_2024.merge(market_score_df, on='TEAM', how='left')

        # 预测
        df_test['LOG_PREDICTED'] = alpha + beta * df_test['RWIN'] + theta * df_test['PLAYER_EXPENSES'] + gamma * \
                                   df_test['MARKET_SCORE']
        df_test['PREDICTED_TV'] = np.exp(df_test['LOG_PREDICTED']) * 1.084
        df_test['ERROR'] = df_test['PREDICTED_TV'] - df_test['ACTUAL_TV']

        # 计算R²
        ss_res = np.sum(df_test['ERROR'] ** 2)
        ss_tot = np.sum((df_test['ACTUAL_TV'] - df_test['ACTUAL_TV'].mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        results.append({
            'GDP_weight': w1,
            'FANS_weight': w2,
            'ATTEND_weight': w3,
            'R2': r2
        })

# 转换为DataFrame
results_df = pd.DataFrame(results)
print(f" Done!")
print(f"✓ Sampled {len(results_df)} valid weight combinations")

# ============================================================
# 创建热力图
# ============================================================
print("\n[4] Creating high-resolution heatmap visualization...")

# 准备热力图数据
heatmap_data = np.full((n_points, n_points), np.nan)

for _, row in results_df.iterrows():
    i = np.where(w_gdp == row['GDP_weight'])[0][0]
    j = np.where(w_fans == row['FANS_weight'])[0][0]
    heatmap_data[j, i] = row['R2']  # 注意：j是行索引（y轴），i是列索引（x轴）

# 确定R²范围
r2_min = results_df['R2'].min()
r2_max = results_df['R2'].max()
print(f"  R² range: {r2_min:.4f} to {r2_max:.4f}")

# 创建热力图
fig, ax = plt.subplots(figsize=(14, 12))

# 热力图 - 使用自定义色系
im = ax.imshow(heatmap_data,
               extent=[w_gdp.min(), w_gdp.max(), w_fans.min(), w_fans.max()],
               origin='lower',
               aspect='auto',
               cmap=custom_cmap,
               interpolation='bilinear',  # 增加插值使图像更平滑
               vmin=max(0.5, r2_min - 0.01),  # 动态设置范围
               vmax=min(0.6, r2_max + 0.01))

# 添加等高线
if not np.all(np.isnan(heatmap_data)):
    # 动态确定等高线级别
    contour_levels = np.linspace(r2_min, r2_max, 10)
    CS = ax.contour(w_gdp, w_fans, heatmap_data,
                    levels=contour_levels,
                    colors='white',
                    linewidths=0.8,
                    alpha=0.8)
    ax.clabel(CS, inline=True, fontsize=9, fmt='%.3f', colors='white')

# 标记你的四个实验点
experiments = [
    (0.33, 0.33, 0.33, 'Uniform', 'o', 10),  # 圆形
    (0.90, 0.05, 0.05, 'GDP-dom', 's', 10),  # 正方形
    (0.05, 0.90, 0.05, 'FANS-dom', '^', 12),  # 三角形
    (0.05, 0.05, 0.90, 'ATTEND-dom', 'D', 10)  # 菱形
]

# 先绘制实验点标记
for gdp_w, fans_w, attend_w, label, marker, markersize in experiments:
    # 查找对应的R²值
    r2_value = None
    matching = results_df[(np.abs(results_df['GDP_weight'] - gdp_w) < 0.001) &
                          (np.abs(results_df['FANS_weight'] - fans_w) < 0.001)]
    if not matching.empty:
        r2_value = matching.iloc[0]['R2']

    # 绘制标记点
    ax.scatter(gdp_w, fans_w,
               s=markersize * 15,  # 增大标记点
               marker=marker,
               edgecolors='black',
               facecolors='white',
               linewidths=2,
               zorder=10,  # 确保在最上层
               label=f'{label}: R²={r2_value:.4f}' if r2_value is not None else label)

# 添加颜色条
cbar = plt.colorbar(im, ax=ax, pad=0.02)
cbar.set_label('Validation R² (2024)', fontsize=13, fontweight='bold')
cbar.ax.tick_params(labelsize=11)

# 设置坐标轴
ax.set_xlabel('GDP Weight (w₁)', fontsize=13, fontweight='bold')
ax.set_ylabel('Fans Weight (w₂)', fontsize=13, fontweight='bold')
ax.set_title('Market Factor Weight Sensitivity Analysis: Performance Landscape',
             fontsize=16, fontweight='bold', pad=20)

# 添加三角形边界线（表示w₃ = 1 - w₁ - w₂ ≥ 0）
triangle_x = [0, 1, 0, 0]
triangle_y = [0, 0, 1, 0]
ax.plot(triangle_x, triangle_y, 'black', linewidth=2, alpha=0.8, linestyle='--',
        label='Feasible region boundary')

# 填充可行域
ax.fill(triangle_x, triangle_y, alpha=0.05, color='gray')

# 添加网格
ax.grid(True, alpha=0.2, linestyle=':', linewidth=0.5)

# 图例
legend = ax.legend(loc='upper right', fontsize=11, framealpha=0.95)
legend.get_frame().set_edgecolor('black')

# 添加统计信息文本框
stats_text = f"""
Grid Resolution: {n_points}×{n_points}
Valid Samples: {len(results_df):,}
R² Range: {r2_min:.4f} - {r2_max:.4f}
ΔR²: {(r2_max - r2_min):.4f}

Optimal Weights:
GDP: {results_df.loc[results_df['R2'].idxmax(), 'GDP_weight']:.3f}
Fans: {results_df.loc[results_df['R2'].idxmax(), 'FANS_weight']:.3f}
Attend: {results_df.loc[results_df['R2'].idxmax(), 'ATTEND_weight']:.3f}
Max R²: {results_df['R2'].max():.4f}
"""

ax.text(0.02, 0.98, stats_text,
        transform=ax.transAxes,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray'),
        fontsize=10,
        family='monospace')

# 美化坐标轴刻度
ax.tick_params(axis='both', which='major', labelsize=11)
ax.set_xticks(np.arange(0, 1.1, 0.1))
ax.set_yticks(np.arange(0, 1.1, 0.1))

plt.tight_layout()
plt.savefig('market_weight_sensitivity_heatmap_highres.png', dpi=400, bbox_inches='tight')
print("✓ High-resolution heatmap saved as 'market_weight_sensitivity_heatmap_highres.png'")

# 显示详细统计信息
print(f"\n📊 DETAILED STATISTICS:")
print(f"  Grid resolution: {n_points}×{n_points}")
print(f"  Valid samples: {len(results_df)}")
print(f"  R² range: {r2_min:.4f} to {r2_max:.4f}")
print(f"  R² spread: {(r2_max - r2_min):.4f}")

print(f"\n🏆 OPTIMAL WEIGHT COMBINATION:")
best_comb = results_df.loc[results_df['R2'].idxmax()]
print(f"  GDP weight: {best_comb['GDP_weight']:.4f}")
print(f"  FANS weight: {best_comb['FANS_weight']:.4f}")
print(f"  ATTENDANCE weight: {best_comb['ATTEND_weight']:.4f}")
print(f"  Validation R²: {best_comb['R2']:.4f}")

print(f"\n🔍 YOUR EXPERIMENTAL POINTS:")
for gdp_w, fans_w, attend_w, label, _, _ in experiments:
    matching = results_df[(np.abs(results_df['GDP_weight'] - gdp_w) < 0.001) &
                          (np.abs(results_df['FANS_weight'] - fans_w) < 0.001)]
    if not matching.empty:
        r2 = matching.iloc[0]['R2']
        rank = (results_df['R2'] > r2).sum() + 1
        print(f"  {label:10s}: R²={r2:.4f} (Rank: {rank}/{len(results_df)})")

print("\n" + "=" * 60)
print("HIGH-RESOLUTION SENSITIVITY ANALYSIS COMPLETE")
print("=" * 60)


# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
# from sklearn.cluster import KMeans
# from matplotlib.colors import LinearSegmentedColormap
#
# # 设置样式
# plt.style.use('default')
#
# # 读取数据
# df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
# df_2425 = pd.read_excel('indicators_noMIA.xlsx')
#
# # 2024实际球队价值
# tv_2024_actual = {
#     'ATL': 3800, 'BOS': 6000, 'BRK': 4800, 'CHA': 3300, 'CHI': 5000,
#     'CLE': 3950, 'DAL': 4700, 'DEN': 3900, 'DET': 3400, 'GSW': 8800,
#     'HOU': 4900, 'IND': 3600, 'LAC': 5500, 'LAL': 7100, 'MEM': 3000,
#     'MIA': 4250, 'MIL': 4000, 'MIN': 3100, 'NOP': 3050, 'NYK': 7500,
#     'OKC': 3650, 'ORL': 3200, 'PHI': 4600, 'PHX': 4300, 'POR': 3500,
#     'SAC': 3700, 'SAS': 3850, 'UTA': 3550, 'WAS': 4100
# }
#
# print("=" * 60)
# print("REPRESENTATIVE TEAMS SELECTION ANALYSIS")
# print("=" * 60)
#
# # ============================================================
# # 1. 计算每个球队的市场特征
# # ============================================================
# print("\n[1] Calculating market characteristics for all teams...")
#
# market_features = {}
# for team in df_2123['TEAM'].unique():
#     team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')
#     latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[
#         -1]
#
#     market_features[team] = {
#         'GDP': latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0,
#         'FANS': latest['FANS'],
#         'ATTENDANCE': latest['ATTENDANCE'] / 100000,
#         'RWIN_2024': df_2425[(df_2425['TEAM'] == team) & (df_2425['SEASON'] == 2024)]['RWIN'].iloc[0] if not df_2425[
#             (df_2425['TEAM'] == team) & (df_2425['SEASON'] == 2024)].empty else 0,
#         'ACTUAL_TV': tv_2024_actual.get(team, 0)
#     }
#
# # 转换为DataFrame
# features_df = pd.DataFrame.from_dict(market_features, orient='index')
# features_df.index.name = 'TEAM'
# features_df = features_df.reset_index()
#
# # 归一化特征（0-1范围）
# for col in ['GDP', 'FANS', 'ATTENDANCE', 'RWIN_2024', 'ACTUAL_TV']:
#     if col in features_df.columns:
#         min_val = features_df[col].min()
#         max_val = features_df[col].max()
#         features_df[f'{col}_NORM'] = (features_df[col] - min_val) / (max_val - min_val) if max_val > min_val else 0.5
#
# print(f"✓ Calculated features for {len(features_df)} teams")
#
# # ============================================================
# # 2. 多维度分析
# # ============================================================
# print("\n[2] Multi-dimensional analysis...")
#
# # 计算每个维度的排名
# dimensions = ['GDP', 'FANS', 'ATTENDANCE', 'RWIN_2024', 'ACTUAL_TV']
# for dim in dimensions:
#     features_df[f'{dim}_RANK'] = features_df[dim].rank(ascending=False, method='min')
#
# print("✓ Rankings calculated")
#
# # ============================================================
# # 3. 聚类分析找到代表性球队
# # ============================================================
# print("\n[3] Clustering teams to find representatives...")
#
# # 使用聚类分析
# cluster_features = features_df[['GDP_NORM', 'FANS_NORM', 'ATTENDANCE_NORM', 'RWIN_2024_NORM', 'ACTUAL_TV_NORM']].values
#
# # 尝试不同的聚类数，找到最佳的代表性
# n_clusters = 4
# kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
# features_df['CLUSTER'] = kmeans.fit_predict(cluster_features)
#
# # 计算每个聚类的中心点
# cluster_centers = kmeans.cluster_centers_
#
# # 找到每个聚类中最接近中心点的球队（代表性球队）
# representative_teams = []
# for cluster_id in range(n_clusters):
#     cluster_data = features_df[features_df['CLUSTER'] == cluster_id]
#     cluster_points = cluster_data[
#         ['GDP_NORM', 'FANS_NORM', 'ATTENDANCE_NORM', 'RWIN_2024_NORM', 'ACTUAL_TV_NORM']].values
#
#     # 计算每个点到聚类中心的距离
#     distances = np.linalg.norm(cluster_points - cluster_centers[cluster_id], axis=1)
#     closest_idx = distances.argmin()
#     rep_team = cluster_data.iloc[closest_idx]['TEAM']
#     representative_teams.append(rep_team)
#
# print(f"✓ Found {len(representative_teams)} representative teams via clustering")
#
# # ============================================================
# # 4. 手动优化选择（确保覆盖不同类型的球队）
# # ============================================================
# print("\n[4] Optimizing selection for diversity...")

# 基于聚类结果，手动微调选择以确保覆盖：
# 1. 大球市球队（高GDP、高粉丝）
# 2. 小球市强队（低GDP、高RWIN）
# 3. 中等球市球队
# 4. 极端类型球队

# 先查看聚类结果
# print("\nCluster composition:")
# for cluster_id in range(n_clusters):
#     cluster_teams = features_df[features_df['CLUSTER'] == cluster_id]['TEAM'].tolist()
#     avg_gdp = features_df[features_df['CLUSTER'] == cluster_id]['GDP'].mean()
#     avg_fans = features_df[features_df['CLUSTER'] == cluster_id]['FANS'].mean()
#     print(f"  Cluster {cluster_id}: {len(cluster_teams)} teams, Avg GDP: {avg_gdp:.1f}, Avg Fans: {avg_fans:.1f}")
#     print(f"    Teams: {', '.join(cluster_teams)}")
#
# # 手动选择四个最具代表性的类型
# candidate_types = {
#     'BIG_MARKET': ['GSW', 'LAL', 'NYK', 'CHI'],
#     'MID_MARKET': ['HOU', 'DAL', 'PHI', 'ATL'],
#     'SMALL_MARKET': ['SAS', 'MIL', 'IND', 'UTA'],
#     'EXTREME_TYPE': ['OKC', 'MEM', 'CHA', 'POR']  # 极端值球队
# }
#
# # 根据实际数据分析选择
# selected_teams = []
#
# # 1. 大球市代表：选择GSW（勇士）- 粉丝经济型
# gsw_data = features_df[features_df['TEAM'] == 'GSW'].iloc[0]
# selected_teams.append({
#     'TEAM': 'GSW',
#     'TYPE': 'Big Market / Fan Economy',
#     'GDP_RANK': int(gsw_data['GDP_RANK']),
#     'FANS_RANK': int(gsw_data['FANS_RANK']),
#     'ATTEND_RANK': int(gsw_data['ATTENDANCE_RANK']),
#     'RWIN_RANK': int(gsw_data['RWIN_2024_RANK']),
#     'TV_RANK': int(gsw_data['ACTUAL_TV_RANK'])
# })
#
# # 2. 经济驱动型：选择HOU（火箭）- 综合平衡型
# hou_data = features_df[features_df['TEAM'] == 'HOU'].iloc[0]
# selected_teams.append({
#     'TEAM': 'HOU',
#     'TYPE': 'Balanced / Economy-driven',
#     'GDP_RANK': int(hou_data['GDP_RANK']),
#     'FANS_RANK': int(hou_data['FANS_RANK']),
#     'ATTEND_RANK': int(hou_data['ATTENDANCE_RANK']),
#     'RWIN_RANK': int(hou_data['RWIN_2024_RANK']),
#     'TV_RANK': int(hou_data['ACTUAL_TV_RANK'])
# })
#
# # 3. 小球市代表：选择SAS（马刺）- 运营稳定型
# sas_data = features_df[features_df['TEAM'] == 'SAS'].iloc[0]
# selected_teams.append({
#     'TEAM': 'SAS',
#     'TYPE': 'Small Market / Stable Operation',
#     'GDP_RANK': int(sas_data['GDP_RANK']),
#     'FANS_RANK': int(sas_data['FANS_RANK']),
#     'ATTEND_RANK': int(sas_data['ATTENDANCE_RANK']),
#     'RWIN_RANK': int(sas_data['RWIN_2024_RANK']),
#     'TV_RANK': int(sas_data['ACTUAL_TV_RANK'])
# })
#
# # 4. 极端值代表：选择NYK（尼克斯）- 估值异常型
# nyk_data = features_df[features_df['TEAM'] == 'NYK'].iloc[0]
# selected_teams.append({
#     'TEAM': 'NYK',
#     'TYPE': 'Extreme Value / Market Premium',
#     'GDP_RANK': int(nyk_data['GDP_RANK']),
#     'FANS_RANK': int(nyk_data['FANS_RANK']),
#     'ATTEND_RANK': int(nyk_data['ATTENDANCE_RANK']),
#     'RWIN_RANK': int(nyk_data['RWIN_2024_RANK']),
#     'TV_RANK': int(nyk_data['ACTUAL_TV_RANK'])
# })
#
# selected_df = pd.DataFrame(selected_teams)
# print(f"\n✓ Selected 4 representative teams:")
#
# # ============================================================
# # 5. 可视化选择结果
# # ============================================================
# print("\n[5] Visualizing team selection...")
#
# fig, axes = plt.subplots(1, 2, figsize=(16, 6))
#
# # 图1: 球队特征雷达图
# ax1 = axes[0]
# categories = ['GDP', 'FANS', 'ATTENDANCE', 'RWIN_2024', 'ACTUAL_TV']
# N = len(categories)
#
# # 创建雷达图
# angles = [n / float(N) * 2 * np.pi for n in range(N)]
# angles += angles[:1]  # 闭合图形
#
# ax1 = plt.subplot(1, 2, 1, polar=True)
# ax1.set_theta_offset(np.pi / 2)
# ax1.set_theta_direction(-1)
#
# plt.xticks(angles[:-1], categories, size=11)
# ax1.set_rlabel_position(0)
# plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], size=9)
# plt.ylim(0, 1)
#
# # 绘制每个球队
# colors = ['#274753', '#299d8f', '#e7c66b', '#e66d50']
# for idx, (_, row) in enumerate(selected_df.iterrows()):
#     team = row['TEAM']
#     team_data = features_df[features_df['TEAM'] == team].iloc[0]
#
#     values = []
#     for cat in categories:
#         norm_col = f'{cat}_NORM'
#         if norm_col in team_data:
#             values.append(team_data[norm_col])
#         else:
#             values.append(0.5)
#
#     values += values[:1]  # 闭合图形
#     ax1.plot(angles, values, linewidth=2, linestyle='solid', label=team, color=colors[idx])
#     ax1.fill(angles, values, alpha=0.1, color=colors[idx])
#
# plt.title('Representative Teams: Multi-dimensional Profiles', size=14, fontweight='bold', pad=20)
# ax1.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
#
# # 图2: 球队排名条形图
# ax2 = axes[1]
# x = np.arange(len(categories))
# width = 0.2
#
# for idx, (_, row) in enumerate(selected_df.iterrows()):
#     team = row['TEAM']
#     ranks = [row['GDP_RANK'], row['FANS_RANK'], row['ATTEND_RANK'], row['RWIN_RANK'], row['TV_RANK']]
#     ax2.bar(x + idx * width - 0.3, ranks, width, label=team, color=colors[idx], alpha=0.8)
#
# ax2.set_xlabel('Dimension', fontsize=12, fontweight='bold')
# ax2.set_ylabel('Rank (1=Best)', fontsize=12, fontweight='bold')
# ax2.set_title('Team Rankings Across Dimensions', fontsize=14, fontweight='bold')
# ax2.set_xticks(x)
# ax2.set_xticklabels(categories, fontsize=11)
# ax2.invert_yaxis()  # 排名1在顶部
# ax2.legend()
# ax2.grid(True, alpha=0.3, axis='y')
#
# plt.tight_layout()
# plt.savefig('representative_teams_selection.png', dpi=300, bbox_inches='tight')
# print("✓ Selection visualization saved")
#
# # ============================================================
# # 6. 输出详细选择报告
# # ============================================================
# print("\n" + "=" * 60)
# print("SELECTED REPRESENTATIVE TEAMS")
# print("=" * 60)
#
# for _, row in selected_df.iterrows():
#     team = row['TEAM']
#     team_data = features_df[features_df['TEAM'] == team].iloc[0]
#
#     print(f"\n🏀 {team} - {row['TYPE']}")
#     print(f"  GDP: ${team_data['GDP'] * 1000:.0f}M (Rank: {row['GDP_RANK']}/29)")
#     print(f"  Fans: {team_data['FANS']:.1f} (Rank: {row['FANS_RANK']}/29)")
#     print(f"  Attendance: {team_data['ATTENDANCE'] * 100000:.0f} (Rank: {row['ATTEND_RANK']}/29)")
#     print(f"  RWIN 2024: {team_data['RWIN_2024']:.3f} (Rank: {row['RWIN_RANK']}/29)")
#     print(f"  Actual TV 2024: ${team_data['ACTUAL_TV']:.0f}M (Rank: {row['TV_RANK']}/29)")
#
# print("\n📊 SELECTION RATIONALE:")
# print("  1. GSW (Golden State Warriors): Big market, fan economy dominant")
# print("  2. HOU (Houston Rockets): Balanced mid-market, economy-driven")
# print("  3. SAS (San Antonio Spurs): Small market, stable operation")
# print("  4. NYK (New York Knicks): Extreme valuation, market premium")
#
# # 保存选择结果
# selected_df.to_excel('selected_representative_teams.xlsx', index=False)
# print(f"\n✓ Selection saved to 'selected_representative_teams.xlsx'")
#
# # 输出最终的球队列表（供热力图代码使用）
# final_teams = selected_df['TEAM'].tolist()
# print(f"\n🎯 FINAL SELECTED TEAMS FOR HEATMAPS: {final_teams}")
#
# print("\n" + "=" * 60)
# print("READY FOR HEATMAP GENERATION")
# print("=" * 60)
#
# # 返回选中的球队列表
# print(f"\n# Copy this list for heatmap generation:")
# print(f"selected_teams = {final_teams}")