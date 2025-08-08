# crew/discern_crew.py
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task, crew

@CrewBase
class DiscernCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, user_prompt=None, context=None):
        super().__init__()
        self.user_prompt = user_prompt
        self.context = context or {}

    # ---- Agents ----
    @agent
    def intent_router(self) -> Agent:
        return Agent(config=self.agents_config["intent_router"], verbose=True)

    @agent
    def scripture_retriever(self) -> Agent:
        return Agent(config=self.agents_config["scripture_retriever"], verbose=True)

    @agent
    def doctrine_teacher(self) -> Agent:
        return Agent(config=self.agents_config["doctrine_teacher"], verbose=True)

    @agent
    def pastoral_counselor(self) -> Agent:
        return Agent(config=self.agents_config["pastoral_counselor"], verbose=True)

    @agent
    def assurance_shepherd(self) -> Agent:
        return Agent(config=self.agents_config["assurance_shepherd"], verbose=True)

    @agent
    def berean_validator(self) -> Agent:
        return Agent(config=self.agents_config["berean_validator"], verbose=True)

    @agent
    def final_editor(self) -> Agent:
        return Agent(config=self.agents_config["final_editor"], verbose=True)

    # ---- Tasks ----
    @task
    def route_intent_task(self) -> Task:
        t = Task(config=self.tasks_config["route_intent_task"])
        t.agent = self.intent_router()
        return t

    @task
    def gather_scripture_task(self) -> Task:
        t = Task(config=self.tasks_config["gather_scripture_task"])
        t.agent = self.scripture_retriever()
        return t

    @task
    def teach_answer_task(self) -> Task:
        t = Task(config=self.tasks_config["teach_answer_task"])
        t.agent = self.doctrine_teacher()
        return t

    @task
    def pastoral_answer_task(self) -> Task:
        t = Task(config=self.tasks_config["pastoral_answer_task"])
        t.agent = self.pastoral_counselor()
        return t

    @task
    def assurance_answer_task(self) -> Task:
        t = Task(config=self.tasks_config["assurance_answer_task"])
        t.agent = self.assurance_shepherd()
        return t

    @task
    def berean_validate_task(self) -> Task:
        t = Task(config=self.tasks_config["berean_validate_task"])
        t.agent = self.berean_validator()
        return t

    @task
    def final_edit_task(self) -> Task:
        t = Task(config=self.tasks_config["final_edit_task"])
        t.agent = self.final_editor()
        return t

    # ---- Crew ----
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.intent_router(),
                self.scripture_retriever(),
                self.doctrine_teacher(),
                self.pastoral_counselor(),
                self.assurance_shepherd(),
                self.berean_validator(),
                self.final_editor(),
            ],
            tasks=[
                self.route_intent_task(),
                self.gather_scripture_task(),
                # One of teach/pastoral/assurance will be used by your handler based on router output,
                # or leave all here if you’re chaining regardless:
                self.teach_answer_task(),
                self.pastoral_answer_task(),
                self.assurance_answer_task(),
                self.berean_validate_task(),
                self.final_edit_task(),
            ],
            process=Process.sequential,
            verbose=True
        )
