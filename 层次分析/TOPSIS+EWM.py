# import numpy as np
# import pandas as pd
# from sklearn.decomposition import PCA
# from sklearn.preprocessing import StandardScaler
# import os
#
#
# class SimplePCA_TOPSIS:
#     """简化版PCA+TOPSIS分析（包含分类标准化）"""
#
#     def __init__(self, df, pos):
#         self.df = df
#         self.pos = pos
#
#     def classify_normalize(self):
#         """分类标准化"""
#         df_norm = self.df.copy()
#
#         # 1. 百分比指标：反正弦变换
#         percentage_cols = ['eFG']
#         for col in percentage_cols:
#             if col in df_norm.columns:
#                 data = df_norm[col].values.astype(float)
#                 # 处理异常值（0和1值）
#                 data = np.clip(data, 0.001, 0.999)
#                 df_norm[col] = np.arcsin(np.sqrt(data))
#
#         # 2. 计数指标：对数变换
#         count_cols = ['MP', 'FG', 'FGA', 'TOV', 'PF','TRB','G']
#         for col in count_cols:
#             if col in df_norm.columns:
#                 data = df_norm[col].values.astype(float)
#                 # 确保非负
#                 data = np.maximum(data, 0)
#                 df_norm[col] = np.log1p(data)
#
#         # 3. 效率指标：ORtg直接使用，DRtg特殊处理
#         if 'ORtg' in df_norm.columns:
#             # ORtg已经是正向指标，保持原值
#             pass
#
#         if 'DRtg' in df_norm.columns:
#             # DRtg是逆向指标：值越小越好
#             data = df_norm['DRtg'].values.astype(float)
#             # 倒置处理：DRtg越小越好，所以用最大值减
#             max_val = np.max(data[data > 0]) if np.any(data > 0) else 130
#             df_norm['DRtg'] = max_val - data
#             # 按位置放大差异
#             if self.pos == 'C':
#                 df_norm['DRtg'] = np.power(df_norm['DRtg'], 1.5)
#             elif self.pos == 'PG':
#                 df_norm['DRtg'] = np.power(df_norm['DRtg'], 1.2)
#
#         # 4. 逆向指标（除了DRtg）：取负值
#         negative_cols = ['TOV', 'PF']
#         for col in negative_cols:
#             if col in df_norm.columns:
#                 df_norm[col] = -df_norm[col]
#
#         # 5. 排除非数值列
#         exclude_cols = ['Rk', 'Player', 'Team', 'Pos', 'Age','MP']
#         numeric_cols = [col for col in df_norm.columns
#                         if col not in exclude_cols and pd.api.types.is_numeric_dtype(df_norm[col])]
#
#         # 6. 最后统一Z-score标准化
#         if numeric_cols:
#             scaler = StandardScaler()
#             df_norm[numeric_cols] = scaler.fit_transform(df_norm[numeric_cols])
#
#         return df_norm, numeric_cols
#
#     def analyze(self):
#         """执行PCA+TOPSIS分析"""
#         print(f"\n{'=' * 60}")
#         print(f"位置: {self.pos}")
#
#         # 1. 分类标准化
#         df_norm, numeric_cols = self.classify_normalize()
#         print(f"可用指标 ({len(numeric_cols)}个):")
#         for i, col in enumerate(numeric_cols):
#             print(f"  {i + 1:2d}. {col}")
#
#         # 2. 提取数据
#         X = df_norm[numeric_cols].values
#         players = self.df['Player'].values if 'Player' in self.df.columns else [f"Player_{i}" for i in
#                                                                                 range(len(self.df))]
#
#         # 3. PCA计算权重
#         pca = PCA()
#         pca.fit(X)
#
#         # 累积方差85%的主成分数
#         cum_var = np.cumsum(pca.explained_variance_ratio_)
#         n_comp = np.where(cum_var > 0.85)[0][0] + 1
#
#         print(f"\nPCA信息:")
#         print(f"  主成分数: {n_comp}")
#         print(f"  累积方差: {cum_var[n_comp - 1]:.2%}")
#
#         # 计算PCA权重
#         weights = np.zeros(len(numeric_cols))
#         for i in range(n_comp):
#             weights += pca.explained_variance_ratio_[i] * np.abs(pca.components_[i])
#         weights = weights / weights.sum()
#
#         # 4. 输出权重排序
#         print(f"\n指标权重排序:")
#         sorted_idx = np.argsort(-weights)
#         total_weight = 0
#         for i, idx in enumerate(sorted_idx):
#             weight = weights[idx]
#             total_weight += weight
#             weight_pct = weight * 100
#             cum_pct = total_weight * 100
#             print(f"  {i + 1:2d}. {numeric_cols[idx]:10s}: {weight:.4f} ({weight_pct:5.1f}%) [累积: {cum_pct:5.1f}%]")
#
#         # 5. TOPSIS评分
#         # 应用权重
#         X_weighted = X * weights
#
#         # 确定正负理想解（所有指标都已经正向化）
#         pos_ideal = np.max(X_weighted, axis=0)
#         neg_ideal = np.min(X_weighted, axis=0)
#
#         # 计算得分
#         scores = []
#         for i in range(len(X_weighted)):
#             d_pos = np.sqrt(np.sum((X_weighted[i] - pos_ideal) ** 2))
#             d_neg = np.sqrt(np.sum((X_weighted[i] - neg_ideal) ** 2))
#             score = d_neg / (d_pos + d_neg) if (d_pos + d_neg) > 0 else 0
#             scores.append(score)
#
#         # 归一化到0-100
#         scores = np.array(scores)
#         min_score, max_score = scores.min(), scores.max()
#         if max_score > min_score:
#             scores_norm = 100 * (scores - min_score) / (max_score - min_score)
#         else:
#             scores_norm = np.full_like(scores, 50)
#
#         # 6. 输出球员排名（前15）
#         sorted_indices = np.argsort(-scores_norm)
#         print(f"\n球员排名 (前15):")
#         for i, idx in enumerate(sorted_indices[:15]):
#             player_name = players[idx]
#             # 截断长名字
#             display_name = player_name[:20] + "..." if len(player_name) > 23 else player_name.ljust(23)
#             print(f"  {i + 1:2d}. {display_name}: {scores_norm[idx]:6.1f}")
#
#         return weights, scores_norm
#
#
# def analyze_all():
#     """分析所有位置"""
#     positions = ['PG', 'SG', 'SF', 'PF', 'C']
#
#     for pos in positions:
#         file_path = f"Pos_{pos}2526.xlsx"
#         if os.path.exists(file_path):
#             try:
#                 df = pd.read_excel(file_path)
#                 analyzer = SimplePCA_TOPSIS(df, pos)
#                 analyzer.analyze()
#             except Exception as e:
#                 print(f"分析{pos}时出错: {e}")
#         else:
#             print(f"文件不存在: {file_path}")
#
#
# if __name__ == "__main__":
#     print("PCA+TOPSIS分析（包含分类标准化）")
#     print("=" * 60)
#     analyze_all()


