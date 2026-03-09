import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# 设置英文字体
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 使用你提供的配色方案
BLUE_GREEN_GOLD = [
    '#274753',  # 深蓝绿
    '#297270',  # 蓝绿
    '#299d8f',  # 青绿
    '#8ab07c',  # 黄绿
    '#E7C66B',  # 金黄色
    '#F3A361',  # 橙黄色
    '#E66D50'  # 橙红色
]

# 创建对应的浅色版本
LIGHT_VERSIONS = [
    '#3A5C6B',
    '#3D8A87',
    '#3DB7A5',
    '#A0C08E',
    '#F0D485',
    '#F6B988',
    '#EB8C74'
]


def plot_age_risk_curves(df):
    """方案1：年龄-风险曲线图"""
    fig, ax = plt.subplots(figsize=(12, 8))

    # 定义不同的MP负荷水平
    mp_levels = [300, 600, 1000, 1500, 2000, 2500]

    # 生成年龄序列
    ages = np.linspace(19, 41, 50)

    # 计算每个MP水平的风险曲线
    for i, mp in enumerate(mp_levels):
        risks = []
        for age in ages:
            # 计算年龄因子
            if age <= 27:
                age_effect = (age - 27) * 0.03
            else:
                age_effect = (age - 27) * 0.09

            # 计算负荷因子
            load_effect = np.log(mp / 677 + 1) * 0.6

            # 假设外线球员（无位置惩罚）
            z = -2.0 + age_effect + load_effect
            risk = 1 / (1 + np.exp(-z))
            risks.append(risk)

        # 绘制曲线
        color_idx = i % len(BLUE_GREEN_GOLD)
        ax.plot(ages, risks, linewidth=3,
                color=BLUE_GREEN_GOLD[color_idx],
                marker='o', markersize=8, markevery=5,
                markerfacecolor=LIGHT_VERSIONS[color_idx],
                markeredgecolor=BLUE_GREEN_GOLD[color_idx],
                markeredgewidth=1.5,
                label=f'MP={mp}')

    # 美化图表
    ax.set_xlabel('Age (years)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Injury Risk', fontsize=13, fontweight='bold')
    ax.set_title('Age-Risk Curves (Different Workloads)', fontsize=15, fontweight='bold', pad=20)

    # 设置精细刻度
    ax.set_xticks(np.arange(19, 42, 2))
    ax.set_yticks(np.arange(0, 0.55, 0.05))

    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=11, frameon=True,
              fancybox=True, shadow=True, framealpha=0.9,
              title='Total Minutes Played')
    ax.set_xlim(19, 41)
    ax.set_ylim(0, 0.5)

    # 添加背景色
    ax.set_facecolor('#F5F7FA')
    fig.patch.set_facecolor('white')

    plt.tight_layout()
    plt.savefig('age_risk_curves.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_risk_heatmap():
    """方案2：年龄-风险热力图"""
    # 创建数据网格
    age_groups = np.arange(20, 41, 2)  # 20-40岁，每2岁一组
    mp_groups = np.array([200, 500, 800, 1100, 1400, 1700, 2000, 2300, 2600, 2900])

    # 创建风险矩阵
    risk_matrix = np.zeros((len(mp_groups), len(age_groups)))

    for i, mp in enumerate(mp_groups):
        for j, age in enumerate(age_groups):
            if age <= 27:
                age_effect = (age - 27) * 0.03
            else:
                age_effect = (age - 27) * 0.09

            load_effect = np.log(mp / 677 + 1) * 0.6
            z = -2.0 + age_effect + load_effect
            risk = 1 / (1 + np.exp(-z))
            risk_matrix[i, j] = risk

    # 创建热力图
    fig, ax = plt.subplots(figsize=(14, 10))

    # 使用配色创建渐变色
    cmap = LinearSegmentedColormap.from_list('blue_green_gold', BLUE_GREEN_GOLD)

    # 绘制热力图
    im = ax.imshow(risk_matrix, cmap=cmap, aspect='auto', interpolation='spline36',
                   vmin=0.05, vmax=0.45)

    # 设置坐标轴
    ax.set_xticks(np.arange(len(age_groups)))
    ax.set_yticks(np.arange(len(mp_groups)))
    ax.set_xticklabels([f'{int(age)}' for age in age_groups], fontsize=11)
    ax.set_yticklabels([f'{int(mp)}' for mp in mp_groups], fontsize=11)

    # 添加数值标签 - 修复这里的问题
    for i in range(len(mp_groups)):
        for j in range(len(age_groups)):
            text_color = "white" if risk_matrix[i, j] > 0.25 else "black"
            # 简化bbox设置，避免复杂颜色
            ax.text(j, i, f'{risk_matrix[i, j]:.2f}',
                    ha="center", va="center",
                    color=text_color,
                    fontsize=9, fontweight='bold')

    ax.set_xlabel('Age (years)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Total Minutes Played', fontsize=13, fontweight='bold')
    ax.set_title('Age-Workload-Risk Heatmap', fontsize=15, fontweight='bold', pad=20)

    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label('Injury Risk', fontsize=12, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)

    # 添加网格线
    ax.set_xticks(np.arange(-0.5, len(age_groups), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(mp_groups), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle='-', linewidth=1, alpha=0.5)
    ax.tick_params(which="minor", size=0)

    fig.patch.set_facecolor('#F5F7FA')
    plt.tight_layout()
    plt.savefig('risk_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()


def plot_age_group_violinplot(df):
    """方案5：年龄分组风险小提琴图 - 优化版"""
    # 创建年龄分组
    bins = [19, 24, 28, 32, 36, 42]
    labels = ['19-23', '24-27', '28-31', '32-35', '36-40']
    df['age_group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)

    fig, ax = plt.subplots(figsize=(14, 9))

    # 准备数据
    violin_data = []
    for group in labels:
        group_data = df[df['age_group'] == group]['injury_risk'].dropna()
        violin_data.append(group_data)

    # 绘制小提琴图 - 使用更清晰的配色
    positions = np.arange(1, len(labels) + 1)

    # 使用渐变蓝色系，更清晰
    VIOLIN_COLORS = [
        '#297270',  # 蓝绿
        '#299d8f',  # 青绿
        '#8ab07c',  # 黄绿
        '#E7C66B',  # 金黄色
        '#F3A361'  # 橙黄色
    ]

    VIOLIN_LIGHT_COLORS = [
        '#3D8A87',  # 浅蓝绿
        '#3DB7A5',  # 浅青绿
        '#A0C08E',  # 浅黄绿
        '#F0D485',  # 浅金黄色
        '#F6B988'  # 浅橙黄色
    ]

    # 先绘制箱线图作为背景（更清晰）
    box_width = 0.4
    for i, data in enumerate(violin_data):
        if len(data) > 0:
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            median = np.median(data)
            mean = np.mean(data)

            # 绘制箱体
            ax.add_patch(plt.Rectangle((positions[i] - box_width / 2, q1),
                                       box_width, q3 - q1,
                                       facecolor=VIOLIN_LIGHT_COLORS[i], alpha=0.4,
                                       edgecolor=VIOLIN_COLORS[i], linewidth=1.5,
                                       zorder=1))

            # 绘制中位线
            ax.plot([positions[i] - box_width / 2, positions[i] + box_width / 2],
                    [median, median],
                    color='#274753', linewidth=3, zorder=2)

            # 绘制均值点
            ax.plot(positions[i], mean, 'o',
                    markersize=10, color='white',
                    markeredgecolor='#274753', markeredgewidth=2,
                    zorder=3)

    # 绘制小提琴图（半透明覆盖）
    parts = ax.violinplot(violin_data, positions=positions, widths=0.7,
                          showmeans=False, showmedians=False,
                          showextrema=False)

    # 设置小提琴颜色为半透明
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(VIOLIN_COLORS[i])
        pc.set_edgecolor(VIOLIN_COLORS[i])
        pc.set_alpha(0.3)  # 更透明，让箱体更清晰
        pc.set_linewidth(1.2)
        pc.set_zorder(0)  # 放在最底层

    # 添加数据点（更稀疏，更清晰）
    for i, data in enumerate(violin_data):
        if len(data) > 0:
            # 使用抖动但控制密度
            x_jitter = np.random.normal(positions[i], 0.05, size=len(data))
            # 减少点的大小和透明度
            ax.scatter(x_jitter, data, alpha=0.3, s=25,
                       color=VIOLIN_COLORS[i],
                       edgecolors=VIOLIN_COLORS[i], linewidth=0.5,
                       zorder=4)

    # 美化图表
    ax.set_xlabel('Age Group (years)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Injury Risk', fontsize=13, fontweight='bold')
    ax.set_title('Injury Risk Distribution by Age Group', fontsize=15, fontweight='bold', pad=20)

    # 设置精细刻度
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=12, fontweight='bold')
    ax.set_yticks(np.arange(0, 0.55, 0.05))
    ax.set_yticklabels([f'{x:.2f}' for x in np.arange(0, 0.55, 0.05)], fontsize=10)

    # 添加网格和背景
    ax.grid(True, alpha=0.2, linestyle='--', axis='y', zorder=0)
    ax.set_facecolor('#F8FAFD')  # 更浅的背景
    ax.set_ylim(0, 0.5)
    ax.set_xlim(0.4, len(labels) + 0.6)

    # 添加统计信息标注
    for i, data in enumerate(violin_data):
        if len(data) > 0:
            median_val = np.median(data)
            mean_val = np.mean(data)
            count = len(data)
            std_val = np.std(data)

            # 在图表顶部添加统计信息
            info_text = f'n={count}\nμ={mean_val:.3f}\nσ={std_val:.3f}'
            ax.text(positions[i], 0.48, info_text,
                    ha='center', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3",
                              facecolor='white',
                              edgecolor=VIOLIN_COLORS[i],
                              alpha=0.9),
                    zorder=5)

    # 添加更清晰的图例
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor=VIOLIN_LIGHT_COLORS[0], alpha=0.4, edgecolor=VIOLIN_COLORS[0],
              label='Interquartile Range (25%-75%)'),
        Line2D([0], [0], color='#274753', lw=3, label='Median'),
        Line2D([0], [0], marker='o', color='white', markerfacecolor='white',
               markeredgecolor='#274753', markeredgewidth=2, markersize=8,
               linestyle='None', label='Mean'),
        Line2D([0], [0], marker='o', color=VIOLIN_COLORS[0],
               markerfacecolor=VIOLIN_COLORS[0], markersize=6,
               linestyle='None', alpha=0.5, label='Individual Data Points')
    ]

    ax.legend(handles=legend_elements, loc='upper right', fontsize=10,
              frameon=True, fancybox=True, shadow=True,
              bbox_to_anchor=(1.02, 1), borderaxespad=0.)

    # 添加横向分布密度曲线（右侧）
    from scipy import stats

    ax2 = ax.twinx()
    ax2.set_ylim(0, 0.5)
    ax2.set_yticks([])  # 隐藏右侧y轴刻度
    ax2.set_ylabel('Density', fontsize=11, fontweight='bold', rotation=270, labelpad=15)

    for i, data in enumerate(violin_data):
        if len(data) > 0 and len(data) > 1:
            # 计算核密度估计
            kde = stats.gaussian_kde(data)
            x_kde = np.linspace(0, 0.5, 100)
            y_kde = kde(x_kde)
            # 标准化到合适高度
            y_kde = y_kde / y_kde.max() * 0.15

            # 绘制密度曲线（在右侧）
            ax2.fill_betweenx(x_kde, positions[i] + 0.5,
                              positions[i] + 0.5 + y_kde,
                              color=VIOLIN_COLORS[i], alpha=0.5, zorder=1)
            ax2.plot(positions[i] + 0.5 + y_kde, x_kde,
                     color=VIOLIN_COLORS[i], linewidth=1.5, alpha=0.8, zorder=2)

    fig.patch.set_facecolor('white')
    plt.tight_layout()
    plt.savefig('age_group_violinplot.png', dpi=300, bbox_inches='tight')
    plt.show()


