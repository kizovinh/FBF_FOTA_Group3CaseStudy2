import requests
import shutil
import logging
import os
from requests.auth import HTTPBasicAuth
from datetime import datetime

class RolloutConnection():
    MANAGEMENT_HOST = "https://api.eu1.bosch-iot-rollouts.com"
    TENANT_ID = "2E35E1B6-9A77-451B-80A3-CC99E1BBC50B"
    USER_ID = "008f063c-8022-415e-8c85-ce1c16fee4e0"
    PASSWORD = "b2bf0164-88f8-4dc1-80d5-58329e5f2ed4"
    rolloutHostAPI = f"{MANAGEMENT_HOST}/rest/v1"
    rolloutAuth = HTTPBasicAuth(username=f"{TENANT_ID}\{USER_ID}", password=PASSWORD)
    
    def __init__(self):
        pass
    
    def _getInfo(self, path: str, params: dict=None):
        apiPath = self.rolloutHostAPI + path
        response = requests.get(apiPath, params=params, auth=self.rolloutAuth)
        return response
    
    def _postInfo(self, path: str, data, isFile=False):
        apiPath = self.rolloutHostAPI + path
        if isFile:
            with open(data, 'rb') as upFile:
                response = requests.post(apiPath, auth=self.rolloutAuth, files={"file": (os.path.basename(data), upFile)})
                print(os.path.basename(data))
                print(response.text)
        else:
            response = requests.post(apiPath, json=data, auth=self.rolloutAuth,
                                 headers={"Content-Type": "application/hal+json"})
        return response

    ### Target manipulation ###
    
    def createNewDevice(self, deviceInfo):
        response = self._postInfo("/targets", deviceInfo)
        return response

    def getTargetList(self, limit=50, offset=0):
        query = {
            "limit": limit,
            "offset": offset
        }
        response = self._getInfo("/targets", params=query)
        targetList = []
        for target in response.json()["content"]:
            targetInfo = {}
            targetInfo["name"] = target["name"]
            targetInfo["description"] = target["description"]
            targetInfo["controllerId"] = target["controllerId"]
            targetInfo["status"] = target["updateStatus"]
            targetInfo["token"] = target["securityToken"]
            targetInfo["id"] = self.getTargetId(target["_links"]["self"]["href"])
            targetList.append(targetInfo)
        return targetList
    

    def getTargetInfo(self, id):
        response = requests.get(self.rolloutHostAPI + f"/targets/{id}", auth=self.rolloutAuth)
        return response.text 
    
    ### Target Type Maninpulation ###
    def createNewTargetType(self, name: str, description=None, color=None,  distributions=None):
        pathAPI = f"{self.rolloutHostAPI}/targettypes"
        headers = {"Content-Type": "application/json"}
        json = [{
            "name": name
        }]
        response = requests.post(pathAPI, headers=headers, json=json, auth=self.rolloutAuth)
        return response.text
    
    def getTargetTypeList(self):
        response = self._getInfo("/targettypes")
        return [targettype["name"]  for targettype in  response.json()["content"]]

    def deleteTargetType(self, name):
        pass
       
    def getTargetActions(self, targetid):
        pathAPI = f"{self.rolloutHostAPI}/targets/{targetid}/actions"
        response = requests.get(pathAPI, auth=self.rolloutAuth)
        return response.text
    
    def addCompatibleDistributionSet(self, targettype_id: int, dstype_id: int):
        pathAPI = f"{self.rolloutHostAPI}/targettypes/{targettype_id}/compatibledistributionsettypes"
        headers = {"Content-Type": "application/json"}
        json = [{
            "id": dstype_id
        }]
        response = requests.post(pathAPI, headers=headers, json=json, auth=self.rolloutAuth)
        return response.text
    
    ### SW Modules Maninpulation ###
    def createNewSWModule(self, swModule):
        response = self._postInfo("/softwaremodules", [swModule])
        print(response.text)
        return response
    
    def getSWModuleList(self):
        swModuleInfoList =  []
        response = self._getInfo(path="/softwaremodules")
        for swModule in response.json()["content"]:
            swModuleInfo = {}
            swModuleInfo["name"] = swModule["name"]
            swModuleInfo["id"] = swModule["id"]
            swModuleInfo["version"] = swModule["version"]
            swModuleInfo["vendor"] = swModule["vendor"]
            swModuleInfo["description"] = swModule["description"]
            
            swModuleInfo["createdAt"] = datetime.fromtimestamp(swModule["createdAt"]/1000).strftime("%d/%m/%Y, %H:%M:%S")
            swModuleInfo["lastModifiedAt"] = datetime.fromtimestamp(swModule["lastModifiedAt"]/1000).strftime("%d/%m/%Y, %H:%M:%S")
            swModuleInfo["artifacts"] = self.getArtifactList(swModuleInfo["id"])
            swModuleInfoList.append(swModuleInfo)
        return swModuleInfoList
                
    def getArtifactList(self, swId: str):
        response = self._getInfo(path=f"/softwaremodules/{swId}/artifacts/")
        swArtifacts = []
        for artifact in response.json():
            artifactInfo = {}
            artifactInfo["name"] = artifact["providedFilename"]
            artifactInfo["size"] = str(artifact["size"])
            artifactInfo["id"] = artifact["id"]
            artifactInfo["createdAt"] = datetime.fromtimestamp(artifact["createdAt"]/1000).strftime("%d/%m/%Y, %H:%M:%S")
            swArtifacts.append(artifactInfo)
        return swArtifacts
            
        
        
    ### Distribution Manipulation ###
    def createNewDistribution(self, distributionInfo):
        response = self._postInfo("/distributionsets", [distributionInfo])
        print(response.text)
        return response
    
    def assginDistribution(self, targetId, assignedDistribution):
        path = f"/targets/{targetId}/assignedDS"
        data = {
            "id": assignedDistribution,
            "type": "forced"
        }
        response = self._postInfo(path, data)
        return response.text
        
    def getDistributionList(self):
        distributionList =  []
        response = self._getInfo(path="/distributionsets")
        for distribution in response.json()["content"]:
            distributionInfo = {}
            distributionInfo["name"] = distribution["name"]
            distributionInfo["id"] = distribution["id"]
            distributionInfo["version"] = distribution["version"]
            distributionInfo["description"] = distribution["description"]
            distributionInfo["createdAt"] = datetime.fromtimestamp(distribution["createdAt"]/1000).strftime("%d/%m/%Y, %H:%M:%S")
            distributionInfo["lastModifiedAt"] = datetime.fromtimestamp(distribution["lastModifiedAt"]/1000).strftime("%d/%m/%Y, %H:%M:%S")
            distributionInfo["swModules"] = []
            for swModule in distribution["modules"]:
                swModuleInfo = {}
                swModuleInfo["name"] = swModule["name"]
                swModuleInfo["version"] = swModule["version"]
                swModuleInfo["id"] = swModule["id"]
                distributionInfo["swModules"].append(swModuleInfo)
            distributionList.append(distributionInfo)
        return distributionList 
    
    def getDistributionTypeList(self):
        pathAPI = f"{self.rolloutHostAPI}/distributionsettypes"
        response = requests.get(pathAPI, auth=self.rolloutAuth)
        return response.text
    
    ### Trigger rollout ###
    def triggerRollout():
        pass
    
    ### SW Module Manipulation ###
    def uploadArtifact(self, moduleid, filepath):
        response = self._postInfo(f"/softwaremodules/{moduleid}/artifacts/" , data=filepath, isFile=True)
        return response.text
    
    def downloadArtifact(self, swid, moduleid, filepath):
        response = requests.get(self.rolloutHostAPI + f"/softwaremodules/{swid}/artifacts/{moduleid}/download", auth=self.rolloutAuth, stream=True)
        with open(filepath, 'wb') as downFile:
            shutil.copyfileobj(response.raw, downFile)
    
    def getTargetId(self, path:str) -> str:
        targetStartIndex = path.rfind('/')
        return path[targetStartIndex+1:]
