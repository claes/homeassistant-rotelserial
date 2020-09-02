import unittest
import roteldataparser

class TestStringMethods(unittest.TestCase):

    def test_terminated(self):
        rotelDataParser = roteldataparser.RotelDataParser()
        rotelDataParser.handleParsedData("source=coax2!freq=44.1!")
        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "source")
        self.assertEqual(rotelData[1], "coax2")
        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "freq")
        self.assertEqual(rotelData[1], "44.1")

    def test_fixedLength(self):
        rotelDataParser = roteldataparser.RotelDataParser()
        rotelDataParser.handleParsedData("display=010,0123456789A")
        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "display")
        self.assertEqual(rotelData[1], "0123456789")
        
    def test_fixedLengthSplit(self):
        rotelDataParser = roteldataparser.RotelDataParser()
        rotelDataParser.handleParsedData("display=010,01234")
        rotelDataParser.handleParsedData("56789A")
        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "display")
        self.assertEqual(rotelData[1], "0123456789")
        
    def test_Mixed(self):
        rotelDataParser = roteldataparser.RotelDataParser()
        rotelDataParser.handleParsedData("disp")
        rotelDataParser.handleParsedData(    "lay=010,01234")
        rotelDataParser.handleParsedData(                 "56789")
        rotelDataParser.handleParsedData("source=coax2!fr")
        rotelDataParser.handleParsedData("eq=44.1!")

        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "display")
        self.assertEqual(rotelData[1], "0123456789")
        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "source")
        self.assertEqual(rotelData[1], "coax2")
        rotelData = rotelDataParser.getNextRotelData()
        self.assertEqual(rotelData[0], "freq")
        self.assertEqual(rotelData[1], "44.1")

if __name__ == '__main__':
    unittest.main()
