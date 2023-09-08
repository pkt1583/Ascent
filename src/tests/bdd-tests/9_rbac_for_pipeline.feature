Feature: RBAC test based on pipeline access token only

  Scenario: Setup cluster and validate get
    Given I am part of below groups
      | group            |
      | plat-dummy-admin |
    And database is cleaned up
    When I hit the v1/clusters to create a cluster with below data
      | name                        | short_name | metadata.label | environment |
      | pipeline-rbac-cluster-dummy | mc         | dummy-valid   | dummy       |
    Then The response status code should be 201
    Given I am part of below groups
      | group              |
      | plat-nothing-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                          | short_name | metadata.label | environment |
      | pipeline-rbac-cluster-nothing | mc         | dummy-valid   | nothing     |
    Then The response status code should be 201
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                          | short_name | metadata.label | environment |
      | pipeline-rbac-cluster-nonprod | mc         | dummy-valid   | nonprod     |
    Then The response status code should be 201
    Given I have a pipeline access token
    When I hit the v1/clusters to get all cluster
    Then The response status code should be 200
    And There should be 3 items in response

  Scenario: Setup Application and validate get
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                       |
      | {"name": "myns-mygroup", "description": "Created for testing", "cost_center": "123", "group": ["mygroup-nonprod"]} |
    Then The response status code should be 201
    And The response should have id
    Given I am part of below groups
      | group           |
      | plat-prod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                 |
      | {"name": "myns-anothergroup", "description": "Created for testing", "cost_center": "123", "group": ["anothergroup-jamura"]} |
    Then The response status code should be 201
    Given I have a pipeline access token
    When I hit the v1/namespaces to get all namespace
    Then The response status code should be 200
    And There should be 2 items in response
    When I hit the v1/applications to create a application with below data
      | name               | repo_url             | repo_branch | repo_path | metadata.app_type        | namespace    |
      | myapp-myns-mygroup | http://some-repo-url | main        | somepath  | app-testing-myns-mygroup | myns-mygroup |
    When I hit the v1/applications to create a application with below data
      | name                    | repo_url             | repo_branch | repo_path | metadata.app_type             | namespace         |
      | myapp-myns-anothergroup | http://some-repo-url | main        | somepath  | app-testing-myns-anothergroup | myns-anothergroup |
    When I hit the v1/applications to get all application
    Then The response status code should be 200
    And There should be 2 items in response
    When I hit the v1/applications?query=name=myapp-myns-mygroup to get all application
    Then The response status code should be 200
    And There should be 1 items in response