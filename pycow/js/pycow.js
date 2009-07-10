
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

repr = function (obj) {
	if ($defined(obj.__repr__))
		return obj.__repr__();
	else
		return JSON.encode(obj);
};

/*  
 *  Javascript sprintf
 *  http://www.webtoolkit.info/
 *
 */

sprintfWrapper = {
	init : function () {
		if (!$defined(arguments))
			return null;
		if (arguments.length < 1)
			return null;
		if ($type(arguments[0]) != "string")
			return null;
		if (!$defined(RegExp))
			return null;
		
		var string = arguments[0];
		var exp = new RegExp(/(%([%]|(\-)?(\+|\x20)?(0)?(\d+)?(\.(\d)?)?([bcdfosxX])))/g);
		var matches = new Array();
		var strings = new Array();
		var convCount = 0;
		var stringPosStart = 0;
		var stringPosEnd = 0;
		var matchPosEnd = 0;
		var newString = '';
		var match = null;
		
		while ((match = exp.exec(string))) {
			if (match[9])
				convCount += 1;
				
			stringPosStart = matchPosEnd;
			stringPosEnd = exp.lastIndex - match[0].length;
			strings[strings.length] = string.substring(stringPosStart, stringPosEnd);
			
			matchPosEnd = exp.lastIndex;
			matches[matches.length] = {
				match: match[0],
				left: match[3] ? true : false,
				sign: match[4] || '',
				pad: match[5] || ' ',
				min: match[6] || 0,
				precision: match[8],
				code: match[9] || '%',
				negative: parseInt(arguments[convCount]) < 0 ? true : false,
				argument: String(arguments[convCount])
			};
		}
		strings[strings.length] = string.substring(matchPosEnd);

		if (matches.length == 0)
			return string;
		if ((arguments.length - 1) < convCount)
			return null;

		var code = null;
		var match = null;
		var i = null;

		for (i=0; i<matches.length; i++) {
			if (matches[i].code == '%') { substitution = '%' }
			else if (matches[i].code == 'b') {
				matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(2));
				substitution = sprintfWrapper.convert(matches[i], true);
			}
			else if (matches[i].code == 'c') {
				matches[i].argument = String(String.fromCharCode(parseInt(Math.abs(parseInt(matches[i].argument)))));
				substitution = sprintfWrapper.convert(matches[i], true);
			}
			else if (matches[i].code == 'd') {
				matches[i].argument = String(Math.abs(parseInt(matches[i].argument)));
				substitution = sprintfWrapper.convert(matches[i]);
			}
			else if (matches[i].code == 'f') {
				matches[i].argument = String(Math.abs(parseFloat(matches[i].argument)).toFixed(matches[i].precision ? matches[i].precision : 6));
				substitution = sprintfWrapper.convert(matches[i]);
			}
			else if (matches[i].code == 'o') {
				matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(8));
				substitution = sprintfWrapper.convert(matches[i]);
			}
			else if (matches[i].code == 's') {
				matches[i].argument = matches[i].argument.substring(0, matches[i].precision ? matches[i].precision : matches[i].argument.length)
				substitution = sprintfWrapper.convert(matches[i], true);
			}
			else if (matches[i].code == 'x') {
				matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(16));
				substitution = sprintfWrapper.convert(matches[i]);
			}
			else if (matches[i].code == 'X') {
				matches[i].argument = String(Math.abs(parseInt(matches[i].argument)).toString(16));
				substitution = sprintfWrapper.convert(matches[i]).toUpperCase();
			}
			else {
				substitution = matches[i].match;
			}
			
			newString += strings[i];
			newString += substitution;
		}
		
		newString += strings[i];
		return newString;
	},
	convert : function(match, nosign){
		if (nosign)
			match.sign = '';
		else
			match.sign = match.negative ? '-' : match.sign;
		
		var l = match.min - match.argument.length + 1 - match.sign.length;
		var pad = new Array(l < 0 ? 0 : l).join(match.pad);
		if (!match.left) {
			if (match.pad == "0" || nosign)
				return match.sign + pad + match.argument;
			else
				return pad + match.sign + match.argument;
		} else {
			if (match.pad == "0" || nosign)
				return match.sign + match.argument + pad.replace(/0/g, ' ');
			else
				return match.sign + match.argument + pad;
		}
	}
};
 
sprintf = sprintfWrapper.init;

String.implement({
	sprintf: function () {
		var args = $A(arguments);
		args.splice(0, 0, this);
		return sprintfWrapper.init.apply(this, args);
	}
});

String.alias("toLowerCase", "lower");
