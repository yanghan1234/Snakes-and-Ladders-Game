"""游戏状态管理器"""
"""让程序知道自己现在处于哪一种状态"""
"""调用逻辑就是 GameState.CONFIGURING"""

from enum import Enum

class GameState(Enum):
    """游戏配置阶段：设置玩家数量，初始化棋盘"""
    CONFIGURING=0
    """等待玩家掷骰子：轮到玩家点击"Roll Dice"按钮"""
    WAITING_ROLL=1
    """骰子正在滚动中:动画播放中，还不能再点击"""
    ROLLING_DICE=2
    """棋子正在移动：玩家走几步后动画执行"""
    MOVING=3
    """检查蛇或梯子：判断玩家是否爬梯或者掉蛇"""
    CHECKING_SNAKE_AND_LADDER=4
    """检查是否顺利：看当前玩家是否到达终点"""
    CHECKING_WIN=5
    """游戏暂停：玩家按下“暂停按钮，所有数据暂时停止加载"""
    PAUSED=6
    """游戏结束：某人赢了，显示结果界面"""
    GAME_OVER=7
