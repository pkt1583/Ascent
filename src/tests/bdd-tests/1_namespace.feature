Feature: Namespace Scenarios

  Scenario: create namespace with all fields
    Given I am part of below groups
      | group       |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                                         |
      | {"name": "myns", "description": "Created for testing", "cost_center": "123", "group": ["mygroup-nonprod", "anothergroup-nonprod"], "environment": "nonprod"} |
    Then The response status code should be 201
    And The response should have id
    And The header should have X-TRACE-ID

  Scenario: create namespace with invalid name
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                                         |
      | {"name": "Myns", "description": "Created for testing", "cost_center": "123", "group": ["mygroup-nonprod", "anothergroup-nonprod"], "environment": "nonprod"} |
    Then The response status code should be 422
    And The header should have X-TRACE-ID

  Scenario: create namespace already existing
    Given I am part of below groups
      | group           |
      | plat-prod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                   |
      | {"name": "myns", "group": ["mygroup-prod", "anothergroup-prod"]} |
    Then The response status code should be 409
    And The response should have id
    And The header should have X-TRACE-ID

  Scenario: create namespace with only name(mandatory fields)
    Given I am part of below groups
      | group       |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                 |
      | {"name": "lean-ns", "group": ["plat-nonprod-admin"]} |
    Then The response status code should be 201
    And The response should have id

  Scenario: create namespace by contributor
    Given I am part of below groups
      | group       |
      | project-nonprod-contributor  |
      | project-nonprod-reader       |
      | project1-nonprod-contributor |
      | project2-prod-contributor  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                   |
      | {"name": "project-ns"} |
    Then The response status code should be 403

  Scenario: create namespace by reader
    Given I am part of below groups
      | group       |
      | project-nonprod-reader |
      | project2-prod-reader  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                   |
      | {"name": "project-ns"} |
    Then The response status code should be 403


  Scenario: create namespace validate groups
    Given I am part of below groups
      | group       |
      | plat-prod-admin  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                  |
      | {"name": "ns-with-user-group", "group": ["bdd-test-group-nonprod"]}   |
      | {"name": "ns-with-user-group1", "group": ["bdd-test-group1-nonprod"]} |
      | {"name": "ns-with-user-group2", "group": ["bdd-test-group2-nonprod"]} |
    Then The response status code should be 201
    When I am part of below groups
      | group       |
      | bdd-test-group-nonprod-reader |
    And I hit the v1/namespaces to get all namespaces
    Then I should get namespaces with names as below
      | name        |
      | ns-with-user-group  |
      | ns-with-user-group2 |
    And The header should have X-TRACE-ID
    When I am part of below groups
      |  group       |
      | plat-nonprod-admin |
    And I hit the v1/namespaces to get all namespaces
    Then I should get namespaces with names as below
      | name        |
      | ns-with-user-group  |
      | ns-with-user-group1 |
      | ns-with-user-group2 |
    When I am part of below groups
      | group       |
      |   |
    And I hit the v1/namespaces to get all namespaces
    Then The response status code should be 403

  Scenario: create namespace and read by id
    Given I am part of below groups
      | group       |
      | project-nonprod-admin     |
      | project2-prod-contributor  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                        |
      | {"name": "project-read-by-id", "description": "some project", "group": ["project-nonprod"]} |
    Then I hit the v1/namespaces to get same namespace with id
    Then The response status code should be 200
    And The header should have X-TRACE-ID
    And The response should have below attribute
    | attribute_name | value |
    | name           |project-read-by-id|
    | description    |some project      |
    | group.0        | project-nonprod    |

  Scenario: create namespace and read by id by user who is contributor
    Given I am part of below groups
      | group       |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                 |
      | {"name": "project-read-by-contributor", "description": "some project", "group": ["project-nonprod"]} |
    Then I am part of below groups
    | group |
    | project-nonprod-contributor |
    Then I hit the v1/namespaces to get same namespace with id
    Then The response status code should be 200

  Scenario: create namespace and read by id by user who is reader
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                            |
      | {"name": "project-read-by-reader", "description": "some project", "group": ["project-nonprod"]} |
    Then I am part of below groups
      | group              |
      | project-nonprod-reader |
    Then I hit the v1/namespaces to get same namespace with id
    Then The response status code should be 200

  Scenario: create namespace and read by id by user who is not part of group
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                 |
      | {"name": "project-read-by-id-not-part", "description": "some project", "group": ["project-nonprod"]} |
    Then I am part of below groups
      | group               |
      | project1-nonprod-reader |
    Then I hit the v1/namespaces to get same namespace with id
    Then The response status code should be 401

  Scenario: create namespace and read by id by user who is admin of different env
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                   |
      | {"name": "project-read-by-another-admin", "description": "some project", "group": ["project-nonprod"]} |
    Then I am part of below groups
      | group                |
      | plat-prod-admin      |
      | plat-something-admin |
    Then I hit the v1/namespaces to get same namespace with id
    Then The response status code should be 401
