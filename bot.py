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
    'גדול נקי': 0, 
    'גדול רס"ר': 0, 
    'קטן נקי': 0, 
    'קטן רס"ר': 0
    }

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

def welcome(bot, update):
    chat_id = update.message.chat_id

    shag, kind = 'קטן', 'נקי'
    reports_num = SHAGS_REPS[shag + ' ' + kind]
    bot.send_message(chat_id=chat_id, text= 'שג ' + shag + " " +kind + 
                                                    ' מס דיווחים: ' + str(reports_num))
    shag, kind = 'גדול', 'נקי'
    reports_num = SHAGS_REPS[shag + ' ' + kind]
    bot.send_message(chat_id=chat_id, text= 'שג ' + shag + " " +kind + 
                                                    ' מס דיווחים: ' + str(reports_num))

    custom_keyboard = [['/report גדול נקי', '/report קטן נקי'], 
                       ['/report גדול רס"ר', '/report קטן רס"ר']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=reply_markup)

    

def cancel_report(bot, update):
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text='דיווח בוטל')

    custom_keyboard = [['/report גדול נקי', '/report קטן נקי'], 
                       ['/report גדול רס"ר', '/report קטן רס"ר']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=reply_markup)
    
def report(bot, update):
    global SHAGS_REPS
    chat_id = update.message.chat_id
    shag = update.message.text.split()[1]
    kind = update.message.text.split()[2]
    SHAGS_REPS[shag + ' ' + kind] += 1
    reports_num = SHAGS_REPS[shag + ' ' + kind]
    logger.info(shag + kind +' reports: ' + str(reports_num))
    custom_keyboard = [['/cancel_report']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.send_message(chat_id=chat_id, text='תודה שדיווחת!', reply_markup=reply_markup)
    bot.send_message(chat_id=chat_id, text= 'שג ' + shag + " " +kind + 
                                                    ' מס דיווחים: ' + str(reports_num))

def main():
    updater = Updater('1085565057:AAH08Gb5L8yB9rIVdLsbrQKx3yTNM_2PJGA' )
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('cancel_report',cancel_report))
    dp.add_handler(CommandHandler('bop',bop))
    dp.add_handler(CommandHandler('report',report))
    dp.add_handler(MessageHandler(Filters.text, welcome))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()