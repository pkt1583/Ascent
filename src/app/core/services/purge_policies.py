import copy
from abc import ABC, abstractmethod
from typing import Dict

from app.core.models.applications import Application
from app.core.models.clusters import Cluster
from app.core.models.targetpolicies import TargetPolicy


class PurgePolicy(ABC):
    @abstractmethod
    def filter_purged(self, apps: list[Application], purge_policies: set[TargetPolicy], policy_under_evaluation: TargetPolicy, **kwargs) -> list[Application]:
        """takes list of applications, all purge target policies and policy under evaluation and any additional argument that concrete implementation needs
        Concrete implementations would apply appropriate rules and returned filted metadata_based_resources"""


class ApplyOnceCronologicalOrderedPurgePolicy(PurgePolicy):
    def filter_purged(self, metadata_based_resources: list[Application | Cluster], purge_policies: set[TargetPolicy], policy_under_evaluation: TargetPolicy, **kwargs) -> list[
        Application | Cluster]:
        """
               Filter out purged appOrCluster based on the given purge policies. it evaluates all purge_policies against current policy.
                Once any of purge_policies is matched then that will never be taken up for matching again
               """
        appOrCluster: list[Application | Cluster] = []
        skipped_purged_policies = kwargs.pop("already_evaluate_purged_policies")
        evaluated_purged_policies = set()
        for resource in metadata_based_resources:
            metadata: Dict[str, str] | None = resource.metadata
            # is matching any of purge_policies application
            skip = False
            for p_policy in purge_policies:
                # There was match with something so no need to evaluate this resource against any other policy
                # No need evaluate against purge policies that were evaluated earlier
                # ignore purge policies before the current target policy
                if self.should_skip_evaluation(policy_under_evaluation, p_policy, skip, skipped_purged_policies):
                    continue
                purge_policy = copy.deepcopy(p_policy)
                purge_meta = []
                # Code smell. Do no use if
                if isinstance(resource, Application):
                    purge_meta = purge_policy.app_selector
                elif isinstance(resource, Cluster):
                    purge_meta = purge_policy.cluster_selector
                for k, v in purge_meta.items():
                    if metadata[k] in v.split(","):
                        skip = True  # Match is found so mark skip loop
                        val = purge_meta[k].split(",")
                        val.remove(metadata[k])  # Removed the matched value. This will be useful in case of comma separated values
                        if isinstance(resource, Application):  # Add rest of elements back to resource selector for matching in next resource iteration
                            purge_policy.app_selector[k] = ",".join(val)
                        elif isinstance(resource, Cluster):
                            purge_policy.cluster_selector[k] = ",".join(val)
                        # purged policy consumed once
                        if len(val) == 0:  # Nothing left in name. This is fully consumed so add to skip policy list
                            evaluated_purged_policies.add(purge_policy.id)
            if not skip:
                appOrCluster.append(resource)
        for policy in evaluated_purged_policies:
            skipped_purged_policies.append(policy)
        return appOrCluster

    def should_skip_evaluation(self, policy_under_evaluation, purge_policy, skip, skipped_purged_policies):
        return skip or purge_policy.id in skipped_purged_policies or purge_policy.updated_on < policy_under_evaluation.updated_on
