import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk, ImageDraw # 需要安装 Pillow 库
import math
import os
import json
from typing import List, Optional, Dict, Tuple

# --- 导入项目内部核心类 ---
from game_state import GameState # 游戏状态枚举
from player import Player       # 玩家类 (来自 player.py)
from dice import Dice           # 骰子类 (来自 dice.py)
from board import Board         # 棋盘类 (来自 board.py)
from game_core import Game      # 游戏核心逻辑类 (来自 game_core.py)
from point import Point         # 坐标类 (来自 point.py)


# --- 常量定义 ---

WINDOW_PX = 700 # 棋盘画布大小
MENU_WIDTH = 250 # 新增：右侧菜单栏宽度
FULL_WINDOW_WIDTH = WINDOW_PX + MENU_WIDTH # 新增：总窗口宽度

PLAYER_RADIUS = 12
PLAYER_COLORS = ["red", "blue", "green", "purple", "orange", "cyan"]
ANIMATION_STEP_MS = 120

ANIMAL_IMAGE_FILES = ["monkey.png", "elephant.png", "giraffe.png", "panda.png"]

ANIMAL_EMOJI = ["🐱", "🐘", "🦒", "🐼"]

DEFAULT_LADDERS = {3: 51, 6: 27, 20: 70, 36: 55, 63: 95, 68: 98}
DEFAULT_SNAKES = {34: 1, 25: 5, 47: 19, 65: 52, 87: 57, 91: 61, 99: 69}

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")

# --- 3D 骰子模拟常量 (新增或修改) ---
DICE_3D_FRAMES_COUNT = 30 
DICE_3D_THROW_BASE_NAME = "dice_3d_throw_" 
DICE_3D_RESULT_BASE_NAME = "dice_3d_result_"


# --- UI 分层配置：SetupDialog (继承 tk.simpledialog.Dialog) ---

class SetupDialog(simpledialog.Dialog):
    def __init__(self, master, load_only: bool = False):
        self.load_only = load_only
        self.players_list: Optional[List[Player]] = None
        self.num_players_var = tk.IntVar(master, value=2)
        self.result = None  # 关键修复：初始化 result 属性，确保总是存在
        super().__init__(master) 

    def body(self, master):
        self.title("Game Setup")
        
        tk.Label(master, text="Snakes and Ladders", font=("Arial", 14, "bold")).pack(pady=10)
        
        if not self.load_only:
            tk.Label(master, text="Number of Human Players (1-4):").pack()
            tk.Spinbox(master, from_=1, to=4, textvariable=self.num_players_var, width=5).pack()
            tk.Label(master, text="Note: 1 player will add a CPU Bot.").pack(pady=(5, 10))
        else:
            tk.Label(master, text="Select Load Game or Cancel.", font=("Arial", 12)).pack(pady=10)

        return None

    def buttonbox(self):
        box = tk.Frame(self)
        if not self.load_only:
            tk.Button(box, text="Start New Game", width=15, command=self.ok).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(box, text="Load Game", width=15, command=self.load_game).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(box, text="Cancel", width=15, command=self.cancel).pack(side=tk.LEFT, padx=5, pady=5)
        
        if not self.load_only:
            self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def apply(self):
        num_human_players = self.num_players_var.get()
        players_list = []
        used_colors = set()
        
        for i in range(num_human_players):
            color = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            name = simpledialog.askstring(
                "Player Name", 
                f"Enter name for Player {i+1}:", 
                initialvalue=f"P{i+1}", 
                parent=self.master
            )
            if not name: name = f"P{i+1}"
            
            players_list.append(Player(name, color, i + 1))
            used_colors.add(color)

        if num_human_players == 1:
            bot_color = next((c for c in PLAYER_COLORS if c not in used_colors), "gray")
            players_list.append(Player("CPU", bot_color, len(players_list) + 1, is_bot=True))
            messagebox.showinfo("Bot Added", "Only one human player. Added CPU Bot.", parent=self.master)
        
        self.result = players_list

    def load_game(self):
        # 实例化 Board 时需要传递必要的参数
        temp_board = Board(DEFAULT_LADDERS, DEFAULT_SNAKES, canvas_px=WINDOW_PX) 
        temp_game = Game(temp_board, [], Dice())
        
        loaded_players = temp_game.load_game(SAVE_PATH)
        
        if loaded_players:
            self.result = loaded_players
            self.cancel() 
        else:
            messagebox.showerror("Load Failed", "No save file found or file is corrupted.", parent=self.master)
            self.result = None


