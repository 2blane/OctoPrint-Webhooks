# def replace_dict_with_data(d, v):
# 	looping_over = d
# 	if type(d) is list:
# 		looping_over = range(0, len(d))
# 	for key in looping_over:
# 		value = d[key]
# 		if type(value) is dict:
# 			d[key] = replace_dict_with_data(value, v)
# 		elif type(value) is str:
# 			# Loop until all @params are replaced
# 			while type(d[key]) is str and d[key].find("@") >= 0:
# 				start_index = d[key].find("@")
# 				# Find the end text by space
# 				end_index = d[key].find(" ", start_index)
# 				if end_index == -1:
# 					end_index = len(d[key])
# 				value_key = d[key][start_index + 1:end_index]
# 				# Check for dot notation
# 				components = value_key.split(".")
# 				current_v = v
# 				comp_found = True
# 				for ic in range(0, len(components)):
# 					comp = components[ic]
# 					if comp in current_v:
# 						current_v = current_v[comp]
# 					else:
# 						comp_found = False
# 						break
# 				if not comp_found:
# 					current_v = ""
# 				if start_index == 0 and end_index == len(d[key]):
# 					d[key] = current_v
# 				else:
# 					d[key] = d[key].replace(d[key][start_index:end_index], str(current_v))
# 		elif type(value) is list:
# 			d[key] = replace_dict_with_data(value, v)
# 	return d
#
# data = {
# 	"abc": "123",
# 	"token": "Bearer @access_token",
# 	"extra": "@extra",
# 	"message": {
# 		"version": "@version",
# 		"command": ["@c1", "@c2", "@c3", {
# 			"inner": "@inner",
# 			"outer": "outer here"
# 		}],
# 		"data": {
# 			"prop": "prop-@prop"
# 		},
# 		"arr": "@arr"
# 	},
# 	"yeoman": "yipyip",
# 	"hello": 123,
# 	"under": 9123.1238913,
# 	"state_text": "@state.flags.operational",
# 	"invalid": "@bumper_cars",
# 	"zzz": "@m1 - @m2 : @m3 and possible @m4 @m5",
# 	"file1": "@snapshot"
# }
# values = {
# 	"access_token": "28sdf9123nsdf923",
# 	"extra": {
# 		"some": "extra data",
# 		"and": "some more"
# 	},
# 	"version": "1.0",
# 	"prop": "selector",
# 	"arr": ["1", "2", "3"],
# 	"c1": "cat",
# 	"c2": "dog",
# 	"c3": ["mouse", "hen"],
# 	"inner": "inner here",
# 	"state": {
# 		"text": "Operational",
# 		"flags": {
# 			"operational": True,
# 			"printing": False,
# 			"cancelling": False,
# 			"pausing": False,
# 			"Resuming": False
# 		}
# 	},
# 	"m1": "50",
# 	"m2": 100,
# 	"m3": "50%",
# 	"m5": "yep"
# }
#
# data = {"topic": "@topic", "message": "@message", "deviceIdentifier": "@deviceIdentifier", "apiSecret": "@apiSecret", "extra": "@extra"}
# values = {"deviceIdentifier": "JackPrint1", "currentTime": 1588606726, "job": {"file": {"date": None, "origin": None, "size": None, "name": None, "path": None}, "estimatedPrintTime": None, "user": None, "filament": {"volume": None, "length": None}, "lastPrintTime": None}, "extra": {"origin": "local", "popup": True, "name": "example.gcode", "time": 50.237335886, "owner": "example_user", "path": "example.gcode", "size": 242038}, "apiSecret": "439549e69f79c7e2bd8bf7763f7425bd", "offsets": {}, "topic": "User Action Needed", "state": {"text": "Operational", "flags": {"cancelling": False, "paused": False, "operational": True, "pausing": False, "printing": False, "resuming": False, "sdReady": True, "error": False, "ready": True, "finishing": False, "closedOrError": False}}, "currentZ": None, "progress": {"completion": None, "filepos": None, "printTime": None, "printTimeLeft": None, "printTimeOrigin": None}, "message": "User action is needed. You might need to change the filament color."}
#
# print(replace_dict_with_data(data, values))

import sys

def convert(unicode_or_str):
	is_string = False
	if sys.version_info[0] >= 3:
		print("Py3")
		if type(unicode_or_str) is str:
			is_string = True
	else:
		print("Py2")
		if type(unicode_or_str) is unicode or type(unicode_or_str) is str:
			is_string = True
	print(is_string)

convert(u"hello")
convert("world")
convert(1234)
convert(["yoyo", "ma"])
convert({"yes":"sir"})
