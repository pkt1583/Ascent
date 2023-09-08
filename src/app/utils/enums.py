
from enum import Enum


class EventType(Enum):
    TARGETPOLICY_ONBOARDING = "TARGETPOLICY_ONBOARDING"
    CLUSTER_ONBOARDING = "CLUSTER_ONBOARDING"
    APP_ONBOARDING = "APP_ONBOARDING"

class DeploymentStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class OnboardStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILURE = "FAILURE"

class Operation(str, Enum):
    CREATE = "CREATE"
    PURGE = "PURGE"