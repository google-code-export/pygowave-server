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

import ast, simplejson, re, random
from StringIO import StringIO

__all__ = ["ParseError", "translate_string", "translate_file"]

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
		self.variables = [] # Holds declared local variables (filled on second pass)
		
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
	
	def declare_variable(self, name):
		"""
		Returns False if the variable is already declared and True if not.
		
		"""
		if name in self.variables:
			return False
		else:
			self.variables.append(name)
			return True

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
	
	NO_SEMICOLON = [
		"Global",
		"If",
		"While",
		"For",
	]
	
	RESERVED_WORDS = [
		"null",
		"undefined",
		"true",
		"false",
		"new",
		"var",
		"switch",
		"case",
		"function",
		"this",
		"default",
		"throw",
		"delete",
		"instanceof",
		"typeof",
	]
	
	IDENTIFIER_RE = re.compile("[A-Za-z_$][0-9A-Za-z_$]*")
	
	def __init__(self, outfile = None, indent = "\t", namespace = ""):
		if outfile == None:
			outfile = StringIO()
		self.__out = outfile
		self.__ichars = indent
		self.__ilevel = 0
		self.__mod_context = None
		self.__curr_context = None
		self.__namespace = namespace
		self.__iteratorid = 0
	
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
		if self.__namespace != "":
			self.__write("var %s = (function() {\n" % (self.__namespace))
			self.__indent()
		public_identifiers = None
		
		for stmt in mod.body:
			if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and \
					isinstance(stmt.targets[0], ast.Name) and stmt.targets[0].id == "__all__":
				if not isinstance(stmt.value, ast.List):
					raise ParseError("Value of `__all__` must be a list expression (line %d)" % (stmt.lineno))
				public_identifiers = []
				for expr in stmt.value.elts:
					if not isinstance(expr, ast.Str):
						raise ParseError("All elements of `__all__` must be strings (line %d)" % (expr.lineno))
					public_identifiers.append(expr.s)
				continue
			self.__do_indent()
			self.visit(stmt)
			self.__semicolon(stmt)
			self.__write("\n") # Extra newline on module layer
		
		if self.__namespace != "":
			self.__write_indented("return {")
			self.__indent()
			if public_identifiers == None:
				public_identifiers = self.__mod_context.identifiers.iterkeys()
			first = True
			for id in public_identifiers:
				if first:
					first = False
					self.__write("\n")
				else:
					self.__write(",\n")
				self.__write_indented("%s: %s" % (id, id))
			self.__indent(False)
			self.__write("\n")
			self.__write_indented("};\n")
			self.__indent(False)
			self.__write_indented("})();\n")
		self.__curr_context = None

	def visit_ImportFrom(self, i):
		"""
		Ignored.
		"""
		self.__write("/* from %s import " % (i.module))
		first = True
		for name in i.names:
			if first:
				first = False
			else:
				self.__write(", ")
			self.__write(name.name)
			if name.asname:
				self.__write(" as %s" % (name.asname))
		self.__write(" */")
	
	def visit_Import(self, i):
		"""
		Ignored.
		"""
		self.__write("/* import ")
		first = True
		for name in i.names:
			if first:
				first = False
			else:
				self.__write(", ")
			self.__write(name.name)
			if name.asname:
				self.__write(" as %s" % (name.asname))
		self.__write(" */")

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
				self.__write(" + \" \" + ")
			self.visit(expr)
		self.__write(")")
	
	def visit_Num(self, n):
		self.__write(str(n.n))
	
	def visit_Str(self, s):
		"""
		Output a quoted string.
		Cleverly uses JSON to convert it ;)
		
		"""
		self.__write(simplejson.dumps(s.s))

	def visit_Expr(self, expr):
		self.visit(expr.value)
	
	def visit_Call(self, c):
		"""
		Translates a function/method call or class instantiation.
		
		"""
		
		cls = self.__curr_context.class_context()
		# Check for 'super'
		if cls != None and isinstance(c.func, ast.Name) and c.func.id == "super":
			if len(c.args) != 2:
				raise ParseError("`super` can only be parsed with two arguments (line %d)" % (c.lineno))
			if not isinstance(c.args[0], ast.Name) or not isinstance(c.args[1], ast.Name):
				raise ParseError("Arguments of `super` must be simple names, no other expressions allowed (line %d)" % (c.lineno))
			if c.args[0].id != cls.name:
				raise ParseError("First argument of `super` must be the current class name (line %d)" % (c.lineno))
			if c.args[1].id != "self":
				raise ParseError("Second argument of `super` must be `self` (line %d)" % (c.lineno))
			self.__write("this.parent")
			return
		
		type = None
		if isinstance(c.func, ast.Name):
			# Look in current context
			type = getattr(self.__curr_context.lookup(c.func.id), "type", None)
		elif isinstance(c.func, ast.Attribute):
			if cls != None and isinstance(c.func.value, ast.Call) and isinstance(c.func.value.func, ast.Name) and c.func.value.func.id == "super":
				# A super call
				if c.func.attr == "__init__":
					# Super constructor
					self.visit(c.func.value) # Checks for errors on the 'super' call
					self.__write("(")
					self.__parse_args(c)
					self.__write(")")
					return
				else:
					# Super method
					type = getattr(cls.child(c.func.attr), "type", None)
			elif isinstance(c.func.value, ast.Name) and c.func.value.id == "self":
				# Look in Class context
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
		
		Some special keywords:
		True -> true
		False -> false
		None -> null
		
		"""
		if self.__curr_context.type == "Method" and n.id == "self":
			self.__write("this")
		elif n.id == "True" or n.id == "False":
			self.__write(n.id.lower())
		elif n.id == "None":
			self.__write("null")
		elif n.id in self.RESERVED_WORDS:
			raise ParseError("`%s` is a reserved word and cannot be used as an identifier (line %d)" % (n.id, n.lineno))
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
	
	def visit_Compare(self, c):
		"""
		Translate a compare block.
		
		"""
		self.visit(c.left)
		for i in xrange(len(c.ops)):
			op, expr = c.ops[i], c.comparators[i]
			self.__write(" %s " % (self.__get_op(op)))
			self.visit(expr)
	
	def visit_Global(self, g):
		"""
		Declares variables as global.
		
		"""
		for name in g.names:
			self.__curr_context.declare_variable(name)
	
	def visit_Lambda(self, l):
		"""
		Translates a lambda function.
		
		"""
		self.__write("function (")
		self.__parse_args(l.args)
		self.__write(") {return ")
		self.visit(l.body)
		self.__write(";}")
	
	def visit_Yield(self, y):
		"""
		Translate the yield operator.
		
		"""
		self.__write("yield ")
		self.visit(l.value)
	
	def visit_Return(self, r):
		"""
		Translate the return statement.
		
		"""
		if r.value:
			self.__write("return ")
			self.visit(r.value)
		else:
			self.__write("return")
	
	def visit_List(self, l):
		"""
		Translate a list expression.
		
		"""
		self.__write("[")
		first = True
		for expr in l.elts:
			if first:
				first = False
			else:
				self.__write(", ")
			self.visit(expr)
		self.__write("]")
	
	def visit_Dict(self, d):
		"""
		Translate a dictionary expression.
		
		"""
		self.__write("{")
		self.__indent()
		first = True
		for i in xrange(len(d.keys)):
			key, value = d.keys[i], d.values[i]
			if first:
				first = False
				self.__write("\n")
			else:
				self.__write(",\n")
			if isinstance(key, ast.Num):
				self.__write_indented("%d: " % (key.n))
			elif not isinstance(key, ast.Str):
				raise ParseError("Only numbers and string literals are allowed in dictionary expressions (line %d)" % (key.lineno))
			else:
				if self.IDENTIFIER_RE.match(key.s):
					self.__write_indented("%s: " % (key.s))
				else:
					self.__write_indented("\"%s\": " % (key.s))
			self.visit(value)
		self.__indent(False)
		if len(d.keys) > 0:
			self.__write("\n")
			self.__do_indent()
		self.__write("}")
	
	def visit_Subscript(self, s):
		"""
		Translate a subscript expression.
		
		"""
		self.visit(s.value)
		if isinstance(s.slice, ast.Index):
			if isinstance(s.slice.value, ast.Str):
				if self.IDENTIFIER_RE.match(s.slice.value.s):
					self.__write(".%s" % (s.slice.value.s))
					return
			self.__write("[")
			self.visit(s.slice.value)
			self.__write("]")
		elif isinstance(s.slice, ast.Slice):
			if s.slice.step != None:
				raise ParseError("Subscript slice stepping '%s' is not supported (line %d)" % (str(s.slice.__class__.__name__), s.lineno))
			if isinstance(s.ctx, ast.Load):
				self.__write(".slice(")
				if s.slice.lower != None:
					self.visit(s.slice.lower)
				else:
					self.__write("0")
				if s.slice.upper != None:
					self.__write(", ")
					self.visit(s.slice.upper)
				self.__write(")")
			elif isinstance(s.ctx, ast.Delete):
				raise ParseError("Subscript slice deleting is not supported (line %d)" % (s.lineno))
			else:
				raise ParseError("Subscript slice assignment is not supported (line %d)" % (s.lineno))
		else:
			raise ParseError("Subscript slice type '%s' is not supported (line %d)" % (str(s.slice.__class__.__name__), s.lineno))
	
	def visit_Delete(self, d):
		"""
		Translate a delete statement.
		
		"""
		first = True
		for target in d.targets:
			if first:
				first = False
			else:
				self.__write("; ")
			self.__write("delete ")
			self.visit(target)

	def visit_Assign(self, a):
		"""
		Translate an assignment.
		Declares a new local variable if applicable.
		
		"""
		is_class = self.__curr_context.type == "Class"
		
		if len(a.targets) > 1:
			raise ParseError("Cannot handle assignment unpacking (line %d)" % (a.lineno))
		if isinstance(a.targets[0], ast.Name):
			if self.__curr_context.declare_variable(a.targets[0].id):
				if not is_class: self.__write("var ")
		elif is_class:
			raise ParseError("Only simple variable assignments are allowed on class scope (line %d)" % (a.targets[0].id, a.lineno))
		self.visit(a.targets[0])
		if is_class:
			self.__write(": ")
		else:
			self.__write(" = ")
		self.visit(a.value)
	
	def visit_AugAssign(self, a):
		"""
		Translate an assignment operator.
		
		"""
		self.visit(a.target)
		if isinstance(a.value, ast.Num) and a.value.n == 1:
			if isinstance(a.op, ast.Add):
				self.__write("++")
				return
			elif isinstance(a.op, ast.Sub):
				self.__write("--")
				return
		self.__write(" %s= " % (self.__get_op(a.op)))
		self.visit(a.value)
	
	def visit_Pass(self, p):
		"""
		Translate the `pass` statement. Places a comment.
		
		"""
		self.__write("/* pass */")
	
	def visit_Attribute(self, a):
		"""
		Translate an attribute chain.
		
		"""
		self.visit(a.value)
		attr = a.attr
		self.__write(".%s" % (attr))
	
	def visit_If(self, i):
		"""
		Translate an if-block.
		
		"""
		self.__write("if (")
		self.visit(i.test)
		
		# Parse body
		if len(i.body) == 1:
			self.__write(")\n")
		else:
			self.__write(") {\n")
		
		self.__indent()
		for stmt in i.body:
			self.__do_indent()
			self.visit(stmt)
			self.__semicolon(stmt)
		self.__indent(False)
		
		if len(i.body) > 1:
			self.__write_indented("}\n")
		
		# Parse else
		if len(i.orelse) == 1:
			self.__write_indented("else\n")
		elif len(i.orelse) > 1:
			self.__write_indented("else {\n")
		
		self.__indent()
		for stmt in i.orelse:
			self.__do_indent()
			self.visit(stmt)
			self.__semicolon(stmt)
		self.__indent(False)
		
		if len(i.orelse) > 1:
			self.__write_indented("}\n")
	
	def visit_While(self, w):
		"""
		Translate a while loop.
		
		"""
		if len(w.orelse) > 0:
			raise ParseError("`else` branches of the `while` statement are not supported (line %d)" % (w.lineno))
		
		self.__write("while (")
		self.visit(w.test)
		
		# Parse body
		if len(w.body) == 1:
			self.__write(")\n")
		else:
			self.__write(") {\n")
		
		self.__indent()
		for stmt in w.body:
			self.__do_indent()
			self.visit(stmt)
			self.__semicolon(stmt)
		self.__indent(False)
		
		if len(w.body) > 1:
			self.__write_indented("}\n")
	
	def visit_For(self, f):
		"""
		Translate a for loop.
		
		"""
		if len(f.orelse) > 0:
			raise ParseError("`else` branches of the `for` statement are not supported (line %d)" % (f.lineno))
		
		xrange = False
		tmp = False
		iter = None
		if isinstance(f.iter, ast.Call) and isinstance(f.iter.func, ast.Name) \
				and (f.iter.func.id == "xrange" or f.iter.func.id == "range"):
			xrange = True
		else:
			if isinstance(f.iter, ast.Name):
				iter = f.iter.id
			else:
				tmp = True
				iter = "__tmp_iter%d_" % (self.__iteratorid)
				self.__iteratorid += 1
				self.__write("var %s = " % (iter))
				self.visit(f.iter)
				self.__write(";\n")
				self.__do_indent()
		
		self.__write("for (")
		if isinstance(f.target, ast.Name):
			if self.__curr_context.declare_variable(f.target.id):
				self.__write("var ")
		self.visit(f.target)
		
		if xrange:
			if len(f.iter.args) == 1:
				self.__write(" = 0; ")
				self.visit(f.target)
				self.__write(" < ")
				self.visit(f.iter.args[0])
				self.__write("; ")
				self.visit(f.target)
				self.__write("++")
			else:
				self.__write(" = ")
				self.visit(f.iter.args[0])
				self.__write("; ")
				self.visit(f.target)
				if len(f.iter.args) == 3:
					if not isinstance(f.iter.args[2], ast.Num):
						raise ParseError("Only numbers allowed in step expression of the range/xrange expression in a `for` statement (line %d)" % (f.lineno))
					if f.iter.args[2].n < 0:
						self.__write(" > ")
					else:
						self.__write(" < ")
				else:
					self.__write(" < ")
				self.visit(f.iter.args[1])
				self.__write("; ")
				self.visit(f.target)
				if len(f.iter.args) == 3:
					if f.iter.args[2].n < 0:
						if f.iter.args[2].n == -1:
							self.__write("--")
						else:
							self.__write(" -= %s" % (str(-f.iter.args[2].n)))
					else:
						self.__write(" += %s" % (str(f.iter.args[2].n)))
				else:
					self.__write("++")
		else:
			self.__write(" in " + iter)
		
		# Parse body
		self.__indent()
		if len(f.body) == 1 and xrange:
			self.__write(")\n")
		else:
			self.__write(") {\n")
			if not xrange:
				self.__do_indent()
				self.visit(f.target)
				self.__write(" = %s[" % (iter))
				self.visit(f.target)
				self.__write("];\n")
		
		for stmt in f.body:
			self.__do_indent()
			self.visit(stmt)
			self.__semicolon(stmt)
		self.__indent(False)
		
		if len(f.body) > 1 or not xrange:
			self.__write_indented("}\n")
		
		if tmp:
			self.__write_indented("delete %s;\n" % (iter))
			self.__iteratorid -= 1
	
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
		
		# Special decorators
		decorators = self.__get_decorators(c)
		if decorators.has_key("Implements"):
			self.__write_indented("Implements: ")
			if len(decorators["Implements"]) == 1:
				self.visit(decorators["Implements"][0])
				self.__write(",\n")
			else:
				self.__write("[")
				first = True
				for expr in decorators["Implements"]:
					if first:
						first = False
					else:
						self.__write(", ")
					self.visit(expr)
				self.__write("],\n")
		if not decorators.has_key("Class"):
			import sys
			sys.stderr.write("Warning: The class `%s` of line %d in the input file/string does not have the `Class` decorator!\n" % (c.name, c.lineno))
		
		# Base classes
		bases = filter(lambda b: not isinstance(b, ast.Name) or b.id != "object", c.bases)
		if len(bases) > 0:
			self.__write_indented("Extends: ")
			if len(bases) == 1:
				self.visit(bases[0])
				self.__write(",\n")
			else:
				self.__write("[")
				first = True
				for expr in bases:
					if first:
						first = False
					else:
						self.__write(", ")
					self.visit(expr)
				self.__write("],\n")
		
		first = True
		statics = []
		for stmt in c.body:
			if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
				continue # Skip docstring
			if isinstance(stmt, ast.FunctionDef):
				if self.__get_decorators(stmt).has_key("staticmethod"):
					statics.append(stmt)
					continue
			if first:
				first = False
			else:
				self.__write(",\n")
			self.__do_indent()
			self.visit(stmt)
		self.__write("\n")
		self.__indent(False)
		
		self.__write_indented("})")
		for stmt in statics:
			self.__write(";\n")
			self.__do_indent()
			self.visit(stmt)
		self.__pop_context()
	
	def visit_FunctionDef(self, f):
		"""
		Translate a Python function into a JavaScript function.
		Depending on the context, it is translated to `var name = function (...)`
		or `name: function (...)`.
		
		"""
		self.__push_context(f.name)
		is_method = self.__curr_context.type == "Method"
		
		# Special decorators
		decorators = self.__get_decorators(f)
		is_static = decorators.has_key("staticmethod")
		
		# Write docstring
		if len(self.__curr_context.docstring) > 0:
			self.__write_docstring(self.__curr_context.docstring)
			self.__do_indent()
		if is_method:
			if is_static:
				self.__write("%s.%s = function (" % (self.__curr_context.class_context().name, f.name))
			elif f.name == "__init__":
				self.__write("initialize: function (")
			else:
				self.__write("%s: function (" % (f.name))
		else:
			self.__write("var %s = function (" % (f.name))
		
		# Parse arguments
		self.__parse_args(f.args, is_method and not is_static)
		self.__write(") {\n")
		
		# Parse body
		self.__indent()
		for stmt in f.body:
			if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):
				continue # Skip docstring
			if isinstance(stmt, ast.Global): # The `global` statement is invisible
				self.visit(stmt)
				continue
			self.__do_indent()
			self.visit(stmt)
			self.__semicolon(stmt)
		self.__pop_context()
		self.__indent(False)
		
		self.__write_indented("}")
	
	def generic_visit(self, node):
		raise ParseError("Could not parse node type '%s' (line %d)" % (str(node.__class__.__name__), node.lineno))
	
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
			raise ParseError("Variable arguments on function definitions are not supported")
	
	def __get_decorators(self, stmt):
		"""
		Return a dictionary of decorators and their parameters.
		
		"""
		decorators = {}
		if isinstance(stmt, ast.FunctionDef):
			for dec in stmt.decorator_list:
				if isinstance(dec, ast.Name):
					if dec.id == "staticmethod":
						decorators["staticmethod"] = []
						continue
				raise ParseError("This function decorator is not supported. Only @staticmethod is supported for now. (line %d)" % (stmt.lineno))
		else:
			for dec in stmt.decorator_list:
				if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
					if dec.func.id == "Implements":
						decorators["Implements"] = dec.args
						continue
				if isinstance(dec, ast.Name) and dec.id == "Class":
					decorators["Class"] = []
					continue
				raise ParseError("This class decorator is not supported. Only decorators of pycow.decorators are supported (line %d)" % (stmt.lineno))
		return decorators

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
		gotnl = False
		first = True
		for line in s.split("\n"):
			line = line.strip()
			if line == "":
				gotnl = True
			else:
				if gotnl and not first:
					self.__write_indented(" *\n")
				gotnl = False
				first = False
				self.__write_indented(" * %s\n" % (line))
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
	
	def __semicolon(self, stmt, no_newline = False):
		"""
		Write a semicolon (and newline) for all statements except the ones
		in NO_SEMICOLON.
		
		"""
		if stmt.__class__.__name__ not in self.NO_SEMICOLON:
			if no_newline:
				self.__write(";")
			else:
				self.__write(";\n")

def translate_string(input, indent = "\t", namespace = ""):
	"""
	Translate a string of Python code to JavaScript.
	Set the `indent` parameter, if you want an other indentation than tabs.
	Set the `namespace` parameter, if you want to enclose the code in a namespace.
	
	"""
	moo = PyCow(indent=indent, namespace=namespace)
	moo.visit(ast.parse(input, "(string)"))
	return moo.output()

def translate_file(in_filename, out_filename = "", indent = "\t", namespace = ""):
	"""
	Translate a Python file to JavaScript.
	If `out_filename` is not given, it will be set to in_filename + ".js".
	Set the `indent` parameter, if you want an other indentation than tabs.
	Set the `namespace` parameter, if you want to enclose the code in a namespace.
	
	"""
	if out_filename == "":
		out_filename = in_filename + ".js"
	outfile = open(out_filename, "w")
	moo = PyCow(outfile, indent, namespace)
	input = open(in_filename, "r").read()
	moo.visit(ast.parse(input, in_filename))
	outfile.close()

if __name__ == "__main__":
	import sys
	import os.path
	
	if len(sys.argv) < 2:
		print "=> PyCow - Python to JavaScript with MooTools translator <="
		print "Usage: %s [OPTION]... filename.py" % (os.path.basename(sys.argv[0]))
		print "Options:"
		print " -o filename   Set the output file name (default: filename.py.js)"
		print " -n namespace  Enclose module in namespace"
		sys.exit()
	
	in_filename = ""
	out_filename = ""
	namespace = ""
	
	i = 1
	while i < len(sys.argv):
		arg = sys.argv[i]
		if arg == "-o":
			if i+1 >= len(sys.argv):
				print "Error parsing command line: Missing parameter for option '-o'."
				sys.exit(1)
			out_filename = sys.argv[i+1]
			i += 1
		elif arg == "-n":
			if i+1 >= len(sys.argv):
				print "Error parsing command line: Missing parameter for option '-n'."
				sys.exit(1)
			namespace = sys.argv[i+1]
			i += 1
		else:
			in_filename = arg
		i += 1
	
	if in_filename == "":
		print "Error parsing command line: Missing input file."
		sys.exit(1)
	
	translate_file(in_filename, out_filename, namespace=namespace)
