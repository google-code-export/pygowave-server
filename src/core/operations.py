
from pycow.decorators import Class, Implements
from pycow.utils import Events

DOCUMENT_INSERT = 'DOCUMENT_INSERT'
DOCUMENT_DELETE = 'DOCUMENT_DELETE'
DOCUMENT_REPLACE = 'DOCUMENT_REPLACE'

@Class
class Range(object):
	"""
	Represents a start and end range with integers.
	
	Ranges map positions in the document. A range must have at least a length
	of zero. If zero, the range is considered to be a single point (collapsed).
	"""
	
	def __init__(self, start=0, end=1):
		"""
		Initializes the range with a start and end position.
		
		Args:
		  start: Start index of the range.
		  end: End index of the range.
		
		Raises:
		  ValueError: Value error if the range is invalid (less than zero).
		"""
		self.start = start
		self.end = end
		#if self.end - self.start < 0:
		#	raise ValueError('Range cannot be less than 0')
	
	def __repr__(self):
		return 'Range(%d,%d)' % (self.start, self.end)
	
	def isCollapsed(self):
		""""
		Returns true if this represents a single point as opposed to a range.
		"""
		return self.end == self.start

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
	"""
	
	def __init__(self, op_type, wave_id, wavelet_id, blip_id='', index=-1, prop=None):
		"""
		Initializes this operation with contextual data.
		
		Args:
		  op_type: Type of operation.
		  wave_id: The id of the wave that this operation is to be applied.
		  wavelet_id: The id of the wavelet that this operation is to be applied.
		  blip_id: The optional id of the blip that this operation is to be applied.
		  index: Optional integer index for content-based operations.
		  prop: A weakly typed property object is based on the context of this
		    operation.
		"""
		self.type = op_type
		self.wave_id = wave_id
		self.wavelet_id = wavelet_id
		self.blip_id = blip_id
		self.index = index
		self.tr_index = index # Special property for transformation (client only)
		self.property = prop
		self.tr_property = prop # Special property for transformation (client only)
	
	def isNull(self):
		"""
		Return weather this operation is a null operation i.e. it does not
		change anything.
		
		"""
		if self.type == DOCUMENT_INSERT:
			return len(self.property) == 0
		elif self.type == DOCUMENT_DELETE:
			return self.property == 0
		return False
	
	def indexMove(self):
		"""
		Return how much a concurrent operation's index must be moved to include
		the effects of this operation.
		
		"""
		if self.type == DOCUMENT_INSERT:
			return len(self.property)
		elif self.type == DOCUMENT_DELETE:
			return -self.property
		return 0
	
	def serialize(self):
		"""
		Serialize this operation into a dictionary.
		
		"""
		return {
			"type": self.type,
			"wave_id": self.wave_id,
			"wavelet_id": self.wavelet_id,
			"blip_id": self.blip_id,
			"index": self.index,
			"property": self.property,
		}

	def __repr__(self):
		return "%s(\"%s\",%d(%d),%s(%s))" % (self.type.lower(), self.blip_id, self.index, self.tr_index, repr(self.property), repr(self.tr_property))

	@staticmethod
	def unserialize(obj):
		"""
		Unserialize an operation from a dictionary.
		
		"""
		return Operation(obj["type"], obj["wave_id"], obj["wavelet_id"], obj["blip_id"], obj["index"], obj["property"])

@Implements(Events)
@Class
class OpManager(object):
	"""
	Manages operations: Creating, merging, transforming, serializing.
	
	The operation manager wraps single operations as functions and generates
	operations in-order. It keeps a list of operations and allows
	transformation, merging and serializing.
	
	An OpManager is always associated with exactly one wave/wavelet.
	"""
	
	def __init__(self, wave_id, wavelet_id):
		"""
		Initializes the op manager with a wave and wavelet ID.
		
		Args:
		  wave_id: The ID of the wave.
		  wavelet_id: The ID of the wavelet
		"""
		self.wave_id = wave_id
		self.wavelet_id = wavelet_id
		self.operations = []

	def isEmpty(self):
		"""
		Return true if this manager is not holding operations.
		"""
		return len(self.operations) == 0

	def transform(self, other_op, outgoing):
		"""
		Transform the manager's operations list on behalf of another operation.
		This deletes null operations and splits split operations.
		
		"""
		
		i = 0
		while i < len(self.operations):
			myop = self.operations[i]
			if OpManager.transformSingle(myop, other_op, outgoing):
				if myop.isNull():
					self.fireEvent("beforeOperationsRemoved", {"start": i, "end": i})
					self.operations.pop(i)
					self.fireEvent("afterOperationsRemoved", {"start": i, "end": i})
				else:
					self.fireEvent("operationChanged", {"index": i})
			i += 1
	
	def reverseTransform(self, op, outgoing):
		"""
		Transform the operation on behalf of the manager's operations list.
		Reverse transformation does neither delete Null operations nor it splits
		split operations.
		
		"""
		
		for myop in self.operations:
			OpManager.transformSingle(op, myop, outgoing)
	
	def transformByManager(self, manager, outgoing):
		"""
		Transform the operations list on behalf of another manager.
		"""
		for op in manager.operations:
			self.transform(op, outgoing)
	
	@staticmethod
	def transformSingle(op, other_op, outgoing):
		"""
		Transform a single operation on behalf of another operation.
		Returns true, if the operation was transformed.
		
		"""
		if op.blip_id == other_op.blip_id and op.index != -1 and other_op.index != -1:
			moveit = False
			if op.type == DOCUMENT_DELETE and other_op.type == DOCUMENT_DELETE:
				# other_op contains op
				if op.tr_index >= other_op.tr_index and op.tr_index < other_op.tr_index + other_op.tr_property:
					if op.tr_index + op.tr_property < other_op.tr_index + other_op.tr_property:
						op.property = 0
					else:
						op.property -= other_op.tr_property - (op.tr_index - other_op.tr_index)
						op.index = other_op.tr_index
						if outgoing: op.tr_index = op.index
					if outgoing: op.tr_property = op.property
					return True
				# op contains other_op
				if other_op.tr_index >= op.tr_index and other_op.tr_index < op.tr_index + op.tr_property:
					if other_op.tr_index + other_op.tr_property < op.tr_index + op.tr_property:
						op.property -= other_op.tr_property
					else:
						op.property = other_op.tr_index - op.tr_index
					if outgoing: op.tr_property = op.property
					return True
			if op.index > other_op.index:
				if op.type == DOCUMENT_INSERT and other_op.type == DOCUMENT_DELETE and \
						op.index < other_op.index + other_op.property:
					op.index = other_op.index
					if outgoing: op.tr_index = op.index
					return True
				moveit = True
			elif op.index == other_op.index:
				if outgoing and (op.type != DOCUMENT_INSERT or other_op.type != DOCUMENT_DELETE):
					moveit = True
				if not outgoing and op.type == DOCUMENT_DELETE:
					moveit = True
				if op.type == DOCUMENT_DELETE and other_op.type == DOCUMENT_DELETE:
					moveit = False
				#print outgoing, op, other_op, moveit
			if moveit: # Index moves
				op.index += other_op.indexMove()
				if outgoing: op.tr_index = op.index
				return True
		return False

	def split(self, other_op):
		"""
		Split the manager's operations on behalf of another operation.
		
		"""
		i = 0
		while i < len(self.operations):
			myop = self.operations[i]
			spl = OpManager.splitSingle(myop, other_op)
			if len(spl) > 0:
					print myop, spl
					myop = spl[0]
					self.operations[i] = myop
					self.fireEvent("operationChanged", {"index": i})
					self.fireEvent("beforeOperationsInserted", {"start": i+1, "end": i+len(spl)-1})
					for j in xrange(1, len(spl)):
						self.operations.insert(i+j, spl[j])
					self.fireEvent("afterOperationsInserted", {"start": i+1, "end": i+len(spl)-1})
					i += 1
			i += 1
	
	def reverseSplit(self, op):
		"""
		Split the operation on behalf of the manager's operations list.
		This returns a list of operations. It contains either the original
		operation or new operations that resulted in splitting the input
		operation.
		
		"""
	
		out = [op]
		
		i = 0
		while i < len(out):
			op = out[i]
			for myop in self.operations:
				spl = OpManager.splitSingle(op, myop)
				if len(spl) > 0:
					op = spl[0]
					out[i] = op
					for j in xrange(1, len(spl)):
						out.insert(i+j, spl[j])
			i += 1
		return out
	
	@staticmethod
	def splitSingle(op, other_op):
		"""
		Check if a split is needed. Returns a list of new operations if so, or
		an empty list if not.
		
		It is needed when a user wants to insert text into a block that has just
		been deleted by another user. The delete operation then has to be
		executed "around" the insertion.
		
		"""
		spl = []
		if op.blip_id == other_op.blip_id and op.index != -1 and other_op.index != -1:
			if op.type == DOCUMENT_DELETE and other_op.type == DOCUMENT_INSERT and \
					other_op.tr_index > op.tr_index and other_op.tr_index < op.tr_index + op.tr_property:
				# a delete operation wraps an insert operation
				newop = Operation(
					DOCUMENT_DELETE,
					op.wave_id, op.wavelet_id, op.blip_id,
					op.tr_index,
					other_op.tr_index - op.tr_index
				)
				spl.append(newop)
				newop = Operation(
					DOCUMENT_DELETE,
					op.wave_id, op.wavelet_id, op.blip_id,
					op.tr_index,
					op.tr_property - (other_op.tr_index - op.tr_index)
				)
				newop.tr_index = op.tr_index + other_op.indexMove()
				spl.append(newop)
		return spl
	

	def fetch(self):
		"""
		Returns the pending operations and removes them from this manager.
		"""
		ops = self.operations
		self.fireEvent("beforeOperationsRemoved", {"start": 0, "end": len(ops)-1})
		self.operations = []
		self.fireEvent("afterOperationsRemoved", {"start": 0, "end": len(ops)-1})
		return ops
	
	def put(self, ops):
		"""
		Opposite of fetch. Inserts all given operations into this manager.
		"""
		if len(ops) == 0:
			return
		start = len(self.operations)
		end = start + len(ops) - 1
		self.fireEvent("beforeOperationsInserted", {"start": start, "end": end})
		self.operations.extend(ops)
		self.fireEvent("afterOperationsInserted", {"start": start, "end": end})

	def serialize(self, fetch):
		"""
		Serialize this manager's operations into a list of dictionaries.
		Set fetch to true to also clear this manager.
		
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
		
		"""
		
		ops = []
		
		for op in serial_ops:
			ops.append(Operation.unserialize(op))
		
		self.put(ops)

	def insert(self, newop):
		"""
		Inserts and probably merges an operation into the manager's
		operation list.
		
		"""
		
		# Only merge with the last op (otherwise this may get a bit complicated)
		i = len(self.operations) - 1
		if i >= 0:
			op = self.operations[i]
			if newop.type == DOCUMENT_INSERT and op.type == DOCUMENT_INSERT:
				if newop.index == op.index: # Prepending
					op.property = newop.property + op.property
					self.fireEvent("operationChanged", {"index": i})
					return
				end = op.index + len(op.property)
				if newop.index == end: # Appending
					op.property += newop.property
					self.fireEvent("operationChanged", {"index": i})
					return
				if op.index < newop.index < end: # Inserting
					op.property = op.property[:newop.index-op.index] + newop.property + op.property[newop.index-op.index:]
					self.fireEvent("operationChanged", {"index": i})
					return
			if newop.type == DOCUMENT_DELETE and op.type == DOCUMENT_INSERT:
				if newop.index == op.index: # Delete from start
					l = len(op.property)
					op.property = op.property[newop.property:]
					if op.property == "":
						self.fireEvent("beforeOperationsRemoved", {"start": i, "end": i})
						self.operations.pop(i)
						self.fireEvent("afterOperationsRemoved", {"start": i, "end": i})
					else:
						self.fireEvent("operationChanged", {"index": i})
					newop.property -= l
					if newop.property <= 0: # Deleted less than last op's length
						return
				end = op.index + len(op.property)
				if op.index < newop.index < end: # Delete from within
					l = len(op.property) - (newop.index - op.index + newop.property)
					op.property = op.property[:newop.index - op.index] + op.property[newop.index - op.index + newop.property:]
					self.fireEvent("operationChanged", {"index": i})
					newop.property = -l
					if newop.property <= 0: # Deleted less than last op's length
						return
			if newop.type == DOCUMENT_DELETE and op.type == DOCUMENT_DELETE:
				if newop.index == op.index: # Delete at start
					op.property += newop.property
					self.fireEvent("operationChanged", {"index": i})
					return
				if newop.index == op.index-newop.property: # Deleta at end
					op.index -= newop.property
					op.property += newop.property
					self.fireEvent("operationChanged", {"index": i})
					return
		
		# If we reach this the operation could not be merged, so add it.
		self.fireEvent("beforeOperationsInserted", {"start": i+1, "end": i+1})
		self.operations.append(newop)
		self.fireEvent("afterOperationsInserted", {"start": i+1, "end": i+1})

	# --------------------------------------------------------------------------

	def documentInsert(self, blip_id, index, content):
		"""
		Requests to insert content into a document at a specific location.
	
		Args:
		  blip_id: The blip id that this operation is applied to.
		  index: The position insert the content at in ths document.
		  content: The content to insert.
		"""
		self.insert(Operation(
			DOCUMENT_INSERT,
			self.wave_id, self.wavelet_id, blip_id,
			index,
			content
		))
	
	def documentDelete(self, blip_id, start, end):
		"""
		Requests to delete content in a given range.
		
		Args:
		  blip_id: The blip id that this operation is applied to.
		  start: Start of the range.
		  end: End of the range.
		"""
		self.insert(Operation(
			DOCUMENT_DELETE,
			self.wave_id, self.wavelet_id, blip_id,
			start,
			end-start # = length
		))
