import os

# Minimum reports number for calculating propability
MIN_REPORTS = 1

KEYBOARD = [['/report גדול נקי', '/report קטן נקי'], 
            ['/report גדול רס"ר', '/report קטן רס"ר'],
            ['מה המצב?']]

# the rate of change towards rasar/clean
CLEAN_FACTOR =  0.75 
RASAR_FACTOR = 0.5

# Getting mode, so we could define run function for local and Heroku setup
MODE = os.getenv("MODE")
BOT_TOKEN = os.getenv("TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