# 使用示例
if __name__ == "__main__":
    print("Starting visualization generation...")
    print("=" * 50)

    # 尝试加载数据
    try:
        df = pd.read_excel("player_values_normalized_with_risk.xlsx")
        print("Data loaded successfully")
    except FileNotFoundError:
        print("Warning: Data file not found. Creating sample data...")
        np.random.seed(42)
        ages = np.random.randint(19, 41, 500)
        mps = np.random.randint(100, 2500, 500)
        positions = np.random.choice(['PG', 'SG', 'SF', 'PF', 'C'], 500)
        df = pd.DataFrame({
            'Player': [f'Player_{i}' for i in range(500)],
            'Age': ages,
            'MP': mps,
            'Pos': positions,
            'injury_risk': np.random.beta(2, 5, 500) * 0.4 + 0.1
        })

    print("\n1. Generating Age-Risk Curves...")
    plot_age_risk_curves(df)

    print("\n2. Generating Risk Heatmap...")
    plot_risk_heatmap()

    print("\n3. Generating Age Group Violin Plot...")
    plot_age_group_violinplot(df)

    print("\n" + "=" * 50)
    print("All visualizations generated and saved as PNG files!")
    print("Generated files:")
    print("  - age_risk_curves.png")
    print("  - risk_heatmap.png")
    print("  - age_group_violinplot.png")