
/*
 * PyCow - Python to JavaScript with MooTools translator
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

/*
 This script contains some Python-compatibility functions and objects.
*/

len = function (obj) {
	var l = 0;
	switch ($type(obj)) {
		case 'array':
		case 'string':
			return obj.length;
		case 'object':
			for (var key in obj)
				l++;
			return l;
		default:
			return 1;
	}
};
