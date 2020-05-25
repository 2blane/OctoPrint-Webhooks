# Replaces any @param in the url with data inside the dictionary
def convert(url, data):
	value = url
	while value.find("@") >= 0:
		start_index = value.find("@")
		# Find the end text by space
		end_index1 = value.find("/", start_index)
		if end_index1 == -1:
			end_index1 = len(value)
		end_index2 = value.find(" ", start_index)
		if end_index2 == -1:
			end_index2 = len(value)
		end_index3 = value.find("?", start_index)
		if end_index3 == -1:
			end_index3 = len(value)
		end_index4 = value.find("#", start_index)
		if end_index4 == -1:
			end_index4 = len(value)
		end_index = min(end_index1, end_index2, end_index3, end_index4)
		value_key = value[start_index + 1:end_index]
		# print(value, start_index, end_index, value_key)
		# Check for dot notation
		components = value_key.split(".")
		current_v = data
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
		if start_index == 0 and end_index == len(value):
			value = current_v
		else:
			value = value.replace(value[start_index:end_index], str(current_v))
	print(url, " -> ", value)
	return value

data = {
	"example": "yoyoma",
	"master": "commander",
	"who": "is there",
	"dot": {
		"a": "alpha",
		"b": "bravo",
		"dot": {
			"1": "one",
			"2": "two",
			"3": "three"
		}
	}
}

convert("https://www.google.com", data)
convert("https://a.b.com/@example", data)
convert("https://a.b.com/yoyo@master", data)
convert("https://a.b.com/w@dot.dot.2/@dot.a?query=@example#frag", data)
convert("https://a.b.com/@dot", data)
convert("https://a.b.com/@master#fragment", data)
convert("https://a.b.com/w@who/apple/berry/@master#fragment/@example?query=quelch", data)
convert("@nice knowing you", data)

