"""This is a player class"""
class Player:
    # 核心修复：添加 is_bot 参数，并设置默认值为 False
    def __init__(self,name:str,color:str,number:int,is_bot:bool=False): 
        self.name = name
        self.color = color
        self.number=number
        """0意味着不在棋盘中"""
        self.position:int = 0
        self.is_bot = is_bot # 核心修复：将 is_bot 赋值为对象属性

    def move_by(self, steps:int):
        # 移动棋子
        #调用player.move_by(6)就是指在原来的基础上移动了6个格子"""
        self.position+=steps
        if self.position>100:
            self.position=100


    def move_to(self,square:int):
        """ 移动到某一个格子"""
        #调用player.move_to(76)就是自己的位置直接跳到76这个位置去
        self.position=square

    

    def get_position(self)->int:
        # 设置新位置
        return self.position
    
    def __repr__(self):
        # 增加 bot 状态以便于调试
        bot_status = ", Bot" if self.is_bot else ""
        return f"Player({self.name}, pos={self.position}{bot_status})"