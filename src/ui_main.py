from enum  import Enum
import subprocess

from PySide6.QtWidgets  import QApplication, QMainWindow

from src.ui_editor  import EditorView, FileDialogView

__version__ = 'pre-alpha'

_editor_edited = False

# the translating hook
class Hook:
	def __init__(self, hookVars):
		super().__setattr__('_hook_hookVars', hookVars)
	
	def __setattr__(self, name, value):
		self._hook_hookVars[name] = value
	
	def __getattr__(self, name):
		return self._hook_hookVars[name]

def windowedPopen(*args, **kwargs):
	stInfo = subprocess.STARTUPINFO(dwFlags=subprocess.STARTF_USESHOWWINDOW)
	return subprocess.Popen(*args, startupinfo=stInfo, **kwargs)

def prepareHook(hookVars):
	_hook = Hook(hookVars)
	rhook = Hook(globals())
	
	_hook._hook = rhook
	rhook._hook = _hook
	
	global app
	app = QApplication([])
	
	_hook.Popen = windowedPopen

def setOptions(opts, args):
	global optmap, optfile
	optmap = {opt: arg  for opt, arg in opts}
	optfile = args

def isEdited():
	return _editor_edited

def loadPages():
	pages = []
	for pageId in list(range(_hook.InitialPage, _hook.PageCount + 1)) + list(range(1, _hook.InitialPage)):
		pages.append( (_hook.PageImage(pageId), (_hook.TexWidth, _hook.TexHeight)))
	
	return pages

def getOptionSettings():
	settings = {
		'transition_selection' : [transition.__name__.lower()  for transition in _hook.AllTransitions]
	}
	return settings

def getPageOptions():
	pageOptions = {}
	pageIdx = 0
	for page in list(range(_hook.InitialPage, _hook.PageCount + 1)) + list(range(1, _hook.InitialPage)):
		options = {}
		options['skip'] = _hook.GetPageProp(page, 'skip', False)
		options['transition'] = _hook.GetPageProp(page, 'transition', '').lower()
		
		pageOptions[pageIdx] = options
		pageIdx += 1
	
	return pageOptions

def processOptions(pageOptions, editor):
	# print('#', pageOptions)
	pageIdx = 0
	for page in list(range(_hook.InitialPage, _hook.PageCount + 1)) + list(range(1, _hook.InitialPage)):
		options = pageOptions[pageIdx]
		if options['skip'] == True:
			_hook.SetPageProp(page, 'skip', True)
		
		transitionMapping = {transition.__name__.lower(): transition  for transition in _hook.AllTransitions}
		if options['transition'] != '':
			transitionName = options['transition']
			_hook.SetPageProp(page, 'transition', transitionMapping[transitionName])
		
		pageIdx += 1
	
	startPage = -1
	for page in list(range(_hook.InitialPage, _hook.PageCount + 1)) + list(range(1, _hook.InitialPage)):
		if not _hook.GetPageProp(page, 'skip', False):
			startPage = page
			break
	
	if startPage < 0:
		editor.popupMessage('All the slides are skipped.')
		return False
	else:
		_hook.Pcurrent = startPage
	
	return True

def printHelp():
	print("""
Impressive GUI [{}]
---
An editor of a nice presentation tool.

Usage: edit the presentation in a user-friendly GUI.
The specified options (see below) would directly be read into impressive.
""".format(__version__))

def run_editor():
	global _editor_edited
	
	editor = EditorView(getOptionSettings())
	editor.loadOptions(getPageOptions())
	for page, size in loadPages():
		editor.addPage(page, size)
	
	editor.show()
	
	app_retcode = app.exec()
	assert( app_retcode == 0 )
	
	proceed = processOptions(editor.getOptions(), editor)
	
	_editor_edited = True
	_hook.Platform.StartDisplay()
	
	return proceed

def getSupportedFiletypes():
	return {
		'PDF': ['pdf'],  # pdf
		
		'PNG': ['png'],  # png
		'JPEG': ['jpg', 'jpeg', 'jpe', 'jif', 'jfif', 'jfi'],  # jpg, jpeg
		'TIFF': ['tiff', 'tif'],  # tiff, tif
		'BMP': ['bmp', 'dib'],  # bmp
		'PGM/PPM': ['pbm', 'pgm', 'ppm', 'pnm'],  # [Netpbm] pgm, ppm
		
		'AVI': ['avi'],  # avi
		'MOV/MP4': ['mov', 'qt', 'mp4', 'm4a', 'm4p', 'm4b', 'm4r', 'm4v'],  # [MOV] mov, qt / [MP4] mp4, m4v
		# ''
	}

def run_openfile(cli_files):
	view = FileDialogView()
	view.setFiletypes(getSupportedFiletypes())
	view.addFiles(cli_files)
	
	view.show()
	app_retcode = app.exec()
	assert( app_retcode == 0 )
	
	return view.getFilelist()