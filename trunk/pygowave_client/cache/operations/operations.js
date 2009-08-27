/* This file was generated with PyCow - the Python to JavaScript translator */

/* 
 * PyGoWave Client Script a.k.a. Microwave
 * Copyright (C) 2009 by p2k
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * 
 */

window.pygowave = $defined(window.pygowave) ? window.pygowave : {};

/**
 * Operations module.
 * @module pygowave.operations
 */
pygowave.operations = (function() {
	/* from pycow.decorators import Class, Implements */;

	/* from pycow.utils import Events */;

	var DOCUMENT_INSERT = "DOCUMENT_INSERT";

	var DOCUMENT_DELETE = "DOCUMENT_DELETE";

	var DOCUMENT_ELEMENT_INSERT = "DOCUMENT_ELEMENT_INSERT";

	var DOCUMENT_ELEMENT_DELETE = "DOCUMENT_ELEMENT_DELETE";

	var DOCUMENT_ELEMENT_DELTA = "DOCUMENT_ELEMENT_DELTA";

	var DOCUMENT_ELEMENT_SETPREF = "DOCUMENT_ELEMENT_SETPREF";

	/**
	 * Represents a generic operation applied on the server.
	 *
	 * This operation class contains data that is filled in depending on the
	 * operation type.
	 *
	 * It can be used directly, but doing so will not result
	 * in local, transient reflection of state on the blips. In other words,
	 * creating a "delete blip" operation will not remove the blip from the local
	 * context for the duration of this session. It is better to use the OpBased
	 * model classes directly instead.
	 *
	 * @class {private} pygowave.operations.Operation
	 */
	var Operation = new Class({

		/**
		 * Initializes this operation with contextual data.
		 *
		 * @constructor {public} initialize
		 * @param {String} op_type Type of operation
		 * @param {String} wave_id The id of the wave that this operation is to
		 * be applied.
		 * @param {String} wavelet_id The id of the wavelet that this operation is
		 * to be applied.
		 * @param {optional String} blip_id The optional id of the blip that this
		 * operation is to be applied.
		 * @param {optional int} index Optional integer index for content-based
		 * operations.
		 * @param {optional Object} prop A weakly typed property object is based
		 * on the context of this operation.
		 */
		initialize: function (op_type, wave_id, wavelet_id, blip_id, index, prop) {
			if (!$defined(blip_id)) blip_id = "";
			if (!$defined(index)) index = -1;
			if (!$defined(prop)) prop = null;
			this.type = op_type;
			this.wave_id = wave_id;
			this.wavelet_id = wavelet_id;
			this.blip_id = blip_id;
			this.index = index;
			this.property = prop;
		},

		/**
		 * Create a copy of this operation.
		 *
		 * @function {public Boolean} clone
		 */
		clone: function () {
			return new Operation(this.type, this.wave_id, this.wavelet_id, this.blip_id, this.index, this.property);
		},

		/**
		 * Return weather this operation is a null operation i.e. it does not
		 * change anything.
		 *
		 * @function {public Boolean} isNull
		 */
		isNull: function () {
			if (this.type == DOCUMENT_INSERT)
				return len(this.property) == 0;
			else if (this.type == DOCUMENT_DELETE)
				return this.property == 0;
			return false;
		},

		/**
		 * Check if the operation can be influenced by `other_op` and vice-versa.
		 *
		 * @function {public Boolean} isCompatibleTo
		 * @param {Operation} other_op
		 */
		isCompatibleTo: function (other_op) {
			if (this.wave_id != other_op.wave_id || this.wavelet_id != other_op.wavelet_id || this.blip_id != this.blip_id)
				return false;
			return true;
		},

		/**
		 * Returns true, if this op is an insertion operation.
		 *
		 * @function {public Boolean} isInsert
		 */
		isInsert: function () {
			return this.type == DOCUMENT_INSERT || this.type == DOCUMENT_ELEMENT_INSERT;
		},

		/**
		 * Returns true, if this op is a deletion operation.
		 *
		 * @function {public Boolean} isDelete
		 */
		isDelete: function () {
			return this.type == DOCUMENT_DELETE || this.type == DOCUMENT_ELEMENT_DELETE;
		},

		/**
		 * Returns true, if this op is an (attribute) change operation.
		 *
		 * @function {public Boolean} isChange
		 */
		isChange: function () {
			return this.type == DOCUMENT_ELEMENT_DELTA || this.type == DOCUMENT_ELEMENT_SETPREF;
		},

		/**
		 * Returns the length of this operation.
		 * This can be interpreted as the distance a concurrent operation's index
		 * must be moved to include the effects of this operation.
		 *
		 * @function {public int} length
		 */
		length: function () {
			if (this.type == DOCUMENT_INSERT)
				return len(this.property);
			else if (this.type == DOCUMENT_DELETE)
				return this.property;
			else if (this.type == DOCUMENT_ELEMENT_INSERT || this.type == DOCUMENT_ELEMENT_DELETE)
				return 1;
			return 0;
		},

		/**
		 * Delete operations: Sets the amount of deleted characters/elements to
		 * `value`.
		 *
		 * Other operations: No effect.
		 *
		 * @function {public} resize
		 * @param {int} value
		 */
		resize: function (value) {
			if (this.type == DOCUMENT_DELETE)
				this.property = value;
		},

		/**
		 * Serialize this operation into a dictionary.
		 *
		 * @function {public String} serialize
		 */
		serialize: function () {
			return {
				type: this.type,
				wave_id: this.wave_id,
				wavelet_id: this.wavelet_id,
				blip_id: this.blip_id,
				index: this.index,
				property: this.property
			};
		},

		__repr__: function () {
			return "%s(\"%s\",%d,%s)".sprintf(this.type.lower(), this.blip_id, this.index, repr(this.property));
		}
	});
	/**
	 * Unserialize an operation from a dictionary.
	 *
	 * @function {public static Operation} unserialize
	 */
	Operation.unserialize = function (obj) {
		return new Operation(obj.type, obj.wave_id, obj.wavelet_id, obj.blip_id, obj.index, obj.property);
	};

	/**
	 * Manages operations: Creating, merging, transforming, serializing.
	 *
	 * The operation manager wraps single operations as functions and generates
	 * operations in-order. It keeps a list of operations and allows
	 * transformation, merging and serializing.
	 *
	 * An OpManager is always associated with exactly one wave/wavelet.
	 *
	 * @class {public} pygowave.operations.OpManager
	 */
	var OpManager = new Class({
		Implements: Events,
		/**
		 * Fired if an operation in this manager has been changed.
		 * @event onOperationChanged
		 * @param {int} index Index of the changed operation
		 */
		/**
		 * Fired if one or more operations are about to be removed.
		 * @event onBeforeOperationsRemoved
		 * @param {int} start Start index of the removal.
		 * @param {int} end End index of the removal.
		 */
		/**
		 * Fired if one or more operations have been removed.
		 * @event onAfterOperationsRemoved
		 * @param {int} start Start index of the removal.
		 * @param {int} end End index of the removal.
		 */
		/**
		 * Fired if one or more operations are about to be inserted.
		 * @event onBeforeOperationsInserted
		 * @param {int} start Start index of the insertion.
		 * @param {int} end End index of the insertion.
		 */
		/**
		 * Fired if one or more operations have been inserted.
		 * @event onAfterOperationsInserted
		 * @param {int} start Start index of the insertion.
		 * @param {int} end End index of the insertion.
		 */

		/**
		 * Initializes the op manager with a wave and wavelet ID.
		 *
		 * @constructor {public} initialize
		 * @param {String} wave_id The ID of the wave
		 * @param {String} wavelet_id The ID of the wavelet
		 */
		initialize: function (wave_id, wavelet_id) {
			this.wave_id = wave_id;
			this.wavelet_id = wavelet_id;
			this.operations = [];
		},

		/**
		 * Return true if this manager is not holding operations.
		 *
		 * @function {public Boolean} isEmpty
		 */
		isEmpty: function () {
			return len(this.operations) == 0;
		},

		/**
		 * Transform the input operation on behalf of the manager's operations
		 * list. This will simultaneously transform the operations list on behalf
		 * of the input operation.
		 * This method returns a list of applicable operations. This list may be
		 * empty or it may contain any number of new operations (according to
		 * results of deletion, modification and splitting; i.e. the input
		 * operation is not modified by itself).
		 *
		 * @function {public Operation[]} transform
		 * @param {Operation} input_op
		 */
		transform: function (input_op) {
			var new_op = null;
			var op_lst = [input_op.clone()];
			var i = 0;
			while (i < len(this.operations)) {
				var myop = this.operations[i];
				var j = 0;
				while (j < len(op_lst)) {
					var op = op_lst[j];
					if (!op.isCompatibleTo(myop))
						continue;
					var end = null;
					if (op.isDelete() && myop.isDelete()) {
						if (op.index < myop.index) {
							end = op.index + op.length();
							if (end <= myop.index) {
								myop.index -= op.length();
								this.fireEvent("operationChanged", i);
							}
							else if (end < (myop.index + myop.length())) {
								op.resize(myop.index - op.index);
								myop.resize(myop.length() - (end - myop.index));
								myop.index = op.index;
								this.fireEvent("operationChanged", i);
							}
							else {
								op.resize(op.length() - myop.length());
								this.fireEvent("beforeOperationsRemoved", [i, i]);
								this.operations.pop(i);
								this.fireEvent("afterOperationsRemoved", [i, i]);
								i--;
								break;
							}
						}
						else {
							end = myop.index + myop.length();
							if (op.index >= end)
								op.index -= myop.length();
							else if (op.index + op.length() <= end) {
								op_lst.pop(j);
								j--;
								myop.resize(myop.length() - op.length());
								if (myop.isNull()) {
									this.fireEvent("beforeOperationsRemoved", [i, i]);
									this.operations.pop(i);
									this.fireEvent("afterOperationsRemoved", [i, i]);
									i--;
									break;
								}
								else
									this.fireEvent("operationChanged", i);
							}
							else {
								myop.resize(myop.length() - (end - op.index));
								this.fireEvent("operationChanged", i);
								op.resize(op.length() - (end - op.index));
								op.index = myop.index;
							}
						}
					}
					else if (op.isDelete() && myop.isInsert()) {
						if (op.index < myop.index) {
							if (op.index + op.length() <= myop.index) {
								myop.index -= op.length();
								this.fireEvent("operationChanged", i);
							}
							else {
								new_op = op.clone();
								op.resize(myop.index - op.index);
								new_op.resize(new_op.length() - op.length());
								op_lst.insert(j + 1, new_op);
								myop.index -= op.length();
								this.fireEvent("operationChanged", i);
							}
						}
						else
							op.index += myop.length();
					}
					else if (op.isInsert() && myop.isDelete()) {
						if (op.index <= myop.index) {
							myop.index += op.length();
							this.fireEvent("operationChanged", i);
						}
						else if (op.index >= (myop.index + myop.length()))
							op.index -= myop.length();
						else {
							new_op = myop.clone();
							myop.resize(op.index - myop.index);
							this.fireEvent("operationChanged", i);
							new_op.resize(new_op.length() - myop.length());
							this.fireEvent("beforeOperationsInserted", [i + 1, i + 1]);
							this.operations.insert(i + 1, new_op);
							this.fireEvent("afterOperationsInserted", [i + 1, i + 1]);
							op.index = myop.index;
						}
					}
					else if (op.isInsert() && myop.isInsert()) {
						if (op.index <= myop.index) {
							myop.index += op.length();
							this.fireEvent("operationChanged", i);
						}
						else
							op.index += myop.length();
					}
					else if (op.isChange() && myop.isDelete()) {
						if (op.index > myop.index) {
							if (op.index <= (myop.index + myop.length()))
								op.index = myop.index;
							else
								op.index -= myop.length();
						}
					}
					else if (op.isChange() && myop.isInsert()) {
						if (op.index >= myop.index)
							op.index += myop.length();
					}
					else if (op.isDelete() && myop.isChange()) {
						if (op.index < myop.index) {
							if (myop.index <= (op.index + op.length())) {
								myop.index = op.index;
								this.fireEvent("operationChanged", i);
							}
							else {
								myop.index -= op.length();
								this.fireEvent("operationChanged", i);
							}
						}
					}
					else if (op.isInsert() && myop.isChange()) {
						if (op.index <= myop.index) {
							myop.index += op.length();
							this.fireEvent("operationChanged", i);
						}
					}
					j++;
				}
				i++;
			}
			return op_lst;
		},

		/**
		 * Returns the pending operations and removes them from this manager.
		 *
		 * @function {public Operation[]} fetch
		 */
		fetch: function () {
			var ops = this.operations;
			this.fireEvent("beforeOperationsRemoved", [0, len(ops) - 1]);
			this.operations = [];
			this.fireEvent("afterOperationsRemoved", [0, len(ops) - 1]);
			return ops;
		},

		/**
		 * Opposite of fetch. Inserts all given operations into this manager.
		 *
		 * @function {public} put
		 * @param {Operation[]} ops
		 */
		put: function (ops) {
			if (len(ops) == 0)
				return;
			var start = len(this.operations);
			var end = start + len(ops) - 1;
			this.fireEvent("beforeOperationsInserted", [start, end]);
			this.operations.extend(ops);
			this.fireEvent("afterOperationsInserted", [start, end]);
		},

		/**
		 * Serialize this manager's operations into a list of dictionaries.
		 * Set fetch to true to also clear this manager.
		 *
		 * @function {public Object[]} serialize
		 * @param {optional Boolean} fetch
		 */
		serialize: function (fetch) {
			if (!$defined(fetch)) fetch = false;
			if (fetch)
				var ops = this.fetch();
			else
				ops = this.operations;
			var out = [];
			for (var __iter0_ = new _Iterator(ops); __iter0_.hasNext();) {
				var op = __iter0_.next();
				out.append(op.serialize());
			}
			delete __iter0_;
			return out;
		},

		/**
		 * Unserialize a list of dictionaries to operations and add them to this
		 * manager.
		 *
		 * @function {public} unserialize
		 * @param {Object[]} serial_ops
		 */
		unserialize: function (serial_ops) {
			var ops = [];
			for (var __iter0_ = new _Iterator(serial_ops); __iter0_.hasNext();) {
				var op = __iter0_.next();
				ops.append(Operation.unserialize(op));
			}
			delete __iter0_;
			this.put(ops);
		},

		/**
		 * Inserts and probably merges an operation into the manager's
		 * operation list.
		 *
		 * @function {private} __insert
		 * @param {Operation} newop
		 */
		__insert: function (newop) {
			var op = null;
			var i = 0;
			if (newop.type == DOCUMENT_ELEMENT_DELTA) {
				for (var __iter0_ = new XRange(len(this.operations)); __iter0_.hasNext();) {
					i = __iter0_.next();
					op = this.operations[i];
					if (op.type == DOCUMENT_ELEMENT_DELTA && newop.property.id == op.property.id) {
						op.property.delta.update(newop.property.delta);
						this.fireEvent("operationChanged", i);
						return;
					}
				}
				delete __iter0_;
			}
			i = len(this.operations) - 1;
			if (i >= 0) {
				op = this.operations[i];
				if (newop.type == DOCUMENT_INSERT && op.type == DOCUMENT_INSERT) {
					if (newop.index == op.index) {
						op.property = newop.property + op.property;
						this.fireEvent("operationChanged", i);
						return;
					}
					var end = op.index + len(op.property);
					if (newop.index == end) {
						op.property += newop.property;
						this.fireEvent("operationChanged", i);
						return;
					}
					if (op.index < newop.index && newop.index < end) {
						op.property = op.property.slice(0, newop.index - op.index) + newop.property + op.property.slice(newop.index - op.index);
						this.fireEvent("operationChanged", i);
						return;
					}
				}
				if (newop.type == DOCUMENT_DELETE && op.type == DOCUMENT_INSERT) {
					if (newop.index == op.index) {
						var l = len(op.property);
						op.property = op.property.slice(newop.property);
						if (op.property == "") {
							this.fireEvent("beforeOperationsRemoved", [i, i]);
							this.operations.pop(i);
							this.fireEvent("afterOperationsRemoved", [i, i]);
						}
						else
							this.fireEvent("operationChanged", i);
						newop.property -= l;
						if (newop.property <= 0)
							return;
					}
					end = op.index + len(op.property);
					if (op.index < newop.index && newop.index < end) {
						l = len(op.property) - (newop.index - op.index + newop.property);
						op.property = op.property.slice(0, newop.index - op.index) + op.property.slice(newop.index - op.index + newop.property);
						this.fireEvent("operationChanged", i);
						newop.property = -l;
						if (newop.property <= 0)
							return;
					}
				}
				if (newop.type == DOCUMENT_DELETE && op.type == DOCUMENT_DELETE) {
					if (newop.index == op.index) {
						op.property += newop.property;
						this.fireEvent("operationChanged", i);
						return;
					}
					if (newop.index == (op.index - newop.property)) {
						op.index -= newop.property;
						op.property += newop.property;
						this.fireEvent("operationChanged", i);
						return;
					}
				}
			}
			this.fireEvent("beforeOperationsInserted", [i + 1, i + 1]);
			this.operations.append(newop);
			this.fireEvent("afterOperationsInserted", [i + 1, i + 1]);
		},

		/**
		 * Requests to insert content into a document at a specific location.
		 *
		 * @function {public} documentInsert
		 * @param {String} blip_id The blip id that this operation is applied to
		 * @param {int} index The position insert the content at in ths document
		 * @param {String} content The content to insert
		 */
		documentInsert: function (blip_id, index, content) {
			this.__insert(new Operation(DOCUMENT_INSERT, this.wave_id, this.wavelet_id, blip_id, index, content));
		},

		/**
		 * Requests to delete content in a given range.
		 *
		 * @function {public} documentDelete
		 * @param {String} blip_id The blip id that this operation is applied to
		 * @param {int} start Start of the range
		 * @param {int} end End of the range
		 */
		documentDelete: function (blip_id, start, end) {
			this.__insert(new Operation(DOCUMENT_DELETE, this.wave_id, this.wavelet_id, blip_id, start, end - start));
		},

		/**
		 * Requests to insert an element at the given position.
		 *
		 * @function {public} documentElementInsert
		 * @param {String} blip_id The blip id that this operation is applied to
		 * @param {int} index Position of the new element
		 * @param {String} type Element type
		 * @param {Object} properties Element properties
		 */
		documentElementInsert: function (blip_id, index, type, properties) {
			this.__insert(new Operation(DOCUMENT_ELEMENT_INSERT, this.wave_id, this.wavelet_id, blip_id, index, {
				type: type,
				properties: properties
			}));
		},

		/**
		 * Requests to delete an element from the given position.
		 *
		 * @function {public} documentElementDelete
		 * @param {String} blip_id The blip id that this operation is applied to
		 * @param {int} index Position of the element to delete
		 */
		documentElementDelete: function (blip_id, index) {
			this.__insert(new Operation(DOCUMENT_ELEMENT_DELETE, this.wave_id, this.wavelet_id, blip_id, index, null));
		},

		/**
		 * Requests to apply a delta to the element at the given position.
		 *
		 * @function {public} documentElementDelta
		 * @param {String} blip_id The blip id that this operation is applied to
		 * @param {int} index Position of the element
		 * @param {Object} delta Delta to apply to the element
		 */
		documentElementDelta: function (blip_id, index, delta) {
			this.__insert(new Operation(DOCUMENT_ELEMENT_DELTA, this.wave_id, this.wavelet_id, blip_id, index, delta));
		},

		/**
		 * Requests to set a UserPref of the element at the given position.
		 *
		 * @function {public} documentElementSetpref
		 * @param {String} blip_id The blip id that this operation is applied to
		 * @param {int} index Position of the element
		 * @param {Object} key Name of the UserPref
		 * @param {Object} value Value of the UserPref
		 */
		documentElementSetpref: function (blip_id, index, key, value) {
			this.__insert(new Operation(DOCUMENT_ELEMENT_SETPREF, this.wave_id, this.wavelet_id, blip_id, index, {
				key: key,
				value: value
			}));
		}
	});

	return {
		OpManager: OpManager,
		DOCUMENT_INSERT: DOCUMENT_INSERT,
		DOCUMENT_DELETE: DOCUMENT_DELETE,
		DOCUMENT_ELEMENT_INSERT: DOCUMENT_ELEMENT_INSERT,
		DOCUMENT_ELEMENT_DELETE: DOCUMENT_ELEMENT_DELETE,
		DOCUMENT_ELEMENT_DELTA: DOCUMENT_ELEMENT_DELTA,
		DOCUMENT_ELEMENT_SETPREF: DOCUMENT_ELEMENT_SETPREF
	};
})();
