from PyQt5.QtCore import (
    Qt,
    QRect,
    QPoint,
    QThread,
    QTimer,
    pyqtSignal,
)

from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QLineEdit,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QPushButton,
    QWidget,
    QSplitter,
    QFileDialog, 
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QComboBox,
    QTabBar,
    QStylePainter,
    QStyleOptionTab,
    QStyle,
    QAbstractItemView
)

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout, 
    QFormLayout
)

from PyQt5.QtGui import (
    QIcon
)

from server import RolloutConnection
import sys
import os

WINDOW_HEIGHT = 500
WINDOW_WIDTH = 600
WINDOW_TITLE = "Flash OTA"
class ServerInfo(QThread):
    finished = pyqtSignal(list)
    
    def run(self):
        deviceList = RolloutConnection.getDeviceList()
        self.finished.emit(deviceList)

class MainWindow(QMainWindow):
    '''The main windows of the application:'''
    UPDATE_TIMER = 30000
    
    def __init__(self, parent: None) -> None:
        super().__init__(parent)
        self.setWindowTitle(WINDOW_TITLE)
        self.setFixedHeight(WINDOW_HEIGHT)
        self.setFixedWidth(WINDOW_WIDTH)
        self.loadInitInfo()
        self.setupUI()
        self.timerUpdate = QTimer(self)
        self.timerUpdate.setInterval(self.UPDATE_TIMER)
        self.timerUpdate.timeout.connect(self.updateInfo)
        self.timerUpdate.start()
    
    def setupUI(self):
        self._addSWModuleWidget()
        self._addDistributionWidget()
        self._addDeviceWidget() 
        self.mainWidget = QTabWidget(self)
        self.mainWidget.setTabBar(TabBar(self.mainWidget))
        self.mainWidget.setTabPosition(QTabWidget.TabPosition.West)
        self.mainWidget.addTab(self._deviceWidget, "Device Info")
        self.mainWidget.addTab(self._swModuleWidget, "Software Module")
        self.mainWidget.addTab(self._distributionWidget, "Distribution Set")
        self.setCentralWidget(self.mainWidget)
    
    def updateInfo(self):
        self.serverUpdate = ServerInfo()
        self.serverUpdate.finished.connect(self.updateStatus)
        self.serverUpdate.start()
        
    def updateStatus(self, deviceList):
        self._deviceList = deviceList
        lastIndex = self._deviceTable.currentRow()
        self._deviceTable.updateView(self._deviceList)
        self.updateDeviceView(lastIndex)
    
    def loadInitInfo(self):
        self._targetTypeList = RolloutConnection.getTargetTypeList()
        self._deviceList = RolloutConnection.getDeviceList()
        self._swModuleList = RolloutConnection.getSWModuleList()
        self._distributionList = RolloutConnection.getDistributionList()
        
    
    def _addSWModuleWidget(self):
        self._swModuleWidget = QSplitter(Qt.Orientation.Vertical, self)
        
        # Add SW Module List
        self._topSWModuleWidget = QWidget()
        topLayout = QVBoxLayout()
        
        topHeaderLayout = QHBoxLayout()
        topHeaderLayout.addWidget(QLabel("<b>Software Module</b>"))
        topHeaderLayout.addStretch()
        self._addSWBtn = QToolButton()
        self._addSWBtn.setAutoRaise(True)
        self._addSWBtn.setIcon(QIcon("add.svg"))
        self._addSWBtn.clicked.connect(self.addSWModule)
        self._addSWBtn.setToolTip("Create new module")
        topHeaderLayout.addWidget(self._addSWBtn)
        
        topLayout.addLayout(topHeaderLayout)
        
        swModuleTableLabels = [("Name", "name"),
                               ("Version", "version"),
                               ("Last modified at", "lastModifiedAt")]
        self._swModuleTable = InfoTableWidget(labels=swModuleTableLabels, items=self._swModuleList)
        topLayout.addWidget(self._swModuleTable)
        self._topSWModuleWidget.setLayout(topLayout)
        
        self._swModuleWidget.addWidget(self._topSWModuleWidget)
        
        # Add Artifact Info
        self._bottomSWModuleWidget = QWidget()
        bottomLayout = QVBoxLayout()
        bottomHeaderLayout = QHBoxLayout()
        bottomHeaderLayout.addWidget(QLabel("<b>Artifacts</b>"))
        bottomHeaderLayout.addStretch()
        
        self._addArtifactBtn = QToolButton()
        self._addArtifactBtn.setAutoRaise(True)
        self._addArtifactBtn.setIcon(QIcon("add.svg"))
        self._addArtifactBtn.clicked.connect(self.addArtifacts)
        self._addArtifactBtn.setToolTip("Add new artifacts")
        bottomHeaderLayout.addWidget(self._addArtifactBtn)
        
        bottomLayout.addLayout(bottomHeaderLayout)
        artifactTableLabels = [("File name", "name"),
                       ("Size (B)", "size"), 
                       ("Created Date", "createdAt")]
        self._artifactTable = InfoTableWidget(labels=artifactTableLabels, items=[])
        
        bottomLayout.addWidget(self._artifactTable)
        self._bottomSWModuleWidget.setLayout(bottomLayout)
        self._swModuleWidget.addWidget(self._bottomSWModuleWidget)
        
        self._swModuleTable.currentRowChanged.connect(self.updateArtifactView)
    
    def _addDistributionWidget(self):
        self._distributionWidget = QSplitter(Qt.Orientation.Vertical, self)
        
        # Add Distribution List
        self._topDistributionWidget = QWidget()
        topLayout = QVBoxLayout()
        
        topHeaderLayout = QHBoxLayout()
        topHeaderLayout.addWidget(QLabel("<b>Distribution sets</b>"))
        topHeaderLayout.addStretch()
        self._addDistributionBtn = QToolButton()
        self._addDistributionBtn.setAutoRaise(True)
        self._addDistributionBtn.setIcon(QIcon("add.svg"))
        self._addDistributionBtn.clicked.connect(self.addDistribution)
        self._addDistributionBtn.setToolTip("Create new distribution")
        topHeaderLayout.addWidget(self._addDistributionBtn)
        
        topLayout.addLayout(topHeaderLayout)
        
        distributionTableLabels = [("Name", "name"),
                               ("Version", "version"),
                               ("Description", "description"),
                               ("Created at", "createdAt")]
        self._distributionTable = InfoTableWidget(labels=distributionTableLabels, items=self._distributionList)
        topLayout.addWidget(self._distributionTable)
        self._topDistributionWidget.setLayout(topLayout)
        self._distributionWidget.addWidget(self._topDistributionWidget)
        
        
        # Map SWModule Info
        self._bottomDistributionWidget = QWidget()
        bottomLayout = QVBoxLayout()
        bottomHeaderLayout = QHBoxLayout()
        bottomHeaderLayout.addWidget(QLabel("<b>Software Module Mapping</b>"))
        bottomHeaderLayout.addStretch()
        
        self._mappingSWBtn = QToolButton()
        self._mappingSWBtn.setAutoRaise(True)
        self._mappingSWBtn.setIcon(QIcon("add.svg"))
        self._mappingSWBtn.clicked.connect(self.mapSWModule)
        self._mappingSWBtn.setToolTip("Map new SW")
        bottomHeaderLayout.addWidget(self._mappingSWBtn)
        
        bottomLayout.addLayout(bottomHeaderLayout)
        
        
        mappingTableLabels = [("Name", "name"),
                               ("Version", "version")]
        self._mappingTable = InfoTableWidget(labels=mappingTableLabels, items=[])
        
        bottomLayout.addWidget(self._mappingTable)
        self._bottomDistributionWidget.setLayout(bottomLayout)
        self._distributionWidget.addWidget(self._bottomDistributionWidget)
        self._distributionTable.currentRowChanged.connect(self.updateMappingView)
    
    def _addDeviceWidget(self):
        self._deviceWidget = QSplitter(Qt.Orientation.Vertical, self)
        self._deviceWidget.setSizes([1, 1])
        
        # Add Device List
        self._topDeviceWidget = QWidget()
        topLayout = QVBoxLayout()
        
        topHeaderLayout = QHBoxLayout()
        topHeaderLayout.addWidget(QLabel("<b>Device Manager</b>"))
        topHeaderLayout.addStretch()
        self._addDeviceBtn = QToolButton()
        self._addDeviceBtn.setAutoRaise(True)
        self._addDeviceBtn.setIcon(QIcon("add.svg"))
        self._addDeviceBtn.clicked.connect(self.addDevice)
        self._addDeviceBtn.setToolTip("Create new device")
        topHeaderLayout.addWidget(self._addDeviceBtn)
        
        topLayout.addLayout(topHeaderLayout)
        
        deviceTableLabels = [("Name", "name"),
                              ("Description", "description"),
                              ("Status", "status"), 
                              ("Last polling", "lastPollAt")]

        self._deviceTable = InfoTableWidget(labels=deviceTableLabels, items=self._deviceList)
        topLayout.addWidget(self._deviceTable)
        
        self._flashBtn = QPushButton(QIcon("flash.png"), "Start Flashing")
        self._flashBtn.clicked.connect(self.triggerFlash)
        topLayout.addWidget(self._flashBtn)
        
        self._topDeviceWidget.setLayout(topLayout)
        self._deviceWidget.addWidget(self._topDeviceWidget)
        
        # Device detail Info
        self._topDeviceWidget = QWidget()
        bottomLayout = QVBoxLayout()
        self._deviceInfoWidget = DeviceInfoWidget()
        bottomLayout.addWidget(self._deviceInfoWidget)
        
        self._topDeviceWidget.setLayout(bottomLayout)
        self._deviceWidget.addWidget(self._topDeviceWidget)
        self._deviceTable.currentRowChanged.connect(self.updateDeviceView)
    
    def updateDeviceView(self, curRow: int):
        if curRow != -1:
            self._deviceInfoWidget.updateView(self._deviceList[curRow])
        else:
            self._artifactTable.updateView([])    
            
    def updateArtifactView(self, curRow: int):
        if curRow != -1:
            self._artifactTable.updateView(self._swModuleList[curRow]["artifacts"])
        else:
            self._artifactTable.updateView([])
    
    def updateMappingView(self, curRow: int):
        if curRow != -1:
            self._mappingTable.updateView(self._distributionList[curRow]["swModules"])
        else:
            self._mappingTable.updateView([])
            
    def addDevice(self):
        dlg = DeviceDlg()
        if dlg.exec():
            deviceInfo = dlg.getDeviceInfo()
            if deviceInfo["securityToken"].strip() == "":
                deviceInfo.pop("securityToken")
        else:
            return
        
        RolloutConnection.createDevice(deviceInfo)
        self._deviceList = RolloutConnection.getDeviceList()
        self.updateDeviceView(-1)
        self._deviceTable.updateView(self._deviceList)
        
    def addSWModule(self):
        dlg = SWModuleDlg()
        if dlg.exec():
            swInfo = dlg.getSWModuleInfo()

        else:
            return
        RolloutConnection.createSWModule(swInfo)
        self._swModuleList = RolloutConnection.getSWModuleList()
        self.updateArtifactView(-1)
        self._swModuleTable.updateView(self._swModuleList)
    
    def addDistribution(self):
        dlg = DistributionDlg()
        if dlg.exec():
            distributionInfo = dlg.getDistributionInfo()
            distributionInfo["type"] = "app"
        else:
            return
        RolloutConnection.createDistribution(distributionInfo)
        self._distributionList = RolloutConnection.getDistributionList()
        self.updateMappingView(-1)
        self._distributionTable.updateView(self._distributionList)
    
    def triggerFlash(self):
        deviceNameList = [device["name"] for device in self._deviceList]
        distributionList = [f"{distribution['name']} v{distribution['version']}" for distribution in self._distributionList]
        dlg = FlashDeviceDlg(deviceNameList, distributionList)
        if dlg.exec():
            flashInfo = dlg.getFlashInfo()
        else:
            return
        targetId = self._deviceList[flashInfo["targetIndex"]]["id"]
        assignedDistribution = self._distributionList[flashInfo["distributionIndex"]]["id"]
        RolloutConnection.assginDistribution(targetId, assignedDistribution)
        self._deviceList = RolloutConnection.getDeviceList()
        self.updateDeviceView(-1)
        self._deviceTable.updateView(self._deviceList)
    
    def mapSWModule(self):
        swModuleList = [f"{module['name']} version {module['version']}" for module in self._swModuleList]
        dlg = MappingDlg(swModuleList)
        curDistributionIndex = self._distributionTable.currentRow()
        if dlg.exec():
            mappingIdx = dlg.getMappingInfo()
        else:
            return
        RolloutConnection.mapDistribution(self._distributionList[curDistributionIndex]["id"], self._swModuleList[mappingIdx]["id"])
        self._distributionList = RolloutConnection.getDistributionList()
        self.updateMappingView(curDistributionIndex)
    
    def addArtifacts(self):
        dlg = QFileDialog()
        dlg.setDirectory(os.getcwd())
        dlg.setFileMode(QFileDialog.FileMode.ExistingFiles)
        curSWIndex = self._swModuleTable.currentRow()
        if curSWIndex != -1 and dlg.exec():
            filepaths = dlg.selectedFiles()
        else:
            return
        
        for filepath in filepaths:
            RolloutConnection.uploadArtifact(self._swModuleList[curSWIndex]["id"], filepath)
        self._swModuleList = RolloutConnection.getSWModuleList()
        self.updateArtifactView(curSWIndex)
    
