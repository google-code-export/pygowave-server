
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
		self.property = prop

@Implements(Events)
@Class
class OpBuilder(object):
	"""
	Wraps all currently supportable operations as functions.
	
	The operation builder wraps single operations as functions and generates
	operations in-order. It keeps a list of operations and allows transformation
	and merging.
	
	An OpBuilder is always associated with exactly one wave/wavelet.
	"""
	
	def __init__(self, wave_id, wavelet_id):
		"""
		Initializes the op builder with a wave and wavelet ID.
		
		Args:
		  wave_id: The ID of the wave.
		  wavelet_id: The ID of the wavelet
		"""
		self.wave_id = wave_id
		self.wavelet_id = wavelet_id
		self.operations = []

	def transform(self, op):
		"""
		Transform the operations list on behalf of another operation (which has
		happened before this operation).
		"""

	def documentInsert(self, blip_id, index, content):
		"""
		Requests to insert content into a document at a specific location.
	
		Args:
		  blip_id: The blip id that this operation is applied to.
		  index: The position insert the content at in ths document.
		  content: The content to insert.
		"""
		at = len(self.operations)
		self.fireEvent("beforeOperationsInserted", {"start": at, "end": at})
		self.operations.append(Operation(
			DOCUMENT_INSERT,
			self.wave_id, self.wavelet_id, blip_id,
			index,
			content
		))
		self.fireEvent("afterOperationsInserted", {"start": at, "end": at})
	
	def documentDelete(self, blip_id, start, end):
		"""
		Requests to delete content in a given range.
		
		Args:
		  blip_id: The blip id that this operation is applied to.
		  start: Start of the range.
		  end: End of the range.
		"""
		at = len(self.operations)
		self.fireEvent("beforeOperationsInserted", {"start": at, "end": at})
		self.operations.append(Operation(
			DOCUMENT_DELETE,
			self.wave_id, self.wavelet_id, blip_id,
			start,
			end
		))
		self.fireEvent("afterOperationsInserted", {"start": at, "end": at})
	
	def fetch(self):
		"""
		Returns the pending operations and removes them from this builder.
		"""
		ops = self.operations
		self.fireEvent("beforeOperationsRemoved", {"start": 0, "end": len(ops)-1})
		self.operations = []
		self.fireEvent("afterOperationsRemoved", {"start": 0, "end": len(ops)-1})
		return ops
