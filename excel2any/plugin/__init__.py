import json

def toFile(data, args):
	f = open(args['output'], "w")
	json.dump(data, f)
	f.close()

def toValue(ctx, raw):
	return raw.value