class DeviceInfoWidget(QWidget):
    '''Device Info widget.
    Show the status and detailed information of the device
    '''
    def __init__(self, deviceInfo=None):
        super().__init__()
        self._mainLayout = QFormLayout()
        self.controllerInfo = QLabel("")
        self.tokenInfo = QLabel("")
        self.statusInfo = QLabel("")
        self.installedDSInfo = QLabel("")
        self.installedDSTimeInfo = QLabel("")
        self.assignedDSInfo = QLabel("")
        self.autoConfirmInfo = QLabel("")
        self._mainLayout.addRow("<b>Device Info</b>", None)
        self._mainLayout.addRow("Status:", self.statusInfo)
        self._mainLayout.addRow("Device ID:", self.controllerInfo)
        self._mainLayout.addRow("Token:", self.tokenInfo)   
        self._mainLayout.addRow("Auto Confirm:", self.autoConfirmInfo)
        self._mainLayout.addRow("Assigned DS:", self.assignedDSInfo)
        self._mainLayout.addRow("Installed DS:", self.installedDSInfo)
        self._mainLayout.addRow("Installed at:", self.installedDSTimeInfo)
        self.setLayout(self._mainLayout)
        self.updateView(deviceInfo)
    
    def updateView(self, deviceInfo: dict[(str, str)]=None):
        if deviceInfo:
            self.controllerInfo.setText(deviceInfo["id"])
            self.tokenInfo.setText(deviceInfo["token"])
            self.statusInfo.setText(deviceInfo["status"].title())
            self.installedDSInfo.setText(deviceInfo["installedDS"])
            self.installedDSTimeInfo.setText(deviceInfo["installedAt"])
            self.autoConfirmInfo.setText(deviceInfo["autoConfirm"])
            self.assignedDSInfo.setText(deviceInfo["assignedDS"])
        else:
            self.controllerInfo.setText("")
            self.tokenInfo.setText("")
            self.statusInfo.setText("")
            self.installedDSInfo.setText("")
            self.installedDSTimeInfo.setText("")
            self.autoConfirmInfo.setText("")
            self.assignedDSInfo.setText("")

