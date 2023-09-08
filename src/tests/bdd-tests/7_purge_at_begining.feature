Feature: Purge features
"""The scenario in this feature file depends on execution of Set up clusters and apps for test testing scenarios"""

  Scenario: Set up clusters and apps for test testing scenarios
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name               | short_name | metadata.region | metadata.country | metadata.setupfor | environment |
      | p7-dbcluster-south | mc         | south           | Australia        | p7-dbbdd          | nonprod     |
      | p7-dbcluster-east  | mc         | east            | Australia        | p7-dbbdd          | nonprod     |
      | p7-dbcluster-west  | mc         | west            | Australia        | p7-dbbdd          | nonprod     |
      | p7-dbcluster-north | mc         | north           | Australia        | p7-dbbdd          | nonprod     |
    And I hit the v1/clusters to create a cluster with below data
      | name                   | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p7-dbcluster-south-gpu | mc         | south           | Australia        | true         | p7-dbbdd          | nonprod     |
      | p7-dbcluster-east-gpu  | mc         | east            | Australia        | true         | p7-dbbdd          | nonprod     |
      | p7-dbcluster-west-gpu  | mc         | west            | Australia        | true         | p7-dbbdd          | nonprod     |
    Then The cluster with below name should be created having status COMPLETED
      | name                   |
      | p7-dbcluster-south     |
      | p7-dbcluster-east      |
      | p7-dbcluster-west      |
      | p7-dbcluster-north     |
      | p7-dbcluster-south-gpu |
      | p7-dbcluster-east-gpu  |
      | p7-dbcluster-west-gpu  |
    When I hit the v1/namespaces to create a namespace with below data
      | data                                                                                                                     |
      | {"name": "p7-dbtest-ns", "description": "Created for testing p", "cost_center": "123", "group": ["p7-dbgroup7-nonprod"]} |
    Then The response status code should be 201
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.need_gpu | metadata.setupfor | namespace    |
      | p7-dbapp1 | http://some-repo-url | main        | somepath  | analytics     | p7-dbapp1     | true              | p7-dbbdd          | p7-dbtest-ns |
      | p7-dbapp2 | http://some-repo-url | main        | somepath  | bot           | p7-dbapp2     | true              | p7-dbbdd          | p7-dbtest-ns |
      | p7-dbapp3 | http://some-repo-url | main        | somepath  | analytics     | p7-dbapp3     | false             | p7-dbbdd          | p7-dbtest-ns |
      | p7-dbapp4 | http://some-repo-url | main        | somepath  | common        | p7-dbapp4     | false             | p7-dbbdd          | p7-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | p7-dbapp1 |
      | p7-dbapp2 |
      | p7-dbapp3 |
      | p7-dbapp4 |
    When I hit the v1/applications to create a application with below data
      | name      | repo_url             | repo_branch | repo_path | metadata.type | metadata.label | metadata.store_type | metadata.need_gpu | metadata.setupfor | namespace    |
      | p7-dbapp5 | http://some-repo-url | main        | somepath  | analytics     | p7-dbapp5     | deli                | true              | p7-dbbdd          | p7-dbtest-ns |
      | p7-dbapp6 | http://some-repo-url | main        | somepath  | bot           | p7-dbapp6     | grocery             | false             | p7-dbbdd          | p7-dbtest-ns |
    Then The application with below name should be created having status COMPLETED
      | name      |
      | p7-dbapp5 |
      | p7-dbapp6 |

  Scenario: Create target policies to purge analytics app from  gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name             | app_selector.name | cluster_selector.gpu | cluster_selector.setupfor | operation |
      | p7-dbgpu-apps-tp | p7-dbapp5         | true                 | p7-dbbdd                  | PURGE     |
    Then The response status code should be 201
    Then There is no application on specified clusters
      | cluster_name           |
      | p7-dbcluster-south-gpu |
      | p7-dbcluster-east-gpu  |
      | p7-dbcluster-west-gpu  |

  Scenario: Create target policies to load analytics app on  gpu clusters
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/targetpolicies to create a targetpolicy with below data
      | name              | app_selector.type | app_selector.setupfor | cluster_selector.gpu | cluster_selector.setupfor |
      | p7-dbgpu-apps-tp1 | analytics         | p7-dbbdd              | true                 | p7-dbbdd                  |
    Then The response status code should be 201
    Then The below applications are present on specified clusters
      | cluster_name                                                       | comma_seperated app_name      |
      | p7-dbcluster-south-gpu,p7-dbcluster-east-gpu,p7-dbcluster-west-gpu | p7-dbapp1,p7-dbapp3,p7-dbapp5 |

  Scenario: Add additional GPU cluster
    Given I am part of below groups
      | group              |
      | plat-nonprod-admin |
    When I hit the v1/clusters to create a cluster with below data
      | name                    | short_name | metadata.region | metadata.country | metadata.gpu | metadata.setupfor | environment |
      | p7-dbcluster-north-gpu1 | mc         | north           | Australia        | true         | p7-dbbdd          | nonprod     |
    Then The response status code should be 201
    And The below applications are present on specified clusters
      | cluster_name                                                                               | comma_seperated app_name      |
      | p7-dbcluster-south-gpu,p7-dbcluster-east-gpu,p7-dbcluster-west-gpu,p7-dbcluster-north-gpu1 | p7-dbapp1,p7-dbapp3,p7-dbapp5 |