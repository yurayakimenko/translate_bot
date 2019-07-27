from telegram.ext import MessageHandler, Updater, Filters, CommandHandler, CallbackQueryHandler
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
        "adverb": "наречие",
        "preposition": "предлог",
        "conjunction": "союз",
        "phrase": "фраза"
    }
}

lang_parts_codes = {
    1: "noun",
    2: "verb",
    3: "adjective",
    4: "adverb",
    5: "preposition",
    6: "abbreviation",
    7: "conjunction",
    8: "pronoun",
    9: "interjection",
    10: "phrase",
    15: "numeral"
}


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def get_translation(message_text):
    lang = translator.detect(message_text).lang
    if lang == 'en':
        translated = translator.translate(message_text, dest='ru')
    else:
        translated = translator.translate(message_text, dest='en')
    return translated


def get_examples(translated):
    e = translated.extra_data.get('examples')
    examples = []
    for example in e[0]:
        examples.append(example[0])
    return examples


def format_examples(examples):
    examples_formatted = str()
    for example in examples:
        examples_formatted += "\n" \
                              "• {}".format(example)
    return examples_formatted


def get_synonyms(translated):
    s = translated.extra_data.get('synonyms')
    synonyms = []
    for lang_part in s:
        lang_part_code = lang_part[-1]
        print(lang_part_code, lang_part[0])
        for word in lang_part[1]:
            synonyms.append(word[0][:2])
    return synonyms


def format_synonyms(synonyms):
    synonyms_formatted = str()
    stop_count = 2 if len(synonyms) >= 3 else 3
    for words in synonyms:
        synonyms_formatted += "\n" \
                              "• {}".format(', '.join(words[:stop_count]))
    return synonyms_formatted


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
    return possible_translations


def format_possible_translations(possible_translations):
    possible_translations_formatted = str()
    if type(possible_translations) == dict:
        stop_count = 2 if len(possible_translations) >= 3 else 3
        for lang_part, words in possible_translations.items():
            possible_translations_formatted += "\n<i>{}</i>\n".format(lang_parts_dict['ru'][lang_part])
            translation_count = 0
            for word, translations in words.items():
                if translation_count < stop_count:
                    possible_translations_formatted += "\t\t{}\n" \
                                                       "\t\t\t\t\t• {}\n\n".format(word, ', '.join(translations[:4]))
                    translation_count += 1
                else:
                    break

    else:
        possible_translations_formatted += "\n• {}".format(', '.join(possible_translations))
    return possible_translations_formatted


def translate(bot, update, callback_text=None):
    if not callback_text:
        message_text = update.message.text
    else:
        message_text = callback_text
    try:
        translated = get_translation(message_text)
    except Exception as e:
        logger.error(e, exc_info=True)
    else:
        # pprint(translated.extra_data)
        possible_translations = get_possible_translations(translated)
        synonyms = translated.extra_data['synonyms']
        examples = translated.extra_data['examples']
        print("synonyms:", synonyms)
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
            if not callback_text:
                update.message.reply_text(reply_text, reply_markup=reply_markup, parse_mode="HTML")
            else:
                update.message.edit_text(reply_text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            reply_text = "{}".format(translated.text or "[ Нет перевода ]")
            if not callback_text:
                update.message.reply_text(reply_text, parse_mode="HTML")
            else:
                update.message.edit_text(reply_text, parse_mode="HTML")
        logger.info("'{}' -> '{}' by {}".format(message_text, translated.text, update.message.chat_id))


def callback_handler(bot, update):
    query = update.callback_query
    query_data = update.callback_query.data
    user_id = query.message.chat_id
    url_parts = query_data.split('/')
    action = url_parts[0]
    if action == 's':
        callback_synonyms(bot, query, url_parts[1])
    elif action == 'e':
        callback_examples(bot, query, url_parts[1])
    elif action == 't':
        translate(bot, query, url_parts[1])


def callback_examples(bot, query, message_text):
    try:
        translated = get_translation(message_text)
        pprint(translated.extra_data)
    except Exception as e:
        logger.error(e, exc_info=True)
    else:
        e = get_examples(translated)
        e_formatted = format_examples(e)
        reply_text = "[ {} → {} ]" \
                     "\n{}".format(message_text, translated.text,
                                   e_formatted)
        synonyms = translated.extra_data['synonyms']
        row = []
        if synonyms:
            row.append(InlineKeyboardButton('Синонимы', callback_data='s/{}'.format(message_text)))
        row.append(InlineKeyboardButton('Перевод', callback_data='t/{}'.format(message_text)))
        reply_markup = InlineKeyboardMarkup([row])
        query.message.edit_text(reply_text, reply_markup=reply_markup, parse_mode="HTML")


def callback_synonyms(bot, query, message_text):
    try:
        translated = get_translation(message_text)
        pprint(translated.extra_data)
    except Exception as e:
        logger.error(e, exc_info=True)
    else:
        s = get_synonyms(translated)
        s_formatted = format_synonyms(s)
        reply_text = "[ {} → {} ]" \
                     "\n{}".format(message_text, translated.text,
                                   s_formatted)
        row = [InlineKeyboardButton('Перевод', callback_data='t/{}'.format(message_text))]
        examples = translated.extra_data['examples']
        if examples:
            row.append(InlineKeyboardButton('Примеры', callback_data='e/{}'.format(message_text)))
        reply_markup = InlineKeyboardMarkup([row])
        query.message.edit_text(reply_text, reply_markup=reply_markup, parse_mode="HTML")


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
    dp.add_handler(MessageHandler(Filters.text, translate))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    updater.start_polling()
    logger.info("Bot started on debug as @{} on polling."
                .format(updater.bot.username))
    updater.idle()


if __name__ == '__main__':
    main()
