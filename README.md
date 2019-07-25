# Google Translate Telegram Bot

**This project is written with python-telegram-bot==11.1.0 and googletrans==2.4.0**

You can view a working version of this telegram bot
[@RUENTranslatorBot](https://t.me/RUENTranslatorBot).

The goal of this project is to make translation of sentences and 
words on the fly while reading articles in Telegram and during 
web surfing in general.

Bot supports `Russian -> English` and `English -> Russian`
with autodetection. So just write word or text to bot 
and get the translation.

## Building

You can simply run:
```sh
$ git clone https://github.com/yurayakimenko/translate_bot.git
$ cd translate_bot
$ ./install.sh
```

Or do it hard way:

```sh
$ git clone https://github.com/yurayakimenko/translate_bot.git
$ cd translate_bot
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
$ mv config_example.ini config.ini
```

Rename `config_example.ini` to `config.ini` and specify your bot token.
You can obtain token by sending message to [@BotFather](https://t.me/BotFather). 

To run bot use: 
 
```sh
$ ./run.sh
```
 or:

```sh
$ python app.py
```

Then visit your bot and type `/start`.
