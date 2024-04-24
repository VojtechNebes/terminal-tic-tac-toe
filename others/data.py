def splitExtraData(data, sep):
    try:
        splitPos = data.index(sep) + 1
    except ValueError:
        return [], data
    else:
        unpackedData = [data[:splitPos]]
        moreUnpackedData, rest = splitExtraData(data[splitPos:], sep)
        
        unpackedData.extend(moreUnpackedData)
        
        return unpackedData, rest