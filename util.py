from pathlib import Path
class Util:
    PREFERENCE_INGESTION_RESPONSE = "Ok, I will save and remember that"
    FILE_NOT_FOUND_ERROR = "No txt file(s) found in the provided path"
    ERROR_GUARD_PII = "I cannot process your personal data like email/phone/date of birth/password for privacy and security reasons"
    CANNOT_PROCESS_MESSAGE = "Sorry, I am a chatbot assistant to answer questions related to EduTrack and I cannot process any other query. Please ask questions related to EduTrack"
    @staticmethod
    def get_instructions(file_path) -> str:
        instructions_file = Path(file_path)
        if instructions_file.exists():
            return instructions_file.read_text().strip()

        raise FileNotFoundError(f"Instructions file not found at: {file_path}")