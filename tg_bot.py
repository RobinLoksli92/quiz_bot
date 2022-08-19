from functools import partial
import os
from turtle import right
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext import ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import logging
from functools import partial
import random
import redis

from get_questions import get_questions


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

NEW_QUESTION_REQUEST = range(1)


def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(
        text='Привет! Я бот для викторин!',
        reply_markup=ReplyKeyboardMarkup([['Новый вопрос', 'Мой счёт']], resize_keyboard=True)
        )
    return NEW_QUESTION_REQUEST


def help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def handle_new_question_request(db, update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    questions_and_answers = get_questions()
    question, answer = random.choice(list(questions_and_answers.items()))
    update.message.reply_text(
        text=question,
        reply_markup=ReplyKeyboardMarkup([['Сдаться']], resize_keyboard=True)
        )
    db.set(user_id, question)

    return NEW_QUESTION_REQUEST


def handle_solution_attempt(db, update: Update, context: CallbackContext):
    user_answer = update.message.text
    user_id = update.effective_message.from_user.id
    question = db.get(user_id)
    questions_and_answers = get_questions()
    full_answer = questions_and_answers[question]
    answer_without_info = full_answer.split('.')[0]
    if user_answer in answer_without_info:
        update.message.reply_text(
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
        )
    else:
        update.message.reply_text(
            text=f'Неправильно… Попробуешь ещё раз?',
            reply_markup=ReplyKeyboardMarkup([['Сдаться']], resize_keyboard=True)
        )

    return NEW_QUESTION_REQUEST


def handle_give_up(db, update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    question = db.get(user_id)
    questions_and_answers = get_questions()
    full_answer = questions_and_answers[question]
    update.message.reply_text(
        text=full_answer
    )
    questions_and_answers = get_questions()
    question, answer = random.choice(list(questions_and_answers.items()))
    update.message.reply_text(
        text=question
        )
    db.set(user_id, question)

    return NEW_QUESTION_REQUEST


def error(update: Update, context: CallbackContext, error):
    """Log Errors caused by Updates."""
    logging.logger.warning('Update "%s" caused error "%s"', update, error)


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
    load_dotenv()
    updater = Updater(os.getenv('TOKEN'))
    
    db = redis.Redis(
        host='redis-13791.c300.eu-central-1-1.ec2.cloud.redislabs.com',
        port=os.getenv('REDIS_DB_PORT'),
        username='default',
        password='tyJIB0VlvTh3EJplw2QjqbpY6dQZL2Qm',
        decode_responses=True,
        charset="utf-8",
        db=0)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler("help", help)
        ],

        states={
            NEW_QUESTION_REQUEST: [
                MessageHandler(Filters.regex('Новый вопрос'), partial(handle_new_question_request, db)),
                MessageHandler(Filters.regex('Попробовать еще раз'), partial(handle_solution_attempt, db)),
                MessageHandler(Filters.regex('Сдаться'), partial(handle_give_up, db)),
                MessageHandler(Filters.text, partial(handle_solution_attempt, db)),
                
            ]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    
    updater.start_polling()


if __name__ == '__main__':
    main()