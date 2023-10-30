from requests.auth import HTTPBasicAuth
from datetime import datetime

import requests
import shutil
import logging
import os

class RolloutConnection():
    MANAGEMENT_HOST = "https://api.eu1.bosch-iot-rollouts.com"
    TENANT_ID = "2E35E1B6-9A77-451B-80A3-CC99E1BBC50B"
    USER_ID = "008f063c-8022-415e-8c85-ce1c16fee4e0"
    PASSWORD = "b2bf0164-88f8-4dc1-80d5-58329e5f2ed4"
    rolloutHostAPI = f"{MANAGEMENT_HOST}/rest/v1"
    rolloutAuth = HTTPBasicAuth(username=f"{TENANT_ID}\{USER_ID}", password=PASSWORD)
    
    @classmethod
    def _getInfo(cls, path: str, params: dict=None):
        apiPath = cls.rolloutHostAPI + path
        response = requests.get(apiPath, params=params, auth=cls.rolloutAuth, )
        return response
    
    @classmethod
    def _postInfo(cls, path: str, data, isFile=False):
        apiPath = cls.rolloutHostAPI + path
        if isFile:
            with open(data, 'rb') as upFile:
                response = requests.post(apiPath, auth=cls.rolloutAuth, files={"file": (os.path.basename(data), upFile)})
        else:
            response = requests.post(apiPath, json=data, auth=cls.rolloutAuth,
                                 headers={"Content-Type": "application/hal+json"})
        return response

    ### Target manipulation ###
    @classmethod
    def createDevice(cls, deviceInfo):
        '''
        '''
        response = cls._postInfo(path="/targets", data=[deviceInfo])
        print(deviceInfo)
        print(response.text)
        return response
    
    @classmethod
    def getDeviceList(cls):
        '''Get the latest information of available device
        The information contains name, token, description, status and distribution info
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/targets-api-guide.html#_get_restv1targets
        '''
        response = cls._getInfo(path="/targets")
        targetList = []
        for target in response.json()["content"]:
            targetInfo = {}
            targetInfo["name"] = target["name"]
            targetInfo["description"] = target["description"]
            targetInfo["id"] = target["controllerId"]
            targetInfo["status"] = target["updateStatus"]
            targetInfo["token"] = target["securityToken"]
            if "lastControllerRequestAt" in target: 
                targetInfo["lastPollAt"] = timestamp2str(target["lastControllerRequestAt"])
            else:
                targetInfo["lastPollAt"] = ""
            if "installedAt" in target and targetInfo["status"] != "error":
                targetInfo["installedAt"] = timestamp2str(target["installedAt"])
                targetInfo["installedDS"] = cls.getInstalledDistribution(targetInfo["id"])
                targetInfo["assignedDS"] = cls.getAssignedDistribution(targetInfo["id"])
            elif targetInfo["status"] == "pending":
                targetInfo["installedAt"] = ""
                targetInfo["installedDS"] = ""
                targetInfo["assignedDS"] = cls.getAssignedDistribution(targetInfo["id"])
            else:
                targetInfo["installedAt"] = ""
                targetInfo["installedDS"] = ""
                targetInfo["assignedDS"] = ""

            targetInfo["autoConfirm"] = str(target["autoConfirmActive"])
            targetList.append(targetInfo)
        return targetList
    
    @classmethod
    def getAssignedDistribution(cls, deviceId):
        info = cls._getInfo(path=f"/targets/{deviceId}/assignedDS").json()
        assignedDSInfo = f"{info['name']} (version {info['version']})"
        return assignedDSInfo
    
    @classmethod
    def getInstalledDistribution(cls, deviceId):
        info = cls._getInfo(path=f"/targets/{deviceId}/installedDS").json()
        installedDSInfo = f"{info['name']} (version {info['version']})"
        return installedDSInfo
    
    ### Target Type Maninpulation ###
    @classmethod
    def createNewTargetType(cls, name: str, description=None, color=None,  distributions=None):
        pathAPI = f"{cls.rolloutHostAPI}/targettypes"
        headers = {"Content-Type": "application/json"}
        json = [{
            "name": name
        }]
        response = requests.post(pathAPI, headers=headers, json=json, auth=cls.rolloutAuth)
        return response.text
    
    @classmethod
    def getTargetTypeList(cls):
        response = cls._getInfo("/targettypes")
        return [targettype["name"]  for targettype in  response.json()["content"]]
    
    @classmethod
    def getTargetActions(cls, targetid):
        pathAPI = f"{cls.rolloutHostAPI}/targets/{targetid}/actions"
        response = requests.get(pathAPI, auth=cls.rolloutAuth)
        return response.text
    
    ### SW Modules Maninpulation ###
    @classmethod
    def createSWModule(cls, swInfo:dict) -> bool:
        '''Create a new software module.
        The information of new software module including name, version, description and only type supported is application
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/softwaremodules-api-guide.html#_post_restv1softwaremodules
        '''
        swInfo["type"] = "application"
        response = cls._postInfo("/softwaremodules", [swInfo])
        return response.ok
    
    @classmethod
    def getSWModuleList(cls) -> list[dict]:
        '''Get the latest information of available software module
        The information contains name, version, vendor and artifacts attached
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/softwaremodules-api-guide.html#_get_restv1softwaremodules
        '''
        swModuleInfoList =  []
        response = cls._getInfo(path="/softwaremodules")
        for swModule in response.json()["content"]:
            swModuleInfo = {}
            swModuleInfo["name"] = swModule["name"]
            swModuleInfo["id"] = swModule["id"]
            swModuleInfo["version"] = swModule["version"]
            swModuleInfo["vendor"] = swModule["vendor"]
            swModuleInfo["description"] = swModule["description"]
            swModuleInfo["createdAt"] = timestamp2str(swModule["createdAt"])
            swModuleInfo["lastModifiedAt"] = timestamp2str(swModule["lastModifiedAt"])
            swModuleInfo["artifacts"] = cls.getArtifactList(swModuleInfo["id"])
            swModuleInfoList.append(swModuleInfo)
        return swModuleInfoList
    
    @classmethod
    def getArtifactList(cls, swId: str) -> list[dict]:
        '''Get the latest information about artifacts in the software.
        The information like name, size and data creation is provided
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/softwaremodules-api-guide.html#_get_restv1softwaremodulessoftwaremoduleidartifacts
        '''
        response = cls._getInfo(path=f"/softwaremodules/{swId}/artifacts/")
        swArtifacts = []
        for artifact in response.json():
            artifactInfo = {}
            artifactInfo["name"] = artifact["providedFilename"]
            artifactInfo["size"] = str(artifact["size"])
            artifactInfo["id"] = artifact["id"]
            artifactInfo["createdAt"] = timestamp2str(artifact["createdAt"])
            swArtifacts.append(artifactInfo)
        return swArtifacts
    
    @classmethod
    def uploadArtifact(cls, swId: int, filepath: str) -> bool:
        '''Upload the artifact to corresponding software by the provided file path
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/softwaremodules-api-guide.html#_post_restv1softwaremodulessoftwaremoduleidartifacts
        '''
        path = f"/softwaremodules/{swId}/artifacts/"
        response = cls._postInfo(path, data=filepath, isFile=True)
        return response.ok
    
    @classmethod
    def downloadArtifact(cls, swId, artifactId, filepath):
        response = requests.get(cls.rolloutHostAPI + f"/softwaremodules/{swId}/artifacts/{artifactId}/download", auth=cls.rolloutAuth, stream=True)
        with open(filepath, 'wb') as downFile:
            shutil.copyfileobj(response.raw, downFile)    
    
    ### Distribution Manipulation ###
    @classmethod
    def createDistribution(cls, distributionInfo: dict) -> bool:
        '''Create a new distribution set.
        The information of the new distribution including name, version, description and only type supported is application
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/distributionsets-api-guide.html#_get_restv1distributionsets
        '''
        distributionInfo["type"] = "app"
        response = cls._postInfo(path="/distributionsets", data=[distributionInfo])
        return response.ok
    
    @classmethod
    def mapDistribution(cls, distributionId: int, swId: int) -> bool:
        '''Mapping the software module to the distribution set.
        The mapping using the specific id from both entity
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/distributionsets-api-guide.html#_post_restv1distributionsetsdistributionsetidassignedsm
        '''
        path = f"/distributionsets/{distributionId}/assignedSM"
        data = [
            {
                "id": swId
            }
        ]
        response = cls._postInfo(path, data)
        return response.ok
    
    @classmethod
    def assginDistribution(cls, targetId: int, distributionId: int) -> bool:
        '''Assign the distribution set to the target device to trigger flasing.
        For simplicity, the type of assignment is fixed as forced
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/targets-api-guide.html#_post_restv1targetstargetidassignedds_assign_single_distribution_set
        '''
        path = f"/targets/{targetId}/assignedDS"
        data = {
            "id": distributionId,
            "type": "forced"
        }
        response = cls._postInfo(path, data)
        return response.ok
    
    @classmethod
    def getDistributionList(cls) -> list[dict]:
        '''Get the latest information about the distribution sets.
        Return a dictionary with some selected info and sw module mapping
        Refers: https://docs.bosch-iot-suite.com/rollouts/rest-api/distributionsets-api-guide.html#_get_restv1distributionsets
        '''
        response = cls._getInfo(path="/distributionsets")
        distributionList =  []
        for distribution in response.json()["content"]:
            distributionInfo = {}
            distributionInfo["name"] = distribution["name"]
            distributionInfo["id"] = distribution["id"]
            distributionInfo["version"] = distribution["version"]
            distributionInfo["description"] = distribution["description"]
            distributionInfo["createdAt"] = timestamp2str(distribution["createdAt"])
            distributionInfo["lastModifiedAt"] = timestamp2str(distribution["lastModifiedAt"])
            distributionInfo["swModules"] = []
            for swModule in distribution["modules"]:
                swModuleInfo = {}
                swModuleInfo["name"] = swModule["name"]
                swModuleInfo["version"] = swModule["version"]
                swModuleInfo["id"] = swModule["id"]
                distributionInfo["swModules"].append(swModuleInfo)
            distributionList.append(distributionInfo)
        return distributionList
    
def timestamp2str(timetamp: int) -> str:
    '''Convert a UTC timestamp (ms) to readable string format "%d/%m/%Y, %H:%M:%S"'''
    # Convert timestamp from ms to s
    timestamp = timetamp / 1000
    return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y, %H:%M:%S")
    
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
    print(connection.assginDistribution("ID2", 226198))
    
