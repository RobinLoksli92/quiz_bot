import os


def get_questions():
    questions = []
    for filename in os.listdir('questions'):
        with open(f'questions/{filename}', 'r', encoding='KOI8-R') as file:
            questions += file.read().split('\n\n')

        questions_and_answers = {}
        for text_part in questions:
            if 'Вопрос' in text_part:
                questions_and_answers[text_part] = questions[questions.index(text_part)+1]

        return questions_and_answers


def main():
    quest = get_questions()
    print(quest)


if __name__ == '__main__':
    main()