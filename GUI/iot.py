from requests.auth import HTTPBasicAuth
from enum import Enum, auto

import logging
import requests
import shutil

class ActionFeedback(Enum):
    DOWNLOAD = auto()
    DOWNLOADED = auto()
    CANCELED = auto()
    SCHEDULED = auto()
    REJECTED = auto()
    RESUMED = auto()
    PROCEEDING = auto()
    
    def __str__(self) -> str:
        return f"{self._name_.lower()}"
    
class ConnectionStatus(Enum):
    DISCONNECT = auto()
    CONNECTED = auto()
    CANCELED = auto()
    DEPLOYED = auto()
    WAIT_FOR_CONFIRM = auto()
    
    def __str__(self) -> str:
        return f"{self._name_.title()}"
    
class DDIConnection():
    TENANT_ID = "2E35E1B6-9A77-451B-80A3-CC99E1BBC50B"
    DDI_HOST = "https://device.eu1.bosch-iot-rollouts.com"
    DDI_ROOT_API = f"{DDI_HOST}/{TENANT_ID}/controller/v1"
    
    def __init__(self, deviceid, token):
        self._autoconfirm: bool = False
        self._pollingTime: int = 100
        self._deviceid: str = deviceid
        self._token: str = token
        self._status: str = "idle"
        self._downloaded = False
        self._flashed = False
        self.pollUpdate()
    
    def getInfo(self, path=""):
        fullpath = f"{self.DDI_ROOT_API}/{self._deviceid}{path}"
        headers = {"Authorization": f"TargetToken {self._token}"}
        response = requests.get(fullpath, headers=headers)
        if response.ok:
            logging.debug("The connection is success.")
        else:
            logging.debug("The connection is lost")
        return response

    def postInfo(self, path="", feedback={}):
        fullpath = f"{self.DDI_ROOT_API}/{self._deviceid}{path}"
        print(fullpath)
        headers = {"Authorization": f"TargetToken {self._token}",
                   "Content-Type": "application/json"}
        response = requests.post(fullpath, headers=headers, json=feedback)
        if response.ok:
            logging.debug("The connection is success.")
        else:
            logging.debug("The connection is lost")
        return response
    
    def getStatus(self):
        return str(self._status)
    
    def pollUpdate(self):
        updateData = self.getInfo().json()
        if "deploymentBase" in updateData["_links"]:
            self._status = ConnectionStatus.DEPLOYED
            self._delployActionId = self.getActionId(updateData["_links"]["deploymentBase"]["href"])
            print(f"There is deployment request {self._delployActionId}")
        elif "cancelAction" in updateData["_links"]:
            self._status = ConnectionStatus.CANCELED
            self._cancelActionId = self.getActionId(updateData["_links"]["cancelAction"]["href"])
            print(f"There is cancel request {self._cancelActionId}")
        elif "confirmationBase" in updateData["_links"]:
            self._status = ConnectionStatus.WAIT_FOR_CONFIRM
            self._confirmActionId = self.getActionId(updateData["_links"]["confirmationBase"]["href"])
            print(f"There is confirm request {self._confirmActionId}")
        else:
            self._status = ConnectionStatus.CONNECTED
            
        if "installedBase" in updateData["_links"]:
            pass
        if "configData" in updateData["_links"]:
            pass
        return str(self._status)
    
    def feedbackProgress(self):
        if self._status == ConnectionStatus.CANCELED:
            self.handleCancelRequest()
        elif self._status == ConnectionStatus.WAIT_FOR_CONFIRM:
            self.hanldeConfirmRequest()
        elif self._status == ConnectionStatus.DEPLOYED:
            self.handleDeployRequest()
    
    def handleCancelRequest(self):
        feedbackData = {
            "status": {
                "execution": "closed",
                "result": {
                    "finished": 'success'
                }
            }
        }
        response = self.postInfo(path=f"/cancelAction/{self._cancelActionId}/feedback", feedback=feedbackData)
        print(response.text)
        
    
    def hanldeConfirmRequest(self):
        feedbackData = {
           "confirmation": "confirmed",
           "message": ["yes"]
        }
        response = self.postInfo(path=f"/confirmationBase/{self._confirmActionId}/feedback", feedback=feedbackData)
        print(response.text)
        
    def closeDeployRequest(self, result):
        feedbackData = {
            "status": {
                "execution": "closed",
                "result": {
                    "finished": result,
                }
            }
        }
        response = self.postInfo(path=f"/deploymentBase/{self._delployActionId}/feedback", feedback=feedbackData)
        self._downloaded = False
        self._flashed = False
        print(response.text)
    
    def getActionInfo(self):
        if self._status == ConnectionStatus.CANCELED:
            response = self.getInfo(f"/cancelAction/{self._cancelActionId}").json()
        elif self._status == ConnectionStatus.WAIT_FOR_CONFIRM:
            response = self.getInfo(f"/confirmationBase/{self._confirmActionId}").json()
        elif self._status == ConnectionStatus.DEPLOYED:
            response = self.getInfo(f"/deploymentBase/{self._delployActionId}").json()
        print(response)
    
    def getDownloadInfo(self):
        artifactsData = self.getInfo(f"/deploymentBase/{self._delployActionId}").json()
        pass
    
    def getDownloadStatus(self):
        return self._downloaded

    def getFlashStatus(self):
        return self._flashed
    
    def setFlashStatus(self, status:bool):
        self._flashed = status
        
    def downloadArtifacts(self):
        artifactsData = self.getInfo(f"/deploymentBase/{self._delployActionId}").json()
        for artifact in artifactsData["deployment"]["chunks"][0]["artifacts"]:
            print(artifact["filename"])
            response = requests.get(artifact["_links"]["download"]["href"])
            with open("./FlashSequence/binInput/" + artifact["filename"], 'wb') as downFile:
                downFile.write(response.content)
        self._downloaded = True
        # self.feedback
    
    def getAutoConfirmInfo(self):
        response = self.getInfo(f"/confirmationBase")
        print(response.text)
        
    def confirmAction(self, msg:str=" "):
        feedbackData = {
            "confirmation": "confirmed",
            "details": [msg]
        }
        response = self.postInfo(path=f"/confirmationBase/{self._confirmActionId}", feedback=feedbackData)
        return response.text
    
    def denyAction(self, msg:str=" "):
        feedbackData = {
            "confirmation": "denied",
            "detailed": [msg]
        }
        response = self.postInfo(path=f"/confirmationBase/{self._confirmActionId}", feedback=feedbackData)
        return response.text
        
    def getActionId(self, path:str) -> str:
        queryStartIndex = path.rfind('?')
        actionStartIndex = path.rfind('/')
        if queryStartIndex != -1:
            return path[actionStartIndex+1:queryStartIndex]
        else:
            return path[actionStartIndex+1:]
    



if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log"),
            logging.StreamHandler()
        ]
    )
    # connection1 = DDIConnection("ID2", "623337ab9b71e051e8c52d2816911c8e")
    # connection1.downloadArtifacts()
    # connection1.handleCancelRequest()
    connection2 = DDIConnection("ID01", "795700dc7ea29dc4b2435631ab217e4d")
    connection2.handleDeployRequest()
    # connection2.downloadArtifacts()
    
    # connection2.getAutoConfirmInfo()
    # connection2.handleCancelRequest()
    # result = connection.createNewTarget("ID2", "ID2", "fafba")
    # result = connection.getTargetList(limit=1)
    # result = connection.getTargetInfo("ID01")
    # result = connection.connectTarget("ID01", "795700dc7ea29dc4b2435631ab217e4d")
    # result = connection.confirmAction("ID2", 4109313, "623337ab9b71e051e8c52d2816911c8e")
    # result = connection.createNewTargetType("ABS")
    # result = connection.getTargetTypeList()
    # result = connection.getDistributionTypeList()
    
