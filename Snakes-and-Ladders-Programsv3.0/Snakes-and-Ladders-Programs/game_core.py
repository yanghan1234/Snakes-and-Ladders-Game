from dice import Dice
from game_state import GameState
from player import Player 
from board import Board 
from snake import Snake # 确保导入
from ladder import Ladder # 确保导入
import json
import os
from typing import List, Optional

class Game:
    def __init__(self, board: Board, players: List[Player], dice: Dice = None):
        self.board = board
        self.players = players
        self.dice = dice if dice else Dice()
        self.current_index = 0
        self.state = GameState.CONFIGURING
        self.winner = None
        # 核心修复: 初始化回合计数器
        self.turn = 0 

    def start_new_game(self):
        """初始化新游戏状态 (确保所有玩家位置回到 0)"""
        self.state = GameState.WAITING_ROLL
        for p in self.players:
            p.move_to(0)
        self.current_index = 0
        self.winner = None
        self.turn = 0 # 重置回合数

    def current_player(self):
        """获取当前轮到行动的玩家"""
        return self.players[self.current_index]

    def next_player(self):
        """循环轮换玩家索引"""
        self.current_index = (self.current_index + 1) % len(self.players)
        
    def take_turn(self):
        """
        处理单人次的完整回合逻辑（如果不需要动画，可以直接调用这个）。
        在 GameUI 中，这部分逻辑被分散到 on_roll 和 step_move 中处理动画。
        """
        p = self.current_player()
        roll = self.dice.roll()

        # 移动
        p.move_by(roll)

        # 边界校正
        final_square = self.board.size * self.board.size
        if p.position > final_square:
            p.move_to(final_square)

        # 蛇梯
        p.move_to(self.board.get_destination(p.position))

        # 检查胜利
        if p.position == final_square:
            self.state = GameState.GAME_OVER
            self.winner = p
        else:
            self.next_player()
        
        return roll, p.position

    def save_game(self, path: str):
        """将当前游戏状态保存到 JSON 文件"""
        data = {
            "current_index": self.current_index,
            "turn": self.turn,
            "players": [
                {
                    "name": p.name,
                    "color": p.color,
                    "number": p.number,
                    "position": p.position,
                    "is_bot": p.is_bot
                }
                for p in self.players
            ],
            # 保存棋盘配置（如果它是动态生成的）
            "snakes": [(s.head, s.tail) for s in self.board.snakes],
            "ladders": [(l.bottom, l.top) for l in self.board.ladders]
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def load_game(self, path: str) -> Optional[List[Player]]:
        """从 JSON 文件加载游戏状态"""
        if not os.path.exists(path):
            return None

        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return None # 文件损坏

        loaded_players = []
        try:
            # 1. 加载玩家
            for p_data in data["players"]:
                player = Player(
                    name=p_data["name"],
                    color=p_data["color"],
                    number=p_data["number"],
                    is_bot=p_data.get("is_bot", False) # 兼容旧版，默认为 False
                )
                player.move_to(p_data["position"])
                loaded_players.append(player)

            self.players = loaded_players
            self.current_index = data.get("current_index", 0)
            self.turn = data.get("turn", 0) # 加载回合数
            self.state = GameState.WAITING_ROLL # 游戏加载后，等待掷骰子

            # 2. 加载棋盘结构（如果有变化）
            self.board.snakes = []
            self.board.ladders = []
            for head, tail in data.get("snakes", []):
                self.board.add_snake(head, tail)
            for bottom, top in data.get("ladders", []):
                self.board.add_ladder(bottom, top)
            
            # 3. 检查是否已结束
            final_square = self.board.size * self.board.size
            winner = next((p for p in self.players if p.position == final_square), None)
            if winner:
                self.state = GameState.GAME_OVER
                self.winner = winner

            return loaded_players # 成功加载时返回玩家列表

        except (KeyError, IndexError, TypeError):
            return None # 数据结构不正确