class MissingClusterStateObjectException(Exception):
    """Exception raised when a cluster state object is missing"""

    def __init__(self, cluster_id, cluster_state=None):
        self.message = f"Cluster state object for cluster {cluster_id} is missing"
        super().__init__(self.message)
        self.cluster_state = cluster_state

    def get_cluster_state(self):
        return self.cluster_state
