
from PyQt4.QtCore import SIGNAL, SLOT, QSignalMapper, QSize, Qt
from PyQt4.QtGui import *
from ui_main_window import Ui_MainWindow

from server_window import ServerWindow
from user_window import UserWindow

class MainWindow(QMainWindow, Ui_MainWindow):
	USERNAMES = ["Alice", "Bob", "Carol", "Dave", "Eve", "Marvin", "Oscar", "Peggy", "Victor", "Ted"]
	
	def __init__(self):
		super(MainWindow, self).__init__()
		self.setupUi(self)
		self.windowMapper = QSignalMapper(self)
		self.connect(self.windowMapper, SIGNAL("mapped(QWidget*)"), self.setActiveSubWindow)
		self.connect(self.menuWindow, SIGNAL("aboutToShow()"), self.updateWindowMenu)
		self.updateWindowMenu()
		self.connect(self.actionAdd_user, SIGNAL("triggered()"), self.addUser)
		
		self.srv = ServerWindow()
		self.connect(self.srv, SIGNAL("userNameChange(int,QString)"), self.__userNameChange)
		self.addSubWindow(self.srv)
		
		self.users = []
		self.next_user_name = 0
		
		self.opsPendingMapper = QSignalMapper(self)
		self.connect(self.opsPendingMapper, SIGNAL("mapped(int)"), self.__operationsPending)
	
	def __operationsPending(self, id):
		pass
	
	def __userNameChange(self, id, name):
		self.users[id].setUserName(name)
	
	def addUser(self):
		user_name = self.USERNAMES[self.next_user_name % 10]
		if self.next_user_name / 10 > 0:
			user_name += str(self.next_user_name / 10)
		self.next_user_name += 1
		user = UserWindow(user_name)
		self.opsPendingMapper.setMapping(user, len(self.users))
		self.connect(user, SIGNAL("operationsPending()"), self.opsPendingMapper, SLOT("map()"))
		self.addSubWindow(user).show()
		self.users.append(user)
		self.srv.registerUser(user_name)
	
	def addSubWindow(self, w, flags = None):
		sz = w.size() + QSize(8, 12)
		if flags == None:
			mdi = self.mdiArea.addSubWindow(w)
		else:
			mdi = self.mdiArea.addSubWindow(w, flags)
		mdi.resize(sz)
		return mdi
	
	def setActiveSubWindow(self, w):
		self.mdiArea.setActiveSubWindow(w)

	def updateWindowMenu(self):
		self.menuWindow.clear()
		self.menuWindow.addAction(self.actionClose)
		self.menuWindow.addAction(self.actionClose_all)
		self.menuWindow.addSeparator()
		self.menuWindow.addAction(self.actionTile)
		self.menuWindow.addAction(self.actionCascade)
		self.menuWindow.addSeparator()
		self.menuWindow.addAction(self.actionNext_window)
		self.menuWindow.addAction(self.actionPrevious_window)
		
		windows = self.mdiArea.subWindowList()
		if len(windows) > 0:
			self.menuWindow.addSeparator()
		
		for window in windows:
			action = self.menuWindow.addAction(window.windowTitle())
			action.setCheckable(True)
			action.setChecked(window == self.mdiArea.activeSubWindow())
			self.connect(action, SIGNAL("triggered()"), self.windowMapper, SLOT("map()"))
			self.windowMapper.setMapping(action, window)
