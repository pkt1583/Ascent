import requests
from requests.adapters import HTTPAdapter, Retry

from app.core.auth.rbac import settings


def retryable_requester():
    s = requests.session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s


def is_valid_role(role: str) -> bool:
    acceptable_roles = settings.VALID_ROLES.split(",")
    return role.lower() in acceptable_roles
