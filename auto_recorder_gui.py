"""
鼠标键盘录制回放自动化工具 - GUI版本
功能：录制鼠标键盘操作，回放实现自动化
"""
import time
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from pynput import mouse, keyboard
import pyautogui

# 禁用pyautogui的安全暂停
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

class AutoRecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("鼠标键盘录制回放工具 v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        self.operations = []
        self.is_recording = False
        self.is_playing = False
        self.recording_start_time = 0

        # 热键设置
        self.START_STOP_KEY = keyboard.Key.f9
        self.PLAY_KEY = keyboard.Key.f10

        # 文件保存目录
        self.file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recordings')
        os.makedirs(self.file_dir, exist_ok=True)

        # 当前文件路径
        self.current_file = None

        # 鼠标监听器
        self.mouse_listener = None
        # 键盘监听器
        self.keyboard_listener = None

        self.setup_gui()
        self.start_listeners()

    def setup_gui(self):
        """设置GUI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="鼠标键盘录制回放工具", font=("微软雅黑", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("微软雅黑", 12), foreground="blue")
        status_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))

        # 控制按钮区域
        control_frame = ttk.LabelFrame(main_frame, text="控制", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # 录制按钮
        self.record_btn = ttk.Button(control_frame, text="🔴 开始录制 (F9)", command=self.toggle_recording)
        self.record_btn.grid(row=0, column=0, padx=5)

        # 回放按钮
        self.play_btn = ttk.Button(control_frame, text="▶️ 开始回放 (F10)", command=self.start_playing)
        self.play_btn.grid(row=0, column=1, padx=5)

        # 停止按钮
        self.stop_btn = ttk.Button(control_frame, text="⏹️ 停止", command=self.stop_all)
        self.stop_btn.grid(row=0, column=2, padx=5)

        # 循环次数设置
        loop_frame = ttk.Frame(control_frame)
        loop_frame.grid(row=0, column=3, padx=10)

        ttk.Label(loop_frame, text="循环次数:").pack(side=tk.LEFT)
        self.loop_var = tk.StringVar(value="1")
        self.loop_entry = ttk.Entry(loop_frame, textvariable=self.loop_var, width=5)
        self.loop_entry.pack(side=tk.LEFT, padx=5)

        # 操作列表区域
        list_frame = ttk.LabelFrame(main_frame, text="操作列表", padding="10")
        list_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 操作列表
        columns = ("序号", "类型", "详情", "延迟(秒)")
        self.op_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        self.op_tree.heading("序号", text="序号")
        self.op_tree.heading("类型", text="类型")
        self.op_tree.heading("详情", text="详情")
        self.op_tree.heading("延迟(秒)", text="延迟(秒)")

        self.op_tree.column("序号", width=60)
        self.op_tree.column("类型", width=120)
        self.op_tree.column("详情", width=400)
        self.op_tree.column("延迟(秒)", width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.op_tree.yview)
        self.op_tree.configure(yscrollcommand=scrollbar.set)

        self.op_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 文件操作区域
        file_frame = ttk.LabelFrame(main_frame, text="文件操作", padding="10")
        file_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(file_frame, text="💾 保存录制", command=self.save_operations).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="📂 加载录制", command=self.load_operations).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="🗑️ 清空列表", command=self.clear_operations).pack(side=tk.LEFT, padx=5)

        self.file_label = ttk.Label(file_frame, text="未保存", foreground="gray")
        self.file_label.pack(side=tk.RIGHT, padx=5)

        # 快捷键提示
        hint_frame = ttk.Frame(main_frame)
        hint_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E))

        ttk.Label(hint_frame, text="快捷键: F9=录制/停止 | F10=回放 | F12=退出", foreground="gray").pack()

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

    def on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件"""
        if not self.is_recording:
            return

        delay = time.time() - self.recording_start_time
        button_str = "left" if button == mouse.Button.left else "right"

        self.operations.append({
            'type': 'mouse_click',
            'x': x,
            'y': y,
            'button': button_str,
            'delay': delay
        })

        action = "按下" if pressed else "释放"
        detail = f"({x}, {y}) - {button_str} - {action}"
        self.root.after(0, self.add_operation_to_list, len(self.operations), "鼠标点击", detail, delay)

    def on_mouse_scroll(self, x, y, dx, dy):
        """鼠标滚轮事件"""
        if not self.is_recording:
            return

        delay = time.time() - self.recording_start_time
        self.operations.append({
            'type': 'mouse_scroll',
            'x': x,
            'y': y,
            'dx': dx,
            'dy': dy,
            'delay': delay
        })

        detail = f"({x}, {y}) - 方向: {dy}"
        self.root.after(0, self.add_operation_to_list, len(self.operations), "鼠标滚轮", detail, delay)

    def on_key_press(self, key):
        """键盘按下事件"""
        if key == self.START_STOP_KEY:
            self.root.after(0, self.toggle_recording)
            return
        elif key == self.PLAY_KEY:
            self.root.after(0, self.start_playing)
            return

        if not self.is_recording:
            return

        delay = time.time() - self.recording_start_time
        key_str = str(key)

        self.operations.append({
            'type': 'key_press',
            'key': key_str,
            'delay': delay
        })

        detail = f"按下: {key_str}"
        self.root.after(0, self.add_operation_to_list, len(self.operations), "按键按下", detail, delay)

    def on_key_release(self, key):
        """键盘释放事件"""
        if not self.is_recording:
            return

        delay = time.time() - self.recording_start_time
        key_str = str(key)

        self.operations.append({
            'type': 'key_release',
            'key': key_str,
            'delay': delay
        })

        detail = f"释放: {key_str}"
        self.root.after(0, self.add_operation_to_list, len(self.operations), "按键释放", detail, delay)

    def add_operation_to_list(self, index, op_type, detail, delay):
        """添加操作到列表"""
        self.op_tree.insert("", tk.END, values=(index, op_type, detail, f"{delay:.3f}"))
        self.op_tree.see(tk.END)
        self.status_var.set(f"已录制 {len(self.operations)} 个操作")

    def toggle_recording(self):
        """切换录制状态"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """开始录制"""
        if self.is_playing:
            messagebox.showwarning("警告", "正在回放中，无法录制")
            return

        self.is_recording = True
        self.operations = []
        self.recording_start_time = time.time()

        # 清空列表
        for item in self.op_tree.get_children():
            self.op_tree.delete(item)

        self.record_btn.configure(text="⏹️ 停止录制 (F9)")
        self.status_var.set("🔴 录制中...")

    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        self.record_btn.configure(text="🔴 开始录制 (F9)")
        self.status_var.set(f"⏹️ 录制停止，共 {len(self.operations)} 个操作")

        if self.operations:
            self.save_operations()

    def save_operations(self):
        """保存操作序列"""
        if not self.operations:
            messagebox.showwarning("警告", "没有操作可保存")
            return

        # 弹出保存对话框
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f'recording_{timestamp}.json'

        filepath = filedialog.asksaveasfilename(
            initialdir=self.file_dir,
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.operations, f, indent=2, ensure_ascii=False)

                self.current_file = filepath
                filename = os.path.basename(filepath)
                self.file_label.configure(text=f"已保存: {filename}", foreground="green")
                messagebox.showinfo("成功", f"操作已保存到：\n{filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

    def load_operations(self, filepath=None):
        """加载操作序列"""
        if filepath is None:
            filepath = filedialog.askopenfilename(
                initialdir=self.file_dir,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.operations = json.load(f)

            # 清空列表并重新填充
            for item in self.op_tree.get_children():
                self.op_tree.delete(item)

            for i, op in enumerate(self.operations, 1):
                if op['type'] == 'mouse_click':
                    detail = f"({op['x']}, {op['y']}) - {op['button']}"
                    op_type = "鼠标点击"
                elif op['type'] == 'mouse_scroll':
                    detail = f"({op['x']}, {op['y']}) - 方向: {op['dy']}"
                    op_type = "鼠标滚轮"
                elif op['type'] == 'key_press':
                    detail = f"按下: {op['key']}"
                    op_type = "按键按下"
                elif op['type'] == 'key_release':
                    detail = f"释放: {op['key']}"
                    op_type = "按键释放"
                else:
                    detail = str(op)
                    op_type = "未知"

                self.op_tree.insert("", tk.END, values=(i, op_type, detail, f"{op.get('delay', 0):.3f}"))

            self.current_file = filepath
            filename = os.path.basename(filepath)
            self.file_label.configure(text=f"已加载: {filename}", foreground="blue")
            self.status_var.set(f"已加载 {len(self.operations)} 个操作")

        except Exception as e:
            messagebox.showerror("错误", f"加载失败：{e}")

    def clear_operations(self):
        """清空操作列表"""
        if self.operations:
            if messagebox.askyesno("确认", "确定要清空所有操作吗？"):
                self.operations = []
                for item in self.op_tree.get_children():
                    self.op_tree.delete(item)
                self.status_var.set("已清空")

    def parse_key(self, key_str):
        """解析按键字符串"""
        if 'Key.' in key_str:
            key_name = key_str.replace('Key.', '').lower()
            special_keys = {
                'ctrl_l': 'ctrl', 'ctrl_r': 'ctrl',
                'alt_l': 'alt', 'alt_r': 'alt',
                'shift': 'shift', 'shift_l': 'shift', 'shift_r': 'shift',
                'enter': 'enter', 'return': 'enter',
                'tab': 'tab',
                'space': 'space',
                'backspace': 'backspace',
                'delete': 'delete',
                'esc': 'escape',
                'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right',
                'home': 'home', 'end': 'end',
                'page_up': 'pageup', 'page_down': 'pagedown',
                'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
                'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
                'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
            }
            return special_keys.get(key_name, key_name)

        if len(key_str) == 3 and key_str.startswith("'") and key_str.endswith("'"):
            return key_str[1:-1]

        return None

    def start_playing(self):
        """开始回放"""
        if self.is_recording:
            messagebox.showwarning("警告", "正在录制中，无法回放")
            return

        if not self.operations:
            messagebox.showwarning("警告", "没有可回放的操作")
            return

        if self.is_playing:
            messagebox.showwarning("警告", "已在回放中")
            return

        try:
            loop_count = int(self.loop_var.get())
        except:
            loop_count = 1

        self.is_playing = True
        self.play_btn.configure(text="⏸️ 回放中...")
        self.status_var.set(f"▶️ 回放中（循环 {loop_count} 次）...")

        # 在新线程中回放
        play_thread = threading.Thread(target=self.play_operations, args=(loop_count,))
        play_thread.daemon = True
        play_thread.start()

    def play_operations(self, loop_count):
        """回放操作序列"""
        try:
            for loop in range(loop_count):
                if not self.is_playing:
                    break

                self.root.after(0, self.status_var.set, f"🔄 第 {loop + 1}/{loop_count} 次循环")
                prev_delay = 0

                for i, op in enumerate(self.operations):
                    if not self.is_playing:
                        break

                    # 等待延迟
                    delay = op.get('delay', 0) - prev_delay
                    if delay > 0:
                        time.sleep(delay)
                    prev_delay = op.get('delay', 0)

                    # 执行操作
                    try:
                        if op['type'] == 'mouse_click':
                            if op['button'] == 'left':
                                pyautogui.click(op['x'], op['y'])
                            else:
                                pyautogui.rightClick(op['x'], op['y'])

                        elif op['type'] == 'mouse_scroll':
                            pyautogui.scroll(op['dy'] * 3, op['x'], op['y'])

                        elif op['type'] == 'key_press':
                            key = self.parse_key(op['key'])
                            if key:
                                pyautogui.keyDown(key)

                        elif op['type'] == 'key_release':
                            key = self.parse_key(op['key'])
                            if key:
                                pyautogui.keyUp(key)

                        # 高亮当前操作
                        self.root.after(0, self.highlight_operation, i + 1)

                    except Exception as e:
                        print(f"操作执行错误：{e}")

                if self.is_playing and loop < loop_count - 1:
                    time.sleep(1)

        except Exception as e:
            self.root.after(0, messagebox.showerror, "错误", f"回放错误：{e}")

        finally:
            self.is_playing = False
            self.root.after(0, self.play_btn.configure, {"text": "▶️ 开始回放 (F10)"})
            self.root.after(0, self.status_var.set, "⏹️ 回放结束")

    def highlight_operation(self, index):
        """高亮当前操作"""
        for item in self.op_tree.get_children():
            self.op_tree.selection_remove(item)

        items = self.op_tree.get_children()
        if index - 1 < len(items):
            self.op_tree.selection_set(items[index - 1])
            self.op_tree.see(items[index - 1])

    def stop_all(self):
        """停止所有操作"""
        if self.is_recording:
            self.stop_recording()
        if self.is_playing:
            self.is_playing = False
            self.status_var.set("⏹️ 已停止回放")

    def start_listeners(self):
        """启动监听器"""
        self.mouse_listener = mouse.Listener(
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )

        self.mouse_listener.start()
        self.keyboard_listener.start()

    def run(self):
        """运行程序"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        """关闭程序"""
        self.stop_all()
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    app = AutoRecorderGUI()
    app.run()
