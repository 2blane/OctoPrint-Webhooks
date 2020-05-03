def replace_dict_with_data(d, v):
	looping_over = d
	if type(d) is list:
		looping_over = range(0, len(d))
	for key in looping_over:
		value = d[key]
		if type(value) is dict:
			d[key] = replace_dict_with_data(value, v)
		elif type(value) is str:
			# Loop until all @params are replaced
			while type(d[key]) is str and d[key].find("@") >= 0:
				start_index = d[key].find("@")
				# Find the end text by space
				end_index = d[key].find(" ", start_index)
				if end_index == -1:
					end_index = len(d[key])
				value_key = d[key][start_index + 1:end_index]
				# Check for dot notation
				components = value_key.split(".")
				current_v = v
				comp_found = True
				for ic in range(0, len(components)):
					comp = components[ic]
					if comp in current_v:
						current_v = current_v[comp]
					else:
						comp_found = False
						break
				if not comp_found:
					current_v = ""
				if start_index == 0 and end_index == len(d[key]):
					d[key] = current_v
				else:
					d[key] = d[key].replace(d[key][start_index:end_index], str(current_v))
		elif type(value) is list:
			d[key] = replace_dict_with_data(value, v)
	return d

data = {
	"abc": "123",
	"token": "Bearer @access_token",
	"extra": "@extra",
	"message": {
		"version": "@version",
		"command": ["@c1", "@c2", "@c3", {
			"inner": "@inner",
			"outer": "outer here"
		}],
		"data": {
			"prop": "prop-@prop"
		},
		"arr": "@arr"
	},
	"yeoman": "yipyip",
	"hello": 123,
	"under": 9123.1238913,
	"state_text": "@state.flags.operational",
	"invalid": "@bumper_cars",
	"zzz": "@m1 - @m2 : @m3 and possible @m4 @m5",
	"file1": "@snapshot"
}
values = {
	"access_token": "28sdf9123nsdf923",
	"extra": {
		"some": "extra data",
		"and": "some more"
	},
	"version": "1.0",
	"prop": "selector",
	"arr": ["1", "2", "3"],
	"c1": "cat",
	"c2": "dog",
	"c3": ["mouse", "hen"],
	"inner": "inner here",
	"state": {
		"text": "Operational",
		"flags": {
			"operational": True,
			"printing": False,
			"cancelling": False,
			"pausing": False,
			"Resuming": False
		}
	},
	"m1": "50",
	"m2": 100,
	"m3": "50%",
	"m5": "yep"
}
print(replace_dict_with_data(data, values))
