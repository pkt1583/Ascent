from app.utils.constants import MANIFESTS_GIT_BRANCH
from app.core.config import get_settings
settings = get_settings()

def prepare_consumer_application_data(application, cluster, target_policy_id):
    consumer_application_template_data = {
        'metadata': {
            'name': f'{application.name}-{cluster.environment}',
            'namespace': 'argocd',
            'labels': f'targetId: {target_policy_id}'
        },
        'spec': {
            "project": "default",
            "source": {
                "repoURL":  application.repo_url,
                "targetRevision": application.repo_branch,
                "path": f'{application.repo_path}/{cluster.environment}/{cluster.name}',
            },
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": application.namespace
            },
            "syncPolicy": {
                "automated": {
                    "prune": "true",
                    "selfHeal": 'true'
                }
            }
        }
    }
    return consumer_application_template_data
    
def prepare_master_application_data(project_name, cluster_name):
    master_application_template_data = {
        "metadata": {
            "name": f"consumer-{project_name}-master-apps",
            "namespace": "argocd"
        },
        "spec": {
            "project": "default",
            "source": {
                "repoURL": settings.ARGOCD_MASTER_APPLICATION_REPO_URL,
                "targetRevision": MANIFESTS_GIT_BRANCH,
                "path": f"{project_name}/{cluster_name}/consumer"
            },
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": f"{project_name}-all"
            },
            "syncPolicy": {
                "automated": {
                    "prune": True,
                    "selfHeal": True
                }
            }
        }
    }
    return master_application_template_data