import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import os
import json


class SimplePCA_TOPSIS:
    """简化版PCA+TOPSIS分析（包含分类标准化）"""

    def __init__(self, df, pos):
        self.df = df
        self.pos = pos

    def classify_normalize(self):
        """分类标准化"""
        df_norm = self.df.copy()

        # 1. 百分比指标：反正弦变换
        percentage_cols = ['eFG']
        for col in percentage_cols:
            if col in df_norm.columns:
                data = df_norm[col].values.astype(float)
                # 处理异常值（0和1值）
                data = np.clip(data, 0.001, 0.999)
                df_norm[col] = np.arcsin(np.sqrt(data))

        # 2. 计数指标：对数变换
        count_cols = ['MP', 'FG', 'FGA', 'TOV', 'PF', 'TRB', 'G']
        for col in count_cols:
            if col in df_norm.columns:
                data = df_norm[col].values.astype(float)
                # 确保非负
                data = np.maximum(data, 0)
                df_norm[col] = np.log1p(data)

        # 3. 效率指标：ORtg直接使用，DRtg特殊处理
        if 'ORtg' in df_norm.columns:
            # ORtg已经是正向指标，保持原值
            pass

        if 'DRtg' in df_norm.columns:
            # DRtg是逆向指标：值越小越好
            data = df_norm['DRtg'].values.astype(float)
            # 倒置处理：DRtg越小越好，所以用最大值减
            max_val = np.max(data[data > 0]) if np.any(data > 0) else 130
            df_norm['DRtg'] = max_val - data
            # 按位置放大差异
            if self.pos == 'C':
                df_norm['DRtg'] = np.power(df_norm['DRtg'], 1.5)
            elif self.pos == 'PG':
                df_norm['DRtg'] = np.power(df_norm['DRtg'], 1.2)

        # 4. 逆向指标（除了DRtg）：取负值
        negative_cols = ['TOV', 'PF']
        for col in negative_cols:
            if col in df_norm.columns:
                df_norm[col] = -df_norm[col]

        # 5. 排除非数值列
        exclude_cols = ['Rk', 'Player', 'Team', 'Pos', 'Age', 'MP']
        numeric_cols = [col for col in df_norm.columns
                        if col not in exclude_cols and pd.api.types.is_numeric_dtype(df_norm[col])]

        # 6. 最后统一Z-score标准化
        if numeric_cols:
            scaler = StandardScaler()
            df_norm[numeric_cols] = scaler.fit_transform(df_norm[numeric_cols])

            # === 新增：保存Z-score参数 ===
            self.zscore_means = {col: float(scaler.mean_[i]) for i, col in enumerate(numeric_cols)}
            self.zscore_stds = {col: float(scaler.scale_[i]) for i, col in enumerate(numeric_cols)}
            # ============================

        return df_norm, numeric_cols

    def analyze(self):
        """执行PCA+TOPSIS分析"""
        print(f"\n{'=' * 60}")
        print(f"位置: {self.pos}")

        # 1. 分类标准化
        df_norm, numeric_cols = self.classify_normalize()
        print(f"可用指标 ({len(numeric_cols)}个):")
        for i, col in enumerate(numeric_cols):
            print(f"  {i + 1:2d}. {col}")

        # 2. 提取数据
        X = df_norm[numeric_cols].values
        players = self.df['Player'].values if 'Player' in self.df.columns else [f"Player_{i}" for i in
                                                                                range(len(self.df))]

        # 3. PCA计算权重
        pca = PCA()
        pca.fit(X)

        # 累积方差85%的主成分数
        cum_var = np.cumsum(pca.explained_variance_ratio_)
        n_comp = np.where(cum_var > 0.85)[0][0] + 1

        print(f"\nPCA信息:")
        print(f"  主成分数: {n_comp}")
        print(f"  累积方差: {cum_var[n_comp - 1]:.2%}")

        # 计算PCA权重
        weights = np.zeros(len(numeric_cols))
        for i in range(n_comp):
            weights += pca.explained_variance_ratio_[i] * np.abs(pca.components_[i])
        weights = weights / weights.sum()

        # 4. 输出权重排序
        print(f"\n指标权重排序:")
        sorted_idx = np.argsort(-weights)
        total_weight = 0
        for i, idx in enumerate(sorted_idx):
            weight = weights[idx]
            total_weight += weight
            weight_pct = weight * 100
            cum_pct = total_weight * 100
            print(f"  {i + 1:2d}. {numeric_cols[idx]:10s}: {weight:.4f} ({weight_pct:5.1f}%) [累积: {cum_pct:5.1f}%]")

        # 5. TOPSIS评分
        # 应用权重
        X_weighted = X * weights

        # 确定正负理想解（所有指标都已经正向化）
        pos_ideal = np.max(X_weighted, axis=0)
        neg_ideal = np.min(X_weighted, axis=0)

        # 计算得分
        scores = []
        for i in range(len(X_weighted)):
            d_pos = np.sqrt(np.sum((X_weighted[i] - pos_ideal) ** 2))
            d_neg = np.sqrt(np.sum((X_weighted[i] - neg_ideal) ** 2))
            score = d_neg / (d_pos + d_neg) if (d_pos + d_neg) > 0 else 0
            scores.append(score)

        # 归一化到0-100
        scores = np.array(scores)
        min_score, max_score = scores.min(), scores.max()
        if max_score > min_score:
            scores_norm = 100 * (scores - min_score) / (max_score - min_score)
        else:
            scores_norm = np.full_like(scores, 50)

        # 6. 输出球员排名（前15）
        sorted_indices = np.argsort(-scores_norm)
        print(f"\n球员排名 (前15):")
        for i, idx in enumerate(sorted_indices[:15]):
            player_name = players[idx]
            # 截断长名字
            display_name = player_name[:20] + "..." if len(player_name) > 23 else player_name.ljust(23)
            print(f"  {i + 1:2d}. {display_name}: {scores_norm[idx]:6.1f}")

        # === 新增：返回标准化参数 ===
        zscore_params = {
            'means': self.zscore_means,
            'stds': self.zscore_stds,
            'drtg_max': float(np.max(self.df['DRtg'].values[self.df['DRtg'] > 0])) if 'DRtg' in self.df.columns else 130
        }
        # ==========================

        return weights, scores_norm, zscore_params  # 修改了返回值


