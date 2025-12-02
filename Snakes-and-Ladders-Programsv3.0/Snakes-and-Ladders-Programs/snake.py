class Snake:
    def __init__(self,head:int,tail:int):
        self.head=head
        self.tail=tail

    def __repr__(self):
        return f"Snake({self.head}->{self.tail})"
    

# sanke_position=Sanke(71,32)
# print(sanke_position)
"""下面是这个代码的输出"""
"""Snake(71->32)"""