import os
import telegram
from telegram.ext import  Updater, InlineQueryHandler, CommandHandler, Defaults, Job, MessageHandler, Filters
import requests # to make requests to external api
import re # regex for pictures of doggos
import logging
from datetime import datetime # use to restart everyday 
import sys

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

reports = []

shags_situation = {
        'גדול': {
            'isRasar':0 # is rasar is a number between 0 and 1, 1- rasar, 0 clean
        },
        'קטן':{
            'isRasar':0
        }
    }

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
BOT_TOKEN = os.getenv("TOKEN")
if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=BOT_TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, BOT_TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)

# When developing, I can use the dev_token and test on RasarDevBot
# DON'T FORGET to change back to bot_token before git commiting.

ADMIN_ID = os.getenv("ADMIN_ID")
KEYBOARD = [['/report גדול נקי', '/report קטן נקי'], 
            ['/report גדול רס"ר', '/report קטן רס"ר'],
            ['מה המצב?']]

# the rate of change towards rasar/clean
CLEAN_FACTOR =  0.75 
RASAR_FACTOR = 0.5

# Get random dog image for the memes
def get_url():
    contents = requests.get('https://random.dog/woof.json').json()
    image_url = contents['url']
    return image_url

def get_image_url():
    allowed_extention = ['jpg', 'jpeg', 'png']
    file_extention = ''
    while file_extention not in allowed_extention:
        url = get_url()
        file_extention = re.search("([^.]*)$",url).group(1)
    logger.info('Sent image url: ' + url)
    return url

def bop(bot, update):
    chat_id = update.message.chat_id
    url = get_image_url()
    bot.send_photo(chat_id=chat_id, photo=url)

def update(bot, update):
    global reports
    chat_id = update.message.chat_id
    for shag in shags_situation:
        isRasar = shags_situation[shag]['isRasar']
        if  isRasar>= 0.5:
            situation = 'רס"ר'
            chance = isRasar*100
        else:
            situation = 'נקי'
            chance = (1-isRasar)*100
        bot.send_message(chat_id=chat_id, text = 'שג ' + shag +' '+ situation+ ' בטוח ב- ' + str(chance) +'%') 
    reply_markup = telegram.ReplyKeyboardMarkup(KEYBOARD)
    bot.send_message(chat_id=chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=reply_markup)

def cancel_report(bot, update):
    # Doesn't really cancel the report yet.
    # For now it's ment to prevent spamming
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text='דיווח בוטל')
    reply_markup = telegram.ReplyKeyboardMarkup(KEYBOARD)
    bot.send_message(chat_id=chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=reply_markup)
    
def report(bot, update):
    global reports
    chat_id = update.message.chat_id
    shag = update.message.text.split()[1]
    state = update.message.text.split()[2]

    reports.append({
        'shag': shag,
        'state': state,
        'chat_id': chat_id,
        'time': datetime.now()
    })
    if state=='רס"ר':
        shags_situation[shag]['isRasar'] +=RASAR_FACTOR*(1-shags_situation[shag]['isRasar'])
    else:
        shags_situation[shag]['isRasar'] *=CLEAN_FACTOR

    custom_keyboard = [['/cancel_report']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard) 
    bot.send_message(chat_id=chat_id, text='תודה שדיווחת!', reply_markup=reply_markup)
    

def send_admin(bot, update):
    chat_id = update.message.chat_id
    message = update.message.text
    if len(message.split()) == 1:
        bot.send_message(chat_id=chat_id, text='יש לכתוב את הפקודה ' + message + ' ולאחר מכן טקסט חופשי.  \n \n טיפ: נגיעה ארוכה על הפקודה תכתוב אותה מבלי לשלוח.') 
    else:
        bot.send_message(chat_id=chat_id, text='תודה רבה :)')
        bot.send_message(chat_id=ADMIN_ID, text=message)

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('cancel_report',cancel_report))
    dp.add_handler(CommandHandler('bop',bop))
    dp.add_handler(CommandHandler('report_bug', send_admin))
    dp.add_handler(CommandHandler('suggest_feature', send_admin))
    dp.add_handler(CommandHandler('report',report))
    dp.add_handler(MessageHandler(Filters.text, update))
    run(updater)
    updater.idle()

if __name__ == '__main__':
    main()