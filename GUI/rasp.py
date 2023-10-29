import PyQt5.QtCore as QtCore
import subprocess

from PyQt5.QtCore import (
    Qt,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QAbstractAnimation,
    QSize,
    QTimer
)

from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QLineEdit,
    QPushButton,
    QToolButton,
    QWidget,
    QListWidget,
    QTabWidget,
    QSplitter,
    QDialog, QGroupBox
)

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLayout
)

from PyQt5.QtGui import (
    QIcon,
    QKeySequence,
)

from iot import DDIConnection
from datetime import datetime
import os
import sys
import json
import threading
import logging

__version__ = "1.0"

class GatewayWindow(QMainWindow):
    _updateTime = 10000
    config_path = "device.json"
    nullECU = {'name': None, 'type': None, 
               'can_config': {'rx_id': None, 'tx_id': None}, 
               'server_config': {'device_id': None, 'token': None}, 
               "sw_info": {
                    "name": None,
                    "version": None,
                    "last_updated": None
            }}
    def __init__(self):
        super().__init__()
        self._ecuList = []
        self._ecuConnectionList = []
        self.setWindowTitle(f"FOTA v{__version__}")
        self.setWindowIcon(QIcon("fota.png"))
        self.timerUpdate = QTimer(self)
        self.timerUpdate.setInterval(self._updateTime)
        
        self._mainSplitter = QSplitter(Qt.Orientation.Vertical, self)
        self._loadLatestConfig()
        self._addECUList()
        self._addECUInfo()
        self._addConnection()
        self.timerUpdate.start()
        
        self.setCentralWidget(self._mainSplitter)
        # self.setLayout(self._mainlayout)
    
    def _addECUList(self):
        self._ecuListWidget = ECUListWidget("MY DEVICE", self._ecuList, self._ecuConnectionList)
        self._mainSplitter.addWidget(self._ecuListWidget)
        
    def _addECUInfo(self):
        self._ecuInfoWidget = ECUInfoWidget(self._ecuList[0], )
        self._mainSplitter.addWidget(self._ecuInfoWidget)
    
    def _addConnection(self):
        self._ecuListWidget.ecuListWidget.currentRowChanged.connect(self._updateInfoView)
        self.timerUpdate.timeout.connect(self._updateInfoCyclic)
        
    def _updateInfoCyclic(self):
        index = self._ecuListWidget.ecuListWidget.currentRow()
        if index != -1:
            self._ecuConnectionList[index].pollUpdate()
            self._ecuInfoWidget.updateView(self._ecuList[index], self._ecuConnectionList[index])
    
    def _updateInfoView(self, index):
        if index != -1 and index < len(self._ecuList):
            self._ecuInfoWidget.updateView(self._ecuList[index], self._ecuConnectionList[index])
        else:
            self._ecuInfoWidget.updateView(self.nullECU, None)
        
    def _loadLatestConfig(self):
        if not os.path.exists(self.config_path):
            return
        with open(self.config_path, 'r') as cfgFile:
            configData = json.load(cfgFile)
            self._ecuList = configData["ecu_list"]
        for ecuData in self._ecuList:
            if ecuData["server_config"]["device_id"] is not None:
                self._ecuConnectionList.append(DDIConnection(ecuData["server_config"]["device_id"], ecuData["server_config"]["token"]))
            else:
                self._ecuConnectionList.append(None)
    
    def _createConsolelog(self):
        pass
    
    def addUpdateInfo(self):
        pass


