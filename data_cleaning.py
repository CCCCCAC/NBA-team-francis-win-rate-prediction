# import pandas as pd
#
# # 读取数据
# df = pd.read_excel('2122/Per100Poss2122.xlsx')  # 替换为你的文件名
#
# # 筛选需要的列
# keep_cols = ['Rk','Player','Age','Team','Pos','G','MP','FG','FGA','eFG%','TOV','PF','ORtg','DRtg']
# df = df[keep_cols]
#
# # 删除MP<15的行
# df = df[df['MP'] >= 15]
#
# # 按球队分组保存
# for team, team_df in df.groupby('Team'):
#     # 剔除Team列
#     team_df = team_df.drop('Team', axis=1)
#     # 保存为Excel
#     team_df.to_excel(f'2122/{team}players.xlsx', index=False)
#     print(f'已保存: {team}players.xlsx')


import os

team_abbr = {
    'atlanta-hawks': 'ATL', 'boston-celtics': 'BOS', 'brooklyn-nets': 'BRK',
    'charlotte-hornets': 'CHA', 'chicago-bulls': 'CHI', 'cleveland-cavaliers': 'CLE',
    'dallas-mavericks': 'DAL', 'denver-nuggets': 'DEN', 'detroit-pistons': 'DET',
    'golden-state-warriors': 'GSW', 'houston-rockets': 'HOU', 'indiana-pacers': 'IND',
    'los-angeles-clippers': 'LAC', 'los-angeles-lakers': 'LAL', 'memphis-grizzlies': 'MEM',
    'miami-heat': 'MIA', 'milwaukee-bucks': 'MIL', 'minnesota-timberwolves': 'MIN',
    'new-orleans-pelicans': 'NOP', 'new-york-knicks': 'NYK', 'oklahoma-city-thunder': 'OKC',
    'orlando-magic': 'ORL', 'philadelphia-76ers': 'PHI', 'phoenix-suns': 'PHX',
    'portland-trail-blazers': 'POR', 'sacramento-kings': 'SAC', 'san-antonio-spurs': 'SAS',
    'toronto-raptors': 'TOR', 'utah-jazz': 'UTA', 'washington-wizards': 'WAS'
}

for f in os.listdir('./Fprediction/fans'):
    if f.startswith('statistic_id'):
        for team, abbr in team_abbr.items():
            if team in f.lower():
                old_path = os.path.join('./Fprediction/fans', f)
                new_path = os.path.join('./Fprediction/fans', f'{abbr}fans.xlsx')
                os.rename(old_path, new_path)
                print(f"Renamed: {f} -> {abbr}fans.xlsx")
                break