cd $(dirname $0)
source venv/bin/activate
screen -X -S translate_bot quit
screen -S translate_bot -dm python app.py