class ECUInfoWidget(QTabWidget):

    def __init__(self, ecuInfo, ecuConnection=None):
        super().__init__()
        self._ecuInfo = ecuInfo
        self._ecuConnection = ecuConnection
        self._addStatusWidget()
        self._addConfigWidget()
        self._addNotificationWidget()
    
    def updateView(self, ecuInfo, ecuConnection: DDIConnection):
        self._ecuInfo = ecuInfo
        self._ecuConnection = ecuConnection
        self.nameLabel.setText(f"Name: {self._ecuInfo['name']}")
        self.typeLabel.setText(f"Type: {self._ecuInfo['type']}")
        if self._ecuConnection is None:
            self.statusLabel.setText(f"Status: unknown")
        else:
            self.statusLabel.setText(f"Status: {self._ecuConnection.getStatus()}")
        self.swNameLabel.setText(f"SW Name: {self._ecuInfo['sw_info']['name']}")
        self.swVersionLabel.setText(f"SW Version: {self._ecuInfo['sw_info']['version']}")
        self.swUpdateTimeLabel.setText(f"Last updated: {self._ecuInfo['sw_info']['last_updated']}")
        self.canRxIdInput.setText(self._ecuInfo['can_config']['rx_id'])
        self.canTxIdInput.setText(self._ecuInfo['can_config']['tx_id'])   
        self.deviceIdInput.setText(self._ecuInfo['server_config']['device_id'])
        self.tokenInput.setText(self._ecuInfo['server_config']['token'])
        self.updateNotification()
    
    def clearLayout(self, layout: QLayout):
        print(layout.count())
        for i in reversed(range(layout.count())): 
            layoutItem = layout.itemAt(i)
            if layoutItem.widget() is not None:
                widgetToRemove = layoutItem.widget()
                widgetToRemove.setParent(None)
                layout.removeWidget(widgetToRemove)
            elif layoutItem.spacerItem() is not None:
                layout.removeItem(layoutItem)
            else:
                layoutToRemove = layout.itemAt(i)
                self.clearLayout(layoutToRemove)
            
    def updateNotification(self):
        self.clearLayout(self.notiLayout)
        if self._ecuConnection is not None:
            if self._ecuConnection.getStatus() == "Deployed":
                sublayout = QHBoxLayout()
                sublayout.addWidget(QLabel("There is new update for this device"))
                sublayout.addStretch()
                self._downloadBtn = QPushButton("Download")
                sublayout.addWidget(self._downloadBtn)
                self._downloadBtn.clicked.connect(self._ecuConnection.downloadArtifacts)
                if not self._ecuConnection.getDownloadStatus():
                    self._ecuConnection.downloadArtifacts()
                    flashRet = subprocess.run("./runFlash.sh")
                    # Flashing code #
                    #flashProcess = subprocess.Popen(["lxterminal", "-e", "python", "./FlashSequence/main.py"]) #"./runFlash.sh"])
                    #returncode = flashProcess.wait()
                    
                    if flashRet.returncode == 0:
                        self._ecuConnection.closeDeployRequest("success")
                        print("success")
                    else:
                        self._ecuConnection.closeDeployRequest("failure")
                        print("failure")
                        
                    self._downloadBtn.setText("Downloaded")
                    self._downloadBtn.setEnabled(False)
                else:
                    self._downloadBtn.setText("Downloaded")
                    self._downloadBtn.setEnabled(False)
                self.notiLayout.addLayout(sublayout)
            elif self._ecuConnection.getStatus() == "Canceled":
                sublayout = QHBoxLayout()
                sublayout.addWidget(QLabel("Cancel update request for this device"))
                sublayout.addStretch()
                cancelBtn = QPushButton("Cancel")
                sublayout.addWidget(cancelBtn)
                cancelBtn.clicked.connect(self._ecuConnection.handleCancelRequest)
                self.notiLayout.addLayout(sublayout)
            else:
                self.notiLayout.addWidget(QLabel("No update is available"))
            self.notiLayout.addStretch()
        else:
            self.notiLayout.addWidget(QLabel("No update is available"))
            self.notiLayout.addStretch()
        
    
    def _addStatusWidget(self):
        self.generalInfoWidget = QWidget()
        layout = QVBoxLayout()
        self.nameLabel = QLabel(f"Name: {self._ecuInfo['name']}")
        self.statusLabel = QLabel(f"Status: unknown")
        self.typeLabel = QLabel(f"Type: {self._ecuInfo['type']}")
        self.swNameLabel = QLabel(f"SW Name: {self._ecuInfo['sw_info']['name']}")
        self.swVersionLabel = QLabel(f"SW Version: {self._ecuInfo['sw_info']['version']}")
        self.swUpdateTimeLabel = QLabel(f"Last updated: {self._ecuInfo['sw_info']['last_updated']}")
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.statusLabel)
        layout.addWidget(self.typeLabel)
        layout.addWidget(self.swNameLabel)
        layout.addWidget(self.swVersionLabel)
        layout.addWidget(self.swUpdateTimeLabel)
        layout.addStretch()
        self.generalInfoWidget.setLayout(layout)
        self.addTab(self.generalInfoWidget, "General")
    
    def _addConfigWidget(self):
        self.configurationWidget = QWidget()
        layout = QVBoxLayout()
        configCANBox = QGroupBox("CAN Configuration")
        self.canRxIdInput = QLineEdit(self._ecuInfo['can_config']['rx_id'])
        self.canTxIdInput = QLineEdit(self._ecuInfo['can_config']['tx_id'])
        configCANForm = QFormLayout()
        configCANForm.addRow("CAN Rx", self.canRxIdInput)
        configCANForm.addRow("CAN Tx", self.canTxIdInput)
        configCANBox.setLayout(configCANForm)
        layout.addWidget(configCANBox)
        
        configServerBox = QGroupBox("Server Configuration")
        self.deviceIdInput = QLineEdit(self._ecuInfo['server_config']['device_id'])
        self.tokenInput = QLineEdit(self._ecuInfo['server_config']['token'])
        self.tokenInput.setEchoMode(QLineEdit.EchoMode.Password)
        configServerForm = QFormLayout()
        configServerForm.addRow("Device ID", self.deviceIdInput)
        configServerForm.addRow("Security Token", self.tokenInput)
        configServerBox.setLayout(configServerForm)
        layout.addWidget(configServerBox)
        self.configurationWidget.setLayout(layout)
        self.addTab(self.configurationWidget, "Configuration")
        
    def _addNotificationWidget(self):
        self.notifWidget = QWidget()
        self.notiLayout = QVBoxLayout()
        self.updateNotification()
        self.notifWidget.setLayout(self.notiLayout)
        self.addTab(self.notifWidget, "Notification")

