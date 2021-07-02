class Hangman:
    def __init__(self, w):
        self.word = w.upper()
        self.correctLetters = []
        self.already= []

        self.boy = ['', '\n  o', '\n/', '|', '\\', '\n /', '\\']
        self.boyStr = ''

        self.miss = 0
        self.win = False
        self.lost = False

        consonants = 0
        vowels = 0
        i = 0

        wordLenght = len(self.word)

        while (i < wordLenght):
            self.correctLetters.append('_')

            for letter in self.word:
                letter = self.word[i]

                if (letter == 'A' or letter == 'E' or letter == 'I' or letter == 'O' or letter == 'U'):
                    vowels = vowels+1
                else:
                    consonants = consonants+1
            i+= 1

        self.difficult = str(round(consonants/vowels*10, 2))

    def attempt(self, guess):
        guess = guess.upper()

        if(guess in self.word and not(guess in self.already)):
            self.already.append(guess)
            i = 0
            for letter in self.word:
                if (guess == letter):
                    self.correctLetters[i] = letter
                i+= 1
        elif not(guess in self.already):
            self.already.append(guess)
            self.miss+= 1
            self.boyStr = self.boyStr + self.boy[self.miss]
        else:
            self.miss+= 1
            self.boyStr = self.boyStr + self.boy[self.miss]

        self.lost = self.miss == 6
        self.win = '_' not in self.correctLetters