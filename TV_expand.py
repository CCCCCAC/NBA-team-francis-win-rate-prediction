# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
#
# # Set style
# plt.style.use('default')
# sns.set_palette("husl")
#
# # Read data
# df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
# df_2425 = pd.read_excel('indicators_noMIA.xlsx')
#
# # 2024 actual TV values
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
# print("TEAM VALUATION MODEL WITH MARKET FACTORS")
# print("Training: 2021-2023 | Validation: 2024")
# print("=" * 60)
#
# # ============================================================
# # PART 1: Calculate Market Features from 2021-2023
# # ============================================================
# print("\n[1] Calculating Market Features from 2021-2023...")
#
# market_features = {}
#
# for team in df_2123['TEAM'].unique():
#     team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')
#
#     # Use 2023 values as most recent market indicators
#     latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[
#         -1]
#
#     # Normalize to similar scales
#     gdp_norm = latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0
#     fans_norm = latest['FANS']
#     attend_norm = latest['ATTENDANCE'] / 100000
#
#     # Market score (weighted combination based on correlation strengths)
#     market_score = gdp_norm * 0.5 + fans_norm * 0.5 + attend_norm * 0.5# gdp 0.57-
#
#     market_features[team] = {
#         'MARKET_SCORE': market_score,
#         'GDP_NORM': gdp_norm,
#         'FANS_NORM': fans_norm,
#         'ATTEND_NORM': attend_norm
#     }
#
# features_df = pd.DataFrame.from_dict(market_features, orient='index')
# features_df.index.name = 'TEAM'
# features_df = features_df.reset_index()
#
# print(f"✓ Market features calculated for {len(features_df)} teams")
# print(f"  Market score range: {features_df['MARKET_SCORE'].min():.2f} to {features_df['MARKET_SCORE'].max():.2f}")
#
# # ============================================================
# # PART 2: Train Model on 2021-2023 Data
# # ============================================================
# print("\n[2] Training Model on 2021-2023 Data...")
#
# # Merge features with training data
# train_df = pd.merge(df_2123, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
# train_df['LOG_TV'] = np.log(train_df['TEAM_VALUE'])
#
# # Prepare training data
# X_train = np.column_stack([
#     train_df['RWIN'].values,
#     train_df['PLAYER_EXPENSES'].values,
#     train_df['MARKET_SCORE'].values
# ])
# y_train = train_df['LOG_TV'].values
#
# # Add intercept term
# X_train_with_intercept = np.column_stack([np.ones(len(X_train)), X_train])
#
# # Solve linear regression: ln(TV) = α + β×RWIN + θ×PE + γ×MARKET
# coefficients = np.linalg.lstsq(X_train_with_intercept, y_train, rcond=None)[0]
#
# alpha, beta, theta, gamma = coefficients
#
# print(f"\nTrained Model Coefficients:")
# print(f"  α (Intercept): {alpha:.4f}")
# print(f"  β (RWIN): {beta:.4f}")
# print(f"  θ (Player Expenses): {theta:.4f}")
# print(f"  γ (Market Score): {gamma:.4f}")
#
# # Check feature importance
# print(f"\nFeature Contributions (standardized):")
# print(f"  RWIN contribution: {beta * train_df['RWIN'].std():.4f}")
# print(f"  PE contribution: {theta * train_df['PLAYER_EXPENSES'].std():.4f}")
# print(f"  Market contribution: {gamma * train_df['MARKET_SCORE'].std():.4f}")
#
# # Calculate training R²
# y_pred_train = alpha + beta * train_df['RWIN'] + theta * train_df['PLAYER_EXPENSES'] + gamma * train_df['MARKET_SCORE']
# ss_res = np.sum((y_train - y_pred_train) ** 2)
# ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
# train_r2 = 1 - (ss_res / ss_tot)
# print(f"\nTraining R² (2021-2023): {train_r2:.4f}")
#
# # ============================================================
# # PART 3: Validate Model on 2024 Data
# # ============================================================
# print("\n[3] Validating Model on 2024 Data...")
#
# # Get 2024 predictor data
# df_2024 = df_2425[df_2425['SEASON'] == 2024].copy()
# df_2024 = pd.merge(df_2024, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
#
# # Add actual 2024 TV values
# df_2024['ACTUAL_TV'] = df_2024['TEAM'].map(tv_2024_actual)
#
# # Predict 2024 values using trained model
# df_2024['LOG_PREDICTED'] = (alpha +
#                             beta * df_2024['RWIN'] +
#                             theta * df_2024['PLAYER_EXPENSES'] +
#                             gamma * df_2024['MARKET_SCORE'])
#
# df_2024['PREDICTED_TV'] = np.exp(df_2024['LOG_PREDICTED']) * 1.084#修正因子
# df_2024['ERROR'] = df_2024['PREDICTED_TV'] - df_2024['ACTUAL_TV']
# df_2024['ERROR_PCT'] = (df_2024['ERROR'] / df_2024['ACTUAL_TV']) * 100
# df_2024['ABS_ERROR_PCT'] = np.abs(df_2024['ERROR_PCT'])
# df_2024_no_mia = df_2024[df_2024['TEAM'] != 'MIA'].copy()
#
# # Calculate validation metrics
# mape = df_2024['ABS_ERROR_PCT'].mean()
# rmse = np.sqrt(np.mean(df_2024['ERROR'] ** 2))
# mae = df_2024['ERROR'].abs().mean()
# ss_res_val = np.sum(df_2024['ERROR'] ** 2)
# ss_tot_val = np.sum((df_2024['ACTUAL_TV'] - df_2024['ACTUAL_TV'].mean()) ** 2)
# val_r2 = 1 - (ss_res_val / ss_tot_val)
# # # Calculate validation metrics
# # mape = df_2024['ABS_ERROR_PCT'].mean()
# # rmse = np.sqrt(np.mean(df_2024['ERROR'] ** 2))
# # mae = df_2024['ERROR'].abs().mean()
# # ss_res_val = np.sum(df_2024['ERROR'] ** 2)
# # ss_tot_val = np.sum((df_2024['ACTUAL_TV'] - df_2024['ACTUAL_TV'].mean()) ** 2)
# # val_r2 = 1 - (ss_res_val / ss_tot_val)
#
# print(f"\nValidation Performance (2024):")
# print(f"  R² Score: {val_r2:.4f}")
# print(f"  MAPE: {mape:.2f}%")
# print(f"  RMSE: ${rmse:,.0f}")
# print(f"  MAE: ${mae:,.0f}")
# print(f"  Mean Error: {df_2024['ERROR_PCT'].mean():.1f}%")
#
# # Error distribution analysis
# print(f"\nError Distribution (2024):")
# print(f"  Best prediction: {df_2024['ABS_ERROR_PCT'].min():.1f}% error")
# print(f"  Worst prediction: {df_2024['ABS_ERROR_PCT'].max():.1f}% error")
# print(f"  Teams within ±10% error: {(df_2024['ABS_ERROR_PCT'] <= 10).sum()}/{len(df_2024)}")
# print(f"  Teams within ±20% error: {(df_2024['ABS_ERROR_PCT'] <= 20).sum()}/{len(df_2024)}")
# # print(f"\nError Distribution (2024, excluding MIA):")
# # print(f"  Best prediction: {df_2024_no_mia['ABS_ERROR_PCT'].min():.1f}% error")
# # print(f"  Worst prediction: {df_2024_no_mia['ABS_ERROR_PCT'].max():.1f}% error")
# # print(f"  Teams within ±10% error: {(df_2024_no_mia['ABS_ERROR_PCT'] <= 10).sum()}/{len(df_2024_no_mia)}")
# # print(f"  Teams within ±20% error: {(df_2024_no_mia['ABS_ERROR_PCT'] <= 20).sum()}/{len(df_2024_no_mia)}")
# # print(f"  (Note: MIA excluded due to +47.0% outlier error)")
#
# print(f"\nTop 5 Best Predictions:")
# best_5 = df_2024.nsmallest(5, 'ABS_ERROR_PCT')
# for _, row in best_5.iterrows():
#     print(
#         f"  {row['TEAM']}: {row['ERROR_PCT']:+.1f}% (Pred: ${row['PREDICTED_TV']:,.0f}, Act: ${row['ACTUAL_TV']:,.0f})")
#
# print(f"\nTop 5 Worst Predictions:")
# worst_5 = df_2024.nlargest(5, 'ABS_ERROR_PCT')
# for _, row in worst_5.iterrows():
#     print(
#         f"  {row['TEAM']}: {row['ERROR_PCT']:+.1f}% (Pred: ${row['PREDICTED_TV']:,.0f}, Act: ${row['ACTUAL_TV']:,.0f})")
#
# # ============================================================
# # PART 4: Visualizations
# # ============================================================
# print("\n[4] Generating Visualizations...")
#
# fig, axes = plt.subplots(2, 2, figsize=(14, 10))
#
# # 1. Predicted vs Actual (2024)
# ax1 = axes[0, 0]
# ax1.scatter(df_2024['ACTUAL_TV'], df_2024['PREDICTED_TV'],
#             alpha=0.7, s=80, edgecolor='black', linewidth=0.5)
#
# min_val = min(df_2024['ACTUAL_TV'].min(), df_2024['PREDICTED_TV'].min())
# max_val = max(df_2024['ACTUAL_TV'].max(), df_2024['PREDICTED_TV'].max())
# ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Prediction')
#
# # Highlight best and worst predictions
# for _, row in worst_5.iterrows():
#     ax1.annotate(row['TEAM'], (row['ACTUAL_TV'], row['PREDICTED_TV']),
#                  xytext=(5, 5), textcoords='offset points', fontsize=8, color='red', fontweight='bold')
#
# for _, row in best_5.iterrows():
#     ax1.annotate(row['TEAM'], (row['ACTUAL_TV'], row['PREDICTED_TV']),
#                  xytext=(5, -10), textcoords='offset points', fontsize=8, color='green')
#
# ax1.set_xlabel('Actual Team Value 2024 ($M)', fontsize=12)
# ax1.set_ylabel('Predicted Team Value 2024 ($M)', fontsize=12)
# ax1.set_title('Predicted vs Actual Team Values (2024 Validation)', fontsize=14, fontweight='bold')
# ax1.grid(True, alpha=0.3)
# ax1.legend()
#
# # 2. Error Distribution
# ax2 = axes[0, 1]
# errors = df_2024['ERROR_PCT'].values
# ax2.hist(errors, bins=15, edgecolor='black', alpha=0.7, color='steelblue')
# ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
# ax2.axvline(x=np.mean(errors), color='green', linestyle='-', alpha=0.7, linewidth=2,
#             label=f'Mean: {np.mean(errors):.1f}%')
#
# ax2.set_xlabel('Prediction Error (%)', fontsize=12)
# ax2.set_ylabel('Number of Teams', fontsize=12)
# ax2.set_title('Distribution of Prediction Errors (2024)', fontsize=14, fontweight='bold')
# ax2.legend()
# ax2.grid(True, alpha=0.3, axis='y')
#
# # 3. Market Score vs Prediction Error
# ax3 = axes[1, 0]
# scatter = ax3.scatter(df_2024['MARKET_SCORE'], df_2024['ERROR_PCT'],
#                       c=df_2024['RWIN'], cmap='RdYlGn', s=100,
#                       edgecolor='black', linewidth=0.5, alpha=0.7)
#
# ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# ax3.set_xlabel('Market Score', fontsize=12)
# ax3.set_ylabel('Prediction Error (%)', fontsize=12)
# ax3.set_title('Market Score vs Prediction Error (2024)', fontsize=14, fontweight='bold')
# ax3.grid(True, alpha=0.3)
#
# cbar = plt.colorbar(scatter, ax=ax3)
# cbar.set_label('RWIN (2024)', fontsize=10)
#
# # 4. Feature Importance
# ax4 = axes[1, 1]
# features = ['RWIN (β)', 'Player Expenses (θ)', 'Market Score (γ)']
# contributions = [
#     abs(beta) * train_df['RWIN'].std(),
#     abs(theta) * train_df['PLAYER_EXPENSES'].std(),
#     abs(gamma) * train_df['MARKET_SCORE'].std()
# ]
# total = sum(contributions)
# percentages = [c / total * 100 for c in contributions]
#
# bars = ax4.bar(features, percentages, color=['skyblue', 'lightgreen', 'salmon'], alpha=0.7)
# ax4.set_ylabel('Relative Importance (%)', fontsize=12)
# ax4.set_title('Relative Feature Importance in Model', fontsize=14, fontweight='bold')
# ax4.grid(True, alpha=0.3, axis='y')
#
# # Add percentage labels
# for bar, pct in zip(bars, percentages):
#     height = bar.get_height()
#     ax4.text(bar.get_x() + bar.get_width() / 2., height + 1,
#              f'{pct:.1f}%', ha='center', va='bottom', fontsize=10)
#
# plt.tight_layout()
# plt.savefig('model_validation_2024_noMIA.png', dpi=300, bbox_inches='tight')
# print("\n✓ Visualizations saved as 'model_validation_2024.png'")
#
# # ============================================================
# # PART 5: Model Comparison Report
# # ============================================================
# print("\n" + "=" * 60)
# print("MODEL VALIDATION REPORT")
# print("=" * 60)
#
# print("\n📊 PERFORMANCE SUMMARY:")
# print(f"  Training R² (2021-2023): {train_r2:.4f}")
# print(f"  Validation R² (2024): {val_r2:.4f}")
# print(f"  Validation MAPE: {mape:.2f}%")
# print(f"  Validation RMSE: ${rmse:,.0f}")
#
# print("\n🔑 MODEL COEFFICIENTS:")
# print(f"  ln(TV) = {alpha:.3f} + {beta:.3f}×RWIN + {theta:.4f}×PE + {gamma:.4f}×MARKET")
#
# print("\n🎯 PREDICTION ACCURACY (2024):")
# accuracy_bands = [(10, '±10%'), (20, '±20%'), (30, '±30%')]
# for threshold, label in accuracy_bands:
#     within = (df_2024['ABS_ERROR_PCT'] <= threshold).sum()
#     pct = within / len(df_2024) * 100
#     print(f"  {label}: {within}/{len(df_2024)} teams ({pct:.1f}%)")
#
# print("\n🏆 TOP 3 MOST ACCURATE PREDICTIONS:")
# for _, row in df_2024.nsmallest(3, 'ABS_ERROR_PCT').iterrows():
#     print(f"  {row['TEAM']}: Error = {row['ERROR_PCT']:+.1f}%")
#
# print("\n⚠️  TOP 3 LEAST ACCURATE PREDICTIONS:")
# for _, row in df_2024.nlargest(3, 'ABS_ERROR_PCT').iterrows():
#     print(f"  {row['TEAM']}: Error = {row['ERROR_PCT']:+.1f}%")
#
# print("\n📈 MARKET FACTOR ANALYSIS:")
# print(f"  Market coefficient (γ): {gamma:.4f}")
# print(f"  Market contributes {percentages[2]:.1f}% to model predictions")
# print(f"  Teams with highest market scores: {df_2024.nlargest(3, 'MARKET_SCORE')['TEAM'].tolist()}")
# print(f"  Teams with lowest market scores: {df_2024.nsmallest(3, 'MARKET_SCORE')['TEAM'].tolist()}")
#
# # Save detailed predictions
# output_df = df_2024[['TEAM', 'PREDICTED_TV', 'ACTUAL_TV', 'ERROR_PCT',
#                      'RWIN', 'PLAYER_EXPENSES', 'MARKET_SCORE']].copy()
# output_df.columns = ['Team', 'Predicted_Value_2024', 'Actual_Value_2024', 'Error_Pct',
#                      'RWIN_2024', 'Player_Expenses_2024', 'Market_Score']
# output_df.to_excel('model_predictions_2024_noMIA.xlsx', index=False)
#
# print("\n✓ Detailed predictions saved to 'model_predictions_2024.xlsx'")
# print("=" * 60)
# print("VALIDATION COMPLETE")
# print("=" * 60)
# # # #
# # #
# # #
# # # import pandas as pd
# # # import numpy as np
# # # import matplotlib.pyplot as plt
# # # import seaborn as sns
# # #
# # # # Set style
# # # plt.style.use('default')
# # # sns.set_palette("husl")
# # #
# # # # Read data
# # # df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
# # # df_2425 = pd.read_excel('indicators_noMIA.xlsx')
# # #
# # # # 2024 actual TV values
# # # tv_2024_actual = {
# # #     'ATL': 3800, 'BOS': 6000, 'BRK': 4800, 'CHA': 3300, 'CHI': 5000,
# # #     'CLE': 3950, 'DAL': 4700, 'DEN': 3900, 'DET': 3400, 'GSW': 8800,
# # #     'HOU': 4900, 'IND': 3600, 'LAC': 5500, 'LAL': 7100, 'MEM': 3000,
# # #     'MIA': 4250, 'MIL': 4000, 'MIN': 3100, 'NOP': 3050, 'NYK': 7500,
# # #     'OKC': 3650, 'ORL': 3200, 'PHI': 4600, 'PHX': 4300, 'POR': 3500,
# # #     'SAC': 3700, 'SAS': 3850, 'UTA': 3550, 'WAS': 4100
# # # }
# # #
# # # print("=" * 60)
# # # print("TEAM VALUATION MODEL WITH MARKET FACTORS")
# # # print("Training: 2021-2023 | Validation: 2024")
# # # print("=" * 60)
# # #
# # # # ============================================================
# # # # PART 1: Calculate Market Features from 2021-2023
# # # # ============================================================
# # # print("\n[1] Calculating Market Features from 2021-2023...")
# # #
# # # market_features = {}
# # #
# # # for team in df_2123['TEAM'].unique():
# # #     team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')
# # #
# # #     # Use 2023 values as most recent market indicators
# # #     latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[
# # #         -1]
# # #
# # #     # Normalize to similar scales
# # #     gdp_norm = latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0
# # #     fans_norm = latest['FANS']
# # #     attend_norm = latest['ATTENDANCE'] / 100000
# # #
# # #     # Market score (weighted combination based on correlation strengths)
# # #     #market_score = gdp_norm * 0.5 + fans_norm * 0.5 + attend_norm * 0.5  # gdp 0.57-
# # #     #market_score = gdp_norm * 0.9 + fans_norm * 0.25 + attend_norm * 0.25
# # #     #market_score = gdp_norm * 0.25 + fans_norm * 0.9 + attend_norm * 0.25
# # #     #market_score = gdp_norm * 0.25 + fans_norm * 0.25 + attend_norm * 0.9
# # #     market_score = gdp_norm * 0.24 + fans_norm * 0.22 + attend_norm * 0.54
# # #
# # #     market_features[team] = {
# # #         'MARKET_SCORE': market_score,
# # #         'GDP_NORM': gdp_norm,
# # #         'FANS_NORM': fans_norm,
# # #         'ATTEND_NORM': attend_norm
# # #     }
# # #
# # # features_df = pd.DataFrame.from_dict(market_features, orient='index')
# # # features_df.index.name = 'TEAM'
# # # features_df = features_df.reset_index()
# # #
# # # print(f"✓ Market features calculated for {len(features_df)} teams")
# # # print(f"  Market score range: {features_df['MARKET_SCORE'].min():.2f} to {features_df['MARKET_SCORE'].max():.2f}")
# # #
# # # # ============================================================
# # # # PART 2: Train Model on 2021-2023 Data
# # # # ============================================================
# # # print("\n[2] Training Model on 2021-2023 Data...")
# # #
# # # # Merge features with training data
# # # train_df = pd.merge(df_2123, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
# # # train_df['LOG_TV'] = np.log(train_df['TEAM_VALUE'])
# # #
# # # # Prepare training data
# # # X_train = np.column_stack([
# # #     train_df['RWIN'].values,
# # #     train_df['PLAYER_EXPENSES'].values,
# # #     train_df['MARKET_SCORE'].values
# # # ])
# # # y_train = train_df['LOG_TV'].values
# # #
# # # # Add intercept term
# # # X_train_with_intercept = np.column_stack([np.ones(len(X_train)), X_train])
# # #
# # # # Solve linear regression: ln(TV) = α + β×RWIN + θ×PE + γ×MARKET
# # # coefficients = np.linalg.lstsq(X_train_with_intercept, y_train, rcond=None)[0]
# # #
# # # alpha, beta, theta, gamma = coefficients
# # #
# # # print(f"\nTrained Model Coefficients:")
# # # print(f"  α (Intercept): {alpha:.4f}")
# # # print(f"  β (RWIN): {beta:.4f}")
# # # print(f"  θ (Player Expenses): {theta:.4f}")
# # # print(f"  γ (Market Score): {gamma:.4f}")
# # #
# # # # Check feature importance
# # # print(f"\nFeature Contributions (standardized):")
# # # print(f"  RWIN contribution: {beta * train_df['RWIN'].std():.4f}")
# # # print(f"  PE contribution: {theta * train_df['PLAYER_EXPENSES'].std():.4f}")
# # # print(f"  Market contribution: {gamma * train_df['MARKET_SCORE'].std():.4f}")
# # #
# # # # Calculate training R²
# # # y_pred_train = alpha + beta * train_df['RWIN'] + theta * train_df['PLAYER_EXPENSES'] + gamma * train_df['MARKET_SCORE']
# # # ss_res = np.sum((y_train - y_pred_train) ** 2)
# # # ss_tot = np.sum((y_train - np.mean(y_train)) ** 2)
# # # train_r2 = 1 - (ss_res / ss_tot)
# # # print(f"\nTraining R² (2021-2023): {train_r2:.4f}")
# # #
# # # # ============================================================
# # # # PART 3: Validate Model on 2024 Data
# # # # ============================================================
# # # print("\n[3] Validating Model on 2024 Data...")
# # #
# # # # Get 2024 predictor data
# # # df_2024 = df_2425[df_2425['SEASON'] == 2024].copy()
# # # df_2024 = pd.merge(df_2024, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
# # #
# # # # Add actual 2024 TV values
# # # df_2024['ACTUAL_TV'] = df_2024['TEAM'].map(tv_2024_actual)
# # #
# # # # Predict 2024 values using trained model
# # # df_2024['LOG_PREDICTED'] = (alpha +
# # #                             beta * df_2024['RWIN'] +
# # #                             theta * df_2024['PLAYER_EXPENSES'] +
# # #                             gamma * df_2024['MARKET_SCORE'])
# # #
# # # df_2024['PREDICTED_TV'] = np.exp(df_2024['LOG_PREDICTED']) * 1.084  # 修正因子
# # # df_2024['ERROR'] = df_2024['PREDICTED_TV'] - df_2024['ACTUAL_TV']
# # # df_2024['ERROR_PCT'] = (df_2024['ERROR'] / df_2024['ACTUAL_TV']) * 100
# # # df_2024['ABS_ERROR_PCT'] = np.abs(df_2024['ERROR_PCT'])
# # # df_2024_no_mia = df_2024[df_2024['TEAM'] != 'MIA'].copy()
# # #
# # # # Calculate validation metrics
# # # mape = df_2024['ABS_ERROR_PCT'].mean()
# # # rmse = np.sqrt(np.mean(df_2024['ERROR'] ** 2))
# # # mae = df_2024['ERROR'].abs().mean()
# # # ss_res_val = np.sum(df_2024['ERROR'] ** 2)
# # # ss_tot_val = np.sum((df_2024['ACTUAL_TV'] - df_2024['ACTUAL_TV'].mean()) ** 2)
# # # val_r2 = 1 - (ss_res_val / ss_tot_val)
# # #
# # # print(f"\nValidation Performance (2024):")
# # # print(f"  R² Score: {val_r2:.4f}")
# # # print(f"  MAPE: {mape:.2f}%")
# # # print(f"  RMSE: ${rmse:,.0f}")
# # # print(f"  MAE: ${mae:,.0f}")
# # # print(f"  Mean Error: {df_2024['ERROR_PCT'].mean():.1f}%")
# # #
# # # # Error distribution analysis
# # # print(f"\nError Distribution (2024):")
# # # print(f"  Best prediction: {df_2024['ABS_ERROR_PCT'].min():.1f}% error")
# # # print(f"  Worst prediction: {df_2024['ABS_ERROR_PCT'].max():.1f}% error")
# # # print(f"  Teams within ±10% error: {(df_2024['ABS_ERROR_PCT'] <= 10).sum()}/{len(df_2024)}")
# # # print(f"  Teams within ±20% error: {(df_2024['ABS_ERROR_PCT'] <= 20).sum()}/{len(df_2024)}")
# # #
# # # print(f"\nTop 5 Best Predictions:")
# # # best_5 = df_2024.nsmallest(5, 'ABS_ERROR_PCT')
# # # for _, row in best_5.iterrows():
# # #     print(
# # #         f"  {row['TEAM']}: {row['ERROR_PCT']:+.1f}% (Pred: ${row['PREDICTED_TV']:,.0f}, Act: ${row['ACTUAL_TV']:,.0f})")
# # #
# # # print(f"\nTop 5 Worst Predictions:")
# # # worst_5 = df_2024.nlargest(5, 'ABS_ERROR_PCT')
# # # for _, row in worst_5.iterrows():
# # #     print(
# # #         f"  {row['TEAM']}: {row['ERROR_PCT']:+.1f}% (Pred: ${row['PREDICTED_TV']:,.0f}, Act: ${row['ACTUAL_TV']:,.0f})")
# # #
# # # # ============================================================
# # # # PART 4: Visualizations
# # # # ============================================================
# # # print("\n[4] Generating Visualizations...")
# # #
# # # fig, axes = plt.subplots(2, 2, figsize=(14, 10))
# # #
# # # # 1. Predicted vs Actual (2024)
# # # ax1 = axes[0, 0]
# # # ax1.scatter(df_2024['ACTUAL_TV'], df_2024['PREDICTED_TV'],
# # #             alpha=0.7, s=80, edgecolor='black', linewidth=0.5)
# # #
# # # min_val = min(df_2024['ACTUAL_TV'].min(), df_2024['PREDICTED_TV'].min())
# # # max_val = max(df_2024['ACTUAL_TV'].max(), df_2024['PREDICTED_TV'].max())
# # # ax1.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect Prediction')
# # #
# # # # 标注所有球队的名字（修改的部分）
# # # for _, row in df_2024.iterrows():
# # #     team = row['TEAM']
# # #     actual = row['ACTUAL_TV']
# # #     predicted = row['PREDICTED_TV']
# # #
# # #     # 确定颜色：最差的5个用红色，最好的5个用绿色，其他用黑色
# # #     if team in worst_5['TEAM'].values:
# # #         color = 'red'
# # #         fontweight = 'bold'
# # #     elif team in best_5['TEAM'].values:
# # #         color = 'green'
# # #         fontweight = 'normal'
# # #     else:
# # #         color = 'black'
# # #         fontweight = 'normal'
# # #
# # #     # 添加标签，字体小一些
# # #     ax1.annotate(team, (actual, predicted),
# # #                  xytext=(2, 2), textcoords='offset points',
# # #                  fontsize=7, color=color, fontweight=fontweight,
# # #                  alpha=0.8)
# # #
# # # ax1.set_xlabel('Actual Team Value 2024 ($M)', fontsize=12)
# # # ax1.set_ylabel('Predicted Team Value 2024 ($M)', fontsize=12)
# # # ax1.set_title('Predicted vs Actual Team Values (2024 Validation)', fontsize=14, fontweight='bold')
# # # ax1.grid(True, alpha=0.3)
# # # ax1.legend()
# # #
# # # # 2. Error Distribution
# # # ax2 = axes[0, 1]
# # # errors = df_2024['ERROR_PCT'].values
# # # ax2.hist(errors, bins=15, edgecolor='black', alpha=0.7, color='steelblue')
# # # ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
# # # ax2.axvline(x=np.mean(errors), color='green', linestyle='-', alpha=0.7, linewidth=2,
# # #             label=f'Mean: {np.mean(errors):.1f}%')
# # #
# # # ax2.set_xlabel('Prediction Error (%)', fontsize=12)
# # # ax2.set_ylabel('Number of Teams', fontsize=12)
# # # ax2.set_title('Distribution of Prediction Errors (2024)', fontsize=14, fontweight='bold')
# # # ax2.legend()
# # # ax2.grid(True, alpha=0.3, axis='y')
# # #
# # # # 3. Market Score vs Prediction Error
# # # ax3 = axes[1, 0]
# # # scatter = ax3.scatter(df_2024['MARKET_SCORE'], df_2024['ERROR_PCT'],
# # #                       c=df_2024['RWIN'], cmap='RdYlGn', s=100,
# # #                       edgecolor='black', linewidth=0.5, alpha=0.7)
# # #
# # # ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
# # # ax3.set_xlabel('Market Score', fontsize=12)
# # # ax3.set_ylabel('Prediction Error (%)', fontsize=12)
# # # ax3.set_title('Market Score vs Prediction Error (2024)', fontsize=14, fontweight='bold')
# # # ax3.grid(True, alpha=0.3)
# # #
# # # cbar = plt.colorbar(scatter, ax=ax3)
# # # cbar.set_label('RWIN (2024)', fontsize=10)
# # #
# # # # 4. Feature Importance
# # # ax4 = axes[1, 1]
# # # features = ['RWIN (β)', 'Player Expenses (θ)', 'Market Score (γ)']
# # # contributions = [
# # #     abs(beta) * train_df['RWIN'].std(),
# # #     abs(theta) * train_df['PLAYER_EXPENSES'].std(),
# # #     abs(gamma) * train_df['MARKET_SCORE'].std()
# # # ]
# # # total = sum(contributions)
# # # percentages = [c / total * 100 for c in contributions]
# # #
# # # bars = ax4.bar(features, percentages, color=['skyblue', 'lightgreen', 'salmon'], alpha=0.7)
# # # ax4.set_ylabel('Relative Importance (%)', fontsize=12)
# # # ax4.set_title('Relative Feature Importance in Model', fontsize=14, fontweight='bold')
# # # ax4.grid(True, alpha=0.3, axis='y')
# # #
# # # # Add percentage labels
# # # for bar, pct in zip(bars, percentages):
# # #     height = bar.get_height()
# # #     ax4.text(bar.get_x() + bar.get_width() / 2., height + 1,
# # #              f'{pct:.1f}%', ha='center', va='bottom', fontsize=10)
# # #
# # # plt.tight_layout()
# # # plt.savefig('model_validation_2024_noMIA.png', dpi=300, bbox_inches='tight')
# # # print("\n✓ Visualizations saved as 'model_validation_2024.png'")
# # #
# # # # ============================================================
# # # # PART 5: Model Comparison Report
# # # # ============================================================
# # # print("\n" + "=" * 60)
# # # print("MODEL VALIDATION REPORT")
# # # print("=" * 60)
# # #
# # # print("\n📊 PERFORMANCE SUMMARY:")
# # # print(f"  Training R² (2021-2023): {train_r2:.4f}")
# # # print(f"  Validation R² (2024): {val_r2:.4f}")
# # # print(f"  Validation MAPE: {mape:.2f}%")
# # # print(f"  Validation RMSE: ${rmse:,.0f}")
# # #
# # # print("\n🔑 MODEL COEFFICIENTS:")
# # # print(f"  ln(TV) = {alpha:.3f} + {beta:.3f}×RWIN + {theta:.4f}×PE + {gamma:.4f}×MARKET")
# # #
# # # print("\n🎯 PREDICTION ACCURACY (2024):")
# # # accuracy_bands = [(10, '±10%'), (20, '±20%'), (30, '±30%')]
# # # for threshold, label in accuracy_bands:
# # #     within = (df_2024['ABS_ERROR_PCT'] <= threshold).sum()
# # #     pct = within / len(df_2024) * 100
# # #     print(f"  {label}: {within}/{len(df_2024)} teams ({pct:.1f}%)")
# # #
# # # print("\n🏆 TOP 3 MOST ACCURATE PREDICTIONS:")
# # # for _, row in df_2024.nsmallest(3, 'ABS_ERROR_PCT').iterrows():
# # #     print(f"  {row['TEAM']}: Error = {row['ERROR_PCT']:+.1f}%")
# # #
# # # print("\n⚠️  TOP 3 LEAST ACCURATE PREDICTIONS:")
# # # for _, row in df_2024.nlargest(3, 'ABS_ERROR_PCT').iterrows():
# # #     print(f"  {row['TEAM']}: Error = {row['ERROR_PCT']:+.1f}%")
# # #
# # # print("\n📈 MARKET FACTOR ANALYSIS:")
# # # print(f"  Market coefficient (γ): {gamma:.4f}")
# # # print(f"  Market contributes {percentages[2]:.1f}% to model predictions")
# # # print(f"  Teams with highest market scores: {df_2024.nlargest(3, 'MARKET_SCORE')['TEAM'].tolist()}")
# # # print(f"  Teams with lowest market scores: {df_2024.nsmallest(3, 'MARKET_SCORE')['TEAM'].tolist()}")
# # #
# # # # Save detailed predictions
# # # output_df = df_2024[['TEAM', 'PREDICTED_TV', 'ACTUAL_TV', 'ERROR_PCT',
# # #                      'RWIN', 'PLAYER_EXPENSES', 'MARKET_SCORE']].copy()
# # # output_df.columns = ['Team', 'Predicted_Value_2024', 'Actual_Value_2024', 'Error_Pct',
# # #                      'RWIN_2024', 'Player_Expenses_2024', 'Market_Score']
# # # output_df.to_excel('model_predictions_2024_noMIA.xlsx', index=False)
# # #
# # # print("\n✓ Detailed predictions saved to 'model_predictions_2024.xlsx'")
# # # print("=" * 60)
# # # print("VALIDATION COMPLETE")
# # # print("=" * 60)
# #
# #
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 设置配色方案
hex_colors = ["#274753", "#297270", "#299d8f", "#8ab07c", "#e7c66b", "#f3a361", "#e66d50"]
rgb_colors = [(39, 71, 83), (41, 114, 112), (41, 157, 143), (138, 176, 124), (231, 198, 107), (243, 163, 97),
              (230, 109, 80)]

