
from PyQt4.QtCore import Qt, QSignalMapper, SIGNAL, SLOT
from PyQt4.QtGui import *

from ui_server_window import Ui_ServerWindow

class LagSettingDelegate(QStyledItemDelegate):
	
	def displayText(self, value, locale):
		return "%d ms" % (value.toInt()[0])
	
	def createEditor(self, parent, option, index):
		spb = QSpinBox(parent)
		spb.setSuffix(" ms")
		spb.setMaximum(10000)
		spb.setSingleStep(500)
		return spb

class ServerWindow(QWidget, Ui_ServerWindow):
	
	def __init__(self, parent = None):
		super(ServerWindow, self).__init__(parent)
		self.setupUi(self)
		self.tblUsers.setColumnCount(3)
		self.tblUsers.setHorizontalHeaderLabels(["User ID", "Lag", "Block"])
		self.delegate1 = LagSettingDelegate()
		self.tblUsers.setItemDelegateForColumn(1, self.delegate1)
		self.blockMapper = QSignalMapper(self)
		self.connect(self.blockMapper, SIGNAL("mapped(int)"), self.blockUser)
		self.connect(self.tblUsers, SIGNAL("cellChanged(int,int)"), self.__cellChanged)
	
	def __cellChanged(self, row, column):
		if column == 0:
			name = self.tblUsers.item(row, column).text()
			self.emit(SIGNAL("userNameChange(int,QString)"), row, name)
	
	def closeEvent(self, event):
		event.ignore()
		self.parent().setWindowState(Qt.WindowMinimized)
	
	def userBlocked(self, id):
		return self.tblUsers.cellWidget(id, 2).isChecked()
	
	def blockUser(self, id):
		pb = self.tblUsers.cellWidget(id, 2)
		print "Block"
	
	def registerUser(self, id):
		rc = self.tblUsers.rowCount()
		self.tblUsers.setRowCount(rc + 1)
		item = QTableWidgetItem(id)
		self.tblUsers.setItem(rc, 0, item)
		self.tblUsers.setItem(rc, 1, QTableWidgetItem("0"))
		pb = QPushButton()
		pb.setText("Block")
		pb.setCheckable(True)
		self.connect(pb, SIGNAL("clicked()"), self.blockMapper, SLOT("map()"))
		self.blockMapper.setMapping(pb, rc)
		self.tblUsers.setCellWidget(rc, 2, pb)
