# Template - Namespace - Openshift

# How it works

Template use unique zabbix external script ( python script) with different parameters

The script use some openshift api and openshift prometheus calls
Discover and check status of deployment config and pods for specifique namespace

Because zabbix macro size limitation ( OCP Token is to big),
the python script use __openshift.json__ config file. 

At time, the supervision is simple

alerting if deployment config or pod status are abormals or pod restart count increase

## Installing

1. Clone the project
2. Copy __request_oc_project.py__ to __/usr/lib/zabbix/externalscripts/__ ( on you zbx server and/or proxy )
3. Copy __openshift.json_model__ to __/usr/lib/zabbix/externalscripts/openshift.json__ 
4. Configure all values present in __/usr/lib/zabbix/externalscripts/openshift.json__  (see Environment config section)
5. Import the template file __zbx-template-ocp-project.xml__ to zabbix ( template name: __Template - Namespace - Openshift__)

For each project/namespace you want to check
1. Create new host where:

   - Host name: what your want for exemple: fqn-ocp-api-namespace 
   - Interface Type: Agent
   - Interface ip: Adress of you cluster api endpoint
   - Interface dns: fqdn of you cluster api endpoint 

Note: 
zbx agent is not use, this config is just made to set some zbx host macro ( like {HOST.IP} ..)

2. Add template __Template - Namespace - Openshift__ to the new host config

set herited template macro value on the new host:

- {$CLUSTER_OCP}: env name of json config file (env1 in this sample)
- {$NAMESPACE} : Name of ocp project to supervise

## Python script usage

For help :

        $ ./request_oc_project.py --help
        Usage:
        ./request_oc_project.py [namespaces|dc_discover|dc_status|pod_discover|pod_status|prom_rate_restart_pod] Options
        Functions
                namespaces: ouput all namespaces ( need env option)
                dc_discover: output deployment config of namespace ( need env and namespace parameters)
                dc_discover: output deployment config of namespace ( need env and namespace parameters)
                dc_status: output deployment config status ( neev envend selflink parameters)
                pod_discover: outpus all pod of namespace (need env and namespace parameters)
        Options:
                -h,--help: this help
                -n,--namespace: Namespace
                -e,--env: name of your openshift env cf openshift.json file
                -s,--selflink: Openshift entity url use by some call
                -p,--param: Optional parameter use by some functions




## Environment config
json config file to define all configurations

You can declare mutliple clusters ( env )

For each environnement you need following informations:
- __endpoint__ : Openshift API Url
- __token__: Openshift token use by http client has bearer token for api access
- __port__: Api TCP port
- __prometheus.endpoint__: Openshift Prometheus url
- __prometheus.token__: Openshift token use by http client has bearer token for prometheus access
- __prometheus.port__: Prometheus TCP port

To get OCP tokens :
- Api Server token :

        oc sa get-token openshift-apiserver-sa -n openshift-apiserver
- Prometheus token:

        oc sa get-token  prometheus-k8s -n openshift-monitoring

openshift.json sample:

        {
           "env1": {
              "endpoint": "api.env1.myopenshift.org",
              "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
              ...
              XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
              "port": "6443",
              "prometheus": {
                  "endpoint": "prometheus-k8s-openshift-monitoring.env1.myopenshift.org",
                  "token":  "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY
                  ...
                  YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",
                  "port": "443"
              }
           },
           "env2": {
              "endpoint": "api.env2.myopenshift.org",
                   ...

           }
        }


 ## Discover functions:
 ### namespaces

        $ request_oc_project.py namespaces -e env1
        {
           "data": [
             {
               "{#REQUESTER}": {
                  "openshift.io/requester": "user1", 
                  "openshift.io/sa.scc.upplemental-groups": "1001280000/0000", 
                  "openshift.io/display-name": "Project One ", 
                  "openshift.io/sa.scc.mcs": "s0:c36,10", 
                  "openshift.io/description": xxxxxxxxx", 
                  "openshift.io/node-selector": type=apps-node", 
                  "openshift.io/sa.scc.uid-range": 1001280000/10000"
               },                    
               "{#STATUS}": "Active", 
               "{#SELFLINK}": "/api/v1/namespaces/project01", 
               "{#NAME}": "project01"
             },               
             {
                 ...
             }
        }


### dc_discover
        $ request_oc_project.py dc_discover -e env1 -n project01
        [
           {
               "{#NAMESPACE}": "project01", 
               "{#SELFLINK}": "/apis/apps.openshift.io/v1/ amespaces/xxxx/deploymentconfigs/dc1", 
               "{#NAME}": "dc1"
           },             
           ...            
           {
               "{#NAMESPACE}": "project01", 
               "{#SELFLINK}": "/apis/apps.openshift.io/v1/ amespaces/yyyyy/deploymentconfigs/dc2", 
               "{#NAME}": "dc2"
           }
        ]
### pod_discover
        $ request_oc_project.py pod_discover -e env1 -n project01
        [
           {
              "{#NAMESPACE}": "project01", 
              "{#SELFLINK}": "/api/v1/namespaces/project01/ods/project01-application-controller-0", 
              "{#NAME}": "project01-application-controller-0"
           },            ...           {
              "{#NAMESPACE}": "project01", 
              "{#SELFLINK}": "/api/v1/namespaces/project01/ods/project01-server-86dc95dfc5-6td2m", 
              "{#NAME}": "project01-server-86dc95dfc5-6td2m"
           }
        ]

## Status functions:

### dc_status
        $ request_oc_project.py dc_status -e env1 -n project01 -s /apis/apps.openshift.io/v1/namespaces/xxxx/deploymentconfigs/dc1 
        {
           "replicas": 2, 
           "observedGeneration": 4, 
           "updatedReplicas": 2, 
           "availableReplicas": 2, 
           "latestVersion": 4, 
           "readyReplicas": 2, 
           "unavailableReplicas": 0
        }

### pod_status
        $ request_oc_project.py pod_status -e env1 -n project01 -s /api/v1/namespaces/project01/pods/project01-application-controller-0
        {
           "containerStatus": {
              "restartCount": 0, 
              "name": "project01-application-controller-0", 
              "started": true, 
              "state": {
                 "running": {
                    "startedAt": "2021-02-09T12:51:38Z"
                 }
              },               
              "ready": true, 
              "lastState": {}
           }, 
           "startTime": "2021-02-09T12:50:45Z", 
           "phase": "Running"
        }

## Zabbix configuration
For performances consideration, all projects ares not automaticly check
You should add project one by one in zabbix supervision

### Add one project
In this example I suppose your OCP fqn api is __api.ocp.whatever__ , ip __192.168.0.1__ and namespace/projet to supervise is named __projectOne__

Add "fake" host where :

Host name : __api.ocp.whatever - projectOne__  ( is just proposition, you can choose what you want)

Agent: __192.168.0.1__ (APi IP) Dns Name:  api.ocp.whatever ( API FQDN)


Templates: Add __Template - Namespace - Openshift__

Macro: 

Set {$NAMESPACE} value with the namespace (__projectOne__ in this example )

Set {$CLUSTER_OCP} value with name of your cluster configuration name ( see openshift.json config: __env1__ in example)
 
If you want add other project you can duplicate this host and just change

__Host name__ : __api.ocp.whatever - projectTwo__ ( don't change agent config ) and __{$NAMESPACE}__ macro value ( projectTwo )

