from crew.discern_crew import DiscernCrew

def run_discern_agents(prompt):
    crew_instance = DiscernCrew(user_prompt=prompt)
    result = crew_instance.crew().kickoff()
    return result.raw
