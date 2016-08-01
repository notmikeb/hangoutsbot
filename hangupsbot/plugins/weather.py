# -*- coding: utf8 -*-
import asyncio, re, logging, json, random

import hangups

import plugins
import time


logger = logging.getLogger(__name__)

def _initialise(bot):
    plugins.register_handler(_handle_weather, type="message")
    plugins.register_admin_command(["weather", "runcode"])
    plugins.start_asyncio_task(_delay_notify_admins, bot)


@asyncio.coroutine
def _delay_notify_admins(bot, args):
    admin_key = "admins"
    global_admins = bot.get_config_option(admin_key) or {}
    if global_admins:
      for admin in global_admins:
        logger.info("admin {}".format(admin))      
        c = bot.get_1on1_conversation(admin)
        if c: 
          logger.info("c {}".format(c))      
          bot.send_message(c, "hi I am online at " + time.asctime())


def _handle_weather(bot, event, command):
    """Handle autoreplies to keywords in messages"""

    if isinstance(event.conv_event, hangups.ChatMessageEvent):
        event_type = "MESSAGE"
    elif isinstance(event.conv_event, hangups.MembershipChangeEvent):
        if event.conv_event.type_ == hangups.MembershipChangeType.JOIN:
            event_type = "JOIN"
        else:
            event_type = "LEAVE"
    elif isinstance(event.conv_event, hangups.RenameEvent):
        event_type = "RENAME"
    else:
        raise RuntimeError("unhandled event type")

    text = event.text.lower().strip()
    message = ''

    if text in ['he', 'hel', 'help']:
      message = 'w : weather \n <4 digital> : taiwan stock \n'
      yield from mysend_reply(bot, event, message)
    elif text in ['w', 'W', 'weather', 'Weather', 'WEATHER']:
      message = u"天氣" + get_weather_string('taipei')
      #bot.coro_send_message(event.conv, "get " + event.text)
      #bot.coro_send_message(event.conv, message)
      yield from mysend_reply(bot, event, message)
      logger.error('location is {} msg len is {}'.format('taipei', message))
    elif text in ['t', 'ti', 'tim', 'time']:
      message = "Time " + time.asctime()
      logger.info( "event.conv {} ".format(event.conv))
      yield from mysend_reply(bot, event, message)
    elif len(text) == 4 and text.isdigit():
      message = get_stock_price(text)
      yield from mysend_reply(bot, event, message)
    elif text in ["me"]:
      yield from sendtwice(bot, event, message)
    elif text in ['count']:
      message = 'count '
      yield from send_count(bot, event, message)
    elif text in ['to', 'todo']:
      message = 'wunderlist todo'
      yield from send_todo_list(bot, event, message)
    elif text.find('/bot') > 0:
      logger.info('weather plugin igonre /bot')
    else:
      logger.error('event.text weather echo {}'.format(event.text))
      yield from mysend_reply(bot, event, "Unknow cmd do echo \n\n" + event.text)

import json,  urllib
import urllib.request

def fetchHTML(url):
    URL = "http://openweathermap.org/data/2.1/find/name?q="+url
    #req = urllib.request(URL)
    response=urllib.request.urlopen(URL)
    return response.read()

def get_weather_string(input_location):
    if len(input_location) == 0:
        input_location = 'taipei'
    output=fetchHTML(input_location)
    data = json.loads(''.join([chr(i) for i in output]))

    result = str( "Location: " + str(data['list'][0]['name']) +
    "\nCountry: " + str(data['list'][0]['name']) + "\nLatitude: " + str(data['list'][0]['coord']['lat'])+
    "\nLongitude: " +str(data['list'][0]['coord']['lon']) + "\nTemperature: "+str(data['list'][0]['main']['temp']-273.15) +" C"+
    "\nHumidity: " + str(data['list'][0]['main']['humidity']) + " %"+
    "\nPressure: " + str(data['list'][0]['main']['pressure']) + " hPa"+
    "\nWind Speed: " + str(data['list'][0]['wind']['speed']) + " mps" +
    "\nWeather Description: " + str(data['list'][0]['weather'][0]['description']+ "\n\nhttps://tw.news.yahoo.com/weather/\n\n") )

    return result


@asyncio.coroutine
def mysend_reply(bot, event, message):
    logger.error('mysend_reply is {} {}'.format(event.text, message))
    values = { "event": event,
               "conv_title": bot.conversations.get_name( event.conv,
                                                         fallback_string=_("Unidentified Conversation") )}

    if "participant_ids" in dir(event.conv_event):
        values["participants"] = [ event.conv.get_user(user_id)
                                   for user_id in event.conv_event.participant_ids ]
        values["participants_namelist"] = ", ".join([ u.full_name for u in values["participants"] ])

    envelopes = []

    logger.info('weather send_reply len {}'.format(len(message)))
    envelopes.append((event.conv, message.format(**values)))

    for send in envelopes:
        logger.info("envelopes is {}".format(send))
        yield from bot.coro_send_message(*send)

    return True


import urllib
import urllib.request
import bs4


import yahoo_finance

