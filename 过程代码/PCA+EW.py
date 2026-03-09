# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from sklearn.decomposition import PCA
# from sklearn.preprocessing import StandardScaler, RobustScaler
# from scipy.stats import entropy
# import os
#
# plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
# plt.rcParams['axes.unicode_minus'] = False
#
#
# class SimpleBasketballNormalizer:
#     """简化的篮球数据归一化器"""
#
#     def __init__(self):
#         self.scalers = {}
#
#     def normalize_dataframe(self, df, pos=None):
#         """对DataFrame中的所有指标进行归一化"""
#         df_norm = df.copy()
#
#         # 1. 百分比指标 (反正弦变换)
#         percentage_cols = ['FG.1', '3P', '3PP', '2P', '2PP', 'FT.1', 'eFG']
#         for col in percentage_cols:
#             if col in df.columns:
#                 # 处理0值和1值
#                 data = df[col].values.astype(float)
#                 data = np.clip(data, 0.0001, 0.9999)
#                 df_norm[col] = np.arcsin(np.sqrt(data)) * 2 / np.pi
#
#         # 2. 计数指标 (对数变换 + MinMax)
#         count_cols = ['G', 'GS', 'MP', 'ORB', 'DRB', 'TRB',
#                       'AST', 'STL', 'BLK', 'FG', '3P', '2P', 'FT', 'PTS']
#         for col in count_cols:
#             if col in df.columns:
#                 data = df[col].values.astype(float) + 1  # 避免log(0)
#                 log_data = np.log10(data)
#                 min_val, max_val = log_data.min(), log_data.max()
#                 if max_val > min_val:
#                     df_norm[col] = (log_data - min_val) / (max_val - min_val)
#
#         # 3. 逆向指标 (倒数变换 + Z-score)
#         negative_cols = ['TOV', 'PF']
#         for col in negative_cols:
#             if col in df.columns:
#                 data = df[col].values.astype(float)
#                 # 处理0值
#                 data = np.where(data == 0, 0.1, data)
#                 inverted = 1 / data
#                 df_norm[col] = (inverted - np.mean(inverted)) / np.std(inverted)
#
#         # 4. 效率指标
#         # ORtg使用RobustScaler
#         if 'ORtg' in df.columns:
#             ortg_data = df['ORtg'].values.astype(float)
#             # 处理0值
#             if np.any(ortg_data == 0):
#                 median_val = np.median(ortg_data[ortg_data > 0])
#                 ortg_data = np.where(ortg_data == 0, median_val, ortg_data)
#
#             scaler = RobustScaler(quantile_range=(25, 75))
#             df_norm['ORtg'] = scaler.fit_transform(ortg_data.reshape(-1, 1)).flatten()
#             self.scalers['ORtg'] = scaler
#
#         # DRtg特殊处理：按位置调整放大系数
#         if 'DRtg' in df.columns:
#             drtg_data = df['DRtg'].values.astype(float)
#
#             # 不同位置使用不同的放大系数
#             if pos == 'C':  # 中锋：DRtg差异更重要
#                 # 倒置（值越小越好）并放大
#                 df_norm['DRtg'] = np.power(130 - drtg_data, 1.5)
#             elif pos == 'PG':  # 控卫：助攻更重要，DRtg权重适中
#                 df_norm['DRtg'] = np.power(130 - drtg_data, 1.2)
#             else:  # 其他位置
#                 df_norm['DRtg'] = 130 - drtg_data  # 简单倒置
#
#             # 标准化到0-1
#             min_val, max_val = df_norm['DRtg'].min(), df_norm['DRtg'].max()
#             if max_val > min_val:
#                 df_norm['DRtg'] = (df_norm['DRtg'] - min_val) / (max_val - min_val)
#
#         # 5. 年龄直接Z-score
#         if 'Age' in df.columns:
#             scaler = StandardScaler()
#             df_norm['Age'] = scaler.fit_transform(df['Age'].values.reshape(-1, 1)).flatten()
#             self.scalers['Age'] = scaler
#
#         # 6. 最后对数值列进行Z-score标准化（确保所有指标在同一量纲）
#         numeric_cols = df_norm.select_dtypes(include=[np.number]).columns
#         final_scaler = StandardScaler()
#         df_norm[numeric_cols] = final_scaler.fit_transform(df_norm[numeric_cols])
#
#         return df_norm
#
#
# class BasketballPlayerAnalyzer:
#     """篮球球员数据分析器：PCA+熵权法混合权重分析"""
#
#     def __init__(self, df, alpha=0.5, pos=None):
#         self.df = df.copy()
#         self.alpha = alpha
#         self.pos = pos  # 保存位置信息
#         self.normalizer = SimpleBasketballNormalizer()
#
#     def preprocess_data(self):
#         """数据预处理：选择数值列并智能归一化"""
#         non_numeric_cols = ['Rk', 'Player', 'Team', 'Pos']
#         self.numeric_columns = [col for col in self.df.columns
#                                 if col not in non_numeric_cols
#                                 and self.df[col].dtype in ['int64', 'float64']]
#
#         # 分离数值数据
#         self.X = self.df[self.numeric_columns].values
#
#         # 使用智能归一化
#         df_normalized = self.normalizer.normalize_dataframe(self.df[self.numeric_columns], self.pos)
#         self.X_scaled = df_normalized.values
#
#         # 保存标准化器供后续使用
#         self.scaler = StandardScaler()
#         self.scaler.fit(self.X_scaled)  # 仅用于兼容性
#
#     def pca_analysis(self, variance_threshold=0.85):
#         """主成分分析"""
#         self.pca = PCA()
#         self.X_pca = self.pca.fit_transform(self.X_scaled)
#         self.explained_variance_ratio = self.pca.explained_variance_ratio_
#         self.cumulative_variance = np.cumsum(self.explained_variance_ratio)
#         self.n_components = np.where(self.cumulative_variance > variance_threshold)[0][0] + 1
#         self.calculate_pca_weights()
#
#     def calculate_pca_weights(self):
#         """计算PCA权重"""
#         pca_weights = np.zeros(len(self.numeric_columns))
#         for i in range(self.n_components):
#             pca_weights += self.explained_variance_ratio[i] * np.abs(self.pca.components_[i])
#         self.pca_weights_normalized = pca_weights / pca_weights.sum()
#         self.pca_weight_dict = dict(zip(self.numeric_columns, self.pca_weights_normalized))
#
#     def entropy_weight_analysis(self):
#         """熵权法分析"""
#         positive_indicators = ['FG', 'FG.1', '3P', '3PP', '2P', '2PP', 'eFG',
#                                'FT', 'FT.1', 'ORB', 'DRB', 'TRB', 'AST', 'STL',
#                                'BLK', 'PTS', 'ORtg', 'G', 'GS', 'MP']
#         negative_indicators = ['TOV', 'PF', 'DRtg']
#
#         X_for_entropy = self.X_scaled.copy().astype(float)
#
#         # 对逆向指标进行倒置处理
#         for i, col in enumerate(self.numeric_columns):
#             if col in negative_indicators:
#                 col_data = self.X_scaled[:, i]
#                 # 对于已经处理过的DRtg，确保正向化
#                 if col == 'DRtg':
#                     X_for_entropy[:, i] = col_data  # DRtg已经正向化
#                 else:
#                     # 其他逆向指标：值越小越好，所以取负
#                     X_for_entropy[:, i] = -col_data
#
#         # 归一化到[0,1]用于熵权计算
#         min_vals = np.min(X_for_entropy, axis=0)
#         max_vals = np.max(X_for_entropy, axis=0)
#         ranges = max_vals - min_vals
#         ranges[ranges == 0] = 1  # 防止除0
#
#         X_normalized = (X_for_entropy - min_vals) / ranges
#
#         # 计算熵值
#         entropy_values = np.zeros(len(self.numeric_columns))
#         for j in range(len(self.numeric_columns)):
#             p = X_normalized[:, j] / np.sum(X_normalized[:, j])
#             p = p[p > 0]  # 移除0值
#             if len(p) > 0:
#                 entropy_values[j] = entropy(p) / np.log(len(p))
#             else:
#                 entropy_values[j] = 0
#
#         # 计算权重
#         diversity = 1 - entropy_values
#         self.entropy_weights_normalized = diversity / np.sum(diversity)
#         self.entropy_weight_dict = dict(zip(self.numeric_columns, self.entropy_weights_normalized))
#
#     def calculate_mixed_weights(self):
#         """计算混合权重"""
#         self.mixed_weights = (self.alpha * self.entropy_weights_normalized +
#                               (1 - self.alpha) * self.pca_weights_normalized)
#         self.mixed_weights_normalized = self.mixed_weights / np.sum(self.mixed_weights)
#         self.mixed_weight_dict = dict(zip(self.numeric_columns, self.mixed_weights_normalized))
#
#         # 创建权重比较表
#         sorted_weights = sorted(self.mixed_weight_dict.items(), key=lambda x: x[1], reverse=True)[:10]
#         self.weight_comparison = pd.DataFrame({
#             '指标': [item[0] for item in sorted_weights],
#             '混合权重': [item[1] for item in sorted_weights],
#             'PCA权重': [self.pca_weight_dict[item[0]] for item in sorted_weights],
#             '熵权权重': [self.entropy_weight_dict[item[0]] for item in sorted_weights]
#         })
#
#     def calculate_player_scores(self):
#         """计算球员综合得分"""
#         # 对于逆向指标，在最终得分计算时取负
#         negative_indicators = ['TOV', 'PF']
#         X_for_scoring = self.X_scaled.copy()
#
#         for i, col in enumerate(self.numeric_columns):
#             if col in negative_indicators:
#                 X_for_scoring[:, i] = -X_for_scoring[:, i]  # 逆向指标取负
#
#         # 使用混合权重计算得分
#         player_scores = X_for_scoring @ self.mixed_weights_normalized
#
#         # 归一化到0-100分
#         min_score, max_score = np.min(player_scores), np.max(player_scores)
#         if max_score > min_score:
#             player_scores_normalized = 100 * (player_scores - min_score) / (max_score - min_score)
#         else:
#             player_scores_normalized = np.full_like(player_scores, 50)  # 所有球员50分
#
#         self.df['综合得分'] = player_scores_normalized
#         self.df_sorted = self.df.sort_values('综合得分', ascending=False).reset_index(drop=True)
#
#     def analyze_by_position(self):
#         """按位置分析"""
#         if 'Pos' in self.df.columns:
#             self.position_stats = self.df.groupby('Pos')['综合得分'].agg(['mean', 'std', 'count'])
#
#     def create_summary_visualization(self):
#         """创建汇总可视化图表"""
#         fig, axes = plt.subplots(2, 3, figsize=(16, 10))
#
#         # 图1: PCA方差解释率
#         ax1 = axes[0, 0]
#         components = range(1, len(self.explained_variance_ratio) + 1)
#         ax1.bar(components[:10], self.explained_variance_ratio[:10], alpha=0.6, color='steelblue')
#         ax1.plot(components[:10], self.cumulative_variance[:10], 'r-', marker='o', linewidth=2)
#         ax1.axhline(y=0.85, color='g', linestyle='--', alpha=0.5, linewidth=1.5)
#         ax1.set_xlabel('主成分')
#         ax1.set_ylabel('方差解释率')
#         ax1.set_title(f'PCA方差解释率 ({self.pos})')
#         ax1.grid(True, alpha=0.3)
#         ax1.legend(['累积解释率', '85%阈值'], loc='lower right')
#
#         # 图2: 混合权重前10指标
#         ax2 = axes[0, 1]
#         top_features = self.weight_comparison.head(10)
#         y_pos = np.arange(len(top_features))
#         colors = plt.cm.Set3(np.linspace(0, 1, len(top_features)))
#         ax2.barh(y_pos, top_features['混合权重'], color=colors)
#         ax2.set_yticks(y_pos)
#         ax2.set_yticklabels(top_features['指标'])
#         ax2.invert_yaxis()
#         ax2.set_xlabel('权重')
#         ax2.set_title(f'混合权重前10指标 ({self.pos})')
#
#         # 在条上添加权重值
#         for i, v in enumerate(top_features['混合权重']):
#             ax2.text(v + 0.002, i, f'{v:.3f}', va='center')
#
#         # 图3: PCA vs 熵权法权重比较
#         ax3 = axes[0, 2]
#         comparison_sample = self.weight_comparison.head(8)
#         x = np.arange(len(comparison_sample))
#         width = 0.35
#         ax3.bar(x - width / 2, comparison_sample['PCA权重'], width,
#                 label='PCA权重', alpha=0.7, color='lightblue')
#         ax3.bar(x + width / 2, comparison_sample['熵权权重'], width,
#                 label='熵权权重', alpha=0.7, color='lightcoral')
#         ax3.set_xticks(x)
#         ax3.set_xticklabels(comparison_sample['指标'], rotation=45, ha='right')
#         ax3.set_ylabel('权重')
#         ax3.set_title(f'PCA权重 vs 熵权权重 ({self.pos})')
#         ax3.legend()
#         ax3.grid(True, alpha=0.3, axis='y')
#
#         # 图4: 球员得分分布
#         ax4 = axes[1, 0]
#         n_bins = min(30, len(self.df) // 5)
#         ax4.hist(self.df['综合得分'], bins=n_bins, edgecolor='black',
#                  alpha=0.7, color='skyblue', density=True)
#
#         # 添加核密度估计
#         from scipy.stats import gaussian_kde
#         score_data = self.df['综合得分'].dropna()
#         if len(score_data) > 1:
#             kde = gaussian_kde(score_data)
#             x_range = np.linspace(score_data.min(), score_data.max(), 100)
#             ax4.plot(x_range, kde(x_range), 'r-', linewidth=2, alpha=0.8)
#
#         ax4.axvline(self.df['综合得分'].mean(), color='red', linestyle='--',
#                     label=f'平均分: {self.df["综合得分"].mean():.1f}', linewidth=2)
#         ax4.set_xlabel('综合得分')
#         ax4.set_ylabel('密度')
#         ax4.set_title(f'球员综合得分分布 ({self.pos})')
#         ax4.legend()
#         ax4.grid(True, alpha=0.3)
#
#         # 图5: 位置平均得分（如果有多位置数据）
#         ax5 = axes[1, 1]
#         if hasattr(self, 'position_stats') and len(self.position_stats) > 1:
#             positions = self.position_stats.index
#             means = self.position_stats['mean']
#             colors = plt.cm.tab10(np.linspace(0, 1, len(positions)))
#             bars = ax5.bar(positions, means, alpha=0.7, color=colors)
#             ax5.set_xlabel('位置')
#             ax5.set_ylabel('平均得分')
#             ax5.set_title('各位置平均综合得分')
#
#             # 添加误差条
#             stds = self.position_stats['std']
#             ax5.errorbar(positions, means, yerr=stds, fmt='none',
#                          ecolor='black', capsize=5, alpha=0.7)
#
#             for bar, mean in zip(bars, means):
#                 height = bar.get_height()
#                 ax5.text(bar.get_x() + bar.get_width() / 2., height, f'{mean:.1f}',
#                          ha='center', va='bottom', fontweight='bold')
#         else:
#             # 如果没有多位置数据，显示前10名球员雷达图
#             self.plot_top_players_radar(ax5)
#
#         # 图6: 综合得分前10名球员
#         ax6 = axes[1, 2]
#         top_10 = self.df_sorted.head(10)
#         y_pos = np.arange(len(top_10))
#         colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_10)))
#         bars = ax6.barh(y_pos, top_10['综合得分'], color=colors, alpha=0.8)
#         ax6.set_yticks(y_pos)
#
#         # 截断长名字
#         player_names = [name[:15] + '...' if len(name) > 15 else name
#                         for name in top_10['Player']]
#         ax6.set_yticklabels(player_names)
#         ax6.invert_yaxis()
#         ax6.set_xlabel('综合得分')
#         ax6.set_title(f'综合得分前10名 ({self.pos})')
#
#         # 在条上添加得分
#         for bar, score in zip(bars, top_10['综合得分']):
#             width = bar.get_width()
#             ax6.text(width + 0.5, bar.get_y() + bar.get_height() / 2.,
#                      f'{score:.1f}', ha='left', va='center')
#
#         plt.tight_layout()
#         # plt.savefig(f'analysis_summary_{self.pos}.png', dpi=150, bbox_inches='tight')
#         plt.show()
#
#     def plot_top_players_radar(self, ax):
#         """绘制前5名球员的雷达图"""
#         if len(self.df_sorted) < 5:
#             return
#
#         top_5 = self.df_sorted.head(5)
#
#         # 选择6个关键指标
#         key_metrics = ['PTS', 'AST', 'TRB', 'STL', 'BLK', '综合得分']
#         available_metrics = [m for m in key_metrics if m in self.df.columns]
#
#         if len(available_metrics) < 3:
#             ax.text(0.5, 0.5, '数据不足生成雷达图',
#                     ha='center', va='center', transform=ax.transAxes)
#             ax.set_title('关键指标雷达图')
#             return
#
#         # 标准化指标数据
#         from sklearn.preprocessing import MinMaxScaler
#         scaler = MinMaxScaler()
#         metrics_data = top_5[available_metrics].values
#         metrics_scaled = scaler.fit_transform(metrics_data)
#
#         # 雷达图设置
#         angles = np.linspace(0, 2 * np.pi, len(available_metrics), endpoint=False).tolist()
#         angles += angles[:1]  # 闭合
#
#         # 绘制每个球员
#         colors = plt.cm.tab10(np.linspace(0, 1, len(top_5)))
#         for idx, (_, player) in enumerate(top_5.iterrows()):
#             values = metrics_scaled[idx].tolist()
#             values += values[:1]  # 闭合
#
#             ax.plot(angles, values, 'o-', linewidth=2, label=player['Player'][:10],
#                     color=colors[idx], alpha=0.7)
#             ax.fill(angles, values, color=colors[idx], alpha=0.1)
#
#         # 设置坐标轴
#         ax.set_xticks(angles[:-1])
#         ax.set_xticklabels(available_metrics)
#         ax.set_title('前5名球员关键指标对比')
#         ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
#         ax.grid(True)
#
#     def run_analysis(self):
#         """运行完整分析流程"""
#         self.preprocess_data()
#         self.pca_analysis()
#         self.entropy_weight_analysis()
#         self.calculate_mixed_weights()
#         self.calculate_player_scores()
#         self.analyze_by_position()
#         self.create_summary_visualization()
#
#         print(f"\n位置: {self.pos}")
#         print(f"球员数: {len(self.df)}")
#         print(f"主成分数: {self.n_components}")
#         print(f"累积方差: {self.cumulative_variance[self.n_components - 1]:.1%}")
#         print(f"最高分: {self.df['综合得分'].max():.1f}")
#         print(f"最低分: {self.df['综合得分'].min():.1f}")
#         print(f"平均分: {self.df['综合得分'].mean():.1f}")
#         print(f"标准差: {self.df['综合得分'].std():.1f}")
#         print(f"前5指标: {', '.join(self.weight_comparison['指标'].head(5).tolist())}")
#         print(f"\n前3名球员:")
#         for i, row in self.df_sorted.head(3).iterrows():
#             print(f"  {i + 1}. {row['Player']}: {row['综合得分']:.1f}分")
#
#         return self.df_sorted
#
#
# def analyze_all_positions():
#     """分析所有位置数据并创建跨位置比较图"""
#     positions = ['PG', 'SG', 'SF', 'PF', 'C']
#     all_results = {}
#
#     # 第一步：分别分析每个位置
#     for pos in positions:
#         file_name = f"Pos_{pos}2526.xlsx"
#         if os.path.exists(file_name):
#             print(f"\n{'=' * 60}")
#             print(f"分析位置: {pos}")
#             print(f"{'=' * 60}")
#
#             df = pd.read_excel(file_name)
#             analyzer = BasketballPlayerAnalyzer(df, alpha=0.5, pos=pos)
#             result_df = analyzer.run_analysis()
#             all_results[pos] = result_df
#
#             # 保存结果
#             result_df.to_csv(f'results_{pos}.csv', index=False, encoding='utf-8-sig')
#             print(f"结果已保存至 results_{pos}.csv")
#         else:
#             print(f"文件 {file_name} 不存在，跳过")
#
#     # 第二步：创建跨位置比较图
#     if all_results:
#         create_cross_position_comparison(all_results)
#
#         # 汇总所有位置结果
#         all_players = pd.concat(all_results.values(), ignore_index=True)
#         all_players_sorted = all_players.sort_values('综合得分', ascending=False).reset_index(drop=True)
#
#         print(f"\n{'=' * 60}")
#         print("全位置综合排名前20:")
#         print(f"{'=' * 60}")
#         print(all_players_sorted[['Player', 'Pos', 'Team', '综合得分']].head(20).to_string(index=False))
#
#         all_players_sorted.to_csv('all_players_ranked.csv', index=False, encoding='utf-8-sig')
#         print(f"\n全位置排名已保存至 all_players_ranked.csv")
#
#     return all_results
#
#
# def create_cross_position_comparison(all_results):
#     """创建跨位置比较的可视化图表"""
#     print("\n创建跨位置比较图...")
#
#     # 准备数据
#     position_data = {}
#     for pos, df in all_results.items():
#         position_data[pos] = df
#
#     # 创建跨位置比较图
#     fig, axes = plt.subplots(2, 3, figsize=(18, 12))
#
#     # 图1: 各位置得分分布比较
#     ax1 = axes[0, 0]
#     colors = plt.cm.tab10(np.linspace(0, 1, len(position_data)))
#
#     for idx, (pos, df) in enumerate(position_data.items()):
#         if '综合得分' in df.columns:
#             scores = df['综合得分'].dropna()
#             # 使用核密度估计
#             from scipy.stats import gaussian_kde
#             if len(scores) > 1:
#                 kde = gaussian_kde(scores)
#                 x_range = np.linspace(0, 100, 200)
#                 ax1.plot(x_range, kde(x_range), label=pos,
#                          color=colors[idx], linewidth=2, alpha=0.8)
#
#     ax1.set_xlabel('综合得分')
#     ax1.set_ylabel('密度')
#     ax1.set_title('各位置综合得分分布比较')
#     ax1.legend()
#     ax1.grid(True, alpha=0.3)
#
#     # 图2: 各位置平均得分
#     ax2 = axes[0, 1]
#     position_stats = []
#     positions_list = []
#
#     for pos, df in position_data.items():
#         if '综合得分' in df.columns:
#             positions_list.append(pos)
#             position_stats.append({
#                 'mean': df['综合得分'].mean(),
#                 'std': df['综合得分'].std(),
#                 'count': len(df)
#             })
#
#     if position_stats:
#         means = [stat['mean'] for stat in position_stats]
#         stds = [stat['std'] for stat in position_stats]
#
#         bars = ax2.bar(positions_list, means, alpha=0.7, color=colors[:len(positions_list)])
#         ax2.errorbar(positions_list, means, yerr=stds, fmt='none',
#                      ecolor='black', capsize=5, alpha=0.7)
#         ax2.set_xlabel('位置')
#         ax2.set_ylabel('平均得分')
#         ax2.set_title('各位置平均综合得分')
#         ax2.grid(True, alpha=0.3, axis='y')
#
#         # 在柱子上添加数值
#         for bar, mean, count in zip(bars, means, [stat['count'] for stat in position_stats]):
#             height = bar.get_height()
#             ax2.text(bar.get_x() + bar.get_width() / 2., height,
#                      f'{mean:.1f}\n(n={count})', ha='center', va='bottom')
#
#     # 图3: 关键指标箱线图比较（选择3个关键指标）
#     ax3 = axes[0, 2]
#     key_metrics = ['PTS', 'AST', 'TRB']
#     available_metrics = []
#
#     # 检查哪些指标在所有位置都存在
#     for metric in key_metrics:
#         if all(metric in df.columns for df in position_data.values()):
#             available_metrics.append(metric)
#
#     if available_metrics:
#         # 为每个指标创建一个子图
#         for i, metric in enumerate(available_metrics):
#             data_to_plot = []
#             pos_labels = []
#             for pos, df in position_data.items():
#                 if metric in df.columns:
#                     data_to_plot.append(df[metric].dropna().values)
#                     pos_labels.append(pos)
#
#             # 使用小提琴图展示分布
#             positions_idx = np.arange(len(pos_labels))
#             vp = ax3.violinplot(data_to_plot, positions=positions_idx,
#                                 showmeans=True, showmedians=True)
#
#             # 设置颜色
#             for pc in vp['bodies']:
#                 pc.set_facecolor(colors[i % len(colors)])
#                 pc.set_alpha(0.7)
#
#             ax3.set_xticks(positions_idx)
#             ax3.set_xticklabels(pos_labels)
#             ax3.set_ylabel(metric)
#             ax3.set_title(f'{metric}分布比较')
#             ax3.grid(True, alpha=0.3)
#
#     # 图4: 各位置顶级球员对比
#     ax4 = axes[1, 0]
#     top_players_by_pos = {}
#
#     for pos, df in position_data.items():
#         if '综合得分' in df.columns and 'Player' in df.columns:
#             top_player = df.nlargest(1, '综合得分').iloc[0]
#             top_players_by_pos[pos] = {
#                 'name': top_player['Player'],
#                 'score': top_player['综合得分'],
#                 'team': top_player.get('Team', 'N/A')
#             }
#
#     if top_players_by_pos:
#         positions = list(top_players_by_pos.keys())
#         names = [top_players_by_pos[pos]['name'][:15] + '...'
#                  if len(top_players_by_pos[pos]['name']) > 15
#                  else top_players_by_pos[pos]['name']
#                  for pos in positions]
#         scores = [top_players_by_pos[pos]['score'] for pos in positions]
#
#         y_pos = np.arange(len(positions))
#         bars = ax4.barh(y_pos, scores, color=plt.cm.viridis(np.linspace(0.3, 0.9, len(positions))))
#         ax4.set_yticks(y_pos)
#         ax4.set_yticklabels([f"{pos}\n{name}" for pos, name in zip(positions, names)])
#         ax4.invert_yaxis()
#         ax4.set_xlabel('综合得分')
#         ax4.set_title('各位置最佳球员')
#
#         # 添加得分和球队信息
#         for bar, score, pos in zip(bars, scores, positions):
#             width = bar.get_width()
#             team = top_players_by_pos[pos]['team']
#             ax4.text(width + 0.5, bar.get_y() + bar.get_height() / 2.,
#                      f'{score:.1f} ({team})', ha='left', va='center')
#
#     # 图5: 指标权重对比（选择共同的关键指标）
#     ax5 = axes[1, 1]
#     # 这里需要从每个位置的权重信息中提取数据
#     # 由于权重信息在每个analyzer对象中，这里简化处理
#     ax5.text(0.5, 0.5, '指标权重对比\n（需要存储各位置权重信息）',
#              ha='center', va='center', transform=ax5.transAxes, fontsize=12)
#     ax5.set_title('各位置指标权重对比')
#     ax5.axis('off')
#
#     # 图6: 各位置球员数量分布
#     ax6 = axes[1, 2]
#     positions = list(position_data.keys())
#     counts = [len(df) for df in position_data.values()]
#
#     wedges, texts, autotexts = ax6.pie(counts, labels=positions, autopct='%1.1f%%',
#                                        colors=colors[:len(positions)], startangle=90)
#
#     # 美化饼图
#     for autotext in autotexts:
#         autotext.set_color('white')
#         autotext.set_fontweight('bold')
#
#     ax6.set_title('各位置球员数量分布')
#
#     plt.tight_layout()
#     # plt.savefig('cross_position_comparison.png', dpi=150, bbox_inches='tight')
#     plt.show()
#
#     print("跨位置比较图已保存至 cross_position_comparison.png")
#
#
# if __name__ == "__main__":
#     # 分析所有位置
#     results = analyze_all_positions()
#
#     if results:
#         print(f"\n分析完成！共分析了 {len(results)} 个位置")
#         print("生成的文件：")
#         for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
#             if pos in results:
#                 print(f"  - results_{pos}.csv")
#         print("  - all_players_ranked.csv")
#         print("  - analysis_summary_<pos>.png (各位置分析图)")
#         print("  - cross_position_comparison.png (跨位置比较图)")


