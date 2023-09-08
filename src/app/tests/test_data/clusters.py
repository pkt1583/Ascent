cluster_post_valid_payload_raw_data01 = {
  "name": "Aus-MB-001",
  "description": "First store in Melbourne",
  "short_name": "Melbourne001",
  "metadata": {
    "city": "Melbourne"
  }
}

cluster_post_valid_payload_raw_data02 = {
  "name": "Aus-MB-002",
  "description": "Second store in Melbourne",
  "short_name": "Melbourne002",
  "metadata": {
    "city": "Melbourne"
  }
}

#Missing store name
cluster_payload_missing_required_data = {
  "description": "First store in Melbourne",
  "short_name": "Melbourne001",
  "metadata": {
    "city": "Melbourne"
  }
}


cluster_post_in_valid_payload_data = {
  "name": 123,
  "description": True,
  "short_name": True,
  "metadata": {
    "city": 45
  }
}
