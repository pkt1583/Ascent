Feature: Cluster Management

  Scenario: Create cluster Auth scenarios
    Given I am part of below groups
      | group              |
      | plat-dummy-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name        | short_name | metadata.label | environment |
      | dummy-valid | mc         | dummy-valid   | dummy       |
    Then The response status code should be 201
    And The manifests should have been created exactly as cluster/cluster-scenario1-1
    And The header should have X-TRACE-ID
    And The response should have below attribute
      | attribute_name | value         |
      | name           | dummy-valid |
      | metadata.label | dummy-valid |
      | onboard_status | COMPLETED     |
    When I hit the v1/clusters to create a cluster with below data
      | name            | short_name | metadata.label  | environment |
      | nonprod-invalid | mc         | nonprod-invalid | dummy-prod  |
    Then The response status code should be 403
    And The header should have X-TRACE-ID
    Given I am part of below groups
      | group              |
      | plat-dummy-admin     |
      | plat-dummyprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name            | short_name | metadata.label  | environment |
      | nonprod-invalid | mc         | nonprod-invalid | dummyprod   |
    Then The response status code should be 201
    And The manifests should have been created exactly as cluster/cluster-scenario1-2

  Scenario: Get all clusters scenario
    Given I am part of below groups
      | group              |
      | plat-allcusternonprod-admin |
      | plat-allcusterprod-admin    |
    When I hit the v1/clusters to create a cluster with below data
      | name                      | short_name | metadata.label            | environment      |
      | allcusternonprod-get-all1 | mc         | allcusternonprod-get-all1 | allcusterprod    |
      | allcusternonprod-get-all2 | mc         | allcusternonprod-get-all2 | allcusternonprod |
    When I hit the v1/clusters to get all cluster
    Then The response should have below attribute
      | attribute_name         | value            |
      | items.0.name           | allcusternonprod-get-all1 |
      | items.0.onboard_status | COMPLETED        |
      | items.1.name           | allcusternonprod-get-all2 |
      | items.1.onboard_status | COMPLETED        |
    And The header should have X-TRACE-ID
    Given I am part of below groups
      | group           |
      | plat-allcusterprod-admin |
    When I hit the v1/clusters to get all cluster
    Then The response should have below attribute
      | attribute_name         | value            |
      | items.0.name           | allcusternonprod-get-all1 |
      | items.0.onboard_status | COMPLETED        |
    Given I am part of below groups
      | group               |
      | plat-allcusternonprod-reader |
    When I hit the v1/clusters to get all cluster
    Then The response should have below attribute
      | attribute_name         | value            |
      | items.0.name           | allcusternonprod-get-all2 |
      | items.0.onboard_status | COMPLETED        |
    Given I am part of below groups
      | group             |
      | plat-dummyrole-reader |
    When I hit the v1/clusters to get all cluster
    Then There should be 0 items in response

  Scenario: Get single clusters scenario
    Given I am part of below groups
      | group              |
      | plat-nonprodsinglecluster-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                            | short_name | metadata.label                  | environment          |
      | nonprodsinglecluster-get-single | mc         | nonprodsinglecluster-get-single | nonprodsinglecluster |
    Then The response should have id
    When I hit the v1/clusters to get same cluster with id
    Then The response should have below attribute
      | attribute_name | value              |
      | name           | nonprodsinglecluster-get-single |
      | onboard_status | COMPLETED          |
    And The header should have X-TRACE-ID
    Given I am part of below groups
      | group           |
      | plat-prodsinglecluster-admin |
    When I hit the v1/clusters to get same cluster with id
    Then The response status code should be 404
    Given I am part of below groups
      | group               |
      | plat-nonprodsinglecluster-reader |
    When I hit the v1/clusters to get same cluster with id
    Then The response should have below attribute
      | attribute_name | value              |
      | name           | nonprodsinglecluster-get-single |
      | onboard_status | COMPLETED          |

  Scenario: Create cluster with metadata
    Given I am part of below groups
      | group       |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name      | short_name | metadata.purpose | metadata.ofType | environment |
      | mycluster | mc         | testing          | bdd             | nonprod     |
    Then The response status code should be 201
    And The response should have id
    And The response to create a cluster should be same as data from create_cluster_output.json
    When I hit the v1/clusters to create a cluster with below data
      | name      | short_name | metadata.purpose | metadata.ofType | environment |
      | mycluster | mc         | testing          | bdd             | nonprod     |
    Then The response status code should be 409
    And The response should have id
    And The response to create a cluster should be same as data from create_cluster_output.json

  Scenario: Create cluster without metadata
    Given I am part of below groups
      | group       |
      | plat-bdd-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                       | environment |
      | mycluster-without-metadata | bdd         |
    Then The response status code should be 500

  Scenario: Create cluster with invalid name
    Given I am part of below groups
      | group          |
      | plat-bdd-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name      | environment |
      | Mycluster | bdd         |
    Then The response status code should be 422

  Scenario: Create cluster with invalid environment
    Given I am part of below groups
      | group          |
      | plat-bdd-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name      | environment |
      | Mycluster | Bdd         |
    Then The response status code should be 422

  Scenario: Create cluster on failed onboarding status
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I have cluster created in DB with below
      | name             | short_name | metadata.purpose | metadata.ofType | environment | onboard_status |
      | mycluster-failed | mc         | testing          | bdd             | nonprod     | FAILURE        |
    When I hit the v1/clusters to create a cluster with below data
      | name             | short_name | metadata.purpose | metadata.ofType | environment |
      | mycluster-failed | mc         | testing          | bdd             | nonprod     |
    Then The response status code should be 201

  Scenario: Prevent cluster on pending onboarding status
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I have cluster created in DB with below
      | name             | short_name | metadata.purpose | metadata.ofType | environment | onboard_status |
      | mycluster-failed | mc         | testing          | bdd             | nonprod     | PENDING        |
    When I hit the v1/clusters to create a cluster with below data
      | name             | short_name | metadata.purpose | metadata.ofType | environment |
      | mycluster-failed | mc         | testing          | bdd             | nonprod     |
    Then The response status code should be 409


  Scenario: Create cluster Auth scenarios
    Given I am part of below groups
      | group          |
      | plat-val-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name         | short_name | metadata.name | environment |
      | dummy-valid4 | mc         | dummy-valid   | val         |
    Then The response status code should be 422