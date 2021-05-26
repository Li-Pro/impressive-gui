from enum  import Enum

from PySide6.QtWidgets  import QApplication, QMainWindow

# from ui_editor  import EditorView

# the translating hook
class Hook:
	def __init__(self, hookVars):
		super().__setattr__('_hook_hookVars', hookVars)
	
	def __setattr__(self, name, value):
		self._hook_hookVars[name] = value
	
	def __getattr__(self, name):
		return self._hook_hookVars[name]

def prepareHook(hookVars):
	_hook = Hook(hookVars)
	rhook = Hook(globals())
	
	_hook._hook = rhook
	rhook._hook = _hook

def setOptions(opts, args):
	global optmap, optfile
	optmap = {opt: arg  for opt, arg in opts}
	optfile = args

def run_editor():
	raise NotImplementedError
	app = QApplication([])
	
	editor = EditorView()
	editor.show()
	
	app_retcode = app.exec()
	assert( app_retcode == 0 )