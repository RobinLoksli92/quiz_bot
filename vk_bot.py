from dotenv import load_dotenv
import random
import redis
import os
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from get_questions import get_questions


def start(event, vk_api, keyboard):
    user_id = event.user_id
    vk_api.messages.send(
        user_id=user_id,
        message='Привет, я бот виторин!',
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000),
    )


def ask_question(event, vk_api, keyboard, db):
    user_id = event.user_id
    questions_and_answers = get_questions()
    question, answer = random.choice(list(questions_and_answers.items()))
    db.set(user_id, question)
    vk_api.messages.send(
        user_id=user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1,1000),
    )


def check_answer(event, vk_api, keyboard, db):
    user_answer = event.text
    user_id = event.user_id
    question = db.get(user_id)
    questions_and_answers = get_questions()
    full_answer = questions_and_answers[question]
    answer_without_info = full_answer.split('.')[0]
    if user_answer in answer_without_info:
        user_score = db.get(f'User_id_{user_id}')
        if not user_score:
            user_score = 0
        db.set(f'User_id_{user_id}', int(user_score)+1)
        vk_api.messages.send(
            user_id=user_id,
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            keyboard=keyboard.get_keyboard(),
            random_id=random.randint(1, 1000)
        )
    else:
        vk_api.messages.send(
            user_id=user_id,
            message=f'Неправильно… Попробуешь ещё раз?',
            keyboard=keyboard.get_keyboard(),
            random_id=random.randint(1, 1000)
        )


def give_up(event, vk_api, keyboard, db):
    user_id = event.user_id
    question = db.get(user_id)
    questions_and_answers = get_questions()
    full_answer = questions_and_answers[question]
    vk_api.messages.send(
        user_id=user_id,
        message=full_answer,
        random_id=random.randint(1, 1000)
    )

    question, answer = random.choice(list(questions_and_answers.items()))

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000)
    )
    db.set(user_id, question)


def my_score(event, vk_api, keyboard, db):
    user_id = event.user_id
    user_score = db.get(f'User_id_{user_id}')
    if not user_score:
        vk_api.messages.send(
            user_id=user_id,
            message='Вы еще не набрали баллов.',
            keyboard=keyboard.get_keyboard(),
            random_id=random.randint(1, 1000)
        )
    score_answer = f'Ваш результат: {user_score}'
    vk_api.messages.send(
        user_id=user_id,
        message=score_answer,
        keyboard=keyboard.get_keyboard(),
        random_id=random.randint(1, 1000)
    )


def main():
    load_dotenv()
    db = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        username=os.getenv('REDIS_USERNAME'),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
        charset="utf-8",
        db=0)

    vk_session = vk.VkApi(token=os.getenv('VK_API_TOKEN'))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.SECONDARY)


    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Начать':
                start(event, vk_api, keyboard)
            elif event.text == 'Новый вопрос':
                ask_question(event, vk_api, keyboard, db)
            elif event.text == 'Сдаться':
                give_up(event, vk_api, keyboard, db)
            elif event.text == 'Мой счёт':
                my_score(event, vk_api, keyboard, db)
            else:
                check_answer(event, vk_api, keyboard, db)


if __name__ == "__main__":
    main()
