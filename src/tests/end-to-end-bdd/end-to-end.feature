Feature: End to End Scenarios

  Scenario: Clusters set up
    Given I am running in end to end mode
    When I hit the v1/clusters to create a cluster with below data
      | name                    | short_name              | metadata.country | metadata.region | metadata.label           | environment |
      | east-nsw-sydney-1001-01-e2e | east-nsw-sydney-1001-01-e2e | Australia        | east            | east-nsw-sydney-1001-01-e2e | nonprod     |
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name   | value                   |
      | name             | east-nsw-sydney-1001-01-e2e |
      | metadata.country | Australia               |
      | metadata.region  | east                    |
      | onboard_status   | COMPLETED               |
    When I hit the v1/clusters to create a cluster with below data
      | name                       | short_name                 | metadata.country | metadata.region | metadata.label              | environment |
      | east-nsw-newcastle-2940-01-e2e | east-nsw-newcastle-2940-01-e2e | Australia        | east            | east-nsw-newcastle-2940-01-e2e | nonprod     |
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name   | value                      |
      | name             | east-nsw-newcastle-2940-01-e2e |
      | metadata.country | Australia                  |
      | metadata.region  | east                       |
      | onboard_status   | COMPLETED                  |
    When I hit the v1/clusters to create a cluster with below data
      | name                         | short_name                   | metadata.country | metadata.region | metadata.label                | environment |
      | south-vic-melbourne-32901-01-e2e | south-vic-melbourne-32901-01-e2e | Australia        | south           | south-vic-melbourne-32901-01-e2e | nonprod     |
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name   | value                        |
      | name             | south-vic-melbourne-32901-01-e2e |
      | metadata.country | Australia                    |
      | metadata.region  | south                        |
      | onboard_status   | COMPLETED                    |

  Scenario: Namespace setup
    Given I am running in end to end mode
    When I hit the v1/namespaces to create a namespace with below data
      | name       | group        |
      | end-to-end | project-nonprod, |
    #comma in group is must to indicate that json is of list type
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name | value       |
      | name           | end-to-end  |
      | group.0        | project-nonprod |

  Scenario: Applications set up
    Given I am running in end to end mode
    When I hit the v1/applications to create a application with below data
      | name  | repo_url             | repo_branch | repo_path | metadata.label | namespace  |
      | app1 | https://dev.azure.com/contoso/_git/plat_multistore_app_demo | master      | manifest/app1 | app1          | end-to-end |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name | repo_url                                                                                     | repo_branch | repo_path     | metadata.label | metadata.common  | namespace  |
      | app2 | https://dev.azure.com/contoso/_git/plat_multistore_app_demo | master      | manifest/app2 | app2   | true    | end-to-end |
    Then The response status code should be 201

  Scenario: Targeting set up
    Given I am running in end to end mode
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name    | app_selector.name | cluster_selector.name        |
      | target1 | app1              | south-vic-melbourne-32901-01-e2e |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name    | app_selector.name | cluster_selector.region        |
      | target2 | app1              | east |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name    | app_selector.common | cluster_selector.region        |
      | target3 | true              | east |
    Then The response status code should be 201