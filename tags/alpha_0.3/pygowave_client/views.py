
#
# PyGoWave Server - The Python Google Wave Server
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

from django.conf import settings as django_settings
from django.http import Http404, HttpResponse, HttpResponseNotModified

from pygowave_client.settings import *

from datetime import datetime, timedelta
import os, gzip

def compile_and_cache(srcfile, cachefile, package, namespace):
	if os.path.exists(srcfile + ".py"):
		srcfile += ".py"
		mtime = datetime.utcfromtimestamp(os.path.getmtime(srcfile))
		if not os.path.exists(cachefile) or os.path.getmtime(srcfile) > os.path.getmtime(cachefile):
			from pycow import translate_file, ParseError # Import has been placed here, so PyCow is not a dependency
			if not os.path.exists(CACHE_FOLDER + package):
				os.mkdir(CACHE_FOLDER + package)
			try:
				translate_file(srcfile, cachefile, namespace=namespace, warnings=False)
				return ("changed", mtime)
			except ParseError, e:
				os.unlink(cachefile)
				return ("error", PARSE_ERROR_MESSAGE % (srcfile, e.value))
	elif os.path.exists(srcfile + ".js"):
		srcfile += ".js"
		mtime = datetime.utcfromtimestamp(os.path.getmtime(srcfile))
		if not os.path.exists(cachefile) or os.path.getmtime(srcfile) > os.path.getmtime(cachefile):
			if not os.path.exists(CACHE_FOLDER + package):
				os.mkdir(CACHE_FOLDER + package)
			# Just symlink/copy for now; TODO: offer minification
			if os.name == "posix":
				target = os.path.relpath(srcfile, os.path.dirname(cachefile))
				os.symlink(target, cachefile)
			else:
				open(cachefile, 'w').write(open(srcfile, 'r').read())
			return ("changed", mtime)
	else:
		raise Http404
	return ("unchanged", mtime)

def view_module(request, package, module):
	"""
	Return the requested JavaScript module, converts files with .py ending via
	PyCow and caches results. Supports If-Modified-Since and gzip compression.
	
	"""
	
	namespace = "pygowave.%s" % (package)
	module = package + os.path.sep + module
	cachefile = CACHE_FOLDER + module + ".js"
	srcfile = SRC_FOLDER + module
	
	result, mtime = compile_and_cache(srcfile, cachefile, package, namespace)
	
	if result == "error":
		return HttpResponse(mtime, mimetype="text/javascript")
	
	# Handle If-Modified-Since
	if request.META.has_key("HTTP_IF_MODIFIED_SINCE"):
		try:
			mstime = datetime.strptime(request.META["HTTP_IF_MODIFIED_SINCE"], RFC_1123_DATETIME)
			if mtime <= mstime:
				return HttpResponseNotModified()
		except ValueError:
			pass
	
	response = HttpResponse(mimetype="text/javascript")
	response["Last-Modified"] = mtime.strftime(RFC_1123_DATETIME)
	
	# Support for gzip
	if "gzip" in request.META["HTTP_ACCEPT_ENCODING"].split(","):
		if not os.path.exists(cachefile + ".gz") or os.path.getmtime(cachefile) > os.path.getmtime(cachefile + ".gz"):
			gzip.open(cachefile + ".gz", 'wb').write(open(cachefile, 'r').read())
		cachefile = cachefile + ".gz"
		response["Content-Encoding"] = "gzip"

	response.write(open(cachefile, "r").read())

	return response

def view_combined(request):
	"""
	Return a concatenation of all pygowave_client scripts.
	
	"""
	
	# Compile all
	changed = False
	for package, modules in STATIC_LOAD_ORDER:
		for module in modules:
			namespace = "pygowave.%s" % (package)
			module = package + os.path.sep + module
			cachefile = CACHE_FOLDER + module + ".js"
			srcfile = SRC_FOLDER + module
			
			result, mtime = compile_and_cache(srcfile, cachefile, package, namespace)
			
			if result == "error":
				return HttpResponse(mtime, mimetype="text/javascript")
			elif result == "changed":
				changed = True
	
	cachefile = CACHE_FOLDER + "pygowave_client_combined.js"
	
	# Combine
	if changed or not os.path.exists(cachefile):
		cf = open(cachefile, 'w')
		first = True
		for package, modules in STATIC_LOAD_ORDER:
			for module in modules:
				modulecachefile = CACHE_FOLDER + package + os.path.sep + module + ".js"
				mcf = open(modulecachefile, 'r')
				infoline = "/* --- pygowave.%s.%s --- */\n\n" % (package, module)
				if first:
					first = False
					# Leave license information; stop after it
					line = mcf.readline()
					while (line.startswith("/*") and not line.startswith("/**")) or line.startswith(" *") or line == "\n":
						cf.write(line)
						line = mcf.readline()
					cf.write(infoline)
					cf.write(line)
				else:
					# Strip license information
					line = mcf.readline()
					while (line.startswith("/*") and not line.startswith("/**")) or line.startswith(" *") or line == "\n":
						line = mcf.readline()
					cf.write("\n" + infoline)
					cf.write(line)
				cf.write(mcf.read())
				mcf.close()
		cf.close()
	
	# Handle If-Modified-Since
	mtime = datetime.utcfromtimestamp(os.path.getmtime(cachefile))
	if request.META.has_key("HTTP_IF_MODIFIED_SINCE"):
		try:
			mstime = datetime.strptime(request.META["HTTP_IF_MODIFIED_SINCE"], RFC_1123_DATETIME)
			if mtime <= mstime:
				return HttpResponseNotModified()
		except ValueError:
			pass

	response = HttpResponse(mimetype="text/javascript")
	response["Last-Modified"] = mtime.strftime(RFC_1123_DATETIME)

	# Support for gzip
	if "gzip" in request.META["HTTP_ACCEPT_ENCODING"].split(","):
		if not os.path.exists(cachefile + ".gz") or os.path.getmtime(cachefile) > os.path.getmtime(cachefile + ".gz"):
			gzip.open(cachefile + ".gz", 'wb').write(open(cachefile, 'r').read())
		cachefile = cachefile + ".gz"
		response["Content-Encoding"] = "gzip"
	
	response.write(open(cachefile, "r").read())

	return response
