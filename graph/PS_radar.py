import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Circle
import warnings

warnings.filterwarnings('ignore')

# 加载之前保存的数据
try:
    df = pd.read_excel('player_values_normalized_with_risk.xlsx')
    print(f"Data loaded successfully. Shape: {df.shape}")
    print(f"First few columns: {list(df.columns)[:10]}")
except FileNotFoundError:
    print("Error: File 'player_values_normalized_with_risk.xlsx' not found.")
    print("Please run the player_value(with_risk).py script first.")
    exit()

# 位置权重和指标方向性定义
POSITION_WEIGHTS = {
    "PG": {
        "indicators": {
            "FGA": {"weight": 20.64, "direction": "positive"},  # 正向：出手数越多越好
            "G": {"weight": 20.03, "direction": "positive"},  # 正向：比赛场次越多越好
            "PF": {"weight": 19.72, "direction": "negative"},  # 负向：犯规越少越好
            "DRtg": {"weight": 19.42, "direction": "negative"},  # 负向：防守效率越高越好（值越小越好）
            "ORtg": {"weight": 18.96, "direction": "positive"}  # 正向：进攻效率越高越好
        }
    },
    "SG": {
        "indicators": {
            "PF": {"weight": 21.86, "direction": "negative"},  # 负向
            "eFG": {"weight": 21.55, "direction": "positive"},  # 正向
            "FGA": {"weight": 20.60, "direction": "positive"},  # 正向
            "TOV": {"weight": 19.81, "direction": "negative"},  # 负向
            "ORtg": {"weight": 19.18, "direction": "positive"}  # 正向
        }
    },
    "SF": {
        "indicators": {
            "eFG": {"weight": 20.90, "direction": "positive"},
            "ORtg": {"weight": 20.44, "direction": "positive"},
            "FGA": {"weight": 19.70, "direction": "positive"},
            "FG": {"weight": 19.26, "direction": "positive"},
            "DRtg": {"weight": 19.11, "direction": "negative"}
        }
    },
    "PF": {
        "indicators": {
            "TOV": {"weight": 21.17, "direction": "negative"},
            "FGA": {"weight": 20.86, "direction": "positive"},
            "eFG": {"weight": 19.48, "direction": "positive"},
            "G": {"weight": 19.02, "direction": "positive"},
            "ORtg": {"weight": 18.87, "direction": "positive"}
        }
    },
    "C": {
        "indicators": {
            "eFG": {"weight": 20.62, "direction": "positive"},
            "FGA": {"weight": 20.47, "direction": "positive"},
            "PF": {"weight": 20.00, "direction": "negative"},
            "FG": {"weight": 19.84, "direction": "positive"},
            "G": {"weight": 19.53, "direction": "positive"}
        }
    }
}


def normalize_indicator(value, indicator_name, pos):
    """
    根据指标方向性进行归一化
    正向指标：值越大越好，归一化到[0,1]
    负向指标：值越小越好，归一化到[0,1]
    """
    # 首先确保数值类型
    if pd.isna(value):
        return 0

    # 定义每个指标的理论范围（可以根据实际数据调整）
    theoretical_ranges = {
        # 正向指标范围
        "FGA": (0, 30),  # 场均出手
        "FG": (0, 15),  # 场均命中
        "eFG": (0, 1),  # 有效命中率
        "ORtg": (80, 130),  # 进攻效率
        "G": (0, 82),  # 出场次数

        # 负向指标范围（值越小越好）
        "PF": (0, 6),  # 场均犯规（越小越好）
        "TOV": (0, 5),  # 场均失误（越小越好）
        "DRtg": (90, 120)  # 防守效率（越小越好）
    }

    # 获取当前指标的信息
    if pos in POSITION_WEIGHTS and indicator_name in POSITION_WEIGHTS[pos]["indicators"]:
        direction = POSITION_WEIGHTS[pos]["indicators"][indicator_name]["direction"]

        if indicator_name in theoretical_ranges:
            min_val, max_val = theoretical_ranges[indicator_name]

            if direction == "positive":
                # 正向指标：值越大越好
                normalized = (value - min_val) / (max_val - min_val)
            else:  # direction == "negative"
                # 负向指标：值越小越好
                # 为了显示，我们反转：值越小->分数越高
                normalized = 1 - ((value - min_val) / (max_val - min_val))

            # 限制在[0,1]范围内
            return max(0, min(1, normalized))

    # 如果没有找到范围定义，使用简单的0-1归一化
    return max(0, min(1, value / 100 if value != 0 else 0))


