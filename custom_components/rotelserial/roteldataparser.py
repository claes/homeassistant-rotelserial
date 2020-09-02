class RotelDataParser:
    'Parses Rotel RS232 protocol'

    def __init__(self):
        self.rotelDataQueue = []
        self.nextKeyValuePair = ""
       
    def getNextRotelData(self):
        if len(self.rotelDataQueue) > 0:
            return self.rotelDataQueue.pop(0)
        else:
            return None

    def pushKeyValuePair(self, keyValuePair):
        keyValue = keyValuePair.split("=")
        self.rotelDataQueue.append(keyValue)
        
    def pushRotelData(self, rotelData):
        self.rotelDataQueue.append(rotelData)        

    def computeFixedLengthDataToRead(self, data):
        if data.startswith("display=") and (len(data) >= len("display=XXX")) :
            nextReadCount = int(data[len("display=") : len("display=XXX")])
            return nextReadCount
        return 0    

    def handleParsedData(self, data):
        for c in data:
            fixedLengthDataToRead = self.computeFixedLengthDataToRead(self.nextKeyValuePair)
            if fixedLengthDataToRead > 0:
                s = self.nextKeyValuePair + c
                startIndex = len("display=XXX") + 1 
                if s.startswith("display=") and ((len(s) - startIndex) >= fixedLengthDataToRead):
                    value = s[startIndex : startIndex + fixedLengthDataToRead]
                    self.pushRotelData(("display", value))
                    self.nextKeyValuePair = ""
                else :
                    self.nextKeyValuePair += c
            elif "!" == c:
                self.pushKeyValuePair(self.nextKeyValuePair)
                self.nextKeyValuePair = ""
            else :
                self.nextKeyValuePair += c
                
