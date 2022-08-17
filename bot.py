import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import ReplyKeyboardMarkup
import logging
import random

from main import get_questions

def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        text='Привет! Я бот для викторин!',
        reply_markup=ReplyKeyboardMarkup([['Новый вопрос', 'Сдаться'], ['Мой счёт']])
        )


def help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    user_reply = update.message.text
    if user_reply == 'Новый вопрос':
        questions_and_answers = get_questions()
        question, answer = random.choice(list(questions_and_answers.items()))
        update.message.reply_text(text=question)


def error(update: Update, context: CallbackContext, error):
    """Log Errors caused by Updates."""
    logging.logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    load_dotenv()
    updater = Updater(os.getenv("TOKEN"))

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_error_handler(error)
    
    updater.start_polling()


if __name__ == '__main__':
    main()