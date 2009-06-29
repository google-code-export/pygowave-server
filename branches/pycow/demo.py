
# Classes, subclasses and functions

class Someclass:
	"""
	Docstring of class
	"""
	def __init__(self, something): # PyCow removes 'self' from method declarations
		"""
		Docstring of constructor/method
		"""
		self.something = something + "string literal" # PyCow replaces 'self' with 'this'
	
	def a_method(self, otherthing):
		print self.something + otherthing # 'print' is translated to 'alert'
	
	def another_method(self):
		obj = SomeExtension() # PyCow can infer types of callables (even declared later); here it will place 'new', because SomeExtension is a class
		self.var = "test"

class SomeExtension(Someclass):
	def __init__(self):
		super(SomeExtension, self).__init__("1234") # PyCow correctly treats the 'super' function of Python; here it's the call to the super constructor
	
	def a_method(self, otherthing):
		super(SomeExtension, self).a_method(otherthing) # Here it's a call to the super class' method
		print otherthing, self.something

def a_function():
	"""
	Docstring of function
	
	Note that PyCow removes
			whitespaces.
	
	
	
	And normalizes newlines.
	"""
	test = 2 # PyCow automatically declares local variables
	test = 4 # once
	print test+     2 # Because PyCow parses semantics only, it will ignore whitespaces (but avoid to do something like that anyways)

obj = Someclass()

obj.a_method("test") # PyCow's type inference does not include types of variables (atm)

a_function() # PyCow does not put "new" here, because a_function is a simple function

x = "hello again"

def another_function():
	global x # Because of the 'global' statement
	x = "go ahead" # PyCow does not declare x as local here
	return x

# Standard statements

if True: # If statement
	print "Welcome"
	if False:
		pass
	else:
		print "Nested if"
else:
	print "You're not welcome..."

i = 0
while i < 3: # While statement
	print i
	i += 1 # Assignment operator

for j in xrange(3): # For statement (xrange)
	print j

for j in xrange(1,4): # For statement (xrange; with start)
	print j

for j in xrange(1,4,2): # For statement (xrange; with start and step)
	print j
	
for j in xrange(4,1,-1): # For statement (xrange; with start and step backwards)
	print j

f = lambda x: x*2 # Lambda functions

a = [1,2,3,f(2)] # List expression

print a[1:3] # Slicing

b = {} # Empty dictionary

# Dictionary with strings and numbers as indices
b = {"a": 1, "b": 2,
	 1: "x", 2: "y",
	 "-test-": 1+2, "0HAY0": "a"+"B"}

# Accessing subscript (simple string)
print b["a"]

# Accessing subscript (other string; assignment)
b["-test-"] = 3

# Accessing subscript (number)
print b[1]

# Deleting from map
del b["a"]
