# chessead-elo-heroku
Heroku deployment of Chessead Elo ranking app with Google Sheets API integration.

<a href="https://jbachlombardo.wordpress.com/2020/02/26/heroku-the-google-sheets-api-deploying-chesseads-elo-calculator/">Brief writeup here.</a>

#### chessead_elo_sheets.py
Script to read / write sheet: 
- input: game results reported through Google Form
- process: calculating new Elo rankings (new players given an initial ranking of 1000)
- output: write updated Elo rankings to secondary Google Sheet and update front page with clean, ordered rankings

#### chessead_elo_sheets_fullrun_fix.py
Same as deployed chessead_elo_sheets.py, but written to recalculate in a single shot if rankings need to be redone (eg certain game results must be removed)

#### clock.py
Scheduler deployed to Heroku (runs 1x per week, on Sundays)

#### requirements.txt
Dependencies for Heroku

#### Procfile
Clock dyno deploy

*Keys file not uploaded*
