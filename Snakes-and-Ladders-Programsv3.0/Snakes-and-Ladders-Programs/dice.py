import random

class Dice:
    def __init__(self,sides:int=6):
        self.sides=sides

    def roll(self):
        return random.randint(1,self.sides)
    
# roll_sides=Dice(6)
# print(roll_sides.roll())
    
