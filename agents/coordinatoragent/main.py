import rag.rag_service as RagService
import agents.synthesizeragent.main as SynthesizerAgent
from typing import Any
from guardrails import Guard
from guardrails.hub import DetectPII
import logfire
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import EqualsExpected, Contains
from agents.coordinatoragent.models.coordinator_agent_request import CoordinatorAgentRequest
from agents.synthesizeragent.models.synthesizer_agent_request import SynthesizerAgentRequest
from util import Util
from pathlib import Path

ENABLE_TRACE_TO_LOGFIRE = True
MODEL_GOOGLE_GEMINI = "google-gla:gemini-2.5-pro"

ERROR_PROBLEM_OCCURRED = "Something went wrong while processing your request. Please try again in a moment."
ERROR_INVALID_INPUT = "Please enter a valid input."


# export GOOGLE_API_KEY="<your google api key>"
# export LANGSMITH_API_KEY="<your lagsmith api key>"
# export OTEL_EXPORTER_OTLP_ENDPOINT="https://api.smith.langchain.com/otel"
# export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=${LANGSMITH_API_KEY}"

if ENABLE_TRACE_TO_LOGFIRE:
    logfire.configure(service_name='second_brain', send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_httpx(capture_all=True)

# Setup Guard
validate_pii_guard = Guard().use(
    DetectPII, ["EMAIL_ADDRESS", "PHONE_NUMBER"]
)

mask_pii_guard = Guard().use(
    DetectPII, ["EMAIL_ADDRESS", "PHONE_NUMBER"],
    on_fail="fix"
)


def validate_sensitive_data(user_input: str) -> bool:
    try:
        validate_pii_guard.validate(user_input)
        return False
    except Exception as e:
        return True


def mask_sensitive_data(user_input: str) -> str | None:
    return mask_pii_guard.validate(user_input).validated_output

@logfire.instrument("CoordinatorAgent.ingest_data_from_docs")
def ingest_data_from_docs() -> None:
    RagService.delete_ingested_data()
    RagService.ingest_data_from_file_or_folder(str(Path(__file__).resolve().parent.parent.parent.joinpath('docs')))


@logfire.instrument("CoordinatorAgent.get_response")
def get_response(request: CoordinatorAgentRequest) -> Any:
    user_input = None
    ingested_data = None

    if not request.user_input or request.user_input.strip() == "":
        SynthesizerAgent.store_conversation_to_memory(user_input if user_input else request.user_input, ERROR_INVALID_INPUT)
        return ERROR_INVALID_INPUT

    try:
        is_sensitive_data_exists = validate_sensitive_data(request.user_input)
        if is_sensitive_data_exists:
            user_input = mask_sensitive_data(request.user_input)
        else:
            user_input = request.user_input
            # Get existing ingested data for the user
            ingested_data = RagService.get_ingested_data(user_input)

        print(f"3. Synthesizer agent is triggered with below details\n"
              f"user_input={user_input}\n"
              f"is_sensitive_data_exists={is_sensitive_data_exists}\n"
              f"ingested_data={ingested_data}")
        synthesizer_agent_request = get_synthesizer_agent_request(is_sensitive_data_exists, ingested_data,
                                                                  user_input)
        return SynthesizerAgent.get_synthesized_response(synthesizer_agent_request)
    except FileNotFoundError as fnfe:
        print("FileNotFound Error occurred:", fnfe)
        SynthesizerAgent.store_conversation_to_memory(user_input if user_input else request.user_input, str(fnfe))
        return str(fnfe)
    except Exception as ex:
        print("Error occurred:", ex)
        SynthesizerAgent.store_conversation_to_memory(user_input if user_input else request.user_input, ERROR_PROBLEM_OCCURRED)
        return ERROR_PROBLEM_OCCURRED

def get_synthesizer_agent_request(is_sensitive_data_exists: bool , ingested_data: str | None,
                                  user_input: str | None) -> SynthesizerAgentRequest:
    return SynthesizerAgentRequest(
        user_query=user_input,
        is_sensitive_data_exists=is_sensitive_data_exists,
        ingestion_context=ingested_data)


dataset = Dataset(
    cases=[
        Case(
            name="Test whether Agent detects PII information",
            inputs=CoordinatorAgentRequest(
                user_input="My email is test@gmail.com",
                user_id="abc",
            ),
            expected_output=Util.ERROR_GUARD_PII,
            evaluators=(EqualsExpected(),),
        )
    ]
)

retrieval_dataset = Dataset(
    cases=[
        Case(
            name="Retrieve answers from Agent for the questions related to EduTrack",
            inputs=CoordinatorAgentRequest(
                user_input="What is EduTrack used for?",
                user_id="abc",
            ),
            expected_output="should contain educational",
            evaluators=[Contains("educational")],
        ),
        Case(
            name="Retrieve answer for general question",
            inputs=CoordinatorAgentRequest(
                user_input="Who is the prime minister of India",
                user_id="abc",
            ),
            expected_output=Util.CANNOT_PROCESS_MESSAGE,
            evaluators=[Contains(Util.CANNOT_PROCESS_MESSAGE)],
        )
    ]
)

if __name__ == "__main__":
    report = dataset.evaluate_sync(get_response)
    retrieval_report = retrieval_dataset.evaluate_sync(get_response)
    combined_report = report
    combined_report.cases.extend(retrieval_report.cases)
    combined_report.print(include_expected_output=True, include_input=True, include_output=True, width=300)
