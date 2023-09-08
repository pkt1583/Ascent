Feature: Purge features for apps onboarding scenario
"""The scenario in this feature file depends on execution of Set up clusters and apps for test testing scenarios"""

  Scenario: Set up clusters and apps for test testing scenarios
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    And database is cleaned up
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.region | metadata.country | metadata.setupfor | environment | metadata.gpu |
      | pa-dbcluster-south | mc         | south           | Australia        | pa-dbbdd          | nonprod     | false        |
      | pa-dbcluster-east  | mc         | east            | Australia        | pa-dbbdd          | nonprod     | false        |
      | pa-dbcluster-west  | mc         | west            | Australia        | pa-dbbdd          | nonprod     | false        |
      | pa-dbcluster-north | mc         | north           | Australia        | pa-dbbdd          | nonprod     | false        |
    And I hit the v1/clusters to create a cluster with below data
      | name                   | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | pa-dbcluster-south-gpu | mc         | south           | Australia        | true         | pa-dbbdd          | nonprod     |
      | pa-dbcluster-east-gpu  | mc         | east            | Australia        | true         | pa-dbbdd          | nonprod     |
      | pa-dbcluster-west-gpu  | mc         | west            | Australia        | true         | pa-dbbdd          | nonprod     |
    Then The cluster with below name should be created having status COMPLETED
      | name                   |
      | pa-dbcluster-south     |
      | pa-dbcluster-east      |
      | pa-dbcluster-west      |
      | pa-dbcluster-north     |
      | pa-dbcluster-south-gpu |
      | pa-dbcluster-east-gpu  |
      | pa-dbcluster-west-gpu  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                     |
      | {"name": "pa-dbtest-ns", "description": "Created for testing p", "cost_center": "123", "group": ["pa-dbgroupa-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.need_gpu | metadata.setupfor | namespace    |
      | pa-dbapp1 | http://some-repo-url | main        | somepath  | analytics     | pa-dbapp1      | true              | pa-dbbdd          | pa-dbtest-ns |
      | pa-dbapp2 | http://some-repo-url | main        | somepath  | bot           | pa-dbapp2      | true              | pa-dbbdd          | pa-dbtest-ns |
      | pa-dbapp3 | http://some-repo-url | main        | somepath  | analytics     | pa-dbapp3      | false             | pa-dbbdd          | pa-dbtest-ns |
      | pa-dbapp4 | http://some-repo-url | main        | somepath  | common        | pa-dbapp4      | false             | pa-dbbdd          | pa-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | pa-dbapp1 |
      | pa-dbapp2 |
      | pa-dbapp3 |
      | pa-dbapp4 |
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace    |
      | pa-dbapp5 | http://some-repo-url | main        | somepath  | analytics     | pa-dbapp5      | deli                | true              | pa-dbbdd          | pa-dbtest-ns |
      | pa-dbapp6 | http://some-repo-url | main        | somepath  | bot           | pa-dbapp6      | grocery             | false             | pa-dbbdd          | pa-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | pa-dbapp5 |
      | pa-dbapp6 |

  Scenario: Create target policies and verify
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.need_gpu | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | pa-dbgpu-apps-tp | true                  | pa-dbbdd              | true                 | pa-dbbdd                  |
    Then The response status code should be 201
    Then The below applications are present on specified clusters
      | cluster_name                                                       | comma_seperated app_name      |
      | pa-dbcluster-south-gpu,pa-dbcluster-east-gpu,pa-dbcluster-west-gpu | pa-dbapp1,pa-dbapp2,pa-dbapp5 |


  Scenario: Install non gpu apps on non gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.need_gpu | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | pa-dbgpu-apps-tp2 | false                 | pa-dbbdd              | false                | pa-dbbdd                  |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                              | comma_seperated app_name      |
      | pa-dbcluster-south-gpu,pa-dbcluster-east-gpu,pa-dbcluster-west-gpu        | pa-dbapp1,pa-dbapp2,pa-dbapp5 |
      | pa-dbcluster-south,pa-dbcluster-east,pa-dbcluster-west,pa-dbcluster-north | pa-dbapp3,pa-dbapp4,pa-dbapp6 |


  Scenario: Remove dbapp1 from all gpu cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.name | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | pa-dbgpu-apps-tp3 | pa-dbapp1         | true                 | pa-dbbdd                  | PURGE     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                              | comma_seperated app_name      |
      | pa-dbcluster-south-gpu,pa-dbcluster-east-gpu,pa-dbcluster-west-gpu        | pa-dbapp2,pa-dbapp5           |
      | pa-dbcluster-south,pa-dbcluster-east,pa-dbcluster-west,pa-dbcluster-north | pa-dbapp3,pa-dbapp4,pa-dbapp6 |

  Scenario: Remove dbapp8 from all non gpu cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.name | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | pa-dbgpu-apps-tp4 | pa-dbapp8         | false                | pa-dbbdd                  | PURGE     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                              | comma_seperated app_name      |
      | pa-dbcluster-south-gpu,pa-dbcluster-east-gpu,pa-dbcluster-west-gpu        | pa-dbapp2,pa-dbapp5           |
      | pa-dbcluster-south,pa-dbcluster-east,pa-dbcluster-west,pa-dbcluster-north | pa-dbapp3,pa-dbapp4,pa-dbapp6 |

  Scenario: Create dbapp8 application
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace    |
      | pa-dbapp8 | http://some-repo-url | main        | somepath  | analytics     | pa-dbapp8      | deli                | false             | pa-dbbdd          | pa-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | pa-dbapp8 |
    And The below applications are present on specified clusters
      | cluster_name                                                              | comma_seperated app_name      |
      | pa-dbcluster-south-gpu,pa-dbcluster-east-gpu,pa-dbcluster-west-gpu        | pa-dbapp2,pa-dbapp5           |
      | pa-dbcluster-south,pa-dbcluster-east,pa-dbcluster-west,pa-dbcluster-north | pa-dbapp3,pa-dbapp4,pa-dbapp6 |

