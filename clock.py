from apscheduler.schedulers.blocking import BlockingScheduler
import runpy

scheduler = BlockingScheduler()

def elo_job() :
    runpy.run_path('chessead_elo_sheets.py')

# scheduler.add_job(elo_job, 'interval', weeks = 1, start_date='2020-02-16 12:00:00')
scheduler.add_job(elo_job, 'cron', day_of_week = 'wed, sun', hour = 12)

scheduler.start()
