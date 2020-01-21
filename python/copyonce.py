#-*- encoding: utf-8 -*-

import sqlite3
import hashlib
import os
from os import path
import shutil
import sys
import argparse

def table_exist(cur, name):
	cur.execute("SELECT tbl_name FROM sqlite_master WHERE type='table' AND tbl_name='%s'" % name)
	return None != cur.fetchone()

def table_create(cur, name):
	sql = """CREATE TABLE [%s](
		[id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
		[hash] TEXT NOT NULL,
		[filename] TEXT NOT NULL,
		[ctime] TIMESTAMP NOT NULL)
	""" % name
	cur.execute(sql)
	cur.execute("CREATE INDEX [idx_%s] ON [%s]([hash])" % (name, name))

def hash_exist(cur, hashstr):
	name = "tbl_%s" % hashstr[:2]
	if not table_exist(cur, name):
		return False
	cur.execute("SELECT id FROM %s WHERE hash='%s'" %(name, hashstr))
	return None != cur.fetchone()

def hash_append(cur, hashstr, filename):
	name = "tbl_%s" % hashstr[:2]
	if not table_exist(cur, name):
		table_create(cur, name)
	sql = "INSERT INTO %s(hash, filename, ctime) VALUES('%s', '%s', datetime(CURRENT_TIMESTAMP, 'localtime'))" % (name, hashstr, filename.replace("'", "''"))
	# print(sql)
	cur.execute(sql)

def file_hash(filename):
	with open(filename, 'rb') as f:
		h = hashlib.sha1()
		while True:
			s = f.read(64*1024)
			if s == b'':
				break
			h.update(s)
		return h.hexdigest()

def solename(name):
	t = path.splitext(name)
	i = 0
	while True:
		s = "%s%d%s" % (t[0], i, t[1])
		if not path.exists(s):
			return s
		i = i + 1

def match_filter(ext, filters=[]):
	if len(filters)==0:
		return True

	return ext in filters


def copyonefile(conn, cur, root, name, folder, tofolder, autoremove):
	fullname = path.join(root, name)
	hashstr = file_hash(fullname)
	if not hash_exist(cur, hashstr):
		todir = path.relpath(root, folder)
		toname = path.join(tofolder, todir, name)
		if path.exists(toname):
			toname = solename(toname)
		todir = path.split(toname)[0]
		if not path.exists(todir):
			os.makedirs(todir)
		print("复制到", toname)
		shutil.copy(fullname, toname)
		hash_append(cur, hashstr, name)
		conn.commit()
	else:
		print("重复文件:", fullname)
	if autoremove:
		os.remove(fullname)

def copyfileonce(filename, tofolder, autoremove=False):
	conn = sqlite3.connect("copyonce.dat")
	cur = conn.cursor()

	root, name = path.split(filename)
	copyonefile(conn, cur, root, name, root, tofolder, autoremove)

	conn.close()


def copyonce(folder, tofolder, filters=[], autoremove=False):
	if path.exists(folder) and path.isfile(folder):
		copyfileonce(folder, tofolder, autoremove)
		return

	conn = sqlite3.connect("copyonce.dat")
	cur = conn.cursor()

	for root, dirs, files in os.walk(folder):
		for name in files:
			ext = path.splitext(name)[1]
			if match_filter(ext, filters):
				copyonefile(conn, cur, root, name, folder, tofolder, autoremove)

	conn.close()

def string2bool(s):
	if s in ['y', 'Y', '1', "True", "true", "Yes", "yes"]: return True
	return False

def main():
	parser = argparse.ArgumentParser(description='去重备份工具')
	parser.add_argument('folder', help='要备份的源路径')
	parser.add_argument('-o', '--tofolder', required=True, help='要备份的目标路径')
	parser.add_argument('-a', '--autoremove', action='store_true', help='备份成功后是否自动删除源文件')
	parser.add_argument('--filters', help='设置要备份的文件后缀(例如:".txt|.jpg|.png')

	args = parser.parse_args()

	filters = []
	if args.filters:
		filters = args.filters.split('|')

	# print('folder', args.folder)
	# print('tofolder', args.tofolder)
	# print('filters', filters)
	# print('autoremove', args.autoremove)

	copyonce(args.folder, args.tofolder, filters, args.autoremove)


if __name__ == "__main__":
	main()