import pandas as pd
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import sys

# ----- Custom functions -----

def make_result_numeric(x) :
    """Translate string results to numbers"""
    if x == 'Win': x = 1
    elif x == 'Loss': x = 0
    else : x = 0.5
    return x

def calculate_elo(player, results_df, current_elo_df, new_player = False, starting_elo = 1000, k = 32) :
    """Calculate Elo for existing / new players based on results"""
    if new_player :
        current_elo = starting_elo
    else :
        current_elo = current_elo_df.loc[current_elo_df['Name'] == player, 'Elo'].item()
    host = results_df.loc[results_df['You'] == player]
    guest = results_df.loc[results_df['Opponent'] == player]
    guest['Result01'] = abs(guest['Result01'] - 1) #Result when entered as opponent is inverse of real result
    personal_results = pd.DataFrame(columns = ['Opponent', 'Result01'])
    personal_results = pd.concat([personal_results, host[['Opponent', 'Result01']], guest[['You', 'Result01']].rename(columns = {'You': 'Opponent'})])
    personal_results = personal_results.merge(current_elo_df.set_index('Name')['Elo'], left_on = 'Opponent', right_index = True, how = 'left')
    personal_results['Elo'] = personal_results['Elo'].fillna(starting_elo)
    personal_results['E_Result01'] = personal_results['Elo'].apply(lambda x: 1/(1 + 10**((x - current_elo)/400)))
    score = personal_results['Result01'].sum()
    expected_score = personal_results['E_Result01'].sum()
    new_elo = round(current_elo + (k * (score - expected_score)))
    n_games = len(personal_results)
    return new_elo, n_games

# ----- Authorize access -----
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('chessead-secret.json', scope)
client = gspread.authorize(creds)

# ----- Access sheet -----
elo_gsheet = client.open('Chessead Elo rankings')

# ----- Get results data and fix dtypes -----
results_sheet = elo_gsheet.worksheet('Results Form Responses')
results_list = results_sheet.get_all_values()
results = pd.DataFrame(results_list[1:], columns = results_list[0])
results['Timestamp'] = pd.to_datetime(results['Timestamp'])
results['Result01'] = results['Result'].apply(make_result_numeric)

# # ----- Importing from downloaded excel for update, fix dtypes -----
# results = pd.read_excel('Update_results/results_110420_forupdate.xlsx', sheet_name = 'Results Form Responses')
# results['Timestamp'] = pd.to_datetime(results['Timestamp'])
# results['Result01'] = results['Result'].apply(make_result_numeric)

# ----- Group results by week and iterate through -----
current = pd.DataFrame(columns = ['Name', 'Elo', 'Games played'])

for name, week in results.set_index('Timestamp').groupby(pd.Grouper(freq = 'W')) :

    # ----- Get all players -----
    yous = week['You'].unique()
    opponents = week['Opponent'].unique()
    played_game = list()
    for l in [yous, opponents] :
        for p in l :
            if p in played_game :
                continue
            else :
                played_game.append(p)

    did_not_play = [x for x in current['Name'] if x not in played_game]

    # ----- Calculate new Elos -----
    updates = {}

    for p in played_game :
        if p in current['Name'].to_list() :
            updates[p] = calculate_elo(p, week, current)
        else :
            updates[p] = calculate_elo(p, week, current, new_player = True)
    updated_elos = pd.DataFrame.from_dict(updates, orient = 'index').reset_index().rename(columns = {'index': 'Name', 0: 'Elo', 1: 'Games played'})

    for player in updated_elos['Name'] :
        if player in current['Name'].to_list() :
            current.loc[current['Name'] == player, 'Elo'] = updated_elos.loc[updated_elos['Name'] == player, 'Elo'].item()
            current.loc[current['Name'] == player, 'Games played'] += updated_elos.loc[updated_elos['Name'] == player, 'Games played'].item()
        else :
            current = current.append(updated_elos.loc[updated_elos['Name'] == player])

current['Last update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

# ----- Remove old Elo sheet, create new sheet for updated Elos -----
current_sheet = elo_gsheet.worksheet('INSEAD Elo rankings')
elo_gsheet.del_worksheet(current_sheet)
new_current_sheet = elo_gsheet.add_worksheet('INSEAD Elo rankings', rows = len(updated_elos), cols = 10)
new_current_sheet.insert_row(list(current.columns), 1)
row_num = 2
for i, row in current.sort_values(by = 'Elo', ascending = False).iterrows() :
    new_current_sheet.insert_row(list(row), row_num)
    row_num += 1

# ----- Redo Elo frontpage -----
inseadelo = elo_gsheet.worksheet('INSEADElo')
for n in np.arange(2, len(current) + 2) :
    inseadelo.update_acell('A{}'.format(n), '=if(isnumber(C{}),RANK(C{},C:C),"")'.format(n, n))
    inseadelo.update_acell('B{}'.format(n), "='INSEAD Elo rankings'!A{}".format(n, n))
    inseadelo.update_acell('C{}'.format(n), "='INSEAD Elo rankings'!B{}".format(n, n))
    inseadelo.update_acell('D{}'.format(n), "='INSEAD Elo rankings'!C{}".format(n, n))
