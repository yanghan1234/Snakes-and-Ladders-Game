import tkinter as tk
from tkinter import simpledialog, messagebox
import os
from typing import List, Optional

# --- 导入核心组件 ---
try:
    from game_ui import GameUI, SetupDialog  # 假设 SetupDialog 也移到了 game_ui.py
    from player import Player
    from PIL import Image 
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please ensure GameUI, SetupDialog, Player, and PIL are correctly set up and imported.")
    
# --- 常量定义（与应用启动相关的部分） ---
ANIMAL_IMAGE_FILES = ["monkey.png", "elephant.png", "giraffe.png", "panda.png"]
MAIN_MENU_WIDTH = 800
MAIN_MENU_HEIGHT = 500

# --- Main Menu 界面 ---

class MainMenu(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg='darkslategrey')
        self.app = app
        self.pack(fill=tk.BOTH, expand=True)

        # 标题
        tk.Label(self, text="Snakes and Ladders (GUI)", font=("Arial", 24, "bold"), fg='white', bg='darkslategrey').pack(pady=(50, 5))
        tk.Label(self, text="Author: group12", font=("Arial", 10), fg='lightgray', bg='darkslategrey').pack(pady=(0, 30))

        # 按钮
        tk.Button(self, text="New Game", width=20, command=lambda: self.app.start_setup(load_only=False)).pack(pady=10)
        tk.Button(self, text="Load Game", width=20, command=lambda: self.app.start_setup(load_only=True)).pack(pady=10)
        tk.Button(self, text="Exit", width=20, command=self.app.quit).pack(pady=10)


# --- GameApp (主窗口应用) ---

class GameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Snakes and Ladders")
        # 初始化时显示主菜单
        self.game_ui: Optional[GameUI] = None 
        self.show_main_menu()

    def clear_window(self):
        """销毁窗口中的所有子控件，并取消旧的 after 任务。"""
        # 核心修复：在清理窗口前，尝试取消旧 GameUI 中的所有 after 任务
        if self.game_ui:
             if hasattr(self.game_ui, '_cancel_all_pending_animations'):
                 self.game_ui._cancel_all_pending_animations()
                 
        for widget in self.winfo_children():
            widget.destroy()
            
        # 确保在清理后，主窗口处于正常状态
        self.update_idletasks() # 强制更新，确保 destroy 完成

    def show_main_menu(self):
        """显示主菜单"""
        self.clear_window()
        # 确保在显示菜单时，将主窗口大小设回菜单大小
        self.geometry(f"{MAIN_MENU_WIDTH}x{MAIN_MENU_HEIGHT}")
        self.resizable(False, False)
        # 清除旧的 GameUI 引用
        self.game_ui = None 
        MainMenu(self, self)

    def start_setup(self, load_only: bool = False, current_game_ui: Optional[GameUI] = None):
        """
        启动配置/加载对话框，并处理结果。
        
        :param current_game_ui: 正在运行的旧 GameUI 实例（如果从 New/Load 按钮调用）。
        """
        
        # 1. 如果是从游戏界面调用，先取消旧 GameUI 的动画并销毁其内容
        if current_game_ui and hasattr(current_game_ui, 'main_frame'):
            try:
                current_game_ui.main_frame.destroy()
            except Exception:
                pass
        
        # 2. 启动设置对话框（对话框在主线程阻塞直到完成）
        dialog = SetupDialog(self, load_only=load_only)
        
        players_config: Optional[List[Player]] = dialog.result
        
        # 3. 处理结果
        if players_config:
            # 成功配置新游戏或加载成功，启动新游戏 UI
            self.show_game(players_config)
            
        else: 
            # 用户在对话框中取消，返回主菜单
            self.show_main_menu()
            
    def show_game(self, players: List[Player]):
        """
        根据玩家配置列表创建并显示 GameUI。
        """
        # 确保窗口是空的
        self.clear_window() 
        # GameUI 内部会处理窗口大小调整
        self.resizable(True, False) 
        self.game_ui = GameUI(self, players)

    def restart_game_with_dialog(self):
        """
        从游戏界面中点击 New Game 时调用，直接弹出设置对话框。
        这个方法在主线程中执行，避免在事件处理中销毁窗口树。
        """
        def show_dialog():
            self.start_setup(load_only=False)
        
        # 延迟执行，确保按钮事件处理完成
        self.after(50, show_dialog)


# --- 应用程序启动入口 ---

def check_and_create_placeholder_images():
    """检查并为玩家头像创建占位符图片，防止图片缺失时程序崩溃。"""
    # 占位函数
    pass
    

if __name__ == "__main__":
    # check_and_create_placeholder_images() 
    app = GameApp()
    app.mainloop()