import telegram
from telegram.ext import  Updater, InlineQueryHandler, CommandHandler, Defaults, Job, MessageHandler, Filters
import requests # to make requests to external api
import re # regex for pictures of doggos
import logging
import datetime # use to restart everyday 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


SHAGS_REPS = {
    'גדול': {
        'נקי': 0, 
        'רס"ר': 0, 
    },
    'קטן':{
        'נקי': 0, 
        'רס"ר': 0
    }
}

# When developing, I can use the dev_token and test on RasarDevBot
# DON'T FORGET to change back to bot_token before git commiting.
dev_token = '1094786502:AAFkEu9_sjyj2zSz9RlUc980D4wHLQ2ij9g'
BOT_TOKEN = '1085565057:AAH08Gb5L8yB9rIVdLsbrQKx3yTNM_2PJGA' 
ADMIN_ID = 698233004
KEYBOARD = [['/report גדול נקי', '/report קטן נקי'], 
            ['/report גדול רס"ר', '/report קטן רס"ר'],
            ['מה המצב?']]

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

def isClean(): #TODO: modify when updating db
    global SHAGS_REPS
    #TODO: stub
        


def update(bot, update):
    chat_id = update.message.chat_id

    for shag, data in SHAGS_REPS.items():
        for cond in data.keys():
            reports_num = SHAGS_REPS[shag][cond]
            bot.send_message(chat_id=chat_id, text= 'שג ' + shag + " " +cond + 
                            ' מס דיווחים: ' + str(reports_num))
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
    global SHAGS_REPS
    chat_id = update.message.chat_id
    shag = update.message.text.split()[1]
    kind = update.message.text.split()[2]
    SHAGS_REPS[shag][kind] += 1
    reports_num = SHAGS_REPS[shag][kind]
    logger.info(shag + kind +' reports: ' + str(reports_num))
    custom_keyboard = [['/cancel_report']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=chat_id, text='תודה שדיווחת!', reply_markup=reply_markup)
    bot.send_message(chat_id=chat_id, text= 'שג ' + shag + " " +kind + 
                                                    ' מס דיווחים: ' + str(reports_num))

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
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()