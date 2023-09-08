Feature: Get affected Target policy
"""The scenario in this feature file depends on execution of Set up clusters and apps for test testing scenarios"""

  Scenario: Set up clusters and apps for test testing scenarios
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    And database is cleaned up
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.region | metadata.country | metadata.setupfor | environment | metadata.gpu |
      | dbcluster-south | mc         | south           | Australia        | dbbdd          | nonprod     | false        |
      | dbcluster-east  | mc         | east            | Australia        | dbbdd          | nonprod     | false        |
      | dbcluster-west  | mc         | west            | Australia        | dbbdd          | nonprod     | false        |
      | dbcluster-north | mc         | north           | Australia        | dbbdd          | nonprod     | false        |
    And I hit the v1/clusters to create a cluster with below data
      | name                   | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | dbcluster-south-gpu | mc         | south           | Australia        | true         | dbbdd          | nonprod     |
      | dbcluster-east-gpu  | mc         | east            | Australia        | true         | dbbdd          | nonprod     |
      | dbcluster-west-gpu  | mc         | west            | Australia        | true         | dbbdd          | nonprod     |
    Then The cluster with below name should be created having status COMPLETED
      | name                   |
      | dbcluster-south     |
      | dbcluster-east      |
      | dbcluster-west      |
      | dbcluster-north     |
      | dbcluster-south-gpu |
      | dbcluster-east-gpu  |
      | dbcluster-west-gpu  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                     |
      | {"name": "dbtest-ns", "description": "Created for testing p", "cost_center": "123", "group": ["dbgroup-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.need_gpu | metadata.setupfor | namespace    |
      | dbapp1 | http://some-repo-url | main        | somepath  | analytics     | dbapp1      | true              | dbbdd          | dbtest-ns |
      | dbapp2 | http://some-repo-url | main        | somepath  | bot           | dbapp2      | true              | dbbdd          | dbtest-ns |
      | dbapp3 | http://some-repo-url | main        | somepath  | analytics     | dbapp3      | false             | dbbdd          | dbtest-ns |
      | dbapp4 | http://some-repo-url | main        | somepath  | common        | dbapp4      | false             | dbbdd          | dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | dbapp1 |
      | dbapp2 |
      | dbapp3 |
      | dbapp4 |
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace    |
      | dbapp5 | http://some-repo-url | main        | somepath  | analytics     | dbapp5      | deli                | true              | dbbdd          | dbtest-ns |
      | dbapp6 | http://some-repo-url | main        | somepath  | bot           | dbapp6      | grocery             | false             | dbbdd          | dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | dbapp5 |
      | dbapp6 |

  Scenario: Create target policies and verify
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.need_gpu | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | dbgpu-apps-tp | true                  | dbbdd              | true                 | dbbdd                  |
    Then The response status code should be 201
    Then The below applications are present on specified clusters
      | cluster_name                                                       | comma_seperated app_name      |
      | dbcluster-south-gpu,dbcluster-east-gpu,dbcluster-west-gpu | dbapp1,dbapp2,dbapp5 |


  Scenario: Get target policy applied for dbapp1 deployment on dbcluster-east-gpu
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies/dbapp1?cluster_name=dbcluster-south-gpu to get all targetpolicies
    Then The response status code should be 200
    And The response should have below attribute
        | attribute_name | value |
        | items.0.name           | dbgpu-apps-tp   |

  Scenario: Remove dbapp1 from all gpu cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.name | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | dbgpu-apps-tp3 | dbapp1         | true                 | dbbdd                  | PURGE     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                              | comma_seperated app_name      |
      | dbcluster-south-gpu,dbcluster-east-gpu,dbcluster-west-gpu | dbapp2,dbapp5 |

  Scenario: Get target policy applied for dbapp1 deployment on dbcluster-east-gpu
  Given I am part of below groups
    | group              |
    | plat-nonprod-admin |
  When I hit the v1/targetpolicies/dbapp1?cluster_name=dbcluster-south-gpu to get all targetpolicies
  Then The response status code should be 200
  And The response should have below attribute
      | attribute_name | value |
      | items.0.name           | dbgpu-apps-tp3   |
      | items.0.operation      |  PURGE               |
