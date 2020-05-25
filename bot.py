import telegram
from telegram.ext import  Updater, InlineQueryHandler, CommandHandler, Defaults, Job, MessageHandler, Filters
import requests # to make requests to external api
import re # regex for pictures of doggos
import logging
from datetime import datetime # use to restart everyday 
import sys
from consts import *

reports = []
shags_situation = {
        'גדול': {
            'isRasar':0 # is rasar is a number between 0 and 1, 1- rasar, 0 clean
        },
        'קטן':{
            'isRasar':0
        }
    }
    
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if MODE == "dev":
    def run(updater):
        updater.start_polling()
elif MODE == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=BOT_TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, BOT_TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)
    
# For easy monitoring during beta stage
def log_admin(bot, info):
    logger.info(info)
    bot.send_message(chat_id=ADMIN_ID, text="LOG: %s"%info) 

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

def reset_shags():
    global shags_situation
    shags_situation['גדול']['isRasar'] = 0
    shags_situation['קטן']['isRasar'] = 0

def count_reports_in_shag(shag):
    global reports
    return len(list(filter(lambda report: report['shag']==shag, reports)))

# Get update of the rasar situation
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
        reports_count = count_reports_in_shag(shag)
        if reports_count >= MIN_REPORTS:
            bot.send_message(chat_id=chat_id, text = 'שג ' + shag +' '+ situation+ ' בטוח ב- ' 
            + str(chance) +'%\n' 
            + "התקבלו " + str(reports_count) + " דיווחים")
        else:
            bot.send_message(chat_id=chat_id, text = "לא התקבלו דיווחים בשג " + shag)

def cancel_report(bot, update):
    global reports
    chat_id = update.message.chat_id
    report = next((report for report in reports if report["chat_id"] == chat_id), None)
    if report:
        reports.remove(report) 
        calculate_prob() 
        bot.send_message(chat_id=chat_id, text='דיווח בוטל')
        user_name = str(update.effective_user.full_name)
        log_admin(bot, "Cancel report by user: %s" % user_name)
    else:
        bot.send_message(chat_id=chat_id, text='הדיווח כבר בוטל או שלא נשלח מעולם')
    reply_markup = telegram.ReplyKeyboardMarkup(KEYBOARD)
    bot.send_message(chat_id=chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=reply_markup)
    
def calculate_prob():
    global reports, shags_situation
    reset_shags()
    for report in reports:
        shag  = report['shag']
        state = report['state']
        if state=='רס"ר':
            shags_situation[shag]['isRasar'] +=RASAR_FACTOR*(1-shags_situation[shag]['isRasar'])
        else:
            shags_situation[shag]['isRasar'] *=CLEAN_FACTOR

def report(bot, update):
    global reports
    chat_id = update.message.chat_id
    shag = update.message.text.split()[1]
    state = update.message.text.split()[2]
    old_report = next((report for report in reports if report["chat_id"] == chat_id), None)
    if old_report:
        reports.remove(old_report) 
    reports.append({
        'shag': shag,
        'state': state,
        'chat_id': chat_id,
        'time': datetime.now()
    })
    calculate_prob()
    custom_keyboard = [['/cancel_report', '/new_report'],
                        ['מה המצב?']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard) 
    bot.send_message(chat_id=chat_id, text='תודה שדיווחת!', reply_markup=reply_markup)
    user_name = str(update.effective_user.full_name)
    log_admin(bot, "Recived report: %s %s by user: %s" % (shag, state, user_name))

def send_to_admin(bot, update):
    chat_id = update.message.chat_id
    message = update.message.text
    if len(message.split()) == 1:
        bot.send_message(chat_id=chat_id, text='יש לכתוב את הפקודה ' + message + ' ולאחר מכן טקסט חופשי.  \n \n טיפ: נגיעה ארוכה על הפקודה תכתוב אותה מבלי לשלוח.') 
    else:
        bot.send_message(chat_id=chat_id, text='תודה רבה :)')
        bot.send_message(chat_id=ADMIN_ID, text=message)

def new_report(bot, update):
    bot.send_message(chat_id=update.message.chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=telegram.ReplyKeyboardMarkup(KEYBOARD))

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('cancel_report',cancel_report))
    dp.add_handler(CommandHandler('bop',bop))
    dp.add_handler(CommandHandler('report_bug', send_to_admin))
    dp.add_handler(CommandHandler('suggest_feature', send_to_admin))
    dp.add_handler(CommandHandler('report',report))
    dp.add_handler(CommandHandler('new_report',new_report))
    dp.add_handler(MessageHandler(Filters.text("מה המצב?"), update))
    run(updater)
    updater.idle()

if __name__ == '__main__':
    main()