from functools import partial
import os
from re import A
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


logger = logging.getLogger(__name__)

NEW_QUESTION_REQUEST, ANSWER = range(2)


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


def handle_new_question_request(db, questions_and_answers, update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    question, answer = random.choice(list(questions_and_answers.items()))
    update.message.reply_text(
        text=question,
        reply_markup=ReplyKeyboardMarkup([['Сдаться']], resize_keyboard=True)
        )
    db.set(user_id, question)

    return ANSWER


def handle_solution_attempt(db, questions_and_answers, update: Update, context: CallbackContext):
    user_answer = update.message.text
    user_id = update.effective_message.from_user.id
    question = db.get(user_id)
    full_answer = questions_and_answers[question]
    answer_without_info = full_answer.split('.')[0]
    if user_answer in answer_without_info:
        user_score = db.get(f'User_id_{user_id}')
        if not user_score:
            user_score = 0
        db.set(f'User_id_{user_id}', int(user_score)+1)
        update.message.reply_text(
            text='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            reply_markup=ReplyKeyboardMarkup([['Новый вопрос', 'Мой счёт']], resize_keyboard=True)
        )
        return NEW_QUESTION_REQUEST
    else:
        update.message.reply_text(
            text=f'Неправильно… Попробуешь ещё раз?',
            reply_markup=ReplyKeyboardMarkup([['Сдаться']], resize_keyboard=True)
        )
        return ANSWER
    


def handle_give_up(db, questions_and_answers, update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    question = db.get(user_id)
    full_answer = questions_and_answers[question]
    update.message.reply_text(
        text=full_answer
    )
    question, answer = random.choice(list(questions_and_answers.items()))

    update.message.reply_text(
        text=question
        )
    db.set(user_id, question)

    return ANSWER


def check_my_score(db, update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_score = db.get(f'User_id_{user_id}')
    if not user_score:
        update.message.reply_text(
            text='Вы еще не набрали баллов.'
        )
        return NEW_QUESTION_REQUEST

    update.message.reply_text(
        text=f'Ваш результат: {user_score}'
    )
    return NEW_QUESTION_REQUEST


def catch_error(update: Update, context: CallbackContext, error):
    """Log Errors caused by Updates."""
    logging.logger.warning('Update "%s" caused error "%s"', update, error)


def cancel(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

    load_dotenv()
    updater = Updater(os.getenv('TG_BOT_TOKEN'))
    
    db = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        username=os.getenv('REDIS_USERNAME'),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
        charset="utf-8",
        db=0)
    questions_and_answers = get_questions()

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler("help", help)
        ],

        states={
            NEW_QUESTION_REQUEST: [
                MessageHandler(Filters.regex('Новый вопрос'), partial(handle_new_question_request, db, questions_and_answers)),
                MessageHandler(Filters.regex('Мой счёт'), partial(check_my_score, db)),
                
            ],
            ANSWER: [
                MessageHandler(Filters.regex('Сдаться'), partial(handle_give_up, db, questions_and_answers)),
                MessageHandler(Filters.text, partial(handle_solution_attempt, db, questions_and_answers)),
            ]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    dp.add_error_handler(catch_error)
    
    updater.start_polling()


if __name__ == '__main__':
    main()