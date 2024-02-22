import requests
import random
import html


def answers(correct: str, falsies: list[str]) -> tuple[list[str], int]:
    questions_list = ["", "", "", ""]
    tries = 0
    while tries < 4:
        place = random.randint(0, 3)
        if correct not in questions_list:
            questions_list[place] = correct
            tries += 1
        if not questions_list[place]:
            if falsies[0] not in questions_list:
                questions_list[place] = falsies[0]
                tries += 1
            elif falsies[1] not in questions_list:
                questions_list[place] = falsies[1]
                tries += 1
            elif falsies[2] not in questions_list:
                questions_list[place] = falsies[2]
                tries += 1
    return questions_list, questions_list.index(correct) + 1


def load_questions() -> dict[int, dict[str, list[str] | str | int]]:
    response = requests.get("https://opentdb.com/api.php?amount=50&type=multiple")
    order = response.json()
    questions: dict[int, dict[str, list[str] | str | int]] = {}
    for value in order["results"]:
        quest = random.randrange(1, 60)
        if quest not in questions.keys():
            all_questions, correctly_place = answers(
                value["correct_answer"], value["incorrect_answers"]
            )
            questions[quest] = {
                "question": html.unescape(value["question"]),
                "answers": all_questions,
                "correct": correctly_place,
            }
    return questions
