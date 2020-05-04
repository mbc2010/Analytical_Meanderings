# Importing all the libraries we need
import pandas as pd
import numpy as np
import collections
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
import matplotlib.pyplot as plt
import seaborn as sns
import re
import math

# Some initalizations to help our ETL phase
player_data = pd.DataFrame()
hand = pd.DataFrame()
hand_history = pd.DataFrame()

index = 0
num_players = 0
position_counter = 0
active_infront = 0
stage = ['blinds','preflop', 'flop', 'turn', 'river']
stage_counter = 0
pot_size = 0
flop1 = ""
flop2 = ""
flop3 = ""
turn = ""
river = ""
raw_hands = pd.DataFrame()

# Computationaly intensive ETL code. The repository contains the output entitled "HANDS.csv"
files = [str(item) for item in range(1,20)]

for file in files:
    raw_hands = raw_hands.append(
        pd.read_csv('C:/poker/anon_files/' + file + '.txt', header=None, error_bad_lines=False, warn_bad_lines=False),
        ignore_index=True)

# I need to learn regex
for line in raw_hands.iloc[:, 0]:

    if 'PokerStars Hand #' in line:
        game_id = line.split('#')[1].split(":")[0]

    elif 'is the button' in line:
        button = int(line.split()[-4].split("#")[1])

    elif re.search(r'Seat [0-9]+:' and 'in chips', line):
        num_players += 1
        split = line.split()

        current_player = pd.DataFrame({
            "Player Name": str(split[2]),
            "Starting Stack": float(split[-3][2:]),
            "Position": 100,
            "Card 1": '',
            "Card 2": '',
            "Game ID": game_id,}, index=[0])

        player_data = player_data.append(current_player, ignore_index=True)

    elif re.search(r'posts [a-z]+ blind', line):
        hand.loc[index, 'Player Name'] = line.split()[0].split(':')[0]
        hand.loc[index, 'Action'] = line.split()[-3] + ' blind'
        hand.loc[index, 'Amount'] = float(line.split()[-1][1:])
        hand.loc[index, 'Stage'] = stage[stage_counter]
        pot_size += hand.loc[index, 'Amount']
        hand.loc[index, 'Invested Post Action'] = hand.loc[index, 'Amount']
        hand.loc[index, 'Starting Stack'] = player_data[player_data['Player Name'] == hand.loc[index, 'Player Name']]['Starting Stack'].sum()
        hand.loc[index, 'Invested Pre Action'] = 0
        hand.loc[index, 'Remaining Pre Action'] = hand.loc[index, 'Starting Stack']

        if player_data[player_data['Player Name'] == hand.loc[index, 'Player Name']].iloc[0, :].loc['Position'] == 100:
            player_data.loc[player_data['Player Name'] == hand.loc[index, 'Player Name'], 'Position'] = position_counter
            position_counter += 1

        index += 1

        if 'posts big blind' in line:
            stage_counter += 1

    elif 'folds' in line or 'checks' in line or 'calls' in line or 'bets' in line or 'raises' in line:
        hand.loc[index, 'Player Name'] = line.split()[0].split(':')[0]
        hand.loc[index, 'Flop 1'] = flop1
        hand.loc[index, 'Flop 2'] = flop2
        hand.loc[index, 'Flop 3'] = flop3
        hand.loc[index, 'Turn'] = turn
        hand.loc[index, 'River'] = river
        hand.loc[index, 'Active'] = active_infront
        hand.loc[index, 'Stage'] = stage[stage_counter]

        if player_data[player_data['Player Name'] == hand.loc[index, 'Player Name']].iloc[0, :].loc['Position'] == 100:
            player_data.loc[player_data['Player Name'] == hand.loc[index, 'Player Name'], 'Position'] = position_counter
            position_counter += 1

        prior_action = hand[hand['Player Name'] == hand.loc[index, 'Player Name']]['Invested Post Action'].max()
        if math.isnan(prior_action):
            prior_action = 0
        hand.loc[index, 'Invested Pre Action'] = prior_action

        hand.loc[index, 'Starting Stack'] = player_data[player_data['Player Name'] == line.split()[1]]['Starting Stack'].sum()
        hand.loc[index, 'Remaining Pre Action'] = hand.loc[index, 'Starting Stack'] - hand.loc[index, 'Invested Pre Action']
        hand.loc[index, 'Pot Size'] = pot_size
        hand.loc[index, 'Amount to Call'] = hand['Invested Post Action'].max() - prior_action

        if 'folds' in line:
            hand.loc[index, 'Action'] = 'folds'
            hand.loc[index, 'Invested Post Action'] = hand.loc[index, 'Invested Pre Action']
        elif 'checks' in line or 'calls' in line:
            hand.loc[index, 'Action'] = 'calls'
            hand.loc[index, 'Invested Post Action'] = hand.loc[index, 'Invested Pre Action'] + hand.loc[index, 'Amount to Call']
            if 'calls' in line:
                active_infront += 1
        elif 'bets' in line or 'raises' in line:
            hand.loc[index, 'Action'] = 'raises'
            hand.loc[index, 'Amount'] = float(line.split('$')[-1].split()[0])
            active_infront += 1

            prior_stage = hand[hand['Stage'] == stage[stage_counter - 1]]['Invested Post Action'].max()

            if math.isnan(prior_stage):
                prior_stage = 0

            hand.loc[index, 'Invested Post Action'] = hand.loc[index, 'Amount'] + prior_stage
            pot_size += hand.loc[index, 'Invested Post Action'] - hand.loc[index, 'Invested Pre Action']

        index += 1


    elif '*** FLOP ***' in line:
        flop1 = line.split()[-1][:-1]
        flop2 = line.split()[-2]
        flop3 = line.split()[-3][1:]
        stage_counter += 1

    elif '*** TURN ***' in line:
        turn = line.split()[-1][1:-1]
        stage_counter += 1

    elif '*** RIVER ***' in line:
        river = line.split()[-1][1:-1]
        stage_counter += 1

    elif '(a hand...)' in line:
        name = line.split()[0].split(':')[0]
        player_data.loc[player_data['Player Name'] == name, 'Card 1'] = line.split()[-4][1:]
        player_data.loc[player_data['Player Name'] == name, 'Card 2'] = line.split()[-3][:-1]

    elif '*** SUMMARY ***' in line:
        hand['Number of Players'] = num_players
        hand = hand.drop('Starting Stack', axis=1)
        hand = pd.merge(hand, player_data, on='Player Name', how='left')
        player_data = player_data.iloc[0:0]
        hand_history = hand_history.append(hand, ignore_index=True)
        hand = pd.DataFrame()
        position_counter = 0
        stage_counter = 0
        pot_size = 0
        num_players = 0
        active_infront = 0
        flop1 = ""
        flop2 = ""
        flop3 = ""
        turn = ""
        river = ""

