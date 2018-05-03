#-*- encoding: utf-8

from openpyxl import load_workbook
from openpyxl import cell
import re
import plugin

class xlsx2anyError(Exception):
	def __init__(self, name, title, row, column):
		self.name = name 
		self.title = title
		self.row = row
		self.column = column

	def __str__(self):
		return "ERROR: row=%d, column=%s in <%s>[%s]" % (self.row, self.column, self.name, self.title)

def isEmptyRow(row):
	for i in row:
		if not isinstance(i, cell.read_only.EmptyCell):
			return False
	return True

def isEmptyCell(data):
	if isinstance(data, cell.read_only.EmptyCell):
		return True
	if data.value == None:
		return True
	return False


class xcell(object):
	def __init__(self, sheet, row, column, value):
		self.sheet = sheet
		self.value = value 
		self.row = row
		self.column = column

class xsheet(object):

	def __init__(self, book, ws):
		self.book = book
		self.title = ws.title

		temp = []
		for i in ws.rows:
			temp.append(i)

		names = []
		column = 0
		for i in temp[0]:
			if isinstance(i, cell.read_only.EmptyCell):
				raise xlsx2anyError(self.book.name, self.title, 0, column)
			else:
				names.append(i.value)
			column = column + 1

		types = []
		column = 0
		for i in temp[1]:
			if isinstance(i, cell.read_only.EmptyCell):
				raise xlsx2anyError(self.book.name, self.title, 1, column)
			else:
				types.append(i.value.strip())

		exports = []
		for i in temp[2]:
			if isinstance(i, cell.read_only.EmptyCell):
				exports.append("")
			else:
				exports.append(i.value.strip())

		labels = []
		for i in temp[3]:
			if isinstance(i, cell.read_only.EmptyCell):
				raise xlsx2anyError(self.book.name, self.title, 3, column)
			else:
				labels.append(i.value.strip())

		data = []
		p =  re.compile("^\\[.+\\]")

		for i in range(4, len(temp)):
			if not isEmptyRow(temp[i]):
				if isEmptyCell(temp[i][0]):
					continue
				row = []
				column = 0
				for j in temp[i]:
					if p.match(types[column]) != None: #list
						l = [ j.value ]
						for k in range(i+1, len(temp)):
							if not isEmptyCell(temp[k][0]):
								break
							l.append( temp[k][column].value )
						row.append(l)
					else:
						row.append(j.value)
					column = column + 1
				data.append(row)

		self.names = names
		self.types = types
		self.exports = exports
		self.labels = labels
		self.data = data

	def columnCount(self):
		return len(self.names)

	def rowCount(self):
		return len(self.data)

	def getCell(self, row, column):
		return xcell(self, row, column, self.data[row][column])

	def getName(self, column):
		return self.names[column]

	def getLabel(self, column):
		return self.labels[column]

	def getType(self, column):
		return self.types[column]

	def getExport(self, column):
		return self.exports[column]


class xbook(object):
	def __init__(self, bookname):
		self.sheets = []
		self.name = bookname
		self.workbook = load_workbook(filename=bookname, read_only=True)
		self.efiles = []

		ws = self.workbook["导出"]	
		rowcount = 0 
		for i in ws.rows:
			if rowcount == 0:
				if i[0].value != "表名":
					raise xlsx2anyError(name, '导出', 0, 0)
				elif i[1].value != "导出文件":
					raise xlsx2anyError(name, '导出', 0, 1)
				elif i[2].value != "使用端":
					raise xlsx2anyError(name, '导出', 0, 2)
			else:
				if not isEmptyRow(i):
					self.efiles.append({
						"sheetname" : i[0].value,
						"output" : i[1].value,
						"filter" : i[2].value
					})
			rowcount = rowcount + 1

	def openSheet(self, name):
		for i in self.sheets:
			if i.title == name:
				return i
		ws = xsheet(self, self.workbook[name])
		self.sheets.append(ws)
		return ws

	def exportFiles(self):
		return self.efiles



class xlsx2any(object):
	def __init__(self):
		self.books = []

	def openBook(self, bookname):
		for v in self.books:
			if v.name == bookname:
				return v

		book = xbook(bookname)
		self.books.append(book)
		return book 

	def openSheet(self, bookname, sheetname):
		return self.openBook(bookname).openSheet(sheetname)

def exportBook(bookname):
	ctx = xlsx2any()
	book = ctx.openBook(bookname)
	files = book.exportFiles()
	for v in files:
		exportSheet(ctx, book.openSheet(v["sheetname"]), v)


def exportSheet(ctx, sheet, args):
	data = []
	columnCount = sheet.columnCount()
	rowCount = sheet.rowCount()

	for i in range(rowCount):
		row = {}
		for j in range(columnCount):
			if (lambda a, b: a=="" or a in b)(sheet.getExport(j), args["filter"]):
				row[sheet.getName(j)] = plugin.toValue(ctx, sheet.getCell(i, j))
		data.append(row)
	
	plugin.toFile(data, args)

def main():
	try:
		exportBook("nature.xlsx")
	except xlsx2anyError as e:
		print(e)
	except:
		raise

if __name__ == "__main__":
	main()