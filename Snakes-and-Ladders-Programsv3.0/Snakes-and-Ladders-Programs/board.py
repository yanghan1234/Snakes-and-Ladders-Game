from point import Point
from snake import Snake
from ladder import Ladder
from typing import Dict, List, Tuple

BOARD_SIZE = 10
FINAL_SQUARE = BOARD_SIZE * BOARD_SIZE

class Board:
    # 核心修复: 添加 ladders 和 snakes 参数
    def __init__(self, 
                 ladders: Dict[int, int] = None, 
                 snakes: Dict[int, int] = None, 
                 image_path: str = None, 
                 canvas_px: int = 700):
        
        self.size = BOARD_SIZE
        self.image_path = image_path
        self.snakes: List[Snake] = []
        self.ladders: List[Ladder] = []
        self.canvas_px = canvas_px
        """每个格子的边长（整数除法），例如700//10=70像素"""
        self.cell_px = canvas_px // self.size
        """字典，键为格子编号（1..100),值为该格子中心的Point(x,y),由后面这个函数来生成"""
        self.square_coord = self.generate_square_coordinates()

        # 核心修复: 根据传入的字典配置棋盘
        if snakes:
            for head, tail in snakes.items():
                self.add_snake(head, tail)
        
        if ladders:
            for bottom, top in ladders.items():
                self.add_ladder(bottom, top)


    """下面的两个方法是将Snake和Ladder对象加入列表"""
    def add_snake(self, head: int, tail: int):
        self.snakes.append(Snake(head, tail))

    def add_ladder(self, bottom: int, top: int):
        self.ladders.append(Ladder(bottom, top))

    """下面的方法就是加入你在游戏中，遇到蛇头或者蛇尾的时候，你会跳格子，往上跳或者是往下跳"""
    def get_destination(self, square: int) -> int:
        #检查玩家所处的格子有没有蛇或者是梯子
        for s in self.snakes:
            if s.head == square:
                return s.tail
        
        for l in self.ladders:
            if l.bottom == square:
                return l.top
        """如果既不是蛇头，又不是梯子的底部，则返回原来所处的位置"""
        return square
    
    """下面的方法是生成棋盘上每个格子“像素中心坐标”的关键方法"""
    def generate_square_coordinates(self) -> Dict[int, Point]:
        coords = {}
        """遍历所有的格号"""
        for n in range(1, FINAL_SQUARE + 1):
            """将格号转化为0基索引，这样方便于将格号转成0索引，便于整除与取余计算"""
            idx = n - 1
            
            # 计算行和列 (从底行开始编号为0)
            row = idx // self.size
            col = idx % self.size

            # 核心修复: 根据用户反馈，强制所有行都从左到右 (L-to-R)
            # 或者反转逻辑以纠正用户观察到的“反向”移动
            if row % 2 == 0:
                # 偶数索引行（底行、第3行...）: 从左到右 (L-to-R)，保持不变
                x_pos_index = col
            else:
                # 奇数索引行（第2行、第4行...）: 原本是 R-to-L。
                # ！！！根据用户的“反着”反馈，将其改为 L-to-R ！！！
                x_pos_index = col
                # 原来的逻辑 (R-to-L): x_pos_index = self.size - 1 - col
                
            y_pos_index = self.size - 1 - row # Tkinter坐标系：Y轴向下为正，所以需要反转行索引

            # 计算中心像素坐标
            center_offset = self.cell_px / 2
            x_center = x_pos_index * self.cell_px + center_offset
            y_center = y_pos_index * self.cell_px + center_offset
            
            coords[n] = Point(int(x_center), int(y_center))
            
        return coords