def calculate_personal_score(player):
    """
    计算personal score = PCA评分 × MP系数
    """
    pos = player['Pos']

    if pos not in POSITION_WEIGHTS:
        return 0, 0, 0

    # 计算PCA评分
    weights = POSITION_WEIGHTS[pos]["indicators"]
    pca_score = 0
    for indicator, info in weights.items():
        weight = info["weight"] / 100  # 转换为权重系数
        if indicator in player.index:
            # 使用原始值计算
            value = player[indicator]
            if not pd.isna(value):
                pca_score += value * weight

    # 计算MP因子
    REASONABLE_MAX_MP = 82 * 35  # 2870分钟

    if 'normalized_mp' in player.index and pd.notna(player['normalized_mp']):
        mp_value = player['normalized_mp']
    else:
        mp_value = player['MP']

    mp_ratio = min(1.0, mp_value / REASONABLE_MAX_MP)
    mp_factor = 0.2 + 0.8 * (mp_ratio ** 0.5)

    # Personal score
    personal_score = pca_score * mp_factor

    return personal_score, pca_score, mp_factor


def create_radar_chart_for_position(pos, top_players, save_path):
    """
    为特定位置创建雷达图
    """
    if pos not in POSITION_WEIGHTS:
        print(f"未知位置: {pos}")
        return

    indicators = list(POSITION_WEIGHTS[pos]["indicators"].keys())
    N = len(indicators)

    # 创建图形
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, polar=True)

    # 角度设置
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # 闭合图形

    # 冷色调颜色方案
    # cool_colors = [
    #     '#1f77b4', '#2ca02c', '#9467bd', '#8c564b', '#e377c2',  # 主色调
    #     '#3182bd', '#31a354', '#756bb1', '#636363', '#de2d26'  # 备用色调
    # ]
    TOL_BRIGHT = [
        '#4477AA', '#EE6677', '#228833', '#CCBB44', '#66CCEE',
        '#AA3377', '#BBBBBB', '#000000', '#88CCEE', '#DDCC77'
    ]
    # TOL_BRIGHT = [
    #     '#297270',  # 蓝绿
    #     '#299d8f',  # 青绿
    #     '#8ab07c',  # 黄绿
    #     '#3D8A87',  # 浅蓝绿
    #     '#3DB7A5',  # 浅青绿
    #     '#A0C08E',  # 浅黄绿
    #     '#F0D485',  # 浅金黄色
    #     '#F6B988'  # 浅橙黄色
    # ]

    # 绘制每个球员
    for i, (idx, player) in enumerate(top_players.iterrows()):
        # 获取归一化后的指标值
        values = []
        for indicator in indicators:
            if indicator in player.index:
                raw_value = player[indicator]
                norm_value = normalize_indicator(raw_value, indicator, pos)
                values.append(norm_value)
            else:
                values.append(0)

        # 闭合数据
        values += values[:1]

        # 选择颜色
        # color = cool_colors[i % len(cool_colors)]
        color = TOL_BRIGHT[i % len(TOL_BRIGHT)]

        # 绘制雷达图
        ax.plot(angles, values, 'o-', linewidth=2, color=color,
                label=f"{player['Player']} ({player['personal_score']:.1f})")
        ax.fill(angles, values, alpha=0.15, color=color)

    # 设置雷达图标签
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([f"{ind}\n({POSITION_WEIGHTS[pos]['indicators'][ind]['direction'][0]})"
                        for ind in indicators], fontsize=15)

    # 设置径向标签
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=12, color='gray')
    ax.set_ylabel('Normalized Score (0=worst, 1=best)', fontsize=15, labelpad=20)


    # 添加内圈作为参考
    for r in [0.2, 0.4, 0.6, 0.8]:
        circle = Circle((0, 0), r, transform=ax.transData._b,
                        facecolor='none', edgecolor='gray', linestyle='--', alpha=0.3)
        ax.add_patch(circle)

    # 设置标题
    plt.title(f'Top 5 {pos}s - Radar Chart of Key Performance Indicators\n'
              f'Personal Score = PCA Score × MP Factor',
              fontsize=13, fontweight='bold', pad=20)

    # 添加图例
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=10)

    # 调整布局
    plt.tight_layout()

    # 保存图形
    output_dir = './graph/'
    plt.savefig(f'{save_path}.pdf', format='pdf', bbox_inches='tight', dpi=300)
    plt.savefig(f'{save_path}.png', format='png', bbox_inches='tight', dpi=300)
    print(f"Saved: {save_path}.pdf and {save_path}.png")

    plt.show()


