#-*- encoding: utf-8

import os
import re
import os.path
import shutil
import json
import sys

source_file_exts = (".cpp", ".c", ".cc", ".cxx")
prog = re.compile("^\s*#include\s+[<\"]([a-zA-Z_\-0-9/\\\.]+)[>\"]")

inc_directories = []
unscan_files = []
scaned_files = []
absent_files = []


def find_file(filename):
	if os.path.exists(filename):
		return filename

	for d in inc_directories:
		fullname = d.rstrip('/\\') + "/" + filename.lstrip('/\\')
		if os.path.exists(fullname):
			return fullname
	absent_files.append(filename)
	return None


def scan_file(filename):
	# print("scan: " + filename)
	f = open(filename, "r")
	lines = f.readlines()
	f.close()
	for line in lines:
		m = prog.match(line)
		if m:
			filename = m.group(1)
			fullname = find_file(filename)
			if fullname != None: 
				add_unscan_file(filename)

def add_inc_directory(folder):
	if folder not in inc_directories:
		inc_directories.append(folder)

def add_unscan_file(filename):
	if filename not in unscan_files:
		unscan_files.append(filename)

def find_source_file(filename):
	r = os.path.split(filename)
	name = os.path.splitext(r[1])
	for v in source_file_exts:
		fullname = find_file(name[0] + v)
		if fullname != None:	
			return name[0] + v, fullname
	return None, None

def is_source_file(filename):
	r = os.path.splitext(filename)
	return r[1] in source_file_exts

def scan_all():
	while len(unscan_files) > 0:
		filename = unscan_files.pop()
		fullname = find_file(filename)
		if fullname != None and fullname not in scaned_files:
			scaned_files.append(fullname)
			scan_file(fullname)
		if not is_source_file(filename):
			filename, fullname = find_source_file(filename)
			if fullname != None and fullname not in scaned_files:
				scaned_files.append(fullname)
				scan_file(fullname)

def main():
	if len(sys.argv) != 2:
		print("usage: pbcp config.json")
		return -1

	dat = json.load(open(sys.argv[1], "r"))
	if "includes" in dat:
		for v in dat["includes"]:
			add_inc_directory(v)
	if "files" in dat:
		for v in dat["files"]:
			add_unscan_file(v)

	output = "output"
	if "output" in dat:
		output = dat["output"]
	output.rstrip("/\\")

	scan_all()

	for v in scaned_files:
		dst = output + "/" + v
		r = os.path.split(dst)
		if not os.path.exists(r[0]):
			os.makedirs(r[0])
		shutil.copyfile(v, dst)

def test():
	add_inc_directory("Foundation/src")
	add_inc_directory("Foundation/include")
	add_unscan_file("Foundation/src/Bugcheck.cpp")
	scan_all()

if __name__ == "__main__":
	main()
	# test()


# 功能: 从某个c/c++工程中抽取部分模块的工具
# 用法: 配置如下样式的json文件, 运行pbcp json文件
# {
# 	"includes" : [
# 		"Foundation/include",
# 		"Foundation/src",
# 		"Net/include",
# 		"Net/src",
# 		"JSON/include",
# 		"JSON/src",
# 		"Util/include",
# 		"Util/src",
# 		"XML/include",
# 		"XML/src"
# 	],
# 	"files" : [
# 		"StreamSocket.cpp"
# 	],
# 	"output" : "minipoco"
# }