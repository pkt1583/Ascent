Feature: Purge features
"""The scenario in this feature file depends on execution of Set up clusters and apps for test testing scenarios"""

  Scenario: Set up clusters and apps for test testing scenarios
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    And database is cleaned up
    When I hit the v1/clusters to create a cluster with below data
      | name              | short_name | metadata.region | metadata.country | metadata.setupfor | environment |
      | p-dbcluster-south | mc         | south           | Australia        | p-dbbdd           | nonprod     |
      | p-dbcluster-east  | mc         | east            | Australia        | p-dbbdd           | nonprod     |
      | p-dbcluster-west  | mc         | west            | Australia        | p-dbbdd           | nonprod     |
      | p-dbcluster-north | mc         | north           | Australia        | p-dbbdd           | nonprod     |
    And I hit the v1/clusters to create a cluster with below data
      | name                  | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-dbcluster-south-gpu | mc         | south           | Australia        | true         | p-dbbdd           | nonprod     |
      | p-dbcluster-east-gpu  | mc         | east            | Australia        | true         | p-dbbdd           | nonprod     |
      | p-dbcluster-west-gpu  | mc         | west            | Australia        | true         | p-dbbdd           | nonprod     |
    Then The cluster with below name should be created having status COMPLETED
      | name                  |
      | p-dbcluster-south     |
      | p-dbcluster-east      |
      | p-dbcluster-west      |
      | p-dbcluster-north     |
      | p-dbcluster-south-gpu |
      | p-dbcluster-east-gpu  |
      | p-dbcluster-west-gpu  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                  |
      | {"name": "p-dbtest-ns", "description": "Created for testing p", "cost_center": "123", "group": ["p-dbgroup-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name     | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.need_gpu | metadata.setupfor | namespace   |
      | p-dbapp1 | http://some-repo-url | main        | somepath  | analytics     | p-dbapp1      | true              | p-dbbdd           | p-dbtest-ns |
      | p-dbapp2 | http://some-repo-url | main        | somepath  | bot           | p-dbapp2      | true              | p-dbbdd           | p-dbtest-ns |
      | p-dbapp3 | http://some-repo-url | main        | somepath  | analytics     | p-dbapp3      | false             | p-dbbdd           | p-dbtest-ns |
      | p-dbapp4 | http://some-repo-url | main        | somepath  | common        | p-dbapp4      | false             | p-dbbdd           | p-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name     |
      | p-dbapp1 |
      | p-dbapp2 |
      | p-dbapp3 |
      | p-dbapp4 |
    When I hit the v1/applications to create a application with below data
      | name     | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace   |
      | p-dbapp5 | http://some-repo-url | main        | somepath  | analytics     | p-dbapp5      | deli                | true              | p-dbbdd           | p-dbtest-ns |
      | p-dbapp6 | http://some-repo-url | main        | somepath  | bot           | p-dbapp6      | grocery             | false             | p-dbbdd           | p-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name     |
      | p-dbapp5 |
      | p-dbapp6 |

  Scenario: Create target policies and verify manifests
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name            | app_selector.need_gpu | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | p-dbgpu-apps-tp | true                  | p-dbbdd               | true                 | p-dbbdd                   |
    Then The response status code should be 201
    Then The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name   |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu | p-dbapp1,p-dbapp2,p-dbapp5 |


  Scenario: Purge non existing apps from non gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.name  | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | p-dbgpu-apps-tp1 | p-non-existing-app | false                | p-dbbdd                   | PURGE     |
    Then The response status code should be 201
    Then The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name   |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu | p-dbapp1,p-dbapp2,p-dbapp5 |

    When I hit the v1/clusters to create a cluster with below data
      | name          | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-dbcluster-1 | mc         | south           | Australia        | false        | p-dbbdd           | nonprod     |
    Then The response status code should be 201
    And The manifests should have been created exactly as cluster/target_policy_p-cluster1-1

  Scenario: Install non gpu apps on non gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.need_gpu | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | p-dbgpu-apps-tp2 | false                 | p-dbbdd               | false                | p-dbbdd                   |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name   |
      | p-dbcluster-1                                                   | p-dbapp3,p-dbapp4,p-dbapp6 |
      #Verify the previous state as tests will run one after another
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu | p-dbapp1,p-dbapp2,p-dbapp5 |


  Scenario: Remove dbapp1 from all gpu cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.name | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | p-dbgpu-apps-tp3 | p-dbapp1          | true                 | p-dbbdd                   | PURGE     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name   |
      | p-dbcluster-1                                                   | p-dbapp3,p-dbapp4,p-dbapp6 |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu | p-dbapp2,p-dbapp5          |

  Scenario: Add additional GPU cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                  | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-dbcluster-north-gpu | mc         | north           | Australia        | true         | p-dbbdd           | nonprod     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name   |
      | p-dbcluster-1                                                   | p-dbapp3,p-dbapp4,p-dbapp6 |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu | p-dbapp2,p-dbapp5          |
      | p-dbcluster-north-gpu                                           | p-dbapp2,p-dbapp5          |

  Scenario: Add new Application with matching target policy
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/applications to create a application with below data
      | name     | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace   |
      | p-dbapp7 | http://some-repo-url | main        | somepath  | analytics     | p-dbapp7      | deli                | true              | p-dbbdd           | p-dbtest-ns |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name   |
      | p-dbcluster-1                                                   | p-dbapp3,p-dbapp4,p-dbapp6 |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu | p-dbapp2,p-dbapp5,p-dbapp7 |
      | p-dbcluster-north-gpu                                           | p-dbapp2,p-dbapp5,p-dbapp7 |


  #Creating target policy will reset stuff
  Scenario: Add dbapp1 back to gpu enabled clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    #I can also do need_gpu true here but i already have that so for now only selecting app with name
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.name | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | p-dbgpu-apps-tp4 | p-dbapp1          | p-dbbdd               | true                 | p-dbbdd                   |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                                          | comma_seperated app_name            |
      | p-dbcluster-1                                                                         | p-dbapp3,p-dbapp4,p-dbapp6          |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu,p-dbcluster-north-gpu | p-dbapp1,p-dbapp2,p-dbapp5,p-dbapp7 |

  Scenario: Onboard another GPU cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                   | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-dbcluster-north-gpu1 | mc         | north           | Australia        | true         | p-dbbdd           | nonprod     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                                                                 | comma_seperated app_name            |
      | p-dbcluster-1                                                                                                | p-dbapp3,p-dbapp4,p-dbapp6          |
      | p-dbcluster-south-gpu,p-dbcluster-east-gpu,p-dbcluster-west-gpu,p-dbcluster-north-gpu,p-dbcluster-north-gpu1 | p-dbapp1,p-dbapp2,p-dbapp5,p-dbapp7 |

  Scenario: Remove p-dbapp2 from south clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    #I can also do need_gpu true here but i already have that so for now only selecting app with name
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.name | cluster_selector.region | cluster_selector.setupfor | operation |
      | p-dbgpu-apps-tp4 | p-dbapp2          | south                   | p-dbbdd                   | PURGE     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                    | comma_seperated app_name            |
      | p-dbcluster-1                                                   | p-dbapp3,p-dbapp4,p-dbapp6          |
      | p-dbcluster-east-gpu,p-dbcluster-west-gpu,p-dbcluster-north-gpu | p-dbapp1,p-dbapp2,p-dbapp5,p-dbapp7 |
      | p-dbcluster-south-gpu                                           | p-dbapp1,p-dbapp5,p-dbapp7          |

  Scenario: Remove p-dbapp2,p-dbapp1 from east clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    #I can also do need_gpu true here but i already have that so for now only selecting app with name
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | data                                                                                                                                                             |
      | {"name": "p-dbgpu-apps-tp5", "app_selector": {"name": "p-dbapp2,p-dbapp1"}, "cluster_selector": {"region": "east", "setupfor": "p-dbbdd"}, "operation": "PURGE"} |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                               | comma_seperated app_name            |
      | p-dbcluster-1                              | p-dbapp3,p-dbapp4,p-dbapp6          |
      | p-dbcluster-west-gpu,p-dbcluster-north-gpu | p-dbapp1,p-dbapp2,p-dbapp5,p-dbapp7 |
      | p-dbcluster-south-gpu                      | p-dbapp1,p-dbapp5,p-dbapp7          |
      | p-dbcluster-east-gpu                       | p-dbapp5,p-dbapp7                   |

  Scenario: Onboard another cluster in east and south region with gpu and validate dbapp1 and dbapp2 is not created in east
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                   | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p-dbcluster-south-gpu1 | mc         | south           | Australia        | true         | p-dbbdd           | nonprod     |
      | p-dbcluster-east-gpu1  | mc         | east            | Australia        | true         | p-dbbdd           | nonprod     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                 | comma_seperated app_name            |
      | p-dbcluster-1                                | p-dbapp3,p-dbapp4,p-dbapp6          |
      | p-dbcluster-west-gpu,p-dbcluster-north-gpu   | p-dbapp1,p-dbapp2,p-dbapp5,p-dbapp7 |
      | p-dbcluster-south-gpu,p-dbcluster-south-gpu1 | p-dbapp1,p-dbapp5,p-dbapp7          |
      | p-dbcluster-east-gpu,p-dbcluster-east-gpu1   | p-dbapp5,p-dbapp7                   |