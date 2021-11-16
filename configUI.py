import time
import json
from typing import Dict, List, Tuple
import urllib.request as http
from datetime import datetime
from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import QAction, QInputDialog

from PyQt5.QtWidgets import QApplication, QLineEdit, QDialogButtonBox, QFormLayout, QDialog, QMessageBox
from typing import List

config = mw.addonManager.getConfig(__name__)

class InputDialog(QDialog):
    def __init__(self, labels:List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration Kanji Stats")
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout = QFormLayout(self)
        
        self.inputs = []
        for lab in labels:
            self.inputs.append(QLineEdit(self))
            layout.addRow(lab, self.inputs[-1])
        
        layout.addWidget(buttonBox)
        
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
    
    def getInputs(self):
        return tuple(input.text() for input in self.inputs)
        
    def setInput(self, inputid: int, txt: str):
        self.inputs[inputid].setText(txt)

def configurationKanjiStats():
    dialog = InputDialog(labels=["Type de note","Champs sources(séparés par une virgule)"])   
    dialog.setInput(0,config['noteTypes'])
    srcFields = ','.join(config['srcFields'])
    dialog.setInput(1,srcFields)
            
    if dialog.exec_() :
        inputs = dialog.getInputs()
        if inputs[0] :
            config["noteTypes"] = str(inputs[0]).strip()
            mw.addonManager.writeConfig(__name__, config)
        if inputs[1] :
            config["srcFields"] = str(inputs[1]).strip().split()
            mw.addonManager.writeConfig(__name__, config)

# Create a new menu item
action = QAction("Configuration Kanji Stats", mw)
qconnect(action.triggered, configurationKanjiStats)
mw.form.menuTools.addAction(action)