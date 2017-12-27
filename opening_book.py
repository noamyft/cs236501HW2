import operator


class OpeningBook:

    FILE_PATH = "data/book.gam"
    MOVES = 10
    MOVE_LENGHT = 3
    TOP = 70

    def __init__(self):
        self.openings = {}
        self.openingsMoves = {}
        self.openings = self.__analyzeFile()
        self.openingsMoves = self.__buildOpeningMove(self.openings)

    def __fixChar(self, ch):
        if (ch >= 'a') and (ch <= 'h'):
            ch = chr(ord(ch) - ord('a') + ord('0'))
        elif (ch >= '1') and (ch <= '9'):
            ch = chr(ord(ch) - 1)
            ch = 7 - int(ch)
            ch = str(ch)
        else:
            ch = ''

        return ch

    def __analyzeFile(self):
        with open(OpeningBook.FILE_PATH, "r") as file:
            for line in file:
                opening = line[:OpeningBook.MOVES * OpeningBook.MOVE_LENGHT]
                #format moves:
                opening = ''.join(map(self.__fixChar, opening))
                if opening in self.openings:
                    self.openings[opening] += 1
                else:
                    self.openings[opening] = 1

            topOpening = sorted(self.openings.items(), key=operator.itemgetter(1))
            topOpening = topOpening[-OpeningBook.TOP:]
            topOpening = [ item[0] for item in topOpening]

        return topOpening

    def __buildOpeningMove(self, opening):
        result = {}
        for o in opening:
            for i in range(0,OpeningBook.MOVES * (OpeningBook.MOVE_LENGHT-1) - 2,2):
                index = o[:i]
                result[index] = [int(o[i]), int(o[i+1])]


        return result

    def get(self,move):
        return self.openingsMoves.get(move)

if __name__ == '__main__':
    OpeningBook()