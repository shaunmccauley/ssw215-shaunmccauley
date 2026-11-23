import base64
import os

import requests
from dotenv import load_dotenv


load_dotenv()

README_LIMIT = 4000


class GitHubRepositoryError(Exception):
    pass


class GitHubRepositoryNotFoundError(GitHubRepositoryError):
    pass


class GitHubReadmeTooShortError(GitHubRepositoryError):
    pass


def fetch_repository_readme(owner, repo):
    if not isinstance(owner, str) or not owner.strip():
        raise GitHubRepositoryError("Repository owner is required")
    if not isinstance(repo, str) or not repo.strip():
        raise GitHubRepositoryError("Repository name is required")

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner.strip()}/{repo.strip()}/readme",
            headers=headers,
            timeout=8,
        )
    except requests.RequestException as error:
        raise GitHubRepositoryError("GitHub could not be reached") from error

    if response.status_code == 404:
        raise GitHubRepositoryNotFoundError("Repository or README not found")
    if response.status_code != 200:
        raise GitHubRepositoryError("GitHub could not fetch the repository")

    try:
        readme = base64.b64decode(response.json()["content"]).decode("utf-8")
    except (KeyError, ValueError, UnicodeDecodeError) as error:
        raise GitHubRepositoryError("The README could not be decoded") from error

    readme = readme.strip()
    if len(readme) < 20:
        raise GitHubReadmeTooShortError("The README is shorter than 20 characters")

    return readme[:README_LIMIT]
