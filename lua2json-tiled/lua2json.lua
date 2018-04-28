-- 将tiled生成的lua文件转换为可以由tiled打开的json文件
-- 用法: lua2json lua文件名

local json  = assert(loadfile "fjson.lua")()

function toJson(name)
	local dat = require(name)
	for _, v in pairs(dat.tilesets) do
		local tiles = {}
		for __, v1 in pairs(v.tiles) do
			v1.imagewidth = v1.width
			v1.imageheight = v1.height
			v1.width = nil
			v1.height = nil
			local id = tostring(v1.id)
			v1.id = nil
			tiles[id] = v1
		end
		v.tiles = tiles
	end

	for k, v in pairs(dat.tilesets) do
		v.tilecount = #v.tiles
	end

	for k, v in pairs(dat.layers) do
		v.encoding = nil
	end

	local str = json:encode(dat)

	f = io.open(name..".json", "w")
	f:write(str)
	f:close()
end

print(({...})[1])
toJson(({...})[1])