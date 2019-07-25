from telegram.ext import MessageHandler, Updater, Filters, CommandHandler
from telegram import Sticker
import logging
import configparser
import os
from googletrans import Translator
from pprint import pprint

PROJECT_DIR = os.path.dirname(__file__)
CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(PROJECT_DIR, 'config.ini'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
translator = Translator()


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def message_handler(bot, update):
    message_text = update.message.text
    lang = translator.detect(message_text).lang
    if lang == 'en':
        translated = translator.translate(message_text, dest='ru').text
    else:
        translated = translator.translate(message_text, dest='en').text
    update.message.reply_text(translated)


def start(bot, update):
    update.message.reply_text("Привет! Пришли мне текст до 15 тыс. "
                              "символов на русском или английском и "
                              "я переведу его для тебя! You're welcome!")
    sticker = Sticker(file_id='CAADAgAD8wcAAhhC7gj21R3ZVhUQAwI', height=512, width=512)
    bot.send_sticker(chat_id=update.message.chat_id, sticker=sticker)


def main():
    updater = Updater(token=CONFIG['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, message_handler))
    updater.start_polling()
    logger.info("Bot started on debug as @{} on polling."
                .format(updater.bot.username))
    updater.idle()


if __name__ == '__main__':
    main()