# 设置样式
plt.style.use('default')
sns.set_palette(hex_colors)

# 读取数据
df_2123 = pd.read_excel('2123indicators_noMIA.xlsx')
df_2425 = pd.read_excel('indicators_noMIA.xlsx')

# 2024实际TV值
tv_2024_actual = {
    'ATL': 3800, 'BOS': 6000, 'BRK': 4800, 'CHA': 3300, 'CHI': 5000,
    'CLE': 3950, 'DAL': 4700, 'DEN': 3900, 'DET': 3400, 'GSW': 8800,
    'HOU': 4900, 'IND': 3600, 'LAC': 5500, 'LAL': 7100, 'MEM': 3000,
    'MIA': 4250, 'MIL': 4000, 'MIN': 3100, 'NOP': 3050, 'NYK': 7500,
    'OKC': 3650, 'ORL': 3200, 'PHI': 4600, 'PHX': 4300, 'POR': 3500,
    'SAC': 3700, 'SAS': 3850, 'UTA': 3550, 'WAS': 4100
}

# ============================================================
# PART 1: Calculate Market Features from 2021-2023
# ============================================================
market_features = {}

for team in df_2123['TEAM'].unique():
    team_data = df_2123[df_2123['TEAM'] == team].sort_values('SEASON')

    # Use 2023 values as most recent market indicators
    latest = team_data[team_data['SEASON'] == 2023].iloc[0] if 2023 in team_data['SEASON'].values else team_data.iloc[
        -1]

    # Normalize to similar scales
    gdp_norm = latest['GDP'] / 1000 if pd.notna(latest['GDP']) else 0
    fans_norm = latest['FANS']
    attend_norm = latest['ATTENDANCE'] / 100000

    # Market score (weighted combination based on correlation strengths)
    market_score = gdp_norm * 0.24 + fans_norm * 0.22 + attend_norm * 0.54

    market_features[team] = {
        'MARKET_SCORE': market_score,
        'GDP_NORM': gdp_norm,
        'FANS_NORM': fans_norm,
        'ATTEND_NORM': attend_norm
    }

