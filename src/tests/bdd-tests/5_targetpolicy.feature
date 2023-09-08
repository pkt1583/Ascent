Feature: Target Policy Management

  Scenario: create targetpolicy using app selector and cluster selector
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                          |
      | {"name": "targetpolicyns", "group": ["targetpolicy-nonprod"]} |
    Then The response status code should be 201

    Given I am part of below groups
      | group                            |
      | targetpolicy-nonprod-contributor |
    When I hit the v1/applications to create a application with below data
      | name             | repo_url             | repo_branch | repo_path | metadata.app_type  | namespace      |
      | targetpolicy-app | http://some-repo-url | main        | somepath  | targetpolicy-label | targetpolicyns |
    Then The response status code should be 201
    Given I am part of below groups
      | group                      |
      | targetpolicy-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                 | short_name | metadata.purpose     | metadata.ofType  | environment |
      | targetpolicy-cluster | tc         | targetpolicy-testing | targetpolicy-bdd | nonprod     |
    Then The response status code should be 201
    Given I am part of below groups
      | group                            |
      | targetpolicy-nonprod-contributor |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name           | app_selector.app_type | cluster_selector.purpose |
      | mytargetpolicy | targetpolicy-label    | targetpolicy-testing     |
    Then The response status code should be 201
    And The response should have id
    And The response should have below attribute
      | attribute_name           | value                |
      | name                     | mytargetpolicy       |
      | app_selector.app_type    | targetpolicy-label   |
      | cluster_selector.purpose | targetpolicy-testing |
      | onboard_status           | COMPLETED            |
    And The deployment should have been created with this criteria target_policy_id having id as received in response
    And The deployment should have details as per below table
      | operation | comma_separated_app_name | cluster_name         |
      | add       | targetpolicy-app         | targetpolicy-cluster |
    And The manifests should have been created exactly as manifests-scenario_1
    And The below applications are present on specified clusters
      | cluster_name         | comma_seperated app_name |
      | targetpolicy-cluster | targetpolicy-app         |

  Scenario: Authorization checks for create targetpolicy using app selector and cluster selector for user
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                              |
      | {"name": "targepolicycorrectrolens", "group": ["targepolicycorrectrole-nonprod"]} |
    Then The response status code should be 201
    Given I am part of below groups
      | group                                  |
      | targepolicycorrectrole-nonprod-contributor |
    When I hit the v1/applications to create a application with below data
      | name                       | repo_url             | repo_branch | repo_path | metadata.app_type            | namespace                |
      | targepolicycorrectrole-app | http://some-repo-url | main        | somepath  | targepolicycorrectrole-label | targepolicycorrectrolens |
    Then The response status code should be 201
    Given I am part of below groups
      | group                                |
      | targepolicycorrectrole-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                           | short_name | metadata.purpose               | metadata.ofType            | environment |
      | targepolicycorrectrole-cluster | tc         | targepolicycorrectrole-testing | targepolicycorrectrole-bdd | nonprod     |
    Then The response status code should be 201

    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name                   | app_selector.app_type        | cluster_selector.purpose       |
      | targepolicycorrectrole | targepolicycorrectrole-label | targepolicycorrectrole-testing |
    Then The response status code should be 201
    And The response should have id
    And The response should have below attribute
      | attribute_name           | value                          |
      | name                     | targepolicycorrectrole         |
      | app_selector.app_type    | targepolicycorrectrole-label   |
      | cluster_selector.purpose | targepolicycorrectrole-testing |
      | onboard_status           | COMPLETED                      |

    When I am part of below groups
      | group                                      |
      | targepolicycorrectrole-anther-contributor |
    And I hit the v1/targetpolicies to create a targetpolicy with below data
      | name                    | app_selector.app_type        | cluster_selector.purpose       |
      | targepolicycorrectrole1 | targepolicycorrectrole-label | targepolicycorrectrole-testing |
    Then The response status code should be 403

  Scenario: Targeting multiple environments with user having correct roles
    Given I am part of below groups
      | group          |
      | plat-nonprod-admin |
    #Should nonprod admin be allowed to bind prod role to namespaces?? no
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                      |
      | {"name": "targetpolicyenv", "group": ["targetpolicyenv-nonprod", "targetpolicyenv-prod"]} |
    Then The response status code should be 201
    Given I am part of below groups
      | group                           |
      | targetpolicyenv-nonprod-contributor |
    When I hit the v1/applications to create a application with below data
      | name                | repo_url             | repo_branch | repo_path | metadata.app_type     | namespace       |
      | targetpolicyenv-app | http://some-repo-url | main        | somepath  | targetpolicyenv-label | targetpolicyenv |
    Then The response status code should be 201
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
      | plat-prod-admin    |
    When I hit the v1/clusters to create a cluster with below data
      | name                         | short_name | metadata.purpose        | environment |
      | targetpolicyenv-cluster-nonprod | tc         | targetpolicyenv-testing | nonprod     |
      | targetpolicyenv-cluster-prod | tc         | targetpolicyenv-testing | prod        |
    Then The response status code should be 201
    Given I am part of below groups
      | group                            |
      | targetpolicyenv-nonprod-contributor |
      | targetpolicyenv-prod-contributor |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name            | app_selector.app_type | cluster_selector.purpose |
      | targetpolicyenv | targetpolicyenv-label | targetpolicyenv-testing  |
    Then The response status code should be 201
    And The response should have id
    And The response should have below attribute
      | attribute_name           | value                   |
      | name                     | targetpolicyenv         |
      | app_selector.app_type    | targetpolicyenv-label   |
      | cluster_selector.purpose | targetpolicyenv-testing |
      | onboard_status           | COMPLETED               |

  Scenario: Targeting multiple environments with user not having all roles for environment
    Given I am part of below groups
      | group                           |
      | targetpolicyenv-nonprod-contributor |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name                | app_selector.app_type | cluster_selector.purpose |
      | targetpolicyenv-nonprod | targetpolicyenv-label | targetpolicyenv-testing  |
    Then The response status code should be 403

  Scenario: Targeting multiple environments with user not belonging to correct group
    Given I am part of below groups
      | group                    |
      | tpgroup-anything-contributor |
      | tpgroup-prod-contributor |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name               | app_selector.app_type | cluster_selector.purpose |
      | targetpolicyenv-tp | targetpolicyenv-label | targetpolicyenv-testing  |
    Then The response status code should be 403

  Scenario: Targeting to application with Failed onboarding status after target policy creation
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                            |
      | {"name": "failed-app-ns", "group": ["targetpolicyenv-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.label     | environment |
      | failed-app-cluster | mc         | failed-app-cluster | nonprod     |
    When I have application created in DB with below
      | name       | repo_url             | repo_branch | repo_path | metadata.label | namespace     | onboard_status |
      | failed-app | http://some-repo-url | main        | somepath  | failed-app    | failed-app-ns | FAILURE        |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.name  | cluster_selector.name |
      | failed-app-tp | failed-app        | failed-app-cluster    |
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name        | value              |
      | name                  | failed-app-tp      |
      | app_selector.name     | failed-app         |
      | cluster_selector.name | failed-app-cluster |
      | onboard_status        | COMPLETED          |
    When I hit the v1/applications to create a application with below data
      | name       | repo_url             | repo_branch | repo_path | metadata.label | namespace     |
      | failed-app | http://some-repo-url | main        | somepath  | failed-app    | failed-app-ns |
    Then The manifests should have been created exactly as target_failed_apps

  Scenario: Targeting to cluster with Failed onboarding
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                |
      | {"name": "failed-cluster-ns", "group": ["targetpolicyenv-nonprod"]} |
    Then The response status code should be 201
    When I have cluster created in DB with below
      | name           | short_name | metadata.label | metadata.ofType | environment | onboard_status |
      | failed-cluster | mc         | failed-cluster | failed-cluster  | nonprod     | FAILURE        |
    When I hit the v1/applications to create a application with below data
      | name               | repo_url             | repo_branch | repo_path | metadata.label     | namespace         |
      | failed-cluster-app | http://some-repo-url | main        | somepath  | failed-cluster-app | failed-cluster-ns |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.name  | cluster_selector.name |
      | failed-cluster-tp | failed-cluster-app | failed-cluster        |
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name        | value              |
      | name                  | failed-cluster-tp  |
      | app_selector.name     | failed-cluster-app |
      | cluster_selector.name | failed-cluster     |
      | onboard_status        | COMPLETED          |
    When I hit the v1/clusters to create a cluster with below data
      | name           | short_name | metadata.label | metadata.ofType | environment |
      | failed-cluster | mc         | failed-cluster | failed-cluster  | nonprod     |
    Then The manifests should have been created exactly as target_failed_cluster

  Scenario: Targeting to application not present during target creation
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                            |
      | {"name": "absent-app-ns", "group": ["targetpolicyenv-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.label     | environment |
      | absent-app-cluster | mc         | absent-app-cluster | nonprod     |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name          | app_selector.name | cluster_selector.name |
      | absent-app-tp | absent-app        | absent-app-cluster    |
    Then The response status code should be 201
    And The response should have below attribute
      | attribute_name        | value              |
      | name                  | absent-app-tp      |
      | app_selector.name     | absent-app         |
      | cluster_selector.name | absent-app-cluster |
      | onboard_status        | COMPLETED          |
    When I hit the v1/applications to create a application with below data
      | name       | repo_url             | repo_branch | repo_path | metadata.label | namespace     |
      | absent-app | http://some-repo-url | main        | somepath  | absent-app    | absent-app-ns |
    Then The manifests should have been created exactly as absent-app

  Scenario: Targeting to application with invalid name
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                |
      | {"name": "invalid-tp-app-ns", "group": ["targetpolicyenv-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name           | repo_url             | repo_branch | repo_path | metadata.app_type | namespace         |
      | invalid-tp-app | http://some-repo-url | main        | somepath  | invalid-tp-label  | invalid-tp-app-ns |
    Then The response status code should be 201
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.label     | environment |
      | invalid-tp-nonprod | tc         | invalid-tp-cluster | nonprod     |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name           | app_selector.name | cluster_selector.name |
      | invalid1-tp-tp | invalid-tp-app    | invalid-tp-cluster    |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name          | app_selector.name | cluster_selector.name |
      | Invalid-tp-tp | invalid-tp-app    | invalid-tp-cluster    |
    Then The response status code should be 422
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name          | app_selector.name | cluster_selector.name |
      | invalid_tp-tp | invalid-tp-app    | invalid-tp-cluster    |
    Then The response status code should be 422
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name          | app_selector.name | cluster_selector.name |
      | @nvalid-tp-tp | invalid-tp-app    | invalid-tp-cluster    |
    Then The response status code should be 422

  Scenario: Update application scenarios
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                   |
      | {"name": "update-app-ns", "group": ["update-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.label     | metadata.type | environment |
      | update-app-cluster | mc         | update-app-cluster | nonprod       | nonprod     |
    When I hit the v1/applications to create a application with below data
      | name        | repo_url             | repo_branch | repo_path | metadata.label | metadata.gpu | namespace     |
      | update-app1 | http://some-repo-url | main        | somepath  | update-app1   | true         | update-app-ns |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name        | repo_url             | repo_branch | repo_path | metadata.label | metadata.gpu | namespace     |
      | update-app2 | http://some-repo-url | main        | somepath  | update-app2   | true         | update-app-ns |
    Then The response status code should be 201
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name           | app_selector.name | cluster_selector.name |
      | update-app-tp1 | update-app1       | update-app-cluster    |
    Then The response status code should be 201
    And The response should have id
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name           | app_selector.name | cluster_selector.name |
      | update-app-tp2 | update-app2       | another-cluster       |
    Then The response status code should be 201
    And There should be no manifest created
    When I hit the v1/clusters to create a cluster with below data
      | name            | short_name | metadata.label  | metadata.type | environment |
      | another-cluster | mc         | another-cluster | nonprod       | nonprod     |
    Then The response status code should be 201
    And The manifests should have been created exactly as update-application-scenario-1
    Given I have manifest checked out from update-application-scenario-1 at manifest-scenario-1
    When I hit the v1/clusters to create a cluster with below data
      | name | short_name | metadata.label  | metadata.type | environment |
      | cl1  | mc         | another-cluster | nonprod       | nonprod     |
    Then The response status code should be 201
    And The manifests should have been created exactly as update-application-scenario-2
    Given I have manifest checked out from update-application-scenario-1 at manifest-scenario-1
    When I hit the v1/applications to create a application with below data
      | name        | repo_url             | repo_branch | repo_path | metadata.label | namespace     |
      | update-app3 | http://some-repo-url | main        | somepath  | update-app2   | update-app-ns |
    Then The response status code should be 201
    And The manifests should have been created exactly as update-application-scenario-3