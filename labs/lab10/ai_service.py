import os
import uuid
import json

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


class ProjectExtraction(BaseModel):
    title: str
    summary: str
    technologies: list[str]


class GitHubProjectDraft(BaseModel):
    title: str
    summary: str
    technologies: list[str]
    difficulty: str


class AIRefusalError(Exception):
    pass


class AIProviderError(Exception):
    pass


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


sessions = {}


def draft_github_project(readme):
    if client is None:
        raise AIProviderError("OPENAI_API_KEY is not configured")

    history = [
        {
            "role": "system",
            "content": (
                "Create a portfolio project draft from the provided README. "
                "Return a short title, a summary of one or two sentences, "
                "a list of technologies, and difficulty exactly one of "
                "Beginner, Intermediate, or Advanced."
            ),
        },
        {"role": "user", "content": readme[:4000]},
    ]
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=history,
            response_format=GitHubProjectDraft,
        )
    except Exception as error:
        raise AIProviderError("The provider request failed") from error

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise AIRefusalError(message.refusal)
    if message.parsed is None:
        raise AIProviderError("The provider returned no structured result")

    draft = normalize_github_draft(message.parsed)
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "draft": draft,
        "history": history + [
            {"role": "assistant", "content": json.dumps(draft)},
        ],
    }
    return session_id, draft


def refine_github_project(session_id, feedback):
    if session_id not in sessions:
        raise KeyError(session_id)
    if client is None:
        raise AIProviderError("OPENAI_API_KEY is not configured")

    session = sessions[session_id]
    history = session["history"] + [{"role": "user", "content": feedback}]
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=history,
            response_format=GitHubProjectDraft,
        )
    except Exception as error:
        raise AIProviderError("The provider request failed") from error

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise AIRefusalError(message.refusal)
    if message.parsed is None:
        raise AIProviderError("The provider returned no structured result")

    draft = normalize_github_draft(message.parsed)
    session["draft"] = draft
    session["history"] = history + [{"role": "assistant", "content": json.dumps(draft)}]
    return draft


def get_github_draft(session_id):
    if session_id not in sessions:
        raise KeyError(session_id)
    return sessions[session_id]["draft"]


def normalize_github_draft(draft):
    difficulty = draft.difficulty.strip()
    if difficulty not in {"Beginner", "Intermediate", "Advanced"}:
        difficulty = "Intermediate"
    return {
        "title": draft.title.strip(),
        "summary": draft.summary.strip(),
        "technologies": [
            technology.strip()
            for technology in draft.technologies
            if technology.strip()
        ],
        "difficulty": difficulty,
    }


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
