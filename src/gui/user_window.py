
from PyQt4.QtCore import SIGNAL, QAbstractTableModel, QModelIndex, Qt, QVariant
from PyQt4.QtGui import *

from core.operations import OpBuilder
from core.diffop_generator import generateDiffOps
from ui_user_window import Ui_UserWindow

class OperationsModel(QAbstractTableModel):
	HEADER = ["Operation", "Blip", "Index", "Property"]
	
	def __init__(self, builder, parent = None):
		super(OperationsModel, self).__init__(parent)
		self.builder = builder
		self.builder.addEvent("beforeOperationsInserted", self.__beforeOperationsInserted)
		self.builder.addEvent("afterOperationsInserted", self.__afterOperationsInserted)
		self.builder.addEvent("beforeOperationsRemoved", self.__beforeOperationsRemoved)
		self.builder.addEvent("afterOperationsRemoved", self.__afterOperationsRemoved)
	
	def __del__(self):
		self.builder.removeEvent("beforeOperationsInserted", self.__beforeOperationsInserted)
		self.builder.removeEvent("afterOperationsInserted", self.__afterOperationsInserted)
		self.builder.removeEvent("beforeOperationsRemoved", self.__beforeOperationsRemoved)
		self.builder.removeEvent("afterOperationsRemoved", self.__afterOperationsRemoved)
	
	def rowCount(self, parent = QModelIndex()):
		return len(self.builder.operations)
	
	def columnCount(self, parent = QModelIndex()):
		return 4
	
	def data(self, index, role = Qt.DisplayRole):
		if not role == Qt.DisplayRole:
			return QVariant()
		
		op = self.builder.operations[index.row()]
		
		if index.column() == 0:
			return QVariant(op.type)
		elif index.column() == 1:
			return QVariant(op.blip_id)
		elif index.column() == 2:
			return QVariant(op.index)
		elif index.column() == 3:
			return QVariant(repr(op.property))
		
		return QVariant()

	def headerData(self, section, orientation, role = Qt.DisplayRole):
		if not role == Qt.DisplayRole:
			return QVariant()
		
		if orientation == Qt.Horizontal:
			return QVariant(self.HEADER[section])
		else:
			return QVariant(section)
	
	def __beforeOperationsInserted(self, args):
		self.beginInsertRows(QModelIndex(), args["start"], args["end"])
	
	def __afterOperationsInserted(self, args):
		self.endInsertRows()
	
	def __beforeOperationsRemoved(self, args):
		self.beginRemoveRows(QModelIndex(), args["start"], args["end"])
	
	def __afterOperationsRemoved(self, args):
		self.endRemoveRows()

class UserWindow(QWidget, Ui_UserWindow):
	def __init__(self, name, parent = None):
		super(UserWindow, self).__init__(parent)
		self.setupUi(self)
		self.setUserName(name)
		self.connect(self.rootBlip, SIGNAL("textChanged()"), self.__rootBlipChanged)
		self.oldText = ""
		self.builder = OpBuilder("wave", "wavelet")
		self.model = OperationsModel(self.builder, self)
		self.tblOperations.setModel(self.model)
		self.builder.addEvent("afterOperationsInserted", self.__afterOperationsInserted)
		
		self.__pendingOps = []
		self.__version = 0
	
	def setUserName(self, name):
		self.setWindowTitle("User \"%s\"" % (name))

	def __rootBlipChanged(self):
		newText = unicode(self.rootBlip.toPlainText())
		generateDiffOps(self.builder, "root_blip", self.oldText, newText)
		self.oldText = newText

	def closeEvent(self, event):
		event.ignore()
		self.parent().setWindowState(Qt.WindowMinimized)
	
	def version(self):
		return self.__version

	def pendingOperations(self):
		return self.__pendingOps

	def applyOperations(self, ops, version):
		self.__version = version
		self.lblVersion.setText("v%d" % version)

	def acknowledge(self, version):
		self.__version = version
		self.lblVersion.setText("v%d" % version)
		if len(self.builder.operations) > 0:
			self.__pendingOps = self.builder.fetch()
			self.emit(SIGNAL("operationsPending()"))
		else:
			self.__pendingOps = []

	def __afterOperationsInserted(self, args):
		if len(self.__pendingOps) == 0:
			self.__pendingOps = self.builder.fetch()
			self.emit(SIGNAL("operationsPending()"))
