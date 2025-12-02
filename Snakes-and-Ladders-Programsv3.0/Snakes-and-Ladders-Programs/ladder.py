class Ladder:
    """类似于C++中的构造函数"""
    def __init__(self,bottom:int,top:int):
        self.bottom=bottom
        self.top=top

    def __repr__(self):
        return f"Ladder({self.bottom}->{self.top})"
    
# ladder_position=Ladder(45,98)
# print(ladder_position)