def get_stock_price(stock_no):
    result = ""
    x = yahoo_finance.Share( stock_no[:4] + '.TW')
    if x.get_price():
      result += x.get_trade_datetime() + "\n"
      result += u'價格: '+ x.get_price() + "\n"
      result += u'昨天價格: '+ x.get_prev_close() + "\n"
      result += u'開盤價格: '+ x.get_open() + "\n"


      url = 'http://www.cmoney.tw/finance/f00025.aspx?s=' + stock_no[:4]
      b = urllib.request.urlopen(url)
      d = b.readall()
      s = bs4.BeautifulSoup(d, "html.parser")
      if s and s.title and s.title.string:
        i = s.title.string.find('-')
        result += s.title.string[:i].strip() + "\n"
      result += "\n\n{}\n\n".format(url)
    else:
        result += "Stock {} NOT Found !".format(stock_no[:4])

    return result

def runcode(bot, event, cmd=None, *args):
    """ runcode <source code>
    """
    message = ""
    if cmd and len(cmd) > 0:
      if args and len(args) > 0:
        logger.info("cmd {} len:{} args:".format(cmd, len(cmd)) )
      else:
        logger.info("cmd {} no args len:{}".format(cmd, len(cmd)))
      if cmd[0] == '"' and cmd[-1] == '"':
         cmd = cmd[1:-1]
      c = compile(cmd, 'None', 'exec')
    
      try:
         p = eval(c)
         message += str(p)
      except Exception:
         message += str(e)
      html = "<b>{}</b>".format(message)
    else:
      html = "<b>runcode:</b> <br /> {}".format(value)

    yield from bot.coro_send_message(event.conv_id, html)
       

def weather(bot, event, cmd=None, *args):
    """adds or removes an autoreply.
    Format:
    /bot weather list  # list all regmister weather chat_id
    /bot weather add   # add current user as a weather register guy
    /bot weather remove # remove current user from register weather users
    """

    path = ["weather"]
    argument = " ".join(args)
    html = ""
    value = bot.config.get_by_path(path)

    if cmd == 'add':
        if isinstance(value, list):
            value.append(json.loads(argument))
            bot.config.set_by_path(path, value)
            bot.config.save()
        else:
            html = "Append failed on non-list"
    elif cmd == 'remove':
        if isinstance(value, list):
            value.remove(json.loads(argument))
            bot.config.set_by_path(path, value)
            bot.config.save()
        else:
            html = "Remove failed on non-list"
    else:
        logger.error ("unknow cmd {}".format( cmd))
    logger.info("cmd is {}".format(cmd))

    # Reload the config
    bot.config.load()

    if html == "":
        value = bot.config.get_by_path(path)
        html = "<b>weather config:</b> <br /> {}".format(value)

    yield from bot.coro_send_message(event.conv_id, html)

def mysend_message(bot, event, message):
    logger.info("mysend_message :{}".format(message))
    bot.send_message(event.conv_id, message)


def get_todo_list(maxno):
    client_id  = '8f2bd5d6ab84ea8df8e8'
    client_secret = 'f1850a45b5e3a2689de61a05b71e447c9d6b510a96d9058b8fac751be985'
    access_token = 'fa7b2df966a4bc58d6598fca2e2553bb7a427427983f2baa8a2fa01734f2'
    import wunderpy2
    api = wunderpy2.WunderApi()
    client = api.get_client(access_token, client_id)    # Fill in your values
    
    max = 50
    lists = client.get_lists()
    result = "https://www.wunderlist.com/webapp#/lists/inbox\n\n"
    num = 0
    for list in lists:
      tasks = client.get_tasks(list['id'])
      if len(tasks) > 0:
        result += "=====list-title= {}\n".format(list['title'][:max])
        if len(tasks) > 0:
          for task in tasks:
            num += 1
            result += "task-title= {}  ".format(task['title'][:max])
            result += "task-id= {}\n".format(task['id'])
            notes = client.get_task_notes(task['id'])
            if len(notes) > 0:
              for note in notes:
                if len(note['content']) > 0:
                  result += "note-content= \n{}\n".format(note['content'][:max])
            result += "\n"
            if num > maxno:
               result += "====="
               return result
        result += "=====" 
    return result

@asyncio.coroutine
def send_todo_list(bot, event, message):
  #https://developer.wunderlist.com/apps
  global t2, todo
  import time

  t1 = time.time()
  if 'todo' not in globals():
     todo = ""
  if 't2' not in globals():
     t2 = 0 
  if (t1-t2) < 60:
     #use result
     logger.info('Use the old result')
     pass
  else:   
    yield from mysend_reply(bot, event, "Prepare the wunderlist of todo items\nPlease wait\n") 
    # get max 3 records from todo lists
    result = get_todo_list(3)
    
    t2 = time.time()
    result += "\nTakes {0:.2f} sec\n".format(t2-t1)
    todo = result
    logger.info("Get wonderlist len:{}".format(len(result)))
  # send the result
  logger.info("yield to mysend_reply by get_todo_list")
  yield from mysend_reply(bot, event, todo) 

@asyncio.coroutine
def send_count(bot, event, message):
  for count in range(10):
     yield from mysend_reply(bot, event, message + str(count) ) 

@asyncio.coroutine
def sendtwice(bot, event, message):
  import time
  yield from mysend_reply(bot, event, message +" first") 
  time.sleep(5)
  yield from mysend_reply(bot, event, message + " second") 