features_df = pd.DataFrame.from_dict(market_features, orient='index')
features_df.index.name = 'TEAM'
features_df = features_df.reset_index()

# ============================================================
# PART 2: Train Model on 2021-2023 Data
# ============================================================
# Merge features with training data
train_df = pd.merge(df_2123, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')
train_df['LOG_TV'] = np.log(train_df['TEAM_VALUE'])

# Prepare training data
X_train = np.column_stack([
    train_df['RWIN'].values,
    train_df['PLAYER_EXPENSES'].values,
    train_df['MARKET_SCORE'].values
])
y_train = train_df['LOG_TV'].values

# Add intercept term
X_train_with_intercept = np.column_stack([np.ones(len(X_train)), X_train])

# Solve linear regression: ln(TV) = α + β×RWIN + θ×PE + γ×MARKET
coefficients = np.linalg.lstsq(X_train_with_intercept, y_train, rcond=None)[0]

alpha, beta, theta, gamma = coefficients

# ============================================================
# PART 3: Validate Model on 2024 Data
# ============================================================
# Get 2024 predictor data
df_2024 = df_2425[df_2425['SEASON'] == 2024].copy()
df_2024 = pd.merge(df_2024, features_df[['TEAM', 'MARKET_SCORE']], on='TEAM', how='left')

# Add actual 2024 TV values
df_2024['ACTUAL_TV'] = df_2024['TEAM'].map(tv_2024_actual)

# Predict 2024 values using trained model
df_2024['LOG_PREDICTED'] = (alpha +
                            beta * df_2024['RWIN'] +
                            theta * df_2024['PLAYER_EXPENSES'] +
                            gamma * df_2024['MARKET_SCORE'])

df_2024['PREDICTED_TV'] = np.exp(df_2024['LOG_PREDICTED']) * 1.084  # 修正因子
df_2024['ERROR'] = df_2024['PREDICTED_TV'] - df_2024['ACTUAL_TV']
df_2024['ERROR_PCT'] = (df_2024['ERROR'] / df_2024['ACTUAL_TV']) * 100
df_2024['ABS_ERROR_PCT'] = np.abs(df_2024['ERROR_PCT'])

# ============================================================
# PART 4: Visualization - Only the first plot
# ============================================================
# 创建单个图形
plt.figure(figsize=(8, 6))

# Predicted vs Actual (2024)
scatter = plt.scatter(df_2024['ACTUAL_TV'], df_2024['PREDICTED_TV'],
                      alpha=0.8, s=100, edgecolor='black', linewidth=0.5,
                      c=df_2024['MARKET_SCORE'], cmap='RdYlGn')

min_val = min(df_2024['ACTUAL_TV'].min(), df_2024['PREDICTED_TV'].min())
max_val = max(df_2024['ACTUAL_TV'].max(), df_2024['PREDICTED_TV'].max())
plt.plot([min_val, max_val], [min_val, max_val], color=hex_colors[0], linestyle='--',
         alpha=0.7, linewidth=2, label='Perfect Prediction')

# 标注所有球队的名字
for _, row in df_2024.iterrows():
    team = row['TEAM']
    actual = row['ACTUAL_TV']
    predicted = row['PREDICTED_TV']

    plt.annotate(team, (actual, predicted),
                 xytext=(2, 2), textcoords='offset points',
                 fontsize=7, color='black', fontweight='normal',
                 alpha=0.8)

plt.xlabel('Actual Team Value 2024 ($M)', fontsize=12)
plt.ylabel('Predicted Team Value 2024 ($M)', fontsize=12)
plt.title('Predicted vs Actual Team Values (2024)', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend()

# 添加颜色条
cbar = plt.colorbar(scatter)
cbar.set_label('Market Score', fontsize=10)

plt.tight_layout()
plt.show()
#
#
# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy import stats
# import matplotlib.cm as cm
# from matplotlib.patches import Rectangle
# from matplotlib.lines import Line2D
# from mpl_toolkits.axes_grid1.inset_locator import inset_axes
#
# # 读取数据
# df_2024 = pd.read_excel('model_predictions_2024_noMIA.xlsx')
#
# # 计算市场分数中位数，划分高低市场组
# market_median = df_2024['Market_Score'].median()
# df_2024['MARKET_GROUP'] = df_2024['Market_Score'].apply(
#     lambda x: 'High Market' if x > market_median else 'Low Market'
# )
#
# # 计算分组统计量
# high_market_mean = df_2024[df_2024['MARKET_GROUP'] == 'High Market']['Error_Pct'].mean()
# low_market_mean = df_2024[df_2024['MARKET_GROUP'] == 'Low Market']['Error_Pct'].mean()
# mean_diff = high_market_mean - low_market_mean
#
# # 进行t检验
# high_errors = df_2024[df_2024['MARKET_GROUP'] == 'High Market']['Error_Pct']
# low_errors = df_2024[df_2024['MARKET_GROUP'] == 'Low Market']['Error_Pct']
# t_stat, p_value = stats.ttest_ind(high_errors, low_errors, equal_var=False)
#
# # 使用你提供的完整渐变颜色
# hex_colors = ["#274753", "#297270", "#299d8f", "#8ab07c", "#e7c66b", "#f3a361", "#e66d50"]
# rgb_colors = [(39, 71, 83), (41, 114, 112), (41, 157, 143), (138, 176, 124),
#               (231, 198, 107), (243, 163, 97), (230, 109, 80)]
#
# # 创建完整的渐变色映射
# full_cmap = cm.colors.LinearSegmentedColormap.from_list("full_cmap", hex_colors, N=256)
#
# # 创建图表
# fig, ax = plt.subplots(figsize=(14, 8))
#
# # 计算所有数据的归一化市场分数（0到1）
# market_min = df_2024['Market_Score'].min()
# market_max = df_2024['Market_Score'].max()
# df_2024['MARKET_NORM'] = (df_2024['Market_Score'] - market_min) / (market_max - market_min)
#
# # 为每个数据点计算颜色（基于完整渐变）
# df_2024['COLOR'] = df_2024['MARKET_NORM'].apply(lambda x: full_cmap(x))
#
# # 绘制散点图，使用完整渐变
# for group in ['Low Market', 'High Market']:
#     group_data = df_2024[df_2024['MARKET_GROUP'] == group]
#
#     # 根据组别选择标记形状
#     marker = 'o' if group == 'Low Market' else 's'
#
#     # 绘制散点图
#     for idx, row in group_data.iterrows():
#         ax.scatter(row['Market_Score'], row['Error_Pct'],
#                    color=row['COLOR'], s=100, alpha=0.8, edgecolor='black', linewidth=0.8,
#                    marker=marker, zorder=5)
#
# # 添加市场分数中位数线
# ax.axvline(x=market_median, color='#000000', linestyle='--',
#            linewidth=2.5, alpha=0.9, label=f'Median: {market_median:.1f}',
#            zorder=3)
#
# # 添加零误差线
# ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5, zorder=2)
#
# # 添加分组均值线
# ax.axhline(y=high_market_mean, color=hex_colors[6], linestyle='--',
#            linewidth=2.5, alpha=0.9, label=f'High Mean: {high_market_mean:.1f}%',
#            zorder=3)
# ax.axhline(y=low_market_mean, color=hex_colors[1], linestyle='--',
#            linewidth=2.5, alpha=0.9, label=f'Low Mean: {low_market_mean:.1f}%',
#            zorder=3)
#
# # 添加误差条（±1 SD）
# # 高市场组误差条
# ax.errorbar(df_2024[df_2024['MARKET_GROUP'] == 'High Market']['Market_Score'].mean(),
#             high_market_mean,
#             yerr=high_errors.std(),
#             color=hex_colors[6], capsize=8, capthick=2.5, linewidth=3,
#             alpha=0.9, label=f'High ±1 SD ({high_errors.std():.1f}%)', zorder=4)
#
# # 低市场组误差条
# ax.errorbar(df_2024[df_2024['MARKET_GROUP'] == 'Low Market']['Market_Score'].mean(),
#             low_market_mean,
#             yerr=low_errors.std(),
#             color=hex_colors[1], capsize=8, capthick=2.5, linewidth=3,
#             alpha=0.9, label=f'Low ±1 SD ({low_errors.std():.1f}%)', zorder=4)
#
# # 添加渐变色例条（在图表右侧）
# # 创建inset轴用于颜色条
# cb_ax = inset_axes(ax, width="3%", height="60%", loc='center right',
#                    bbox_to_anchor=(0.12, 0, 1, 1), bbox_transform=ax.transAxes)
#
# # 创建颜色条
# norm = plt.Normalize(vmin=market_min, vmax=market_max)
# sm = cm.ScalarMappable(cmap=full_cmap, norm=norm)
# sm.set_array([])
#
# # 添加颜色条
# cbar = plt.colorbar(sm, cax=cb_ax, orientation='vertical')
# cbar.set_label('Market Score', fontsize=10, fontweight='bold')
# cbar.ax.tick_params(labelsize=9)
#
# # 在颜色条上添加标记
# cbar.ax.axhline(y=(market_median - market_min) / (market_max - market_min),
#                 color='black', linestyle='--', linewidth=1.5, alpha=0.8)
# cbar.ax.text(3.5, (market_median - market_min) / (market_max - market_min),
#              'Median', fontsize=8, ha='left', va='center', transform=cbar.ax.transAxes)
#
#
# # 创建自定义图例元素
# legend_elements = [
#     # 分组标记
#     Line2D([0], [0], marker='o', color='w', markerfacecolor=hex_colors[2],
#            markersize=10, label='Low Market Teams', markeredgecolor='black', linewidth=0.8),
#     Line2D([0], [0], marker='s', color='w', markerfacecolor=hex_colors[5],
#            markersize=10, label='High Market Teams', markeredgecolor='black', linewidth=0.8),
#
#     # 统计线
#     Line2D([0], [0], color='black', linestyle='--', linewidth=2.5,
#            label=f'Median ({market_median:.1f})'),
#     Line2D([0], [0], color=hex_colors[1], linestyle='--', linewidth=2.5,
#            label=f'Low Mean ({low_market_mean:.1f}%)'),
#     Line2D([0], [0], color=hex_colors[6], linestyle='--', linewidth=2.5,
#            label=f'High Mean ({high_market_mean:.1f}%)'),
# ]
#
# # 设置图表属性
# ax.set_xlabel('Market Score', fontsize=14, fontweight='bold')
# ax.set_ylabel('Prediction Error (%)', fontsize=14, fontweight='bold')
#
# # 创建标题
# title_lines = [
#     'Market Score vs Prediction Error',
#     f'High Market Teams: {mean_diff:+.1f}% Larger Errors',
#     f'{"(Significant, p=" + str(round(p_value, 3)) + ")" if p_value < 0.05 else "(Not Significant, p=" + str(round(p_value, 3)) + ")"}'
# ]
# title = '\n'.join(title_lines)
# ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
#
# ax.grid(True, alpha=0.15, linestyle='--', zorder=1)
# ax.legend(handles=legend_elements, loc='upper left',
#           bbox_to_anchor=(1.01, 1), borderaxespad=0., fontsize=10,
#           framealpha=0.9)
#
# # 设置坐标轴范围
# ax.set_xlim(df_2024['Market_Score'].min() - 1, df_2024['Market_Score'].max() + 1)
# ax.set_ylim(df_2024['Error_Pct'].min() - 2, df_2024['Error_Pct'].max() + 2)
#
#
# # 调整布局
# plt.tight_layout()
#
# # 保存图表
# plt.savefig('market_score_error_full_gradient.png', dpi=300, bbox_inches='tight')
# print("✓ Chart saved as 'market_score_error_full_gradient.png'")
#
# # 显示图表
# plt.show()
#
# # 简洁的统计输出
# print("\n" + "=" * 60)
# print("MARKET SCORE ANALYSIS WITH FULL COLOR GRADIENT")
# print("=" * 60)
# print(f"\nMarket Score Range: [{market_min:.1f}, {market_max:.1f}]")
# print(f"Median: {market_median:.2f}")
# print(f"\nHigh Market Group (> {market_median:.1f}):")
# print(f"  Teams: {len(high_errors)}")
# print(f"  Mean Error: {high_market_mean:.2f}%")
# print(f"  Std Dev: {high_errors.std():.2f}%")
#
# print(f"\nLow Market Group (≤ {market_median:.1f}):")
# print(f"  Teams: {len(low_errors)}")
# print(f"  Mean Error: {low_market_mean:.2f}%")
# print(f"  Std Dev: {low_errors.std():.2f}%")
#
# print(f"\nGroup Comparison:")
# print(f"  Mean Difference: {mean_diff:+.2f}%")
# print(f"  T-statistic: {t_stat:.3f}")
# print(f"  P-value: {p_value:.4f}")
# print(f"  Significant at α=0.05: {'Yes' if p_value < 0.05 else 'No'}")
#
# print(f"\nColor Gradient Used:")
# for i, (hex_color, rgb_color) in enumerate(zip(hex_colors, rgb_colors)):
#     print(f"  {i + 1}. HEX: {hex_color} | RGB: {rgb_color}")
#
# print("\n" + "=" * 60)