extra = {"popup":True}
#extra = {}
#extra = "hello world"
#extra = None

print(type(extra), type(extra) is dict)

if type(extra) is dict and "popup" in extra:
	print("popup is in extra")
else:
	print("not in popup")