hand_history = hand_history[hand_history['Action'] != 'small blind']
hand_history = hand_history[hand_history['Action'] != 'big blind'].reset_index(drop=True)
hand_history = hand_history[hand_history['Stage']=='preflop'].reset_index(drop=True)

# This function breaks down a card string (e.g. Ac) into a distint float value and a string for the suit
def card_breakdown(df, card, value_col, suit_col):
	df[value_col] = df[df[card] != ""][card].str[:-1]
	card_values = {'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
	df[value_col].replace(card_values, inplace=True)
	df[value_col] = df[value_col].astype('float')
	df[suit_col] = df[df[card] != ""][card].str[-1]
	return

# Breaking down all the recorded card values
card_breakdown(hand_history, 'Card 1', 'Value 1', 'Suit 1')
card_breakdown(hand_history, 'Card 2', 'Value 2', 'Suit 2')
card_breakdown(hand_history, 'Flop 1', 'Value Flop1', 'Suit Flop1')
card_breakdown(hand_history, 'Flop 2', 'Value Flop2', 'Suit Flop2')
card_breakdown(hand_history, 'Flop 3', 'Value Flop3', 'Suit Flop3')
card_breakdown(hand_history, 'Turn', 'Value Turn', 'Suit Turn')
card_breakdown(hand_history, 'River', 'Value River', 'Suit River')

# descriptive metrics for suits
def suitCounter(suit_string):
	if len(suit_string) !=0:
		return collections.Counter(suit_string).most_common(1)[0][1]
	else:
		return 0

hand_history['Common Suits'] = hand_history['Suit Flop1'].fillna('') + hand_history['Suit Flop2'].fillna('') + hand_history['Suit Flop3'].fillna('') + hand_history['Suit Turn'].fillna('') + hand_history['Suit River'].fillna('')
hand_history['Player Suits'] = hand_history['Common Suits'] + hand_history['Suit 1'] + hand_history['Suit 2']
hand_history['Common Suits'] = hand_history['Common Suits'].apply(suitCounter)
hand_history['Player Suits'] = hand_history['Player Suits'].apply(suitCounter)
hand_history['Raise Amount'] = hand_history['Amount'] - hand_history['Amount to Call']
hand_history['Raise Amount'] = hand_history['Raise Amount'].fillna(0)
features_pre = ['Value 1', 'Value 2', 'Player Suits', 'Amount to Call', 'Pot Size', 'Remaining Pre Action', 'Position', 'Active', 'Invested Pre Action', 'Starting Stack', 'Game ID']

hand_history['actions'] = hand_history['Action']
hand_history = pd.get_dummies(hand_history, columns=['Action'])

labels_col = ['Action_calls', 'Action_folds', 'Action_raises', 'Raise Amount']
labels = hand_history.loc[:, labels_col]

hand_history.to_csv('C:/poker/anon_files/HANDS.csv')

# This code block scales and transforms features and labels into normally distributed data
# Without the normalization, our MLP algorthirm throws errors
scaler = StandardScaler()
scaler = scaler.fit(hand_history[features_pre])
standardized = scaler.transform(hand_history[features_pre])

scaler_label = StandardScaler()
scaler_label = scaler_label.fit(labels)
labels = scaler_label.transform(labels)

highest_train_row = int(hand_history.shape[0] * .80)
train_x = standardized[0:highest_train_row]
test_x = standardized[highest_train_row:]
train_y = labels[0:highest_train_row]
test_y = labels[highest_train_row:]

# Our linear regression code block
lir = LinearRegression()
lir.fit(train_x, train_y)
predictions = lir.predict(test_x)
predictions = scaler_label.inverse_transform(predictions)
predictions = pd.DataFrame(predictions, columns = ['calls', 'folds', 'raises', 'Raise Amount'])
lin_results = predictions.iloc[:,:3].idxmax(axis=1)

mlp = MLPRegressor(hidden_layer_sizes=(100,100), activation='logistic', max_iter=2000)
mlp.fit(train_x, train_y)
predictions = mlp.predict(test_x)
predictions = scaler_label.inverse_transform(predictions)
predictions = pd.DataFrame(predictions, columns = ['calls', 'folds', 'raises', 'Raise Amount'])
ML_results = predictions.iloc[:,:3].idxmax(axis=1)

test_results = pd.DataFrame({
    "Action":hand_history.loc[highest_train_row:,'actions'].reset_index(drop=True),
    "ML_results":ML_results,
    "lin_results":lin_results})

lin_acc = test_results[test_results['Action']==test_results['lin_results']].shape[0]/test_results.shape[0]
ML_acc = test_results[test_results['Action']==test_results['ML_results']].shape[0]/test_results.shape[0]

print(lin_acc)
print(ML_acc)
hand_history.to_csv('C:/poker/anon_files/processeddata.csv')

ML = test_results.pivot_table(index='Action', columns='ML_results', aggfunc='size', fill_value=0)
lin = test_results.pivot_table(index='Action', columns='lin_results', aggfunc='size', fill_value=0)
print(ML)
print(lin)

viz = hand_history[features_pre]

# Compute the correlation matrix
corr = viz.corr()
mask = np.triu(np.ones_like(corr, dtype=np.bool))

# Generate a custom diverging colormap
cmap = sns.diverging_palette(220, 10, as_cmap=True)

# Draw the heatmap with the mask and correct aspect ratio
sns.heatmap(corr, mask=mask, cmap=cmap, vmax=.3, center=0,
            square=True, linewidths=.5, cbar_kws={"shrink": .5})
plt.show()