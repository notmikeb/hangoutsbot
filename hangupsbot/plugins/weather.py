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

    if text in ['he', 'hel', 'help']:
      message = 'w : weather \n <4 digital> : taiwan stock \n'
      yield from mysend_reply(bot, event, message)
    if text in ['w', 'W', 'weather', 'Weather', 'WEATHER']:
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
    else:
      logger.error('event.text weather is {}'.format(event.text))
    logger.error('Done event.text weather is {}'.format(event.text))

#            if isinstance(kwds, list):
#                for kw in kwds:
#                    if _words_in_text(kw, event.text) or kw == "*":
#                        logger.info("matched chat: {}".format(kw))
#                        yield from send_reply(bot, event, message)
#                        break
#
#            elif event_type == kwds:
#                logger.info("matched event: {}".format(kwds))
#                yield from send_reply(bot, event, message)
#
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
    "\nWeather Description: " + str(data['list'][0]['weather'][0]['description']) )
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
      html = "<b>weather config:</b> <br /> {}".format(value)

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
