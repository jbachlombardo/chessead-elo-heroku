# chessead-elo-heroku
Heroku deployment of Chessead Elo ranking app with Google Sheets API integration

#### chessead_elo_sheets.py
Script to read / write sheet: 
- input: game results reported through Google Form
- process: calculating new Elo rankings
- output: write updated Elo rankings to secondary Google Sheet and update front page with clean, ordered rankings

#### clock.py
Scheduler deployed to Heroku

#### requirements.txt
Dependencies for Heroku

#### Procfile
Clock dyno deploy

*Keys file not uploaded*
