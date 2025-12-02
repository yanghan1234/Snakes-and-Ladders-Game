class Point:
    """类似C++里面的构造函数"""
    def __init__(self,x:int,y:int):
        self.x=x
        self.y=y


    def __repr__(self):
        return f"Point({self.x},{self.y})"
    
    """让被打印对象更加直观"""
#p=Point(5,3)
#print(p.x)
