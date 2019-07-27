from telegram.ext import MessageHandler, Updater, Filters, CommandHandler, InlineQueryHandler
from telegram import Sticker, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import configparser
import os
from googletrans import Translator
from logging.handlers import RotatingFileHandler
from pprint import pprint

PROJECT_DIR = os.path.dirname(__file__)
CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(PROJECT_DIR, 'config.ini'))

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
fh = RotatingFileHandler('./log/logfile',
                         mode='a', maxBytes=int(3 * 1024 * 1024),
                         backupCount=5, encoding=None, delay=0)
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
translator = Translator()

lang_parts_dict = {
    "ru": {
        "noun": "имя сущ.",
        "verb": "глагол",
        "adjective": "имя прилаг.",
        "pronoun": "местоимение",
        "abbreviation": "сокращение",
        "numeral": "числительное",
        "adverb": "наречие"
    }
}

lang_parts_codes = {
    1: "noun",
    2: "verb",
    3: "adjective",
    4: "adverb",
    6: "abbreviation",
    8: "pronoun",
    15: "numeral"
}


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def get_possible_translations(translated):
    all_translations = translated.extra_data.get('all-translations')
    possible_translations = translated.extra_data.get('possible-translations')
    if all_translations:
        possible_translations = {}
        for lang_part in all_translations:
            variants = {}
            lang_part_code = lang_part[-1]
            print(lang_part_code, lang_part[0])
            for word in lang_part[2]:
                variants[word[0]] = word[1]
            possible_translations[lang_parts_codes[lang_part_code]] = variants
    elif possible_translations:
        possible_translations = []
        for word in translated.extra_data.get('possible-translations')[0][2]:
            possible_translations.append(word[0])
        print(possible_translations)
    return possible_translations


def format_possible_translations(possible_translations):
    possible_translations_formatted = str()
    if type(possible_translations) == dict:
        for lang_part, words in possible_translations.items():
            possible_translations_formatted += "\n<i>{}</i>\n".format(lang_parts_dict['ru'][lang_part])
            translation_count = 0
            print(words)
            for word, translations in words.items():
                if translation_count <= 3:
                    possible_translations_formatted += "\t\t{}\n" \
                                                       "\t\t\t\t\t• {}\n\n".format(word, ', '.join(translations[:4]))
                else:
                    break
                translation_count += 1

    else:
        possible_translations_formatted += "\n• {}".format(', '.join(possible_translations))
    return possible_translations_formatted


def message_handler(bot, update):
    message_text = update.message.text
    try:
        lang = translator.detect(message_text).lang
        if lang == 'en':
            translated = translator.translate(message_text, dest='ru')
        else:
            translated = translator.translate(message_text, dest='en')
    except Exception as e:
        logger.error(e, exc_info=True)
    else:
        # pprint(translated.extra_data)
        possible_translations = get_possible_translations(translated)
        synonyms = translated.extra_data['synonyms']
        examples = translated.extra_data['examples']
        print(possible_translations)
        if possible_translations and len(message_text.encode('utf-8')) <= 64 - 2 and type(
                possible_translations) == dict:
            possible_translations_formatted = format_possible_translations(possible_translations)
            reply_text = "[ {} → {} ]" \
                         "\n{}".format(message_text, translated.text,
                                       possible_translations_formatted)
            row = []
            if synonyms:
                row.append(InlineKeyboardButton('Синонимы', callback_data='s/{}'.format(message_text)))
            if examples:
                row.append(InlineKeyboardButton('Примеры', callback_data='e/{}'.format(message_text)))
            reply_markup = InlineKeyboardMarkup([row])
            update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            reply_text = "{}".format(translated.text)
            update.message.reply_text(reply_text, parse_mode="HTML")
        logger.info("'{}' -> '{}' by {}".format(message_text, translated.text, update.message.chat_id))


def callback_handler(bot, update):
    pass


def start(bot, update):
    update.message.reply_text("Привет! Пришли мне слово или текст до 15 тыс. "
                              "символов на русском или английском и "
                              "я переведу его для тебя! You're welcome!")
    sticker = Sticker(file_id='CAADAgAD8wcAAhhC7gj21R3ZVhUQAwI', height=512, width=512)
    bot.send_sticker(chat_id=update.message.chat_id, sticker=sticker)


def main():
    updater = Updater(token=CONFIG['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, message_handler))
    dp.add_handler(InlineQueryHandler(callback_handler))
    updater.start_polling()
    logger.info("Bot started on debug as @{} on polling."
                .format(updater.bot.username))
    updater.idle()


if __name__ == '__main__':
    main()