import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import entropy
import os


class FactorImportanceAnalyzer:
    """因素重要性分析器：PCA+熵权法混合权重分析"""

    def __init__(self, df, alpha=0.5):
        self.df = df.copy()
        self.alpha = alpha  # 混合权重参数
        self.factor_importance = {}  # 存储因素重要性排名

    def preprocess_data(self):
        """数据预处理：选择数值列并标准化"""
        non_numeric_cols = ['Rk', 'Player', 'Team', 'Pos']
        self.numeric_columns = [col for col in self.df.columns
                                if col not in non_numeric_cols
                                and self.df[col].dtype in ['int64', 'float64']]

        self.X = self.df[self.numeric_columns].values

        # 简单标准化（保持原算法）
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)

    def calculate_pca_weights(self, variance_threshold=0.85):
        """计算PCA权重"""
        pca = PCA()
        X_pca = pca.fit_transform(self.X_scaled)

        # 确定主成分数量
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        n_components = np.where(cumulative_variance > variance_threshold)[0][0] + 1

        # 计算PCA权重
        pca_weights = np.zeros(len(self.numeric_columns))
        for i in range(n_components):
            pca_weights += pca.explained_variance_ratio_[i] * np.abs(pca.components_[i])

        # 归一化
        if pca_weights.sum() > 0:
            self.pca_weights_normalized = pca_weights / pca_weights.sum()
        else:
            self.pca_weights_normalized = np.ones_like(pca_weights) / len(pca_weights)

        self.pca_weight_dict = dict(zip(self.numeric_columns, self.pca_weights_normalized))

        # 保存PCA信息
        self.n_components = n_components
        self.cumulative_variance = cumulative_variance[n_components - 1]

    def calculate_entropy_weights(self):
        """计算熵权法权重"""
        # 识别逆向指标
        negative_indicators = ['TOV', 'PF', 'DRtg']

        X_for_entropy = self.X.copy().astype(float)

        # 处理逆向指标
        for i, col in enumerate(self.numeric_columns):
            if col in negative_indicators:
                col_data = self.X[:, i]
                min_val = np.min(col_data)
                if min_val <= 0:
                    col_data = col_data - min_val + 1e-10
                X_for_entropy[:, i] = 1.0 / col_data

        # 归一化到[0,1]
        min_vals = np.min(X_for_entropy, axis=0)
        max_vals = np.max(X_for_entropy, axis=0)
        ranges = max_vals - min_vals
        ranges[ranges == 0] = 1

        X_normalized = (X_for_entropy - min_vals) / ranges

        # 计算熵值
        entropy_values = np.zeros(len(self.numeric_columns))
        for j in range(len(self.numeric_columns)):
            p = X_normalized[:, j] / np.sum(X_normalized[:, j])
            p = p[p > 0]
            if len(p) > 0:
                entropy_values[j] = entropy(p) / np.log(len(p))
            else:
                entropy_values[j] = 0

        # 计算权重
        diversity = 1 - entropy_values
        if diversity.sum() > 0:
            self.entropy_weights_normalized = diversity / diversity.sum()
        else:
            self.entropy_weights_normalized = np.ones_like(diversity) / len(diversity)

        self.entropy_weight_dict = dict(zip(self.numeric_columns, self.entropy_weights_normalized))

    def calculate_mixed_weights(self):
        """计算混合权重：alpha * 熵权权重 + (1-alpha) * PCA权重"""
        self.mixed_weights = (self.alpha * self.entropy_weights_normalized +
                              (1 - self.alpha) * self.pca_weights_normalized)

        # 归一化
        if self.mixed_weights.sum() > 0:
            self.mixed_weights_normalized = self.mixed_weights / self.mixed_weights.sum()
        else:
            self.mixed_weights_normalized = np.ones_like(self.mixed_weights) / len(self.mixed_weights)

        self.mixed_weight_dict = dict(zip(self.numeric_columns, self.mixed_weights_normalized))

        # 按混合权重排序
        self.sorted_factors = sorted(self.mixed_weight_dict.items(),
                                     key=lambda x: x[1], reverse=True)

    def get_factor_importance_ranking(self, top_n=10):
        """获取因素重要性排名"""
        ranking = []
        for i, (factor, weight) in enumerate(self.sorted_factors[:top_n], 1):
            ranking.append({
                '排名': i,
                '因素': factor,
                '混合权重': weight,
                'PCA权重': self.pca_weight_dict[factor],
                '熵权权重': self.entropy_weight_dict[factor]
            })

        return pd.DataFrame(ranking)

    def get_factor_statistics(self):
        """获取各因素的统计信息"""
        stats_list = []

        for factor in self.numeric_columns:
            idx = self.numeric_columns.index(factor)
            data = self.X[:, idx]

            stats = {
                '因素': factor,
                '平均值': np.mean(data),
                '标准差': np.std(data),
                '最小值': np.min(data),
                '最大值': np.max(data),
                '中位数': np.median(data),
                '混合权重': self.mixed_weight_dict.get(factor, 0),
                'PCA权重': self.pca_weight_dict.get(factor, 0),
                '熵权权重': self.entropy_weight_dict.get(factor, 0)
            }
            stats_list.append(stats)

        stats_df = pd.DataFrame(stats_list)

        # 按混合权重排序
        stats_df = stats_df.sort_values('混合权重', ascending=False)
        stats_df.insert(0, '排名', range(1, len(stats_df) + 1))

        return stats_df

    def analyze(self):
        """运行完整分析"""
        print(f"分析开始，数据量: {len(self.df)}")

        # 1. 数据预处理
        self.preprocess_data()
        print(f"数值特征数量: {len(self.numeric_columns)}")

        # 2. 计算PCA权重
        self.calculate_pca_weights()
        print(f"PCA主成分数: {self.n_components}")
        print(f"PCA累积方差: {self.cumulative_variance:.1%}")

        # 3. 计算熵权法权重
        self.calculate_entropy_weights()
        print("熵权法权重计算完成")

        # 4. 计算混合权重
        self.calculate_mixed_weights()
        print(f"混合权重计算完成 (alpha={self.alpha})")

        # 5. 获取分析结果
        importance_df = self.get_factor_importance_ranking(top_n=10)
        stats_df = self.get_factor_statistics()

        return importance_df, stats_df


