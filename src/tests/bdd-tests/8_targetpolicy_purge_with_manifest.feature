Feature: Purge features

  Scenario: Set up clusters and apps for test testing scenarios
    Given database is cleaned up
    And I am part of below groups
      | group              |
      | plat-nonprod-admin |
    #TODO: Add name as implicit metadata
    When I hit the v1/clusters to create a cluster with below data
      | name            | short_name | metadata.region | metadata.country | metadata.setupfor | environment |
      | p-cluster-south | mc         | south           | Australia        | pf-bdd            | nonprod     |
      | p-cluster-east  | mc         | east            | Australia        | pf-bdd            | nonprod     |
      | p-cluster-west  | mc         | west            | Australia        | pf-bdd            | nonprod     |
      | p-cluster-north | mc         | north           | Australia        | pf-bdd            | nonprod     |
    And I hit the v1/clusters to create a cluster with below data
      | name                | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-cluster-south-gpu | mc         | south           | Australia        | true         | pf-bdd            | nonprod     |
      | p-cluster-east-gpu  | mc         | east            | Australia        | true         | pf-bdd            | nonprod     |
      | p-cluster-west-gpu  | mc         | west            | Australia        | true         | pf-bdd            | nonprod     |
    Then The cluster with below name should be created having status COMPLETED
      | name                |
      | p-cluster-south     |
      | p-cluster-east      |
      | p-cluster-west      |
      | p-cluster-north     |
      | p-cluster-south-gpu |
      | p-cluster-east-gpu  |
      | p-cluster-west-gpu  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                              |
      | {"name": "p-test-ns", "description": "Created for testing p", "cost_center": "123", "group": ["p-group-nonprod"]} |
    Then The response status code should be 201
     #TODO: Add name as implicit metadata
    When I hit the v1/applications to create a application with below data
      | name   | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.need_gpu | metadata.setupfor | namespace |
      | p-app1 | http://some-repo-url | main        | somepath  | analytics     | p-app1        | true              | pf-bdd            | p-test-ns |
      | p-app2 | http://some-repo-url | main        | somepath  | bot           | p-app2        | true              | pf-bdd            | p-test-ns |
      | p-app3 | http://some-repo-url | main        | somepath  | analytics     | p-app3        | false             | pf-bdd            | p-test-ns |
      | p-app4 | http://some-repo-url | main        | somepath  | common        | p-app4        | false             | pf-bdd            | p-test-ns |
    Then The application with below name should be created having status COMPLETED
      | name   |
      | p-app1 |
      | p-app2 |
      | p-app3 |
      | p-app4 |
    When I hit the v1/applications to create a application with below data
      | name   | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace |
      | p-app5 | http://some-repo-url | main        | somepath  | analytics     | p-app5        | deli                | true              | pf-bdd            | p-test-ns |
      | p-app6 | http://some-repo-url | main        | somepath  | bot           | p-app6        | grocery             | false             | pf-bdd            | p-test-ns |
    Then The application with below name should be created having status COMPLETED
      | name   |
      | p-app5 |
      | p-app6 |

  Scenario: Create target policies and verify manifests
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name          | app_selector.need_gpu | cluster_selector.gpu | cluster_selector.setupfor |
      | p-gpu-apps-tp | true                  | true                 | pf-bdd                    |
    Then The response status code should be 201
    Then The manifests should have been created exactly as purge-scenario-1


  Scenario: Purge all gpu requiring apps from non gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name           | app_selector.name          | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | p-gpu-apps-tp1 | some-name-non-existing-app | false                | pf-bdd                    | PURGE     |
    Then The response status code should be 201


    When I hit the v1/clusters to create a cluster with below data
      | name        | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-cluster-1 | mc         | south           | Australia        | false        | pf-bdd            | nonprod     |
    Then The response status code should be 201


  Scenario: Install non gpu apps on non gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name          | app_selector.need_gpu | cluster_selector.gpu | cluster_selector.setupfor |
      | p-gpu-apps-tp | false                 | false                | pf-bdd                    |
    Then The response status code should be 201
    Then The manifests should have been created exactly as purge-scenario-non-gpu