class InfoTableWidget(QTableWidget):
    ''' Information Table widget.
    Show the information of the data in form of table
    '''
    currentRowChanged = pyqtSignal(int)
    def __init__(self, labels: list[str], items: list[dict]):
        super().__init__()
        self._labels = labels
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels([label[0] for label in self._labels])
        self.horizontalHeader().setStyleSheet("font-weight: bold;")
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.updateView(items)
        self.currentCellChanged.connect(self._checkRowChanged)
    
    def _checkRowChanged(self, curRow, curCol, prevRow, prevCol):
        if curRow != prevRow:
            self.currentRowChanged.emit(curRow)
            
    def updateView(self, items:list[dict]):
        self.clearContents()
        self.setRowCount(len(items)) 
        self.horizontalHeader().setStretchLastSection(True)
        for row, item in enumerate(items):
            for col, label in enumerate(self._labels):
                self.setItem(row, col, QTableWidgetItem(item[label[1]]))
        self.resizeColumnsToContents()        
    
class TabBar(QTabBar):
    def tabSizeHint(self, index):
        s = QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabShape, opt)
            painter.save()

            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r

            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.ControlElement.CE_TabBarTabLabel, opt)
            painter.restore()

class SWModuleDlg(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create new SW module")
        self._mainLayout = QVBoxLayout()
        
        layout = QFormLayout()
        self.nameInput = QLineEdit("")
        self.versionInput = QLineEdit("")
        self.vendorInput = QLineEdit("")
        self.descriptionInput = QPlainTextEdit ("")
        layout.addRow("Name", self.nameInput)
        layout.addRow("Version", self.versionInput)
        layout.addRow("Vendor", self.vendorInput)
        layout.addRow("Description", self.descriptionInput)
        
        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply
                                       |QDialogButtonBox.StandardButton.Close)
        self._mainLayout.addLayout(layout)
        self._mainLayout.addWidget(self.btnBox)
        self.btnBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.writeSWINfo)
        self.btnBox.rejected.connect(self.reject)

        self.setLayout(self._mainLayout)
    
    def writeSWINfo(self):
        self.swInfo = {}
        self.swInfo["name"] = self.nameInput.text()
        self.swInfo["version"] = self.versionInput.text()
        self.swInfo["vendor"] = self.vendorInput.text()
        self.swInfo["description"] = self.descriptionInput.toPlainText()
        self.accept()

    def getSWModuleInfo(self):
        return self.swInfo

