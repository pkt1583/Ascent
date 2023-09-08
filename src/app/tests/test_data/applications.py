app_post_valid_payload_raw_data01 = {
  "name": "app01",
  "description": "The first sample app on edge",
  "repo_url": "http://someazdolocation/",
  "repo_branch": "main",
  "repo_path": "app01",
  "metadata": {
    "type": "common"
  }
}

app_post_valid_payload_raw_data02 = {
  "name": "app02",
  "description": "The second sample app on edge",
  "repo_url": "http://someazdolocation/",
  "repo_branch": "main",
  "repo_path": "app02",
  "metadata": {
    "type": "common"
  }
}

#Missing required data, name, repo_url, repo_path, and branch all are required
app_payload_missing_required_data = {
  "description": "First app on edges",
  "metadata": {
    "type": "common"
  }
}


app_post_in_valid_payload_data = {
  "name": 2,
  "description": "The second sample app on edge",
  "repo_url": True,
  "repo_branch": True,
  "repo_path": False,
  "metadata": {
    "type": "common"
  }
}
