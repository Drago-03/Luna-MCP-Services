# moved from subdirectory
from dataclasses import dataclass
import os
from typing import Optional

@dataclass
class GitHubOAuthConfig:
    client_id: Optional[str]
    client_secret: Optional[str]
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