class DistributionDlg(QDialog):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create new distribution")
        self._mainLayout = QVBoxLayout()
        
        layout = QFormLayout()
        self.nameInput = QLineEdit("")
        self.versionInput = QLineEdit("")
        self.descriptionInput = QPlainTextEdit ("")
        layout.addRow("Name", self.nameInput)
        layout.addRow("Version", self.versionInput)
        layout.addRow("Description", self.descriptionInput)
        
        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply
                                       |QDialogButtonBox.StandardButton.Close)
        self._mainLayout.addLayout(layout)
        self._mainLayout.addWidget(self.btnBox)
        self.btnBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.writeDistributionInfo)
        self.btnBox.rejected.connect(self.reject)

        self.setLayout(self._mainLayout)
    
    def writeDistributionInfo(self):
        self.distributionInfo = {}
        self.distributionInfo["name"] = self.nameInput.text()
        self.distributionInfo["version"] = self.versionInput.text()
        self.distributionInfo["description"] = self.descriptionInput.toPlainText()
        self.accept()

    def getDistributionInfo(self):
        return self.distributionInfo
    
class FlashDeviceDlg(QDialog):
    
    def __init__(self, deviceList, distributionList):
        super().__init__()
        self.setWindowTitle("Create new device")
        self._mainLayout = QVBoxLayout()
        
        layout = QFormLayout()
        self.targetInput = QComboBox()
        self.targetInput.addItems(deviceList)
        self.targetInput.setCurrentIndex(0)
        self.distributionInput = QComboBox()
        self.distributionInput.addItems(distributionList)
        self.distributionInput.setCurrentIndex(0)
        
        layout.addRow("Target device", self.targetInput)
        layout.addRow("Assigned Distribution", self.distributionInput)
    
        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply
                                       |QDialogButtonBox.StandardButton.Close)
        self._mainLayout.addLayout(layout)
        self._mainLayout.addWidget(self.btnBox)
        self.btnBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.writeFlashInfo)
        self.btnBox.rejected.connect(self.reject)
        self.setLayout(self._mainLayout)
    
    def writeFlashInfo(self):
        self.flashInfo = {}
        self.flashInfo["targetIndex"] = self.targetInput.currentIndex()
        self.flashInfo["distributionIndex"] = self.distributionInput.currentIndex()
        self.accept()

    def getFlashInfo(self):
        return self.flashInfo
    
