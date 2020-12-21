# from consts import *

reports = []
shags_situation = {
        'גדול': {
            'isRasar':0 # is rasar is a number between 0 and 1, 1- rasar, 0 clean
        },
        'קטן':{
            'isRasar':0
        }
    }

def reset_shags():
    global shags_situation
    shags_situation['גדול']['isRasar'] = 0
    shags_situation['קטן']['isRasar'] = 0

def count_reports_in_shag(shag):
    global reports
    return len(list(filter(lambda report: report['shag']==shag, reports)))
