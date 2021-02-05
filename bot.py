import telegram
from telegram.ext import  Updater, InlineQueryHandler, CommandHandler, Defaults, Job, MessageHandler, Filters
import requests # to make requests to external api
import re # regex for pictures of doggos
import logging
from datetime import datetime # use to show time of last report
import pytz # handles timezone difference with remote server
import sys
from consts import *

reports = []
report_chat_id = []
shags_situation = {
        'גדול': {
            'isDirty':0 # is dirty is a number between 0 and 1, 1- dirty, 0 clean
        },
        'קטן':{
            'isDirty':0
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

# Helper functions
def reset_shags():
    global shags_situation
    shags_situation['גדול']['isDirty'] = 0
    shags_situation['קטן']['isDirty'] = 0

def count_reports_in_shag(shag):
    global reports
    return len(list(filter(lambda report: report['shag']==shag, reports)))

def get_last_report(shag):
    global reports
    for report in reversed(reports): 
        if report['shag']==shag:
            return report 

def message_admin(bot, update, text):
    bot.forward_message(chat_id=ADMIN_ID, 
                        from_chat_id=update.message.chat_id, 
                        message_id=update.message.message_id)

def log_admin(bot, info):
    logger.info(info)
    bot.send_message(chat_id=ADMIN_ID, text="LOG: %s"%info) 

def auto_reply_markup(chat_id):
    if next((report for report in reports if report["chat_id"] == chat_id), None):
        return telegram.ReplyKeyboardMarkup(SECOND_KEYBOARD, one_time_keyboard=True)
    else:
        return telegram.ReplyKeyboardMarkup(BASE_KEYBOARD, one_time_keyboard=True)

# Get update of the rasar situation
def update(bot, update):
    global reports
    chat_id = update.message.chat_id
    reply_markup = auto_reply_markup(chat_id)
    for shag in shags_situation:
        isDirty = shags_situation[shag]['isDirty']
        if  isDirty>= 0.5:
            situation = 'מלוכלך'
            chance = isDirty*100
        else:
            situation = 'נקי'
            chance = (1-isDirty)*100
        reports_count = count_reports_in_shag(shag)
        if reports_count >= MIN_REPORTS:
            last_report = get_last_report(shag)
            bot.send_message(chat_id=chat_id, text = 'שג ' + shag +' '+ situation
            + ' בטוח ב- ' + str(chance) +'%\n' 
            + "התקבלו " + str(reports_count) + " דיווחים\n" +
            "דיווח אחרון (" +
             last_report['state'] + 
             ") התקבל ב: " + 
             last_report['time'].strftime("%H:%M:%S"), reply_markup=reply_markup)
        else:
            bot.send_message(chat_id=chat_id, text = "לא התקבלו דיווחים בשג " + shag, reply_markup=reply_markup)

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
    reply_markup = telegram.ReplyKeyboardMarkup(BASE_KEYBOARD, one_time_keyboard=True)
    bot.send_message(chat_id=chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=reply_markup)
    
def calculate_prob():
    global reports, shags_situation
    reset_shags()
    for report in reports:
        shag  = report['shag']
        state = report['state']
        if state=='נקי':
            shags_situation[shag]['isDirty'] *=CLEAN_FACTOR
        else:
            shags_situation[shag]['isDirty'] +=DIRTY_FACTOR*(1-shags_situation[shag]['isDirty'])

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
        'time': pytz.utc.localize(datetime.utcnow()).astimezone(pytz.timezone("Israel"))
    })
    calculate_prob()
    if state == 'מלוכלך':
        global report_chat_id
        reply_markup = telegram.ReplyKeyboardMarkup(STATE_KEYBOARD)
        report_chat_id.append(chat_id)
        bot.send_message(chat_id=chat_id, text=('מה סוג האיום בשג ה'+shag+'? (אם האיום לא נמצא ברשימה, כתבו במקלדת בשפה חופשית)'), reply_markup=reply_markup)
    else:
        reply_markup = telegram.ReplyKeyboardMarkup(SECOND_KEYBOARD, one_time_keyboard=True) 
        bot.send_message(chat_id=chat_id, text='תודה שדיווחת!', reply_markup=reply_markup)
    
    user_name = str(update.effective_user.full_name)
    log_admin(bot, "Recived report: %s %s by user: %s" % (shag, state, user_name))

def send_feedback(bot, update):
    global feedback_message
    chat_id = update.message.chat_id
    message = update.message.text
    if len(message.split()) == 1:
        feedback_message = bot.send_message(chat_id=chat_id, text='דברו אני מקשיב')
    else:
        message_admin(bot, update, message.split(' ', 1)[1])
        bot.send_message(chat_id=chat_id, text='תודה רבה :)', reply_markup=auto_reply_markup(chat_id))

def message_handler(bot, update):
    global feedback_message, state_kind, report_chat_id, reports
    chat_id = update.message.chat_id
    message = update.message.text
    if chat_id in report_chat_id:
        for report in reports:
            if report['chat_id'] == chat_id:
                report['state'] = message
        reply_markup = telegram.ReplyKeyboardMarkup(SECOND_KEYBOARD, one_time_keyboard=True) 
        bot.send_message(chat_id=chat_id, text='תודה שדיווחת!', reply_markup=reply_markup)
        report_chat_id.remove(chat_id)
    elif 'feedback_message' in globals():
            bot.send_message(chat_id=chat_id, text='תודה רבה :)', reply_markup=auto_reply_markup(chat_id))
            message_admin(bot, update, message)
            del feedback_message
    elif chat_id == int(ADMIN_ID) and update.message.reply_to_message:
        user_id = update.message.reply_to_message.forward_from.id
        bot.send_message(chat_id=user_id, text=message)
    else:
        bot.send_message(chat_id=chat_id, text='אם אתם רוצים לספר לי משהו השתמשו בפקודה /send_feedback או שלחו דיווח חדש עם /new_report')

def new_report(bot, update):
    bot.send_message(chat_id=update.message.chat_id, 
                 text="בחרו מהאפשרויות לדיווח", 
                 reply_markup=telegram.ReplyKeyboardMarkup(BASE_KEYBOARD, one_time_keyboard=True))

def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('cancel_report',cancel_report))
    dp.add_handler(CommandHandler('bop',bop))
    dp.add_handler(CommandHandler('send_feedback', send_feedback))
    dp.add_handler(CommandHandler('report',report))
    dp.add_handler(CommandHandler('new_report',new_report))
    dp.add_handler(MessageHandler(Filters.text("מה המצב?"), update))
    dp.add_handler(MessageHandler(Filters.all, message_handler))
    run(updater)
    updater.idle()

if __name__ == '__main__':
    main()