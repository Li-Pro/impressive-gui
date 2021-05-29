from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from PIL  import Image, ImageChops
from PIL.ImageQt  import ImageQt

from io  import BytesIO
# import threading

class _PageThumbnail(QListWidget):
	def __init__(self):
		super().__init__()
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

class _ImageView(QLabel):
	def __init__(self):
		super().__init__()
		self.pixmap = None
		self.currentSize = QSize(600, 450)
	
	def __resetSize(self, viewRect):
		self.currentSize = viewRect
		
		imgSize = self.pixmap.size()
		ratio = min(viewRect.width()/imgSize.width(), viewRect.height()/imgSize.height())
		viewW = int(imgSize.width() * ratio)
		viewH = int(imgSize.height() * ratio)
		
		scaledImg = self.pixmap.scaled(viewW, viewH, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		## gridlayout + spacer
		# centerTrans = QTransform.fromTranslate((viewRect.width() - imgSize.width()) / 2,
												# (viewRect.height() - imgSize.height()) / 2)
		# centerImg = scaledImg.transformed(centerTrans)
		# self.setPixmap(centerImg)
		self.setPixmap(scaledImg)
	
	def setImage(self, pixmap):
		self.pixmap = pixmap
		self.__resetSize(self.currentSize)
	
	def resizeEvent(self, event):
		if self.pixmap == None:
			return
		
		self.__resetSize(event.size())

class _PageOptionField(QListView):
	def __init__(self, optionSetting):
		super().__init__()
		self.optionSetting = optionSetting
		self.listLayout = QVBoxLayout(self)
		
		self.listTitle = QLabel()
		self.listTitle.setText('Page options')
		
		titleFont = self.listTitle.font()
		titleFont.setUnderline(True)
		self.listTitle.setFont(titleFont)
		
		self.formLayout = QFormLayout()
		self.optSkip = self.addCheckbox('skip this slide')
		self.optTransition = self.addCombobox('transition', optionSetting['transition_selection'])
		
		self.listLayout.addWidget(self.listTitle, 1, Qt.AlignTop)
		self.listLayout.addLayout(self.formLayout, 9)
	
	def setOptions(self, options):
		self.optSkip.setCheckState(Qt.Checked  if options['skip'] else Qt.Unchecked)
		
		transition = options['transition']
		allTransition = self.optionSetting['transition_selection']
		self.optTransition.setCurrentIndex(allTransition.index(transition)  if transition != "" else -1)
	
	def getOptions(self):
		options = {}
		
		options['skip'] = (self.optSkip.checkState() == Qt.Checked)
		
		allTransition = self.optionSetting['transition_selection']
		transitionIdx = self.optTransition.currentIndex()
		options['transition'] = allTransition[transitionIdx]  if transitionIdx >= 0 else ""
		
		return options
	
	def addCheckbox(self, name, onUpdate=None):
		opt = QCheckBox()
		
		if callable(onUpdate):
			opt.stateChanged.connect(onUpdate)
		
		opt.setCheckState(Qt.Unchecked)
		self.formLayout.addRow(name, opt)
		return opt
	
	def addCombobox(self, name, optList=[], onUpdate=None):
		opt = QComboBox()
		for optText in optList:
			opt.addItem(optText)
		
		if callable(onUpdate):
			opt.currentIndexChanged.connect(onUpdate)
		
		opt.setCurrentIndex(-1)
		self.formLayout.addRow(name, opt)
		return opt

class _EditField(QFrame):
	def __init__(self, optionSetting):
		super().__init__()
		self.setFrameStyle(QFrame.StyledPanel)
		
		self.fieldLayout = QHBoxLayout(self)
		self.optTypeList = QListWidget()
		
		self.pageOpt = _PageOptionField(optionSetting)
		
		self.fieldLayout.setSpacing(2)
		self.fieldLayout.setContentsMargins(2, 2, 2, 2)
		self.fieldLayout.addWidget(self.optTypeList, 5)
		self.fieldLayout.addWidget(self.pageOpt, 5)
	
	def getCurrentOptions(self):
		return self.pageOpt.getOptions()
	
	def resetOptions(self, options):
		self.pageOpt.setOptions(options)

class _EditorFormView(QWidget):
	def __init__(self, optionSetting):
		super().__init__()
		self.pageOptions = {}
		self.pageImages = []
		self.currentPage = -1
		
		self.formLayout = QGridLayout(self)
		
		self.timgList = _PageThumbnail()
		self.timgList.currentRowChanged.connect(self.onCurrentRowChanged)
		
		self.slideView = _ImageView()
		
		self.editField = _EditField(optionSetting)
		
		self.formLayout.addWidget(self.timgList, 0, 0, 2, 1)
		self.formLayout.addWidget(self.slideView, 0, 1)
		self.formLayout.addWidget(self.editField, 1, 1)
		
		self.formLayout.setRowStretch(0, 3)
		self.formLayout.setRowStretch(1, 1)
		self.formLayout.setColumnMinimumWidth(0, 150)
		self.formLayout.setColumnStretch(0, 1)
		self.formLayout.setColumnStretch(1, 7)
	
	def saveCurrentPage(self):
		if self.currentPage >= 0:
			self.pageOptions[self.currentPage] = self.editField.getCurrentOptions()
	
	def setPageOptions(self, pageOptions):
		self.pageOptions = pageOptions
	
	def switchPage(self, page):
		self.saveCurrentPage()
		
		self.currentPage = page
		options = self.pageOptions[page]
		self.editField.resetOptions(options)
	
	@Slot()
	def onCurrentRowChanged(self, currentRow):
		if currentRow >= 0:
			self.viewPage(currentRow)
		
		self.switchPage(currentRow)
	
	def newTimgItem(self, pixmap):
		item = QListWidgetItem()
		item.setIcon(QIcon(pixmap))
		return item
	
	def viewPage(self, row):
		self.slideView.setImage(self.pageImages[row])
	
	def addPage(self, pixmap, size):
		self.pageImages.append(pixmap)
		
		# broke for different page sizes
		width, height = pixmap.size().width(), pixmap.size().height()
		self.timgList.setIconSize(QSize(130, height*130//width))
		
		item = self.newTimgItem(pixmap)
		self.timgList.addItem(item)
	
	def translateUi(self, lang='en'):
		return

class Ui_editor(object):
	def setupUi(self, editor, optionSetting):
		if not editor.objectName():
			editor.setObjectName(u"editor")
		
		editor.resize(800, 600)
		self.mainWindow = editor
		
		self.mainView = QWidget(editor)
		self.mainView.setObjectName(u"mainView")
		self.mainLayout = QVBoxLayout(self.mainView)
		self.viewport = QStackedWidget()
		self.mainLayout.addWidget(self.viewport)
		editor.setCentralWidget(self.mainView)
		
		self.menubar = QMenuBar(editor)
		self.menubar.setObjectName(u"menubar")
		self.menubar.setGeometry(QRect(0, 0, 800, 22))
		self.menuFile = QMenu(self.menubar)
		self.menuFile.setObjectName(u"menuFile")
		editor.setMenuBar(self.menubar)
		
		self.menubar.addAction(self.menuFile.menuAction())

		self.editFormView = _EditorFormView(optionSetting)
		self.viewport.addWidget(self.editFormView)
		
		self.viewport.setCurrentWidget(self.editFormView)
		
		self.translateUi()
	
	def translateUi(self, lang='en'):
		self.mainWindow.setWindowTitle('Impressive GUI')
		self.menuFile.setTitle('File')
		self.editFormView.translateUi(lang)

class EditorView(QMainWindow):
	def __init__(self, optionSetting):
		super().__init__()
		self.ui = Ui_editor()
		self.ui.setupUi(self, optionSetting)
	
	def loadOptions(self, options):
		self.ui.editFormView.setPageOptions(options)
	
	def getOptions(self):
		return self.ui.editFormView.pageOptions
	
	def addPage(self, img, size):
		buf = BytesIO()
		Image.frombytes('RGB', size, img).save(buf, format='png')
		image = QImage.fromData(buf.getvalue(), format='png')
		pixmap = QPixmap.fromImage(image)
		
		self.ui.editFormView.addPage(pixmap, size)
	
	def closeEvent(self, event):
		self.ui.editFormView.saveCurrentPage()
		super().closeEvent(event)