def analyze_position(pos, alpha=0.5):
    """分析单个位置"""
    file_name = f"Pos_{pos}2526.xlsx"

    if not os.path.exists(file_name):
        print(f"文件 {file_name} 不存在，跳过")
        return None

    print(f"\n{'=' * 60}")
    print(f"分析位置: {pos}")
    print(f"{'=' * 60}")

    # 加载数据
    df = pd.read_excel(file_name)

    # 分析
    analyzer = FactorImportanceAnalyzer(df, alpha=alpha)
    importance_df, stats_df = analyzer.analyze()

    # 保存结果
    importance_df.to_csv(f'importance_{pos}.csv', index=False, encoding='utf-8-sig')
    stats_df.to_csv(f'stats_{pos}.csv', index=False, encoding='utf-8-sig')

    # 打印前10个重要因素
    print(f"\n{pos}位置 - 前10重要因素:")
    print(importance_df[['排名', '因素', '混合权重']].to_string(index=False))

    print(f"\n结果已保存:")
    print(f"  - importance_{pos}.csv (因素重要性排名)")
    print(f"  - stats_{pos}.csv (详细统计数据)")

    return analyzer


def analyze_all_positions(alpha=0.5):
    """分析所有位置"""
    positions = ['PG', 'SG', 'SF', 'PF', 'C']
    results = {}

    for pos in positions:
        analyzer = analyze_position(pos, alpha)
        if analyzer:
            results[pos] = analyzer

    # 创建汇总表
    if results:
        create_summary_table(results)

    return results


