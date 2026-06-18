from ai_service import PjaSenseiAI
from fastapi import FastAPI


def discuss_a_problem():
    ai = PjaSenseiAI()

    problem = input("Podaj treść zadania: ")
    progress = input("Podaj dotychczasowe rozwiązanie: ")
    question = input("Podaj pytanie studenta: ")

    prompt = f"""
    Zadanie:
    {problem}

    Dotychczasowe rozwiązanie:
    {progress}

    Pytanie studenta:
    {question}
    """
    
    print("\nPJASensei przetwarza Twoją wiadomość, za chwilę otrzymasz odpowiedź...\n")
    pja_sensei_answer = ai.message_pja_sensei(prompt)
    print(pja_sensei_answer)

    while True:
        user_answer = input()
        pja_sensei_answer = ai.message_pja_sensei(user_answer)
        print(pja_sensei_answer)

    
if __name__ == "__main__":
    discuss_a_problem()