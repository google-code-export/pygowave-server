#!/usr/bin/env python

#
# PyCow - Python to JavaScript with MooTools translator
# Copyright 2009 Patrick Schneider <patrick.p2k.schneider@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#
# Some Notes:
#
# PyCow does a limited type inference, so it can distinguish function calls
# from class instantiations. However, some conditions can prevent a correct
# evaluation.
#
# PyCow cannot parse comments but can parse docstrings.
#
# No kwargs.
#

import ast, simplejson, re
from StringIO import StringIO

class ParseError(Exception):
	"""
	This exception is raised if the parser detects fatal errors.
	
	"""
	def __init__(self, value):
		self.value = value
	
	def __str__(self):
		return repr(self.value)

class PyCowContext(ast.NodeVisitor):
	"""
	First-pass context parser. Builds an execution context for type inference
	and captures docstrings.
	
	"""
	
	def __init__(self, node, parent = None):
		"""
		Parse the node as a new context. The parent must be another context
		object. Only Module, Class, Method and Function nodes are allowed.
		
		"""
		self.docstring = ""
		self.node = node
		if node.__class__.__name__ == "FunctionDef":
			if parent.type == "Class":
				self.type = "Method"
			else:
				self.type = "Function"
			self.name = node.name
			self.__get_docstring()
		elif node.__class__.__name__ == "ClassDef":
			self.type = "Class"
			self.name = node.name
			self.__get_docstring()
		elif node.__class__.__name__ == "Module":
			self.type = "Module"
			self.name = "(Module)"
		else:
			raise ValueError("Only Module, ClassDef and FunctionDef nodes are allowed")
		
		self.parent = parent
		self.identifiers = {}
		
		self.visit_For = self.visit_body
		self.visit_While = self.visit_body
		self.visit_If = self.visit_body
		self.visit_TryExcept = self.visit_body
		self.visit_ExceptHandler = self.visit_body
		
		self.visit_ClassDef = self.visit_func_or_class
		self.visit_FunctionDef = self.visit_func_or_class
		
		self.visit_body(node)
	
	def visit_func_or_class(self, node):
		if self.identifiers.has_key(node.name):
			old_ctx = self.identifiers[node.name]
			raise ParseError("%s identifier '%s' at line %d is illegaly overwritten on line %d" % (
				old_ctx.type,
				node.name,
				old_ctx.node.lineno,
				node.lineno,
			))
		self.identifiers[node.name] = PyCowContext(node, self)
	
	def visit_body(self, node):
		for stmt in node.body:
			self.visit(stmt)
		for stmt in getattr(node, "orelse", []):
			self.visit(stmt)
	
	def visit_TryFinally(self, node):
		for stmt in node.body:
			self.visit(stmt)
		for stmt in node.finalbody:
			self.visit(stmt)
	
	def generic_visit(self, node):
		pass
	
	def child(self, identifier):
		"""
		Get a named child context.
		
		"""
		if self.identifiers.has_key(identifier):
			return self.identifiers[identifier]
		return None

	def lookup(self, identifier):
		"""
		Get a context in this or the parents context.
		Jumps over Class contexts.
		
		"""
		if self.type != "Class":
			if self.identifiers.has_key(identifier):
				return self.identifiers[identifier]
		if self.parent != None:
			return self.parent.lookup(identifier)
		return None
	
	def class_context(self):
		"""
		Return the topmost class context (useful to get the context for `self`).
		
		"""
		if self.type == "Class":
			return self
		elif self.parent == None:
			return None
		return self.parent.class_context()
	
	def __get_docstring(self):
		if len(self.node.body) > 0:
			stmt = self.node.body[0]
			if isinstance(stmt, ast.Expr):
				if isinstance(stmt.value, ast.Str):
					self.docstring = stmt.value.s