def create_summary_table(results):
    """创建所有位置的汇总表"""
    summary_data = []

    for pos, analyzer in results.items():
        # 获取前5个重要因素
        importance_df = analyzer.get_factor_importance_ranking(top_n=5)

        for _, row in importance_df.iterrows():
            summary_data.append({
                '位置': pos,
                '排名': row['排名'],
                '因素': row['因素'],
                '混合权重': row['混合权重'],
                'PCA权重': row['PCA权重'],
                '熵权权重': row['熵权权重']
            })

    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('all_positions_summary.csv', index=False, encoding='utf-8-sig')

        print(f"\n{'=' * 60}")
        print("所有位置重要因素汇总:")
        print(f"{'=' * 60}")

        # 按位置分组显示
        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            if pos in results:
                pos_data = summary_df[summary_df['位置'] == pos]
                print(f"\n{pos}位置前5重要因素:")
                print(pos_data[['因素', '混合权重']].to_string(index=False))

        print(f"\n汇总表已保存: all_positions_summary.csv")


if __name__ == "__main__":
    # 设置混合权重参数（alpha为熵权法权重，1-alpha为PCA权重）
    ALPHA = 0.5  # 可以调整这个参数

    print("篮球球员因素重要性分析")
    print(f"混合权重参数: alpha={ALPHA} (熵权法), 1-alpha={1 - ALPHA} (PCA)")
    print("=" * 60)

    # 分析所有位置
    results = analyze_all_positions(alpha=ALPHA)

    if results:
        print(f"\n{'=' * 60}")
        print(f"分析完成！共分析了 {len(results)} 个位置")
        print("生成的文件：")
        for pos in ['PG', 'SG', 'SF', 'PF', 'C']:
            if pos in results:
                print(f"  - importance_{pos}.csv")
                print(f"  - stats_{pos}.csv")
        print("  - all_positions_summary.csv")
    else:
        print("未找到任何数据文件，请检查文件是否存在")

