

"""
Operations module.
@module pygowave.operations
"""

__license__ = """
PyGoWave Client Script a.k.a. Microwave
Copyright (C) 2009 by p2k

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from pycow.decorators import Class, Implements
from pycow.utils import Events

# Currently supported and official operations
DOCUMENT_INSERT = 'DOCUMENT_INSERT'
DOCUMENT_DELETE = 'DOCUMENT_DELETE'
DOCUMENT_ELEMENT_INSERT = 'DOCUMENT_ELEMENT_INSERT'
DOCUMENT_ELEMENT_DELETE = 'DOCUMENT_ELEMENT_DELETE'

# Currently supported, but non-official operations
DOCUMENT_ELEMENT_DELTA = 'DOCUMENT_ELEMENT_DELTA'
DOCUMENT_ELEMENT_SETPREF = 'DOCUMENT_ELEMENT_SETPREF'

# Currently supported operations, which are not handled within OT
#WAVELET_ADD_PARTICIPANT = 'WAVELET_ADD_PARTICIPANT'
#WAVELET_REMOVE_SELF = 'WAVELET_REMOVE_SELF'

# Currently not supported operations
#WAVELET_APPEND_BLIP = 'WAVELET_APPEND_BLIP'
#WAVELET_CREATE = 'WAVELET_CREATE'
#WAVELET_DATADOC_SET = 'WAVELET_DATADOC_SET'
#WAVELET_SET_TITLE = 'WAVELET_SET_TITLE'
#BLIP_CREATE_CHILD = 'BLIP_CREATE_CHILD'
#BLIP_DELETE = 'BLIP_DELETE'
#DOCUMENT_ANNOTATION_DELETE = 'DOCUMENT_ANNOTATION_DELETE'
#DOCUMENT_ANNOTATION_SET = 'DOCUMENT_ANNOTATION_SET'
#DOCUMENT_ANNOTATION_SET_NORANGE = 'DOCUMENT_ANNOTATION_SET_NORANGE'
#DOCUMENT_APPEND = 'DOCUMENT_APPEND'
#DOCUMENT_APPEND_STYLED_TEXT = 'DOCUMENT_APPEND_STYLED_TEXT'
#DOCUMENT_REPLACE = 'DOCUMENT_REPLACE'
#DOCUMENT_ELEMENT_APPEND = 'DOCUMENT_ELEMENT_APPEND'
#DOCUMENT_ELEMENT_INSERT_AFTER = 'DOCUMENT_ELEMENT_INSERT_AFTER'
#DOCUMENT_ELEMENT_INSERT_BEFORE = 'DOCUMENT_ELEMENT_INSERT_BEFORE'
#DOCUMENT_ELEMENT_REPLACE = 'DOCUMENT_ELEMENT_REPLACE'
#DOCUMENT_INLINE_BLIP_APPEND = 'DOCUMENT_INLINE_BLIP_APPEND'
#DOCUMENT_INLINE_BLIP_DELETE = 'DOCUMENT_INLINE_BLIP_DELETE'
#DOCUMENT_INLINE_BLIP_INSERT = 'DOCUMENT_INLINE_BLIP_INSERT'
#DOCUMENT_INLINE_BLIP_INSERT_AFTER_ELEMENT = 'DOCUMENT_INLINE_BLIP_INSERT_AFTER_ELEMENT'

__all__ = [
	"OpManager",
	"DOCUMENT_INSERT",
	"DOCUMENT_DELETE",
	"DOCUMENT_ELEMENT_INSERT",
	"DOCUMENT_ELEMENT_DELETE",
	"DOCUMENT_ELEMENT_DELTA",
	"DOCUMENT_ELEMENT_SETPREF",
]

@Class
class Operation(object):
	"""
	Represents a generic operation applied on the server.
	
	This operation class contains data that is filled in depending on the
	operation type.
	
	It can be used directly, but doing so will not result
	in local, transient reflection of state on the blips. In other words,
	creating a "delete blip" operation will not remove the blip from the local
	context for the duration of this session. It is better to use the OpBased
	model classes directly instead.
	
	@class {private} pygowave.operations.Operation
	"""
	
	def __init__(self, op_type, waveId, waveletId, blipId='', index=-1, prop=None):
		"""
		Initializes this operation with contextual data.
		
		@constructor {public} initialize
		@param {String} op_type Type of operation
		@param {String} waveId The id of the wave that this operation is to
			be applied.
		@param {String} waveletId The id of the wavelet that this operation is
		    to be applied.
		@param {optional String} blipId The optional id of the blip that this
			operation is to be applied.
		@param {optional int} index Optional integer index for content-based
			operations.
		@param {optional Object} prop A weakly typed property object is based
			on the context of this operation.
		"""
		self.type = op_type
		self.waveId = waveId
		self.waveletId = waveletId
		self.blipId = blipId
		self.index = index
		self.property = prop
	
	def clone(self):
		"""
		Create a copy of this operation.
		
		@function {public Boolean} clone
		"""
		return Operation(self.type, self.waveId, self.waveletId, self.blipId,
						 self.index, self.property)
	
	def isNull(self):
		"""
		Return weather this operation is a null operation i.e. it does not
		change anything.
		
		@function {public Boolean} isNull
		"""
		if self.type == DOCUMENT_INSERT:
			return len(self.property) == 0
		elif self.type == DOCUMENT_DELETE:
			return self.property == 0
		return False
	
	def isCompatibleTo(self, other_op):
		"""
		Check if the operation can be influenced by `other_op` and vice-versa.
		
		@function {public Boolean} isCompatibleTo
		@param {Operation} other_op
		"""
		
		# Currently all supported operations are compatible to each other (if on the same blip)
		# DOCUMENT_INSERT DOCUMENT_DELETE DOCUMENT_ELEMENT_INSERT DOCUMENT_ELEMENT_DELETE DOCUMENT_ELEMENT_DELTA DOCUMENT_ELEMENT_SETPREF
		if self.waveId != other_op.waveId \
				or self.waveletId != other_op.waveletId \
				or self.blipId != self.blipId:
			return False
		return True

	def isInsert(self):
		"""
		Returns true, if this op is an insertion operation.
		
		@function {public Boolean} isInsert
		"""
		return (self.type == DOCUMENT_INSERT or self.type == DOCUMENT_ELEMENT_INSERT)
	
	def isDelete(self):
		"""
		Returns true, if this op is a deletion operation.
		
		@function {public Boolean} isDelete
		"""
		return (self.type == DOCUMENT_DELETE or self.type == DOCUMENT_ELEMENT_DELETE)

	def isChange(self):
		"""
		Returns true, if this op is an (attribute) change operation.
		
		@function {public Boolean} isChange
		"""
		return (self.type == DOCUMENT_ELEMENT_DELTA or self.type == DOCUMENT_ELEMENT_SETPREF)

	def length(self):
		"""
		Returns the length of this operation.
		This can be interpreted as the distance a concurrent operation's index
		must be moved to include the effects of this operation.
		
		@function {public int} length
		"""
		if self.type == DOCUMENT_INSERT:
			return len(self.property)
		elif self.type == DOCUMENT_DELETE:
			return self.property
		elif self.type == DOCUMENT_ELEMENT_INSERT or self.type == DOCUMENT_ELEMENT_DELETE:
			return 1
		return 0
	
	def resize(self, value):
		"""
		Delete operations: Sets the amount of deleted characters/elements to
		`value`.
		
		Other operations: No effect.
		
		@function {public} resize
		@param {int} value
		"""
		if self.type == DOCUMENT_DELETE:
			self.property = value

	def serialize(self):
		"""
		Serialize this operation into a dictionary. Official robots API format.
		
		@function {public String} serialize
		"""
		return {
			"type": self.type,
			"waveId": self.waveId,
			"waveletId": self.waveletId,
			"blipId": self.blipId,
			"index": self.index,
			"property": self.property,
		}

	def __repr__(self):
		return "%s(\"%s\",%d,%s)" % (self.type.lower(), self.blipId,
									 self.index, repr(self.property))

	@staticmethod
	def unserialize(obj):
		"""
		Unserialize an operation from a dictionary.
		
		@function {public static Operation} unserialize
		"""
		return Operation(obj["type"], obj["waveId"], obj["waveletId"],
						 obj["blipId"], obj["index"], obj["property"])

@Implements(Events)
@Class
class OpManager(object):
	"""
	Manages operations: Creating, merging, transforming, serializing.
	
	The operation manager wraps single operations as functions and generates
	operations in-order. It keeps a list of operations and allows
	transformation, merging and serializing.
	
	An OpManager is always associated with exactly one wave/wavelet.
	
	@class {public} pygowave.operations.OpManager
	"""
	
	# --- Event documentation ---
	"""
	Fired if an operation in this manager has been changed.
	@event onOperationChanged
	@param {int} index Index of the changed operation
	"""
	
	"""
	Fired if one or more operations are about to be removed.
	@event onBeforeOperationsRemoved
	@param {int} start Start index of the removal.
	@param {int} end End index of the removal.
	"""
	
	"""
	Fired if one or more operations have been removed.
	@event onAfterOperationsRemoved
	@param {int} start Start index of the removal.
	@param {int} end End index of the removal.
	"""
	
	"""
	Fired if one or more operations are about to be inserted.
	@event onBeforeOperationsInserted
	@param {int} start Start index of the insertion.
	@param {int} end End index of the insertion.
	"""
	
	"""
	Fired if one or more operations have been inserted.
	@event onAfterOperationsInserted
	@param {int} start Start index of the insertion.
	@param {int} end End index of the insertion.
	"""
	# ---------------------------
	
	def __init__(self, waveId, waveletId):
		"""
		Initializes the op manager with a wave and wavelet ID.
		
		@constructor {public} initialize
		@param {String} waveId The ID of the wave
		@param {String} waveletId The ID of the wavelet
		"""
		self.waveId = waveId
		self.waveletId = waveletId
		self.operations = []

	def isEmpty(self):
		"""
		Return true if this manager is not holding operations.
		
		@function {public Boolean} isEmpty
		"""
		return len(self.operations) == 0

	def transform(self, input_op):
		"""
		Transform the input operation on behalf of the manager's operations
		list. This will simultaneously transform the operations list on behalf
		of the input operation.
		This method returns a list of applicable operations. This list may be
		empty or it may contain any number of new operations (according to
		results of deletion, modification and splitting; i.e. the input
		operation is not modified by itself).
		
		@function {public Operation[]} transform
		@param {Operation} input_op
		"""
		
		new_op = None
		op_lst = [input_op.clone()]
		
		# From The Zen of Python, by Tim Peters:
		# "Complex is better than complicated."
		
		i = 0
		while i < len(self.operations):
			myop = self.operations[i]
			j = 0
			while j < len(op_lst):
				op = op_lst[j]
				
				# Do not handle incompatible operations
				if not op.isCompatibleTo(myop): continue
				
				# Check all possible cases
				
				end = None
				if op.isDelete() and myop.isDelete():
					if op.index < myop.index:
						end = op.index + op.length()
						if end <= myop.index:
							myop.index -= op.length()
							self.fireEvent("operationChanged", i)
						elif end < myop.index + myop.length(): # and end > myop.index
							op.resize(myop.index - op.index)
							myop.resize(myop.length() - (end - myop.index))
							myop.index = op.index
							self.fireEvent("operationChanged", i)
						else: # end >= myop.index + myop.length()
							op.resize(op.length() - myop.length())
							self.fireEvent("beforeOperationsRemoved", [i, i])
							self.operations.pop(i)
							self.fireEvent("afterOperationsRemoved", [i, i])
							i -= 1
							break
					else: # op.index >= myop.index
						end = myop.index + myop.length()
						if op.index >= end:
							op.index -= myop.length()
						elif op.index + op.length() <= end: # and op.index < end
							op_lst.pop(j)
							j -= 1
							myop.resize(myop.length() - op.length())
							if myop.isNull():
								self.fireEvent("beforeOperationsRemoved", [i, i])
								self.operations.pop(i)
								self.fireEvent("afterOperationsRemoved", [i, i])
								i -= 1
								break
							else:
								self.fireEvent("operationChanged", i)
						else: # op.index + op.length() > end
							myop.resize(myop.length() - (end - op.index))
							self.fireEvent("operationChanged", i)
							op.resize(op.length() - (end - op.index))
							op.index = myop.index
				
				elif op.isDelete() and myop.isInsert():
					if op.index < myop.index:
						if op.index + op.length() <= myop.index:
							myop.index -= op.length()
							self.fireEvent("operationChanged", i)
						else: # op.index + op.length() > myop.index
							new_op = op.clone()
							op.resize(myop.index - op.index)
							new_op.resize(new_op.length() - op.length())
							op_lst.insert(j+1, new_op)
							myop.index -= op.length()
							self.fireEvent("operationChanged", i)
					else: # op.index >= myop.index
						op.index += myop.length()
				
				elif op.isInsert() and myop.isDelete():
					if op.index <= myop.index:
						myop.index += op.length()
						self.fireEvent("operationChanged", i)
					elif op.index >= myop.index + myop.length(): # op.index > myop.index
						op.index -= myop.length()
					else: # op.index < myop.index + myop.length()
						new_op = myop.clone()
						myop.resize(op.index - myop.index)
						self.fireEvent("operationChanged", i)
						new_op.resize(new_op.length() - myop.length())
						self.fireEvent("beforeOperationsInserted", [i+1, i+1])
						self.operations.insert(i+1, new_op)
						self.fireEvent("afterOperationsInserted", [i+1, i+1])
						op.index = myop.index
				
				elif op.isInsert() and myop.isInsert():
					if op.index <= myop.index:
						myop.index += op.length()
						self.fireEvent("operationChanged", i)
					else: # op.index > myop.index
						op.index += myop.length()
				elif op.isChange() and myop.isDelete():
					if op.index > myop.index:
						if op.index <= myop.index + myop.length():
							op.index = myop.index
						else:
							op.index -= myop.length()
				elif op.isChange() and myop.isInsert():
					if op.index >= myop.index:
						op.index += myop.length()
				elif op.isDelete() and myop.isChange():
					if op.index < myop.index:
						if myop.index <= op.index + op.length():
							myop.index = op.index
							self.fireEvent("operationChanged", i)
						else:
							myop.index -= op.length()
							self.fireEvent("operationChanged", i)
				elif op.isInsert() and myop.isChange():
					if op.index <= myop.index:
						myop.index += op.length()
						self.fireEvent("operationChanged", i)
				
				j += 1
				
			i += 1
		
		return op_lst
	
	def fetch(self):
		"""
		Returns the pending operations and removes them from this manager.
		
		@function {public Operation[]} fetch
		"""
		ops = self.operations
		self.fireEvent("beforeOperationsRemoved", [0, len(ops)-1])
		self.operations = []
		self.fireEvent("afterOperationsRemoved", [0, len(ops)-1])
		return ops
	
	def put(self, ops):
		"""
		Opposite of fetch. Inserts all given operations into this manager.
		
		@function {public} put
		@param {Operation[]} ops
		"""
		if len(ops) == 0:
			return
		start = len(self.operations)
		end = start + len(ops) - 1
		self.fireEvent("beforeOperationsInserted", [start, end])
		self.operations.extend(ops)
		self.fireEvent("afterOperationsInserted", [start, end])

	def serialize(self, fetch = False):
		"""
		Serialize this manager's operations into a list of dictionaries.
		Set fetch to true to also clear this manager.
		
		@function {public Object[]} serialize
		@param {optional Boolean} fetch
		"""
		if fetch:
			ops = self.fetch()
		else:
			ops = self.operations
		
		out = []
		
		for op in ops:
			out.append(op.serialize())
		
		return out
	
	def unserialize(self, serial_ops):
		"""
		Unserialize a list of dictionaries to operations and add them to this
		manager.
		
		@function {public} unserialize
		@param {Object[]} serial_ops
		"""
		
		ops = []
		
		for op in serial_ops:
			ops.append(Operation.unserialize(op))
		
		self.put(ops)

	def __insert(self, newop):
		"""
		Inserts and probably merges an operation into the manager's
		operation list.
		
		@function {private} __insert
		@param {Operation} newop
		"""
		
		# Element delta's can always merge with predecessors
		op = None
		i = 0
		if newop.type == DOCUMENT_ELEMENT_DELTA:
			for i in xrange(len(self.operations)):
				op = self.operations[i]
				if op.type == DOCUMENT_ELEMENT_DELTA and newop.property["id"] == op.property["id"]:
					op.property["delta"].update(newop.property["delta"])
					self.fireEvent("operationChanged", i)
					return
		
		# Others: Only merge with the last op (otherwise this may get a bit complicated)
		i = len(self.operations) - 1
		if i >= 0:
			op = self.operations[i]
			if newop.type == DOCUMENT_INSERT and op.type == DOCUMENT_INSERT:
				if newop.index == op.index: # Prepending
					op.property = newop.property + op.property
					self.fireEvent("operationChanged", i)
					return
				end = op.index + len(op.property)
				if newop.index == end: # Appending
					op.property += newop.property
					self.fireEvent("operationChanged", i)
					return
				if op.index < newop.index and newop.index < end: # Inserting
					op.property = op.property[:newop.index-op.index] + newop.property + op.property[newop.index-op.index:]
					self.fireEvent("operationChanged", i)
					return
			if newop.type == DOCUMENT_DELETE and op.type == DOCUMENT_INSERT:
				if newop.index == op.index: # Delete from start
					l = len(op.property)
					op.property = op.property[newop.property:]
					if op.property == "":
						self.fireEvent("beforeOperationsRemoved", [i, i])
						self.operations.pop(i)
						self.fireEvent("afterOperationsRemoved", [i, i])
					else:
						self.fireEvent("operationChanged", i)
					newop.property -= l
					if newop.property <= 0: # Deleted less than last op's length
						return
				end = op.index + len(op.property)
				if op.index < newop.index and newop.index < end: # Delete from within
					l = len(op.property) - (newop.index - op.index + newop.property)
					op.property = op.property[:newop.index - op.index] + op.property[newop.index - op.index + newop.property:]
					self.fireEvent("operationChanged", i)
					newop.property = -l
					if newop.property <= 0: # Deleted less than last op's length
						return
			if newop.type == DOCUMENT_DELETE and op.type == DOCUMENT_DELETE:
				if newop.index == op.index: # Delete at start
					op.property += newop.property
					self.fireEvent("operationChanged", i)
					return
				if newop.index == op.index-newop.property: # Deleta at end
					op.index -= newop.property
					op.property += newop.property
					self.fireEvent("operationChanged", i)
					return
		
		# If we reach this the operation could not be merged, so add it.
		self.fireEvent("beforeOperationsInserted", [i+1, i+1])
		self.operations.append(newop)
		self.fireEvent("afterOperationsInserted", [i+1, i+1])

	# --------------------------------------------------------------------------

	def documentInsert(self, blipId, index, content):
		"""
		Requests to insert content into a document at a specific location.
		
		@function {public} documentInsert
		@param {String} blipId The blip id that this operation is applied to
		@param {int} index The position insert the content at in ths document
		@param {String} content The content to insert
		"""
		self.__insert(Operation(
			DOCUMENT_INSERT,
			self.waveId, self.waveletId, blipId,
			index,
			content
		))
	
	def documentDelete(self, blipId, start, end):
		"""
		Requests to delete content in a given range.
		
		@function {public} documentDelete
		@param {String} blipId The blip id that this operation is applied to
		@param {int} start Start of the range
		@param {int} end End of the range
		"""
		self.__insert(Operation(
			DOCUMENT_DELETE,
			self.waveId, self.waveletId, blipId,
			start,
			end-start # = length
		))
	
	def documentElementInsert(self, blipId, index, type, properties):
		"""
		Requests to insert an element at the given position.
		
		@function {public} documentElementInsert
		@param {String} blipId The blip id that this operation is applied to
		@param {int} index Position of the new element
		@param {String} type Element type
		@param {Object} properties Element properties
		"""
		self.__insert(Operation(
			DOCUMENT_ELEMENT_INSERT,
			self.waveId, self.waveletId, blipId,
			index,
			{
				"type": type,
				"properties": properties
			}
		))

	def documentElementDelete(self, blipId, index):
		"""
		Requests to delete an element from the given position.
		
		@function {public} documentElementDelete
		@param {String} blipId The blip id that this operation is applied to
		@param {int} index Position of the element to delete
		"""
		self.__insert(Operation(
			DOCUMENT_ELEMENT_DELETE,
			self.waveId, self.waveletId, blipId,
			index,
			None
		))
	
	def documentElementDelta(self, blipId, index, delta):
		"""
		Requests to apply a delta to the element at the given position.
		
		@function {public} documentElementDelta
		@param {String} blipId The blip id that this operation is applied to
		@param {int} index Position of the element
		@param {Object} delta Delta to apply to the element
		"""
		self.__insert(Operation(
			DOCUMENT_ELEMENT_DELTA,
			self.waveId, self.waveletId, blipId,
			index,
			delta
		))

	def documentElementSetpref(self, blipId, index, key, value):
		"""
		Requests to set a UserPref of the element at the given position.
		
		@function {public} documentElementSetpref
		@param {String} blipId The blip id that this operation is applied to
		@param {int} index Position of the element
		@param {Object} key Name of the UserPref
		@param {Object} value Value of the UserPref
		"""
		self.__insert(Operation(
			DOCUMENT_ELEMENT_SETPREF,
			self.waveId, self.waveletId, blipId,
			index,
			{
				"key": key,
				"value": value
			}
		))