# --- GameUI (主游戏界面) ---

class GameUI:
    def __init__(self, root, initial_players: List[Player], board_image_name="snakes_and_ladders_boardimage.jpg"):
        self.root = root
        self.root.title("Snakes and Ladders")
        self.board_image_name = board_image_name
        self.players = initial_players
        
        # 核心修复 1: 初始化待取消的动画 ID 列表 (解决 TclError 的关键)
        self._pending_after_ids: List[str] = [] 
        
        self.root.geometry(f"{FULL_WINDOW_WIDTH}x{WINDOW_PX + 50}") 
        self.root.resizable(True, False) 

        # 1. 创建主 Frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 2. 初始化棋盘和游戏核心
        self.board = Board(
            ladders=DEFAULT_LADDERS, 
            snakes=DEFAULT_SNAKES, 
            canvas_px=WINDOW_PX
        )
        self.game = Game(self.board, self.players, Dice())
        
        # 检查这是否是一个加载的游戏（即是否有玩家不在起始点 0）
        is_loaded_game = any(p.position > 0 for p in self.players)
        
        if not is_loaded_game:
            # 如果是新游戏（玩家位置都是 0），则调用 start_new_game 彻底初始化状态
            self.game.start_new_game() 
        else:
             # 如果是加载的游戏，我们只需设置当前玩家索引和状态
             self.game.current_index = next((i for i, p in enumerate(self.players) if p.number == 1), 0)
             self.game.state = GameState.WAITING_ROLL
        
        # 3. 布局：左侧画布，右侧控制面板
        self.canvas = tk.Canvas(self.main_frame, width=WINDOW_PX, height=WINDOW_PX, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.Y, expand=False) 
        
        self.control_frame = tk.Frame(self.main_frame, width=MENU_WIDTH, bg='gray')
        self.control_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.control_frame.pack_propagate(False) 
        
        self._load_board_image(board_image_name)
        self._draw_board()
        self._setup_control_panel() 

        # 4. 初始化棋子和骰子
        self.player_tokens = [None] * len(self.players)
        self._animal_image_refs = [None] * len(self.players)
        self._animal_photo_refs = [None] * len(self.players)
        self._draw_all_players()
        
        self._dice_size = 64  # 保持骰子显示大小不变
        # 但在内部以更高分辨率生成，然后缩放到 64px 显示
        self._dice_size_internal = 5120  # 内部生成时用 5120px 的超高分辨率（提高 10 倍）
        self._dice_images = self._prepare_dice_images(self._dice_size_internal) 
        
        self._dice_sequence, self._dice_results_3d = self._load_dice_sequence() 
        self._dice_photo_refs = [ImageTk.PhotoImage(img) for img in self._dice_images] 
        self._dice_canvas_item = None
        
        self.update_status()

    # --- 核心修复 2: 动画调度与取消辅助方法 (解决 TclError 的关键) ---
    def _schedule_animation(self, ms: int, callback):
        """Schedules a callback and stores its ID for later cancellation."""
        if self.root.winfo_exists():
            new_id = self.root.after(ms, callback)
            self._pending_after_ids.append(new_id)
            return new_id
        return None

    def _cancel_all_pending_animations(self):
        """Cancels all stored after() events. (解决 TclError 的关键)"""
        for after_id in self._pending_after_ids:
            try:
                # after_cancel may raise an exception if the ID has already fired/is invalid
                self.root.after_cancel(after_id)
            except Exception:
                pass 
        self._pending_after_ids = []

    # --- UI 辅助方法 (与之前提供的完整代码一致) ---
    
    def _get_resample_mode(self, mode_name: str):
        try:
            return getattr(Image.Resampling, mode_name)
        except AttributeError:
            return getattr(Image, mode_name, Image.BICUBIC)
            
    def _load_board_image(self, img_path):
        resamp = self._get_resample_mode('LANCZOS')
        if os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).resize((WINDOW_PX, WINDOW_PX), resamp)
                self.board_tk = ImageTk.PhotoImage(pil_img)
            except Exception:
                self.board_tk = None
        else:
            self.board_tk = None

    def _setup_control_panel(self):
        # 顶部菜单标题
        menu_label = tk.Label(
            self.control_frame,
            text="Menu",
            font=("Arial", 16, "bold"),
            bg='gray',
            fg='white'
        )
        menu_label.pack(pady=10)

        # 菜单按钮（保持原来顺序和样式）
        tk.Button(
            self.control_frame,
            text="Pause",
            width=15,
            command=lambda: messagebox.showinfo("Pause", "Game Paused")
        ).pack(pady=5)

        tk.Button(
            self.control_frame,
            text="Save",
            width=15,
            command=self.on_save
        ).pack(pady=5)

        tk.Button(
            self.control_frame,
            text="Load",
            width=15,
            command=self.on_load
        ).pack(pady=5)

        tk.Button(
            self.control_frame,
            text="New Game",
            width=15,
            command=self.start_new_game
        ).pack(pady=5)

        tk.Button(
            self.control_frame,
            text="Exit",
            width=15,
            command=self.root.quit
        ).pack(pady=5)

        # 间隔
        tk.Frame(self.control_frame, height=20, bg='gray').pack()

        # 中部状态区：Turn / Player / Dice
        status_frame = tk.Frame(self.control_frame, bg='gray')
        status_frame.pack(fill=tk.X, padx=10, pady=10)

        self.current_label = tk.Label(
            status_frame,
            text="Turn: -\nPlayer: -\nPosition: -",
            justify=tk.LEFT,
            bg='gray',
            fg='white'
        )
        self.current_label.pack(anchor=tk.W, pady=5)

        self.dice_label = tk.Label(
            status_frame,
            text="Dice: -",
            justify=tk.LEFT,
            bg='gray',
            fg='white'
        )
        self.dice_label.pack(anchor=tk.W, pady=5)

        # ✅ 把 Roll 按钮放到右侧面板，用 pack，而不是 root + place
        self.roll_button = tk.Button(
            self.control_frame,
            text="Roll Dice",
            command=self.on_roll,
            width=15
        )
        self.roll_button.pack(pady=(0, 10))

        # ✅ Log 标题单独放在下面（不再挤在 status_frame 里）
        log_label = tk.Label(
            self.control_frame,
            text="Log",
            font=("Arial", 12, "bold"),
            bg='gray',
            fg='white'
        )
        log_label.pack(anchor=tk.W, padx=10, pady=(0, 5))

        # （可选）如果你想要一个黑色的日志框，就加下面几行
        self.log_text = tk.Text(
            self.control_frame,
            height=12,
            bg="black",
            fg="white",
            wrap="word",
            state="disabled"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def add_log(self, text: str):
        """往右下角 Log 区追加一行文字。"""
        if not hasattr(self, "log_text"):
            return
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _draw_board(self):
        if getattr(self, 'board_tk', None):
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.board_tk)
            return
        cell = self.board.cell_px
        for i in range(self.board.size + 1):
            x = i * cell
            self.canvas.create_line(x, 0, x, WINDOW_PX, fill="#aaa")
            y = i * cell
            self.canvas.create_line(0, y, WINDOW_PX, y, fill="#aaa")
        for n, pt in self.board.square_coord.items():
            self.canvas.create_text(pt.x - cell // 2 + 5, pt.y + cell // 2 - 5, text=str(n), anchor=tk.NW, font=("Arial", 8))

    def _prepare_dice_images(self, size: int = 64):
        """生成骰子图像。内部用高分辨率生成，然后缩放到最终显示大小。"""
        imgs = []
        def pip_positions(n, s):
            gap = 0.22; center = (0.5, 0.5); left = (0.5 - gap, 0.5); right = (0.5 + gap, 0.5)
            topleft = (0.5 - gap, 0.5 - gap); topright = (0.5 + gap, 0.5 - gap)
            bottomleft = (0.5 - gap, 0.5 + gap); bottomright = (0.5 + gap, 0.5 + gap)
            mapping = {
                1: [center], 2: [topleft, bottomright], 3: [topleft, center, bottomright],
                4: [topleft, topright, bottomleft, bottomright],
                5: [topleft, topright, center, bottomleft, bottomright],
                6: [topleft, left, topright, bottomleft, right, bottomright]
            }
            pts = mapping.get(n, [center])
            return [(int(x * s), int(y * s)) for (x, y) in pts]
            
        for n in range(1, 7):
            img = Image.new('RGBA', (size, size), (240, 240, 240, 255))
            draw = ImageDraw.Draw(img); pad = int(size * 0.06)
            draw.rounded_rectangle([(pad, pad), (size - pad - 1, size - pad - 1)], radius=max(8, size // 32), fill=(255, 255, 255), outline=(30, 30, 30), width=max(2, size // 128))
            pip_r = max(4, size // 12)
            for (px, py) in pip_positions(n, size):
                draw.ellipse([(px - pip_r, py - pip_r), (px + pip_r, py + pip_r)], fill=(20, 20, 20))
            
            # 如果内部大小大于显示大小，则缩放到显示大小
            if size > self._dice_size:
                resamp = self._get_resample_mode('LANCZOS')
                img = img.resize((self._dice_size, self._dice_size), resamp)
            
            imgs.append(img)
        return imgs

    def _load_dice_sequence(self) -> Tuple[List[Image.Image], Dict[int, Image.Image]]:
        sequence = []
        results = {}
        path_dir = os.path.dirname(os.path.abspath(__file__))
        resamp = self._get_resample_mode('LANCZOS')
        
        try:
            for n in range(1, 7):
                fname = f"{DICE_3D_RESULT_BASE_NAME}{n}.png"
                path = os.path.join(path_dir, fname)
                img = Image.open(path).convert('RGBA')
                # 【新增】对骰子结果图片去除背景
                img = self._remove_background(img, tolerance=50)
                img = img.resize((self._dice_size, self._dice_size), resamp)
                results[n] = img
        except Exception:
            size = self._dice_size
            for n in range(1, 7):
                img_2d = self._prepare_dice_images(size)[n-1]
                results[n] = img_2d
        
        try:
            for i in range(DICE_3D_FRAMES_COUNT):
                frame_num = str(i + 1).zfill(0)
                fname = f"{DICE_3D_THROW_BASE_NAME}{frame_num}.png"
                path = os.path.join(path_dir, fname)
                img = Image.open(path).convert('RGBA')
                # 【新增】对骰子动画帧去除背景
                img = self._remove_background(img, tolerance=50)
                img = img.resize((self._dice_size, self._dice_size), resamp)
                sequence.append(img)
        except Exception:
            sequence = [img.copy() for img in self._dice_images] * (DICE_3D_FRAMES_COUNT // 6 + 1)
            sequence = sequence[:DICE_3D_FRAMES_COUNT] 

        return sequence, results

    # 核心修复 3: 使用 _schedule_animation
    def _animate_dice_throw(self, on_complete):
        start_x, start_y = 60, 60
        end_x = WINDOW_PX // 2
        end_y = WINDOW_PX // 2 
        arc_height = 150
        
        sequence = self._dice_sequence
        total_frames = len(sequence) 
        
        if total_frames == 0:
            roll = self.game.dice.roll()
            on_complete(roll)
            return

        def frame(i):
            if not self.canvas.winfo_exists():
                return
            
            t = i / (total_frames - 1)
            x = int(start_x + (end_x - start_x) * t)
            y = int(start_y + (end_y - start_y) * t - arc_height * (4 * t * (1 - t)))
            
            current_image = sequence[i % len(sequence)]
            
            try: 
                final_canvas = Image.new('RGBA', (WINDOW_PX, WINDOW_PX), (0, 0, 0, 0))
                paste_x = x - current_image.width // 2
                paste_y = y - current_image.height // 2
                final_canvas.paste(current_image, (paste_x, paste_y), current_image)
                
                photo = ImageTk.PhotoImage(final_canvas)
                self._current_dice_photo = photo 
                
                if self._dice_canvas_item is None:
                    self._dice_canvas_item = self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                else:
                    self.canvas.itemconfig(self._dice_canvas_item, image=photo)
            except tk.TclError:
                return
                
            if i + 1 < total_frames:
                self._schedule_animation(40, lambda: frame(i + 1)) 
            else:
                roll = self.game.dice.roll()
                
                if not self.canvas.winfo_exists():
                    on_complete(roll) 
                    return

                try:
                    final_base = self._dice_results_3d[roll] 
                    final_img = Image.new('RGBA', (WINDOW_PX, WINDOW_PX), (0, 0, 0, 0))
                    final_img.paste(
                        final_base, 
                        (end_x - final_base.width // 2, end_y - final_base.height // 2), 
                        final_base
                    )
                    
                    photo_final = ImageTk.PhotoImage(final_img)
                    self._current_dice_photo = photo_final
                    self.canvas.itemconfig(self._dice_canvas_item, image=photo_final)
                except tk.TclError:
                    on_complete(roll)
                    return
                
                def bounce(j):
                    if not self.canvas.winfo_exists():
                        return
                        
                    if j >= 4:
                        self.dice_label.config(text=f"Dice: {roll}")
                        on_complete(roll)
                        return
                    
                    try:
                        offset = -8 if j % 2 == 0 else 5
                        self.canvas.move(self._dice_canvas_item, 0, offset)
                    except tk.TclError:
                        return 
                        
                    self._schedule_animation(80, lambda: bounce(j + 1))
                bounce(0)

        frame(0)

    def _coords_for_square(self, square: int, player_index: int = 0):
        if square <= 0:
            x = 10 + player_index * (PLAYER_RADIUS * 2 + 4)
            y = WINDOW_PX - 10
            return x, y
            
        pt = self.board.square_coord.get(square)
        if not pt:
            return 10 + player_index * (PLAYER_RADIUS * 2 + 4), WINDOW_PX - 10
        offset_x = (player_index % 2) * PLAYER_RADIUS * 1.6
        offset_y = (player_index // 2) * PLAYER_RADIUS * 1.6
        return pt.x + offset_x, pt.y + offset_y

    def _draw_all_players(self):
        resample_mode = self._get_resample_mode('LANCZOS')
            
        for i, p in enumerate(self.players):
            x, y = self._coords_for_square(p.position, i)
            r = PLAYER_RADIUS
            # 增加动物图片大小到棋盘单元格的 1.2 倍，使角色更加逼真
            desired_size = int(self.board.cell_px * 1.2); desired_size = max(desired_size, r * 3)
            img = self._load_animal_image(i, desired_size, resample_mode)

            if p.is_bot and img is not None:
                 img_data = img.getdata()
                 new_data = []
                 for item in img_data:
                     avg_color = int(sum(item[:3]) / 3) 
                     new_data.append(tuple([avg_color] * 3 + [item[3]]))
                 new_img = Image.new('RGBA', img.size)
                 new_img.putdata(new_data)
                 img = new_img
                 
            if img is not None:
                photo = ImageTk.PhotoImage(img)
                self._animal_photo_refs[i] = photo
                # 图像锚点设为 S (底部中心)
                iid = self.canvas.create_image(x, y, image=photo, anchor=tk.S) 
                self.player_tokens[i] = (iid, None)
            else:
                # 几何图形锚点设为中心
                oid = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=p.color, outline="black")
                emoji = ANIMAL_EMOJI[i % len(ANIMAL_EMOJI)]
                txt_id = self.canvas.create_text(x, y, text=emoji, font=("Arial", int(self.board.cell_px * 0.4)))
                self.player_tokens[i] = (oid, txt_id)

    def _remove_background(self, img: Image.Image, tolerance: int = 50) -> Image.Image:
        """
        移除图片背景（基于背景颜色的相似性检测）。
        尝试识别背景颜色并将其转为透明。
        
        :param img: PIL Image 对象（应该是 RGBA 格式）
        :param tolerance: 颜色相似度容差（0-255，较小值为更严格）
        :return: 去除背景后的 Image
        """
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        data = img.getdata()
        new_data = []
        
        # 获取四个角落的颜色，认为这些是背景色
        width, height = img.size
        corner_colors = [
            img.getpixel((0, 0)),  # 左上
            img.getpixel((width - 1, 0)),  # 右上
            img.getpixel((0, height - 1)),  # 左下
            img.getpixel((width - 1, height - 1))  # 右下
        ]
        
        # 计算背景色的平均值
        avg_r = sum(c[0] for c in corner_colors) // len(corner_colors)
        avg_g = sum(c[1] for c in corner_colors) // len(corner_colors)
        avg_b = sum(c[2] for c in corner_colors) // len(corner_colors)
        bg_color = (avg_r, avg_g, avg_b)
        
        # 遍历每个像素，如果与背景色相似，则设为透明
        for item in data:
            if len(item) == 4:
                r, g, b, a = item
                # 计算与背景色的欧氏距离
                dist = ((r - bg_color[0]) ** 2 + (g - bg_color[1]) ** 2 + (b - bg_color[2]) ** 2) ** 0.5
                if dist < tolerance:
                    # 设为透明
                    new_data.append((r, g, b, 0))
                else:
                    new_data.append(item)
            else:
                new_data.append(item)
        
        new_img = Image.new('RGBA', img.size)
        new_img.putdata(new_data)
        return new_img

    def _load_animal_image(self, index: int, size: int, resample_mode):
        fname = ANIMAL_IMAGE_FILES[index % len(ANIMAL_IMAGE_FILES)]
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
        
        if not os.path.exists(path):
            return None
        
        try:
            img = Image.open(path).convert('RGBA')
            
            # 【新增】自动移除背景，根据图片类型调整容差值
            # 不同的图片可能需要不同的容差
            tolerance = 50  # 默认容差
            
            img = self._remove_background(img, tolerance=tolerance)
            
            w, h = img.size; aspect = w / h if h != 0 else 1
            if aspect >= 1: new_w = size; new_h = max(1, int(size / aspect))
            else: new_h = size; new_w = max(1, int(size * aspect))
            img = img.resize((new_w, new_h), resample_mode)
            return img
        except Exception:
            return None

    # 核心修复: 确保 Tcl 操作在 try/except 块中
    def _move_token_canvas(self, player_index: int, square: int):
        if not self.canvas.winfo_exists():
            return

        x, y = self._coords_for_square(square, player_index)
        oid, txt_id = self.player_tokens[player_index]

        try:
            coords = self.canvas.coords(oid)
            cur_x, cur_y = x, y

            if coords:
                if len(coords) == 2:  # 对于图片 (anchor = S)
                    cur_x, cur_y = coords[0], coords[1]
                elif len(coords) >= 4:  # 对于圆形棋子
                    cur_x, cur_y = (coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2

            # 计算移动距离
            dx = x - cur_x
            dy = y - cur_y

            # 先把棋子移动到目标格
            self.canvas.move(oid, dx, dy)
            if txt_id is not None:
                self.canvas.move(txt_id, dx, dy)
            self.canvas.update()

            # ⭐ 只有猴子(0)和大象(1)做“弹跳”动画
            if True:
                self._bounce_token(oid, txt_id, step=0)

        except tk.TclError:
            return
    def _bounce_token(self, oid, txt_id, step=0, max_steps=4, distance=6):
        """让棋子上下弹跳几下，增加“走路”的感觉。"""
        if not self.canvas.winfo_exists():
            return
        if step >= max_steps:
            return

        try:
            # 偶数帧向上，奇数帧向下
            offset = -distance if step % 2 == 0 else distance
            self.canvas.move(oid, 0, offset)
            if txt_id is not None:
                self.canvas.move(txt_id, 0, offset)
        except tk.TclError:
            return

        # 40ms 后继续下一帧
        self._schedule_animation(
            40,
            lambda: self._bounce_token(oid, txt_id, step + 1, max_steps, distance)
        )

    def update_status(self):
        if not self.root.winfo_exists() or not self.main_frame.winfo_exists():
            return
            
        if self.game.state == GameState.GAME_OVER and self.game.winner:
            status_text = f"Winner: {self.game.winner.name}\nTurn: {self.game.turn}"
            self.current_label.config(text=status_text)
            self.roll_button.config(state=tk.DISABLED)
        else:
            cp = self.game.current_player()
            status_text = f"Turn: {self.game.turn}\nPlayer: {cp.name}\nPosition: {cp.position}"
            self.current_label.config(text=status_text)
            
            can_roll = (self.game.state == GameState.WAITING_ROLL)
            self.roll_button.config(state=(tk.NORMAL if can_roll and not cp.is_bot else tk.DISABLED))

            if cp.is_bot and can_roll:
                self._schedule_animation(1000, self.on_roll)

    # 【核心修正】: 切换游戏时，触发完全的清理和角色选择流程
    def start_new_game(self):
        """启动新游戏流程 - 用当前玩家重新开始，所有角色回到起点"""
        # 取消所有待处理的动画
        self._cancel_all_pending_animations()
        
        # 延迟执行，确保按钮事件处理完成
        def restart():
            # 重置所有玩家位置到起点
            for player in self.players:
                player.position = 0
            
            # 调用 Game 的 start_new_game 重置游戏状态
            self.game.start_new_game()
            
            # 清空棋盘上的骰子
            if self.canvas.winfo_exists():
                if self._dice_canvas_item is not None:
                    self.canvas.delete(self._dice_canvas_item)
                    self._dice_canvas_item = None
            
            # 重新绘制所有玩家
            self._draw_all_players()
            
            # 更新状态显示
            self.update_status()
            
            # 重新启用骰子按钮
            if self.roll_button.winfo_exists():
                self.roll_button.config(state=tk.NORMAL)
        
        self.root.after(50, restart)
        
    def on_save(self):
        try:
            self.game.save_game(SAVE_PATH)
            messagebox.showinfo("Save Game", f"Game saved successfully to {os.path.basename(SAVE_PATH)}")
        except Exception as e:
            messagebox.showerror("Save Failed", f"Could not save the game: {e}")

    # 【核心修正】: 切换游戏时，触发完全的清理和加载流程
    def on_load(self):
        """加载游戏流程"""
        # 取消所有待处理的动画
        self._cancel_all_pending_animations()
        
        # 调用 GameApp 的方法来显示加载对话框
        def load_dialog():
            app = self.root.master
            if hasattr(app, 'start_setup'):
                app.start_setup(load_only=True)
        
        # 延迟执行，确保按钮事件处理完成
        self.root.after(50, load_dialog) 

    def on_roll(self):
        if self.game.state != GameState.WAITING_ROLL:
            return

        self.game.state = GameState.ROLLING_DICE
        self.roll_button.config(state=tk.DISABLED)
        cp = self.game.current_player()
        
        if self.game.current_index == 0:
             self.game.turn += 1

        def after_roll(roll):
            if not self.canvas.winfo_exists():
                return
                
            self.dice_label.config(text=f"Dice: {roll}")
            steps = roll
            final_square = self.board.size * self.board.size
            self.add_log(f"{cp.name} rolls {roll}.")

            def step_move(step_left):
                if not self.canvas.winfo_exists():
                    return
                    
                if step_left <= 0:
                    dest = self.board.get_destination(cp.position)
                    if dest != cp.position:
                        cp.move_to(dest)
                        self._move_token_canvas(self.game.current_index, dest)
                        # 使用 _schedule_animation
                        self._schedule_animation(ANIMATION_STEP_MS, lambda: self._check_win_and_next_player(final_square, cp))
                        return
                    else:
                        self._check_win_and_next_player(final_square, cp)
                        return
                
                cp.move_by(1)
                self._move_token_canvas(self.game.current_index, cp.position)
                # 使用 _schedule_animation
                self._schedule_animation(ANIMATION_STEP_MS, lambda: step_move(step_left - 1))

            step_move(steps)

        self._animate_dice_throw(after_roll)

    def _check_win_and_next_player(self, final_square, current_player):
        if not self.canvas.winfo_exists():
            return
            
        if current_player.position == final_square:
            self.game.state = GameState.GAME_OVER
            self.game.winner = current_player
            self.update_status()
            messagebox.showinfo("Game Over", f"{current_player.name} wins in turn {self.game.turn}!")
            self._cancel_all_pending_animations()
            return
        else:
            self.game.next_player()
            self.game.state = GameState.WAITING_ROLL
            self.update_status()