def analyze_all():
    """分析所有位置，并保存标准化参数"""
    positions = ['PG', 'SG', 'SF', 'PF', 'C']
    all_zscore_params = {}  # 保存所有位置的参数

    for pos in positions:
        file_path = f"Pos_{pos}2526.xlsx"
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                analyzer = SimplePCA_TOPSIS(df, pos)
                weights, scores, zscore_params = analyzer.analyze()  # 接收新返回值

                # 保存该位置的Z-score参数
                all_zscore_params[pos] = zscore_params

            except Exception as e:
                print(f"分析{pos}时出错: {e}")
                all_zscore_params[pos] = {}
        else:
            print(f"文件不存在: {file_path}")
            all_zscore_params[pos] = {}

    # === 新增：保存标准化参数到JSON文件 ===
    try:
        with open('global_zscore_params.json', 'w', encoding='utf-8') as f:
            json.dump(all_zscore_params, f, ensure_ascii=False, indent=2)
        print(f"\n{'=' * 60}")
        print("标准化参数已保存到: global_zscore_params.json")
        print(f"{'=' * 60}")
    except Exception as e:
        print(f"\n保存标准化参数时出错: {e}")
    # ====================================


if __name__ == "__main__":
    print("PCA+TOPSIS分析（包含分类标准化）")
    print("=" * 60)
    analyze_all()