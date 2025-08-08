# main.py

import os
from dotenv import load_dotenv
from crew.discern_crew import DiscernCrew

load_dotenv()

if __name__ == "__main__":
    question = input("What would you like to ask? ")

    crew_instance = DiscernCrew(user_prompt=question)
    result = crew_instance.crew().kickoff()

    print("\n=== RESULT ===\n")
    print(result.raw)
