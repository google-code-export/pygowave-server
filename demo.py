
class Someclass:
	"""
	Docstring of class
	"""
	def __init__(self, something):
		"""Docstring of method"""
		self.something = something + "string literal"
	
	def a_method(self, otherthing):
		obj = SomeExtension()
		print self.something + otherthing

class SomeExtension(Someclass):
	def __init__(self):
		super(SomeExtension, self).__init__("1234")
	
	def a_method(self, otherthing):
		print otherthing, self.something

def a_function():
	"""Docstring of function"""
	print 2+2

obj.a_method("test")

a_function()
