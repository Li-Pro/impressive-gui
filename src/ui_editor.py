from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from PIL  import Image, ImageChops
from PIL.ImageQt  import ImageQt

from io  import BytesIO
from pathlib  import Path
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
		self.optTransition = self.addCombobox('transition in', optionSetting['transition_selection'])
		
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
		self.timgList.setCurrentRow(0)
	
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
		self.ui.editFormView.saveCurrentPage()
		return self.ui.editFormView.pageOptions
	
	def addPage(self, img, size):
		buf = BytesIO()
		Image.frombytes('RGB', size, img).save(buf, format='png')
		image = QImage.fromData(buf.getvalue(), format='png')
		pixmap = QPixmap.fromImage(image)
		
		self.ui.editFormView.addPage(pixmap, size)
	
	def closeEvent(self, event):
		super().closeEvent(event)
	
	def popupMessage(self, msg, title='info'):
		QMessageBox.information(self, title, msg)

class FileListModel(QAbstractTableModel):
	def __init__(self):
		super().__init__()
		
		self.fileList = []
	
	def rowCount(self, parent=QModelIndex()):
		return len(self.fileList)
	
	def columnCount(self, parent=QModelIndex()):
		return 3
	
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return ["Name", "Type", "Path"][section]
		
		return None
	
	def data(self, index, role=Qt.DisplayRole):
		if role == Qt.DisplayRole:
			return self.fileList[index.row()][index.column()]
		
		return None
	
	def addFileItem(self, filename, filepath, filetype, realpath):
		self.fileList.append( [filename, filetype, filepath, realpath] )
		
		row = len(self.fileList) - 1
		self.headerDataChanged.emit(Qt.Vertical, row, row)
	
	def removeItems(self, mask):
		rowlen = len(self.fileList)
		
		newFileList = []
		for i in range(rowlen):
			if not i in mask:
				newFileList.append(self.fileList[i])
		
		self.fileList = newFileList
		self.headerDataChanged.emit(Qt.Vertical, 0, rowlen - 1)

class FileListView(QTableView):
	@classmethod
	def shrinkPath(cls, path):
		maxPathLen = 30
		return path
	
	def __init__(self):
		super().__init__()
		
		self.tableModel = FileListModel()
		self.setModel(self.tableModel)
		
		self.setSelectionBehavior(self.SelectRows)
		self.horizontalHeader().setStretchLastSection(True)
		
		self.extFilter = {}
	
	def addFile(self, file):
		targetpath = Path(file).resolve()
		
		if targetpath.is_file():
			filename = str(targetpath.name)
			fileext = filename.split('.')[-1]  if ('.' in filename) else ''
			
			filepath = self.shrinkPath(str(targetpath.parent))
			filetype = self.extFilter.get(fileext, 'Unknown')
			
			self.tableModel.addFileItem(filename, filepath, filetype, targetpath)
		elif targetpath.is_dir():
			filename = str(targetpath.name)
			filepath = self.shrinkPath(str(targetpath.parent))
			filetype = 'Folder'
			
			self.tableModel.addFileItem(filename, filepath, filetype, targetpath)
	
	def getFiles(self):
		filelist = []
		for fname, fpath, ftype, target in self.tableModel.fileList:
			filelist.append(str(target))
		
		return filelist
	
	def setFilters(self, filters):
		newfilter = {}
		for ftype, fexts in filters.items():
			for fext in fexts:
				newfilter[fext] = ftype
		
		self.extFilter = newfilter
	
	@Slot()
	def onOpenFile(self):
		files, fileFilter = QFileDialog.getOpenFileNames(self, "Add Files")
		
		for file in files:
			self.addFile(file)
	
	@Slot()
	def onOpenDir(self):
		path = QFileDialog.getExistingDirectory(self, "Add Directory")
		
		if path:
			self.addFile(path)
	
	@Slot()
	def onRemove(self):
		idxs = set()
		for idx in self.selectedIndexes():
			idxs.add(idx.row())
		
		self.tableModel.removeItems(idxs)

class Ui_openfile(object):
	def setupUi(self, view):
		self.view = view
		self.view.resize(560, 420)
		
		# self.tableCaption = QLabel()
		self.table = FileListView()
		
		self.btnOpenFile = QPushButton()
		self.btnOpenFile.clicked.connect(self.table.onOpenFile)
		
		self.btnOpenDir = QPushButton()
		self.btnOpenDir.clicked.connect(self.table.onOpenDir)
		
		self.btnRemove = QPushButton()
		self.btnRemove.clicked.connect(self.table.onRemove)
		
		self.layout = QGridLayout()
		self.tableLayout = QVBoxLayout()
		# self.tableLayout.addWidget(self.tableCaption)
		self.tableLayout.addWidget(self.table)
		self.layout.addItem(self.tableLayout, 0, 0)
		
		self.btnLayout = QVBoxLayout()
		self.btnLayout.addWidget(self.btnOpenFile)
		self.btnLayout.addWidget(self.btnOpenDir)
		self.btnLayout.addWidget(self.btnRemove)
		# self.btnLayout.addStretch(1)
		self.layout.addItem(self.btnLayout, 0, 1)
		
		self.view.setLayout(self.layout)
		
		self.translateUi()
	
	def translateUi(self, lang='en'):
		self.view.setWindowTitle('Open')
		# self.tableCaption.setText('Add files to presentation')
		self.btnOpenFile.setText('Add File...')
		self.btnOpenDir.setText('Add Folder...')
		self.btnRemove.setText('Remove')

class FileDialogView(QWidget):
	def __init__(self):
		super().__init__()
		
		self.ui = Ui_openfile()
		self.ui.setupUi(self)
		
		self.setAcceptDrops(True)
	
	def setFiletypes(self, filters):
		self.ui.table.setFilters(filters)
	
	def addFiles(self, fileList):
		for file in fileList:
			self.ui.table.addFile(file)
	
	def getFilelist(self):
		return self.ui.table.getFiles()
	
	def dragMoveEvent(self, event):
		event.setDropAction(Qt.CopyAction)
	
	def dragEnterEvent(self, event):
		mimeData = event.mimeData()
		
		if all(url.isLocalFile()  for url in mimeData.urls()):
			event.acceptProposedAction()
	
	def dropEvent(self, event):
		mimeData = event.mimeData()
		localFiles = [url.toLocalFile()  for url in mimeData.urls()]
		
		self.addFiles(localFiles)