class PyCow(ast.NodeVisitor):
	"""
	Second-pass main parser.
	
	"""
	OP_MAP = {
		"Add": "+",
		"Sub": "-",
		"Mult": "*",
		"Div": "/",
		"Mod": "%",
		"Pow": "^",
		"LShift": "<<",
		"RShift": ">>",
		"BitOr": "|",
		"BitXor": "^",
		"BitAnd": "&",
		"FloorDiv": "/",
		
		"And": "&&",
		"Or": "||",
		
		"Not": "!",
		
		"Eq": "==",
		"NotEq": "!=",
		"Lt": "<",
		"LtE": "<=",
		"Gt": ">",
		"GtE": ">=",
	}
	
	def __init__(self, outfile = None, indent = "\t"):
		if outfile == None:
			outfile = StringIO()
		self.__out = outfile
		self.__ichars = indent
		self.__ilevel = 0
		self.__mod_context = None
		self.__curr_context = None
	
	def output(self):
		if isinstance(self.__out, StringIO):
			return self.__out.getvalue()
		else:
			self.__out.seek(0)
			return self.__out.read()
	
	def visit_Module(self, mod):
		"""
		Initial node.
		There is and can be only one Module node.
		
		"""
		# Build context
		self.__mod_context = PyCowContext(mod)
		self.__curr_context = self.__mod_context
		# Parse body
		for stmt in mod.body:
			self.visit(stmt)
			self.__write(";\n")
			if isinstance(stmt, ast.ClassDef) or isinstance(stmt, ast.FunctionDef):
				self.__write("\n") # Extra newline
		self.__curr_context = None

	def visit_Print(self, p):
		"""
		Translate `print` to `alert()`.
		
		"""
		self.__write("alert(")
		first = True
		for expr in p.values:
			if first:
				first = False
			else:
				self.__write(" + ")
			self.visit(expr)
		self.__write(")")
	
	def visit_Num(self, n):
		self.__write(n.n)
	
	def visit_Str(self, s):
		"""
		Output a quoted string.
		Cleverly uses JSON to convert it ;)
		
		"""
		self.__write(simplejson.dumps(s.s))

	def visit_Expr(self, expr):
		self.visit(expr.value)
	
	def visit_Call(self, c):
		type = None
		if isinstance(c.func, ast.Name):
			# Look in current context
			type = getattr(self.__curr_context.lookup(c.func.id), "type", None)
		elif isinstance(c.func, ast.Attribute):
			if isinstance(c.func.value, ast.Name) and c.func.value.id == "self":
				# Look in Class context
				cls = self.__curr_context.class_context()
				if cls != None:
					type = getattr(cls.child(c.func.attr), "type", None)
			else:
				# Create attribute chain
				attrlst = [c.func.attr]
				value = c.func.value
				while isinstance(value, ast.Attribute):
					attrlst.append(value.attr)
					value = value.value
				if isinstance(value, ast.Name): # The last value must be a Name
					ctx = self.__curr_context.lookup(value.id)
					while ctx != None: # Walk up
						ctx = ctx.child(attrlst.pop())
						if ctx != None and len(attrlst) == 0: # Win
							type = ctx.type
							break
		
		if type == None:
			self.__write("/* Warning: Cannot infer type of -> */ ")
		elif type == "Class":
			self.__write("new ")
		
		self.visit(c.func)
		self.__write("(")
		self.__parse_args(c)
		self.__write(")")
	
	def visit_Name(self, n):
		"""
		Translate an identifier. If the context is a method, substitute `self`
		with `this`.
		"""
		if self.__curr_context.type == "Method" and n.id == "self":
			self.__write("this")
		else:
			self.__write(n.id)
	
	def visit_BinOp(self, o):
		"""
		Translates a binary operator.
		
		"""
		self.visit(o.left)
		self.__write(" %s " % (self.__get_op(o.op)))
		self.visit(o.right)
	
	def visit_BoolOp(self, o):
		"""
		Translates a boolean operator.
		
		"""
		first = True
		for expr in o.values:
			if first:
				first = False
			else:
				self.__write(" %s " % (self.__get_op(o.op)))
			self.visit(expr)
	
	def visit_UnaryOp(self, o):
		"""
		Translates a unary operator.
		
		"""
		self.__write(self.__get_op(o.op))
		self.visit(o.operand)
	
	def visit_Lambda(self, l):
		"""
		Translates a lambda function.
		
		"""
		self.__write("function (")
		self.__parse_args(l.args)
		self.__write(") {return ")
		self.visit(l.body)
		self.__write(";}")
	
	def visit_Assign(self, a):
		"""
		Translate an assignment.
		
		"""
		if len(a.targets) > 1:
			self.__write("/* ERROR: Cannot handle assignment unpacking */")
			return
		self.visit(a.targets[0])
		self.__write(" = ")
		self.visit(a.value)
	
	def visit_Attribute(self, a):
		"""
		Translate an attribute chain.
		
		"""
		self.visit(a.value)
		attr = a.attr
		self.__write(".%s" % (attr))
	
	def visit_ClassDef(self, c):
		"""
		Translates a Python class into a MooTools class.
		This inserts a Class context which influences the translation of
		functions and assignments.
		
		"""
		self.__push_context(c.name)
		
		# Write docstring
		if len(self.__curr_context.docstring) > 0:
			self.__write_docstring(self.__curr_context.docstring)
			self.__do_indent()
		self.__write("var %s = new Class({\n" % (c.name))
		self.__indent()
		
		# Base classes
		if len(c.bases) > 0:
			self.__write_indented("Extends: ")
			if len(c.bases) == 1:
				self.visit(c.bases[0])
				self.__write(",\n")
			else:
				self.__write("[")
				first = True
				for expr in c.bases:
					if first:
						first = False
					else:
						self.__write(", ")
					self.visit(expr)
				self.__write("],\n")
		
		first = True
		for stmt in c.body:
			if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
				continue # Skip docstring
			if first:
				first = False
			else:
				self.__write(",\n")
			self.__do_indent()
			self.visit(stmt)
		self.__write("\n")
		self.__pop_context()
		self.__indent(False)
		
		self.__write_indented("}")
	
	def visit_FunctionDef(self, f):
		"""
		Translate a Python function into a JavaScript function.
		Depending on the context, it is translated to `var name = function (...)`
		or `name: function (...)`.
		
		"""
		self.__push_context(f.name)
		is_method = self.__curr_context.type == "Method"
		
		# Write docstring
		if len(self.__curr_context.docstring) > 0:
			self.__write_docstring(self.__curr_context.docstring)
			self.__do_indent()
		if is_method:
			if f.name == "__init__":
				self.__write("initialize: function (")
			else:
				self.__write("%s: function (" % (f.name))
		else:
			self.__write("var %s = function (" % (f.name))
		
		# Parse arguments
		self.__parse_args(f.args, is_method)
		self.__write(") {\n")
		
		# Parse body
		self.__indent()
		for stmt in f.body:
			if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
				continue # Skip docstring
			self.__do_indent()
			self.visit(stmt)
			self.__write(";\n")
		self.__pop_context()
		self.__indent(False)
		
		self.__write_indented("}")
	
	def generic_visit(self, node):
		raise ParseError("Could not parse node type '%s'" % (str(node.__class__.__name__)))
	
	def __parse_args(self, args, strip_first = False):
		"""
		Translate a list of arguments.
		
		"""
		first = True
		for arg in args.args:
			if first:
				if strip_first and isinstance(arg, ast.Name):
					strip_first = False
					continue
				first = False
			else:
				self.__write(", ")
			self.visit(arg)
		if getattr(args, "vararg", None) != None:
			self.__write("/* ERROR: Variable arguments are not supported */")
	
	def __get_op(self, op):
		"""
		Translates an operator.
		
		"""
		return self.OP_MAP[op.__class__.__name__]
	
	def __indent(self, updown = True):
		if updown:
			self.__ilevel += 1
		else:
			self.__ilevel -= 1
	
	def __write(self, s):
		self.__out.write(s)
	
	def __write_indented(self, s):
		self.__out.write(self.__ichars * self.__ilevel + s)
	
	def __write_docstring(self, s):
		self.__out.write("/**\n")
		for line in s.split("\n"):
			self.__write_indented(" * %s\n" % (line.strip()))
		self.__write_indented(" */\n")
	
	def __do_indent(self):
		self.__out.write(self.__ichars * self.__ilevel)
	
	def __push_context(self, identifier):
		"""
		Walk context up.
		
		"""
		old_context = self.__curr_context
		self.__curr_context = self.__curr_context.child(identifier)
		if self.__curr_context == None:
			raise ParseError("Lost context on accessing '%s' from '%s (%s)'" % (identifier, old_context.name, old_context.type))
	
	def __pop_context(self):
		"""
		Walk context down.
		
		"""
		self.__curr_context = self.__curr_context.parent

def translate_string(input):
	"""
	Translate a string of Python code to JavaScript.
	
	"""
	moo = PyCow()
	moo.visit(ast.parse(input))
	return moo.output()

def translate_file(in_filename, out_filename = ""):
	"""
	Translate a Python file to JavaScript.
	
	"""
	moo = PyCow()
	input = open(in_filename, "r").read()
	moo.visit(ast.parse(input, in_filename))
	return moo.output()

if __name__ == "__main__":
	import sys
	import os.path
	
	if len(sys.argv) < 2:
		print "=> PyCow - Python to JavaScript with MooTools translator <="
		print "Usage: %s filename.py" % (os.path.basename(sys.argv[0]))
		sys.exit()
	
	print translate_file(sys.argv[1])
