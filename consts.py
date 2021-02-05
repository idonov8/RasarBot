import os
from dotenv import load_dotenv
load_dotenv()

# Minimum reports number for calculating propability
MIN_REPORTS = 1

BASE_KEYBOARD = [['/report גדול נקי', '/report קטן נקי'], 
            ['/report גדול מלוכלך', '/report קטן מלוכלך'],
            ['מה המצב?']]

SECOND_KEYBOARD = [['/cancel_report', '/new_report', '/send_feedback'],
                    ['מה המצב?']]
STATE_KEYBOARD = [['מ"צ'], ['רס"ר'], ['מניונית'],['איציק']]
# the rate of change towards rasar/clean
CLEAN_FACTOR =  0.75 
DIRTY_FACTOR = 0.5

# Getting mode, so we could define run function for local and Heroku setup
MODE = os.getenv("MODE")
BOT_TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
