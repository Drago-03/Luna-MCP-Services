# moved from subdirectory
import os
from dataclasses import dataclass


@dataclass
class GitHubOAuthConfig:
    client_id: str | None
    client_secret: str | None
    authorize_url: str = "https://github.com/login/oauth/authorize"
    token_url: str = "https://github.com/login/oauth/access_token"
    scopes: str = "repo workflow"

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)


def get_config() -> GitHubOAuthConfig:
    return GitHubOAuthConfig(
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    )


def is_enabled() -> bool:
    return get_config().enabled
