from typing import Any
from agents.synthesizeragent.models.synthesizer_agent_request import SynthesizerAgentRequest
from util import Util
from pydantic_ai import Agent
from agents.memory.agent_memory import AgentMemory
import logfire
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Contains
import os

MODEL_GOOGLE_GEMINI = "google-gla:gemini-2.5-pro"

agent_memory = AgentMemory()

@logfire.instrument("SynthesizerAgent.get_synthesized_response")
def get_synthesized_response(request: SynthesizerAgentRequest
                             ) -> Any:
    if request.is_sensitive_data_exists:
        store_conversation_to_memory(request.user_query, Util.ERROR_GUARD_PII)
        return Util.ERROR_GUARD_PII
    delimiter_context = "####CONTEXT####"
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "instructions.md")
    system_prompt = Util.get_instructions(path)
    system_prompt = system_prompt.replace("####MESSAGE####", Util.CANNOT_PROCESS_MESSAGE)
    if request.ingestion_context:
        system_prompt += f"\n\n{delimiter_context}\n\n{request.ingestion_context}\n\n{delimiter_context}"
    else:
        system_prompt += f"\n\n{delimiter_context}\n\n{delimiter_context}"
    print(f"system_prompt={system_prompt}")
    agent = Agent(
        model=MODEL_GOOGLE_GEMINI,
        system_prompt=[system_prompt],
    )
    result = agent.run_sync(request.user_query)
    print(f"response from synthesizerAgent={result.output}")
    store_conversation_to_memory(request.user_query, result.output)
    return result.output


def store_conversation_to_memory(user_query:str, agent_response:str) -> None:
    agent_memory.add_conversation(user_query, agent_response)

dataset = Dataset(
    cases=[
        Case(
            name="Retrieve answers from Agent for the questions related to EduTrack",
            inputs=SynthesizerAgentRequest(
                user_query='What is EduTrack used for?',
                ingestion_context = """
                EduTrack – Frequently Asked Questions
                Q1: What is EduTrack used for?
                A1: EduTrack helps educational institutions monitor student engagement, analyze learning
                behavior, and proactively support at-risk learners through data-driven insights.
                Q2: Which platforms does EduTrack integrate with?
                A2: EduTrack integrates seamlessly with LMS platforms such as Moodle, Canvas,
                Blackboard, Google Classroom, and can be extended to custom LMS solutions via API.Q5: How does EduTrack benefit teachers?
                A5: Instructors receive weekly summaries, alerts about disengaged students, and tools to
                send personalized feedback or motivational nudges.
                Q6: Can students access their own dashboards?
                A6: Yes. Students can view their own learning progress, receive AI-generated tips, and
                compare their engagement anonymously against peers.
                Q7: Does EduTrack support real-time notifications?access to EduTrack’s support portal.
                Q18: Does EduTrack integrate with Student Information Systems (SIS)?
                A18: Yes. It can sync with most SIS platforms to fetch enrollment, demographics, and
                academic standing data.
                Q19: How does EduTrack notify instructors about at-risk students?
                A19: Faculty receive weekly alerts and visual cues on their dashboards, highlighting students
                who need attention based on defined risk thresholds.
                Q20: Where can users learn about new EduTrack features?
                """,
            ),
            expected_output="should contain educational",
            evaluators=[Contains("educational")],
        ),
        Case(
            name="Retrieve answer for general question",
            inputs=SynthesizerAgentRequest(
                user_query='Who is the prime minister of India?',
            ),
            expected_output=Util.CANNOT_PROCESS_MESSAGE,
            evaluators=[Contains(Util.CANNOT_PROCESS_MESSAGE)],
        )
    ]
)

if __name__ == "__main__":
    report = dataset.evaluate_sync(get_synthesized_response)
    report.print(include_expected_output=True, include_input=True, include_output=True, width=300)