class MappingDlg(QDialog):
    
    def __init__(self, swModuleList):
        super().__init__()
        self.setWindowTitle("Mapping software module")
        self._mainLayout = QVBoxLayout()
        
        layout = QFormLayout()
        self.mappingInput = QComboBox()
        self.mappingInput.addItems(swModuleList)
        self.mappingInput.setCurrentIndex(0)
        
        layout.addRow("SW Module", self.mappingInput)
    
        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply
                                       |QDialogButtonBox.StandardButton.Close)
        self._mainLayout.addLayout(layout)
        self._mainLayout.addWidget(self.btnBox)
        self.btnBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.writeMappingInfo)
        self.btnBox.rejected.connect(self.reject)
        self.setLayout(self._mainLayout)
    
    def writeMappingInfo(self):
        self.mappingId = self.mappingInput.currentIndex()
        self.accept()

    def getMappingInfo(self) -> int:
        return self.mappingId

class DeviceDlg(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create new device")
        self._mainLayout = QVBoxLayout()
        
        layout = QFormLayout()
        self.controllerInput = QLineEdit("")
        self.nameInput = QLineEdit("")
        self.tokenInput = QLineEdit("")
        self.descriptionInput = QPlainTextEdit ("")
        layout.addRow("ControllerID", self.controllerInput)
        layout.addRow("Name", self.nameInput)
        layout.addRow("Token", self.tokenInput)
        layout.addRow("Description", self.descriptionInput)
        
        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply
                                       |QDialogButtonBox.StandardButton.Close)
        self._mainLayout.addLayout(layout)
        self._mainLayout.addWidget(self.btnBox)
        self.btnBox.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.writeDeviceInfo)
        self.btnBox.rejected.connect(self.reject)

        self.setLayout(self._mainLayout)
    
    def writeDeviceInfo(self):
        self.deviceInfo = {}
        self.deviceInfo["name"] = self.nameInput.text()
        self.deviceInfo["controllerId"] = self.controllerInput.text()
        self.deviceInfo["securityToken"] = self.tokenInput.text()
        self.deviceInfo["description"] = self.descriptionInput.toPlainText()
        self.accept()

    def getDeviceInfo(self) ->dict[(str, str)]:
        return self.deviceInfo
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(None)
    window.show()
    sys.exit(app.exec())