class ECUListWidget(QWidget):
    def __init__(self, title, ecuList: list, ecuConnectionList: list):
        super().__init__()
        self._ecuList = ecuList
        self._ecuConnectionList = ecuConnectionList
        self._mainLayout = QVBoxLayout(self)
        self._addHeaderBar(title)
        self._addECUList()
        self._mainLayout.addStretch()
        self.setLayout(self._mainLayout)
        
        
    def _addHeaderBar(self, title):
        layout = QHBoxLayout()
        header = QLabel(title)
        header.setStyleSheet("font-weight: bold")
        layout.addWidget(header)
        layout.addStretch()
        
        self.addBtn = QToolButton()
        self.addBtn.setAutoRaise(True)
        self.addBtn.setIcon(QIcon("add.svg"))
        self.addBtn.clicked.connect(self._addNewECU)
        self.addBtn.setShortcut(QKeySequence.StandardKey.New)
        self.addBtn.setToolTip("Add new connected ECU")
        layout.addWidget(self.addBtn)
        
        self.deleteBtn = QToolButton()
        self.deleteBtn.setAutoRaise(True)
        self.deleteBtn.setIcon(QIcon("delete.png"))
        self.deleteBtn.clicked.connect(self._deleteSelectedECU)
        self.deleteBtn.setShortcut(QKeySequence.StandardKey.Delete)
        self.deleteBtn.setToolTip("Delete ECU")
        layout.addWidget(self.deleteBtn)
        
        self.refreshBtn = QToolButton()
        self.refreshBtn.setAutoRaise(True)
        self.refreshBtn.setIcon(QIcon("refresh.png"))
        self.refreshBtn.clicked.connect(self._refreshECU)
        self.refreshBtn.setShortcut(QKeySequence.StandardKey.Refresh)
        self.refreshBtn.setToolTip("Refresh the ECUs status")
        layout.addWidget(self.refreshBtn)
        self._mainLayout.addLayout(layout)
        
    def _addECUList(self):
        self.ecuListWidget = QListWidget(self)
        for ecuinfo in self._ecuList:
            self.ecuListWidget.addItem(ecuinfo["name"])
        self._mainLayout.addWidget(self.ecuListWidget)
    
    def _deleteSelectedECU(self):
        currentECUIdx = self.ecuListWidget.currentRow()
        if currentECUIdx >= 0:
            self._ecuList.pop(currentECUIdx)
            self._ecuConnectionList.pop(currentECUIdx)
            currentECU = self.ecuListWidget.takeItem(currentECUIdx)
            del currentECU
            self.ecuListWidget.setCurrentRow(-1)
        
    def _addNewECU(self):
        dialog = NewECUCreationDlg()
        if dialog.exec():
            ecuinfo = dialog.getECUInfo()
            self._ecuList.append(ecuinfo)
            self.ecuListWidget.addItem(ecuinfo["name"])
        
    def _refreshECU(self):
        pass

