import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class ProjectExtraction(BaseModel):
    title: str
    summary: str
    technologies: list[str]


class AIRefusalError(Exception):
    pass


class AIProviderError(Exception):
    pass


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def extract_project_details(notes):
    if client is None:
        raise AIProviderError("OPENAI_API_KEY is not configured")

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract a portfolio project from the user's notes. "
                        "Return a short title, a summary of one or two sentences, "
                        "and a list of technologies."
                    ),
                },
                {"role": "user", "content": notes},
            ],
            response_format=ProjectExtraction,
        )
    except Exception as error:
        raise AIProviderError("The provider request failed") from error

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise AIRefusalError(message.refusal)

    if message.parsed is None:
        raise AIProviderError("The provider returned no structured result")

    return message.parsed
