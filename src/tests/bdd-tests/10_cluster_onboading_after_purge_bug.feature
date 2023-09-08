Feature: Purge features Testting bug

  Scenario: Set up clusters and apps for test testing scenarios
    Given database is cleaned up
    And I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | data                                                                                                                                                                          |
      | {"name": "east-nsw-newcastle-2940-01","shortName": "cluster1","environment": "nonprod","metadata": {"gpu": "true","region": "east","country": "Australia","edge": "true"}}    |
      | {"name": "south-vic-melbourne-32901-01","shortName": "cluster2","environment": "nonprod","metadata": {"gpu": "true","region": "south","country": "Australia","edge": "true"}} |
    Then The cluster with below name should be created having status COMPLETED
      | name                         |
      | east-nsw-newcastle-2940-01   |
      | south-vic-melbourne-32901-01 |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                  |
      | {"name": "p-test-bug", "description": "Created for testing p", "cost_center": "123", "group": ["p-test-bug-nonprod"]} |
    When I hit the v1/applications to create a application with below data
      | data                                                                                                                                                                                                  |
      | {"name": "app1","repo_url": "https://repoutl/plat_multistore_app_demo","repo_branch": "master","repo_path": "manifest/app1","metadata": {"common": "true","gpu" : "false"},"namespace": "p-test-bug"} |
      | {"name": "app2","repo_url": "https://repourl/demo-apps","repo_branch": "main","repo_path": "app2","metadata": {"common": "true","gpu" : "true"},"namespace": "p-test-bug"}                            |
    Then The application with below name should be created having status COMPLETED
      | name |
      | app1 |
      | app2 |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | data                                                                                                         |
      | { "name": "common-to-gpu", "app_selector": {   "common": "true" }, "cluster_selector": {   "edge": "true" }} |
    Then The response status code should be 201
    #And The manifests should have been created exactly as 10_cluster_onboard_bug
    And The below applications are present on specified clusters
      | cluster_name                                            | comma_seperated app_name |
      | east-nsw-newcastle-2940-01,south-vic-melbourne-32901-01 | app1,app2                |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | data                                                                                                                                                |
      | {"name": "delete-from-cluster3","operation": "PURGE","app_selector": {  "name" : "app2"},"cluster_selector": {  "name": "east-nsw-sydney-1001-01"}} |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                            | comma_seperated app_name |
      | east-nsw-newcastle-2940-01,south-vic-melbourne-32901-01 | app1,app2                |
    When I have manifest checked out from 10_cluster_onboard_bug at 10_cluster_onboard_bug_tmp
    And I hit the v1/clusters to create a cluster with below data
      | data                                                                                                                                                                    |
      | {"name": "east-nsw-sydney-1001-01","shortName": "cluster3","environment": "nonprod","metadata": {"gpu": "true","region": "east","country": "Australia","edge": "true"}} |
    Then The cluster with below name should be created having status COMPLETED
      | name                    |
      | east-nsw-sydney-1001-01 |
    And The manifests should have been created exactly as 10_cluster_onboard_bug1
    And The below applications are present on specified clusters
      | cluster_name                                            | comma_seperated app_name |
      | east-nsw-newcastle-2940-01,south-vic-melbourne-32901-01 | app1,app2                |
      | east-nsw-sydney-1001-01                                 | app1                     |