class NewECUCreationDlg(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create new ECU")
        self._mainlayout = QVBoxLayout()
        
        generalInfoBox = QGroupBox("General Info")
        generalInfoForm = QFormLayout()
        self.nameInput = QLineEdit("")
        self.typeInput = QLineEdit("")
        generalInfoForm.addRow("&Name", self.nameInput)
        generalInfoForm.addRow("&Type", self.typeInput)
        generalInfoBox.setLayout(generalInfoForm)
        self._mainlayout.addWidget(generalInfoBox)
        
        configCANBox = QGroupBox("CAN Configuration")
        self.canRxIdInput = QLineEdit("")
        self.canTxIdInput = QLineEdit("")
        configCANForm = QFormLayout()
        configCANForm.addRow("CAN Rx", self.canRxIdInput)
        configCANForm.addRow("CAN Tx", self.canTxIdInput)
        configCANBox.setLayout(configCANForm)
        self._mainlayout.addWidget(configCANBox)
        
        configServerBox = QGroupBox("Server Configuration")
        self.deviceIdInput = QLineEdit("")
        self.tokenInput = QLineEdit("")
        self.tokenInput.setEchoMode(QLineEdit.EchoMode.Password)
        configServerForm = QFormLayout()
        configServerForm.addRow("Device ID", self.deviceIdInput)
        configServerForm.addRow("Security Token", self.tokenInput)
        configServerBox.setLayout(configServerForm)
        self._mainlayout.addWidget(configServerBox)
        
        self.createBtn = QPushButton("Create")
        self.createBtn.clicked.connect(self.accept)
        self._mainlayout.addWidget(self.createBtn)
        self.setLayout(self._mainlayout)
    
    def getECUInfo(self):
        ecuInfo = {}
        ecuInfo["name"] = self.nameInput.text()
        ecuInfo["type"] = self.typeInput.text()
        ecuInfo["CAN_config"] = {}
        ecuInfo["CAN_config"]["RX_id"] = self.canRxIdInput.text()
        ecuInfo["CAN_config"]["Tx_id"] = self.canTxIdInput.text()
        ecuInfo["server_config"] = {}
        ecuInfo["server_config"]["device_id"] = self.deviceIdInput.text()
        ecuInfo["server_config"]["token"] = self.tokenInput.text()
        return ecuInfo
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    raspWindow = GatewayWindow()
    raspWindow.show()
    sys.exit(app.exec())
    
