Feature: App Management
   
   Scenario: create Application with proper data
     Given I am part of below groups
       | group          |
       | plat-nonprod-admin |
     When I hit the v1/namespaces to create a namespace with below data
       | data                                                                         |
       | {"name": "mynsforapp", "group": ["mygroup-nonprod", "anothergroup-nonprod"]} |
     Then The response status code should be 201
     And The response should have id
     And The header should have X-TRACE-ID

     Given I am part of below groups
       | group       |
       | mygroup-nonprod-contributor |
     When I hit the v1/applications to create a application with below data
       | name  | repo_url             | repo_branch | repo_path | metadata.app_type | namespace |
       | myapp | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp |
     Then The response status code should be 201
     And The response should have id
     And The header should have X-TRACE-ID
     And The response to create a application should be same as data from create_application_output.json

    Given I am part of below groups
       | group              |
       | mygroup-nonprod-reader |
     When I hit the v1/applications to create a application with below data
       | name  | repo_url             | repo_branch | repo_path | metadata.app_type | namespace  |
       | myapp | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp |
     Then The response status code should be 403
     And The header should have X-TRACE-ID

     Given I am part of below groups
       | group                |
       | somegroup-nonprod-reader |
     When I hit the v1/applications to create a application with below data
       | name   | repo_url             | repo_branch | repo_path | metadata.app_type | namespace  |
       | myapp1 | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp |
     Then The response status code should be 403

  Scenario: create Application with invalid name
    Given I am part of below groups
      | group                       |
      | mygroup-nonprod-contributor |
    When I hit the v1/applications to create a application with below data
      | name  | repo_url             | repo_branch | repo_path | metadata.app_type | namespace  |
      | MyApp | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp |
    Then The response status code should be 422
    And The header should have X-TRACE-ID

  Scenario: create Application without Namespace
    Given I am part of below groups
      | group       |
      | plat-nonprod-admin |
     When I hit the v1/applications to create a application with below data
       | name| repo_url   |repo_branch    |repo_path    |metadata.some_other_meta   |
       | app_without_namespace | http://some-repo-url | main        | somepath  | app-testing              |
    Then The response status code should be 422

  Scenario: create Application with invalid namespace
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/applications to create a application with below data
      | name                      | repo_url             | repo_branch | repo_path | metadata.some_other_meta | namespace  |
      | app-withinvalid-namespace | http://some-repo-url | main        | somepath  | app-testing              | invalid-ns |
    Then The response status code should be 400
    And The header should have X-TRACE-ID

  Scenario: create Application without metadata
    Given I am part of below groups
      | group       |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                 | short_name | metadata.label       | environment |
      | app-without-metadata | mc         | app-without-metadata | nonprod     |
    Then The response status code should be 201
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                                                      |
      | {"name": "app-without-metadata", "description": "Created for testing", "cost_center": "123", "group": ["app-without-metadata"], "environment": "nonprod"} |
    When I hit the v1/applications to create a application with below data
      | name                 | repo_url             | repo_branch | repo_path | namespace |
      | app-without-metadata | http://some-repo-url | main        | somepath  | app-without-metadata |
    Then The response status code should be 500
    And The header should have X-TRACE-ID

  Scenario: find all applications
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                          |
      | {"name": "mynsforapp", "group": ["mygroup-nonprod", "anothergroup-nonprod"]}  |
      | {"name": "mynsforapp2", "group": ["mygroup-nonprod", "anothergroup-nonprod"]} |
      | {"name": "mynsforapp3", "group": ["not-auth-nonprod"]}                        |
    Then The response status code should be 201

    Given I am part of below groups
      | group                    |
      | mygroup-nonprod-contributor  |
      | not-auth-nonprod-contributor |
    When I hit the v1/applications to create a application with below data
      | name   | repo_url             | repo_branch | repo_path | metadata.app_type | namespace   |
      | myapp  | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp  |
      | myapp2 | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp2 |
      | myapp3 | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp2 |
      | myapp4 | http://some-repo-url | main        | somepath  | app-testing       | mynsforapp3 |
    Then The response status code should be 201
    When I am part of below groups
      | group                   |
      | mygroup-nonprod-contributor |
    And I hit the v1/applications to get all application
    Then There should be 3 items in response
    And The response should have below attribute
      | attribute_name | value  |
      | items.0.name   | myapp  |
      | items.1.name   | myapp2 |
      | items.2.name   | myapp3 |

  Scenario: Find Application by id with user
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                     |
      | {"name": "mynsforappwithid-correct", "group": ["mygroupwithid-nonprod"]} |
    Then The response status code should be 201
    And The response should have id

    Given I am part of below groups
      | group                         |
      | mygroupwithid-nonprod-contributor |
    When I hit the v1/applications to create a application with below data
      | name                | repo_url             | repo_branch | repo_path | metadata.app_type | namespace                |
      | myappwithid-correct | http://some-repo-url | main        | somepath  | app-testing       | mynsforappwithid-correct |
    Then The response status code should be 201
    And The response should have id
    When I am part of below groups
      | group                    |
      | mygroupwithid-nonprod-reader |
    And I hit the v1/applications to get same application with id
    Then The response status code should be 200

    Given I am part of below groups
      | group                      |
      | myonegroup-nonprod-contributor |
    When I hit the v1/applications to get same application with id
    Then The response status code should be 401

    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/applications to get same application with id
    Then The response status code should be 200
    And The response should have below attribute
      | attribute_name | value                    |
      | namespace      | mynsforappwithid-correct |
      | name           | myappwithid-correct      |

  Scenario: Create application on failed onboarding status
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                      |
      | {"name": "ns-for-failed-application", "group": ["mygroupwithid-nonprod"]} |
    Then The response status code should be 201
    When I have application created in DB with below
      | name               | repo_url             | repo_branch | repo_path | metadata.app_type | namespace                 | onboard_status |
      | failed-application | http://some-repo-url | main        | somepath  | app-testing       | ns-for-failed-application | FAILURE        |
    When I hit the v1/applications to create a cluster with below data
      | name               | repo_url             | repo_branch | repo_path | metadata.app_type | namespace                 |
      | failed-application | http://some-repo-url | main        | somepath  | app-testing       | ns-for-failed-application |
    Then The response status code should be 201

  Scenario: Prevent application on pending onboarding status
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                       |
      | {"name": "ns-for-pending-application", "group": ["mygroupwithid-nonprod"]} |
    Then The response status code should be 201
    When I have application created in DB with below
      | name                | repo_url             | repo_branch | repo_path | metadata.app_type | namespace                  | onboard_status |
      | pending-application | http://some-repo-url | main        | somepath  | app-testing       | ns-for-pending-application | PENDING        |
    When I hit the v1/applications to create a cluster with below data
      | name                | repo_url             | repo_branch | repo_path | metadata.app_type | namespace                 |
      | pending-application | http://some-repo-url | main        | somepath  | app-testing       | ns-for-failed-application |
    Then The response status code should be 409