def main():
    """主函数"""
    # 配置matplotlib
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    matplotlib.rcParams['font.family'] = 'sans-serif'
    matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']

    # 计算personal score
    print("\nCalculating personal scores...")
    personal_scores = []
    pca_scores = []
    mp_factors = []

    for idx, row in df.iterrows():
        personal_score, pca_score, mp_factor = calculate_personal_score(row)
        personal_scores.append(personal_score)
        pca_scores.append(pca_score)
        mp_factors.append(mp_factor)

    df['personal_score'] = personal_scores
    df['pca_score'] = pca_scores
    df['mp_factor'] = mp_factors

    # 为每个位置生成雷达图
    print("\nGenerating radar charts for each position...")

    for pos in POSITION_WEIGHTS.keys():
        # 筛选该位置的球员
        pos_df = df[df['Pos'] == pos].copy()

        if len(pos_df) < 5:
            print(f"Not enough players for {pos}: {len(pos_df)}")
            continue

        # 获取前5名球员
        top_players = pos_df.sort_values('personal_score', ascending=False).head(5)

        # 输出排名信息
        print(f"\n{'=' * 60}")
        print(f"Top 5 {pos}s by Personal Score")
        print(f"{'=' * 60}")

        for i, (idx, player) in enumerate(top_players.iterrows()):
            print(f"{i + 1}. {player['Player']:<25} | Personal Score: {player['personal_score']:.1f}")
            print(f"   PCA: {player['pca_score']:.1f} | MP Factor: {player['mp_factor']:.3f}")

            # 显示指标值
            indicators = POSITION_WEIGHTS[pos]["indicators"]
            values = []
            for ind in indicators.keys():
                if ind in player.index:
                    raw_val = player[ind]
                    direction = indicators[ind]["direction"][0]  # P or N
                    values.append(f"{ind}({direction}): {raw_val:.2f}")

            if values:
                print(f"   Indicators: {', '.join(values[:3])}")
                if len(values) > 3:
                    print(f"                {', '.join(values[3:])}")
            print(f"{'-' * 60}")

        # 创建雷达图
        save_path = f"radar_top5_{pos}"
        create_radar_chart_for_position(pos, top_players, save_path)

    # 保存结果
    output_file = "players_with_personal_scores.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\nSaved results to: {output_file}")

    # 生成汇总统计
    print(f"\n{'=' * 60}")
    print("SUMMARY STATISTICS")
    print(f"{'=' * 60}")

    for pos in POSITION_WEIGHTS.keys():
        pos_df = df[df['Pos'] == pos]
        if len(pos_df) > 0:
            scores = pos_df['personal_score']
            print(f"{pos}: {len(pos_df)} players")
            print(f"  Avg: {scores.mean():.1f}, Max: {scores.max():.1f}, Min: {scores.min():.1f}")

            top_player = pos_df.loc[pos_df['personal_score'].idxmax()]
            print(f"  Top: {top_player['Player']} ({top_player['personal_score']:.1f})")
            print()


if __name__ == "__main__":
    main()