# host = "https://api.eu1.bosch-iot-rollouts.com/rest/v1/"
# getSW_qry = "softwaremodules/"
# auth = HTTPBasicAuth(username=r"2E35E1B6-9A77-451B-80A3-CC99E1BBC50B\008f063c-8022-415e-8c85-ce1c16fee4e0",
#                      password="b2bf0164-88f8-4dc1-80d5-58329e5f2ed4")
# response = requests.get(host + getSW_qry, auth=auth)
# sw_modules = response.json()
# print(sw_modules)
# module_id = str(sw_modules["content"][0]["id"])

# Create a new SW module
# response = requests.post(host + getSW_qry, auth=auth, json=[{"vendor": "vendor0",
#                                                              "name": "ex1",
#                                                              "type": "application",
#                                                              "description": "a",
#                                                              "version": "0"}],
#                             headers={"Content-Type": "application/hal+json"})
# print(response.text)

# with open("ax.txt", "rb") as upfile:
#     headers={"Content-Type": "aplication/json"}
#     response = requests.post(host + getSW_qry + module_id + "/artifacts", auth=auth, files={"file": ("ax.txt", upfile)})
#     print(response.text)

# response = requests.get(host + getSW_qry + module_id + "/artifacts", auth=auth)
# print(response.json())

# Download a SW module artifacts
# artifact_download_link = response.json()[1]["_links"]["self"]["href"]
# response = requests.get(artifact_download_link + "/download", auth=auth, stream=True)
# with open('c1.txt', 'wb') as outfile:
#     shutil.copyfileobj(response.raw, outfile)


# test_url = "https://jsonplaceholder.typicode.com/todos/2"
# response = requests.get(test_url)
# print(response.json())
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
    connection = RolloutConnection()
    # print(connection.getTargetList())
    print(connection.assginDistribution("ID2", 226198))
    # result = connection.createNewTarget("ID2", "ID2", "fafba")
    # result = connection.getTargetList(limit=1)
    # result = connection.getTargetInfo("ID01")
    # result = connection.connectTarget("ID01", "795700dc7ea29dc4b2435631ab217e4d")
    # result = connection.confirmAction("ID2", 4109313, "623337ab9b71e051e8c52d2816911c8e")
    # result = connection.createNewTargetType("ABS")
    # result = connection.getTargetTypeList()
    # result = connection.getDistributionTypeList()
    