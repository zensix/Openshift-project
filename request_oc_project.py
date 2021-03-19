#!/bin/python
import os, json , sys, getopt, hashlib
import requests
import urllib3

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


s=requests.Session()

def get_data(cfg,link):
   """ Generique function to get data from openshift API
   Parameters: 
   - cfg: Configuration Dict
   - link: API to call
   """
   url = "https://"+cfg['endpoint']+":"+cfg['port']+link
   r = s.request('GET',url,headers={'Authorization': 'Bearer '+cfg['token']},verify=False)
   result = json.loads(r.text)
   return result

def discover_namespaces(cfg):
   """ Discovers namescpaces 
   """
   result=get_data(cfg,"/api/v1/namespaces")
   data={"data":[]}
   for item in result["items"]:
      obj={"{#NAME}":item['metadata']['name'].encode('utf-8'),"{#SELFLINK}":item['metadata']['selfLink'].encode('utf-8'),"{#STATUS}":item['status']['phase'].encode('utf-8'),"{#REQUESTER}":item['metadata']['annotations']}
      data["data"].append(obj)
   print json.dumps(data,indent=2)

def get_namespace(cfg,link):
   """
   Get specifique namescape information 
   """
   result=get_data(cfg,link)
   obj={"name":result['metadata']['name'].encode('utf-8'),"selfLink":result['metadata']['selfLink'].encode('utf-8'),
      "status":result['status']['phase'].encode('utf-8'),"annotations":result['metadata']['annotations']}
   print json.dumps(obj,indent=2)
 
def dc_discover(cfg,namespace):
   """
   Discover deployment Config for specifique namescape 
   """
   url = "https://"+cfg['endpoint']+":"+cfg['port']+"/apis/apps.openshift.io/v1/namespaces/"+namespace+"/deploymentconfigs"
   r = s.request('GET',url,headers={'Authorization': 'Bearer '+cfg['token']},verify=False)
   result = json.loads(r.text)
   data=[]
   for item in result["items"]:
      obj={"{#NAME}":item['metadata']['name'].encode('utf-8'),"{#NAMESPACE}":cfg["namespace"],"{#SELFLINK}":item['metadata']['selfLink'].encode('utf-8')}
      data.append(obj)
   print json.dumps(data,indent=2)
   
def dc_status(cfg,selflink):
   """
   Get specifique deployment Config status 
   """
   result=get_data(cfg,cfg["selflink"])
   del result['status']['conditions']
   del result['status']['details']
   print json.dumps(result['status'],indent=2)

def pod_discover(cfg,namespace):
   """
   Discover pods for specifique namescape 
   """
   url = "https://"+cfg['endpoint']+":"+cfg['port']+'/api/v1/namespaces/'+namespace+'/pods'
   r = s.request('GET',url,headers={'Authorization': 'Bearer '+cfg['token']},verify=False)
   result = json.loads(r.text)
   data=[]
   for item in result["items"]:
       obj={"{#NAME}":item['metadata']['name'].encode('utf-8'),"{#NAMESPACE}":cfg["namespace"],"{#SELFLINK}":item['metadata']['selfLink'].encode('utf-8')}
       data.append(obj)
   print json.dumps(data,indent=2)
   
def pod_status(cfg,selflink):
   """
   Get statsus for specifique pod 
   """
   result=get_data(cfg,cfg["selflink"])
   del result['status']['conditions']
   del result['status']['podIPs']
   del result['status']['hostIP']
   del result['status']['qosClass']
   del result['status']['podIP']
   if result['status'].has_key('initContainerStatuses'):
      del result['status']['initContainerStatuses']
   result['status']['containerStatus']=result['status']['containerStatuses'][0]
   del result['status']['containerStatuses']
   del result['status']['containerStatus']['image']
   del result['status']['containerStatus']['imageID']
   del result['status']['containerStatus']['containerID']
   print json.dumps(result['status'],indent=2)

def prometheus_query(cfg,query):
   """
   Generique prometheus request
   parameters:
   - cfg: General configuration ( dict)
   - query: Prometheus Query
   """
   http = urllib3.PoolManager()
   url =  "https://"+cfg['endpoint']+":"+cfg['port']+"/api/v1/query"
   r = http.request_encode_url('GET',url,fields={'query': query},headers={'Authorization': 'Bearer '+cfg['token']})
   result = json.loads(r.data.decode('utf-8'))
   return result

def prom_rate_restart_pod(cfg,namespace):
   url =  "https://"+cfg['endpoint']+":"+cfg['port']+"/api/v1/query"
   payload={'query':'rate(kube_pod_container_status_restarts_total{job="kube-state-metrics",namespace="'+namespace+'"}[15m])'}
   r = s.request('GET',url,params=payload,headers={'Authorization': 'Bearer '+cfg['token']},verify=False)
   print r.text

def help():
   print '\n'.join([
   "Usage:",
   __file__+ " [namespaces|dc_discover|dc_status|pod_discover|pod_status|prom_rate_restart_pod] Options",
   "Functions",
   "\t namespaces: ouput all namespaces ( need env option)",
   "\t dc_discover: output deployment config of namespace ( need env and namespace parameters)",
   "\t dc_discover: output deployment config of namespace ( need env and namespace parameters)",
   "\t dc_status: output deployment config status ( neev envend selflink parameters)",
   "\t pod_discover: outpus all pod of namespace (need env and namespace parameters)",
   "Options:",
   "\t-h,--help: this help",
   "\t-n,--namespace: Namespace",
   "\t-e,--env: name of your openshift env cf openshift.json file",
   "\t-s,--selflink: Openshift entity url use by some call",
   "\t-p,--param: Optional parameter use by some functions",
  ])

def main(cmd,argv):
   """ Main function
   """
   # Set location of script
   cwd=os.path.dirname(os.path.abspath(__file__))
   # Open openshift config file
   with open(cwd+'/openshift.json') as json_file:
     config = json.load(json_file)
   # Set default value
   namespace=""
   selflink=""
   output="console"
   env=""
   source=os.uname()[1]
   # Pars args
   try:
      opts, args = getopt.getopt(argv,"hn:s:e:p:",["help","namespace=","env=","selflink=","param="])
   except getopt.GetoptError  as err:
      print "Parameter error"
      print(err)
      help()
      sys.exit(2)

   for opt, arg in opts:
      if opt in ("-h","--help"):
         help()
         sys.exit()
      elif opt in ("-e","--env"):
         cfg=config[arg]
      elif opt in ("-n","--namespace"):
         cfg["namespace"] = arg
      elif opt in ("--project"):
         cfg["project"] = arg         
      elif opt in ("-s","--selflink"):
         cfg["selflink"]=arg
      elif opt in ("-p","--param"):
         cfg["param"]=arg
   if(cmd == "namespaces"):
     discover_namespaces(cfg)
   elif(cmd == "dc_discover"):
     dc_discover(cfg,namespace)
   elif(cmd == "dc_status"):
     dc_status(cfg,selflink)
   elif(cmd == "pod_discover"):
     pod_discover(cfg,namespace)
   elif(cmd == "pod_status"):
     pod_status(cfg,selflink)
   elif(cmd == "prom_rate_restart_pod"):
     prom_rate_restart_pod(cfg['prometheus'],namespace)
   else:
     help()
     sys.exit(2)
if __name__ == "__main__":
   urllib3.disable_warnings()
   cmd=sys.argv[1]
   args=sys.argv[2:]
   main(cmd,args)


