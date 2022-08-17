from pprint import pprint


questions = []
with open('questions/znvd98.txt', 'r', encoding='KOI8-R') as file:
    questions = file.read().split('\n\n')

questions_and_answers = {}
for text_part in questions:
    if 'Вопрос' in text_part:
        questions_and_answers[text_part] = questions[questions.index(text_part)+1]

for key, value in questions_and_answers.items():
    print(value)