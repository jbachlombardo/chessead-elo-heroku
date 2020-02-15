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
    return new_elo

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

# ----- Get current Elo stats and fix dtypes / get last update -----
current_sheet = elo_gsheet.worksheet('INSEAD Elo rankings')
current_list = current_sheet.get_all_values()
if len(current_list) > 1 :
    current = pd.DataFrame(current_list[1:], columns = current_list[0])
    current['Last update'] = pd.to_datetime(current['Last update'])
    last_update = current['Last update'].loc[0]
    current['Elo'] = pd.to_numeric(current['Elo'])
else :
    current = pd.DataFrame(columns = current_list[0])
    last_update = pd.to_datetime('1/1/20')

# ----- Filter results for date, check to run, fix dtypes -----
results = results[results['Timestamp'] > last_update]
if len(results) == 0 : # Quit if no new results to calculate
    sys.exit()
results['Result01'] = results['Result'].apply(make_result_numeric)

# ----- Get all players -----
yous = results['You'].unique()
opponents = results['Opponent'].unique()
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

if len(current) > 0 : # Only run if players already in system
    for p in did_not_play :
        updates[p] = current_elo = current.loc[current['Name'] == p, 'Elo'].item()

for p in played_game :
    if p in current['Name'].to_list() :
        updates[p] = calculate_elo(p, results, current)
    else :
        updates[p] = calculate_elo(p, results, current, new_player = True)

updated_elos = pd.DataFrame.from_dict(updates, orient = 'index').reset_index().rename(columns = {'index': 'Name', 0: 'Elo'})
updated_elos['Last update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

# ----- Remove old Elo sheet, create new sheet for updated Elos -----
elo_gsheet.del_worksheet(current_sheet)
new_current_sheet = elo_gsheet.add_worksheet('INSEAD Elo rankings', rows = len(updated_elos), cols = 10)
new_current_sheet.insert_row(list(updated_elos.columns), 1)
row_num = 2
for i, row in updated_elos.sort_values(by = 'Elo', ascending = False).iterrows() :
    new_current_sheet.insert_row(list(row), row_num)
    row_num += 1

# ----- Redo Elo frontpage -----
inseadelo = elo_gsheet.worksheet('INSEADElo')
for n in np.arange(2, len(updated_elos) + 2) :
    inseadelo.update_acell('A{}'.format(n), '=if(isnumber(C{}),RANK(C{},C:C),"")'.format(n, n))
    inseadelo.update_acell('B{}'.format(n), "='INSEAD Elo rankings'!A{}".format(n, n))
    inseadelo.update_acell('C{}'.format(n), "='INSEAD Elo rankings'!B{}".format(n, n))
