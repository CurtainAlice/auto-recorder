"""
鼠标键盘录制回放自动化工具
功能：录制鼠标键盘操作，回放实现自动化
"""
import time
import json
import os
import sys
import threading
import pickle
from datetime import datetime
from pynput import mouse, keyboard
import pyautogui

# 禁用pyautogui的安全暂停
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

class AutoRecorder:
    def __init__(self):
        self.operations = []
        self.is_recording = False
        self.is_playing = False
        self.recording_start_time = 0
        self.file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recordings')
        os.makedirs(self.file_dir, exist_ok=True)

        # 热键设置
        self.START_STOP_KEY = keyboard.Key.f9  # F9 开始/停止录制
        self.PLAY_KEY = keyboard.Key.f10  # F10 回放
        self.QUIT_KEY = keyboard.Key.f12  # F12 退出

        # 鼠标监听器
        self.mouse_listener = None
        # 键盘监听器
        self.keyboard_listener = None

    def on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件"""
        if not self.is_recording:
            return

        event_type = 'mouse_click'
        delay = time.time() - self.recording_start_time

        self.operations.append({
            'type': event_type,
            'x': x,
            'y': y,
            'button': str(button),
            'pressed': pressed,
            'delay': delay
        })

        action = "按下" if pressed else "释放"
        print(f"🖱️ 鼠标{action}：({x}, {y}) - {button}")

    def on_mouse_move(self, x, y):
        """鼠标移动事件"""
        if not self.is_recording:
            return

        # 不记录移动，只记录点击，减少数据量
        pass

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

        print(f"🖱️ 鼠标滚轮：({x}, {y}) - 方向: {dy}")

    def on_key_press(self, key):
        """键盘按下事件"""
        # 检查热键
        if key == self.START_STOP_KEY:
            self.toggle_recording()
            return
        elif key == self.PLAY_KEY:
            self.start_playing()
            return
        elif key == self.QUIT_KEY:
            self.stop_all()
            return

        if not self.is_recording:
            return

        delay = time.time() - self.recording_start_time
        self.operations.append({
            'type': 'key_press',
            'key': str(key),
            'delay': delay
        })

        print(f"⌨️ 按键按下：{key}")

    def on_key_release(self, key):
        """键盘释放事件"""
        if not self.is_recording:
            return

        delay = time.time() - self.recording_start_time
        self.operations.append({
            'type': 'key_release',
            'key': str(key),
            'delay': delay
        })

        print(f"⌨️ 按键释放：{key}")

    def toggle_recording(self):
        """切换录制状态"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """开始录制"""
        if self.is_playing:
            print("⚠️ 正在回放中，无法录制")
            return

        self.is_recording = True
        self.operations = []
        self.recording_start_time = time.time()
        print("\n🔴 开始录制...")
        print("操作将被记录，按 F9 停止录制")
        print("按 F10 回放，按 F12 退出程序")

    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        print(f"\n⏹️ 停止录制，共记录 {len(self.operations)} 个操作")

        if self.operations:
            self.save_operations()

    def save_operations(self):
        """保存操作序列"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'recording_{timestamp}.json'
        filepath = os.path.join(self.file_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.operations, f, indent=2, ensure_ascii=False)

        print(f"💾 操作已保存到：{filepath}")
        return filepath

    def load_operations(self, filepath=None):
        """加载操作序列"""
        if filepath is None:
            # 列出可用文件
            files = [f for f in os.listdir(self.file_dir) if f.endswith('.json')]
            if not files:
                print("❌ 没有找到录制文件")
                return False

            print("\n📁 可用的录制文件：")
            for i, f in enumerate(files, 1):
                print(f"{i}. {f}")

            try:
                choice = int(input("\n选择文件编号：")) - 1
                filepath = os.path.join(self.file_dir, files[choice])
            except:
                print("❌ 无效选择")
                return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.operations = json.load(f)
            print(f"📂 已加载 {len(self.operations)} 个操作")
            return True
        except Exception as e:
            print(f"❌ 加载失败：{e}")
            return False

    def play_operations(self, loop_count=1):
        """回放操作序列"""
        if not self.operations:
            print("❌ 没有可回放的操作")
            return

        if self.is_playing:
            print("⚠️ 已在回放中")
            return

        self.is_playing = True
        print(f"\n▶️ 开始回放（循环 {loop_count} 次）...")
        print("按 F12 停止回放")

        try:
            for loop in range(loop_count):
                if not self.is_playing:
                    break

                print(f"\n🔄 第 {loop + 1} 次循环")
                prev_delay = 0

                for i, op in enumerate(self.operations):
                    if not self.is_playing:
                        print("⏹️ 回放已停止")
                        break

                    # 等待延迟
                    delay = op.get('delay', 0) - prev_delay
                    if delay > 0:
                        time.sleep(delay)
                    prev_delay = op.get('delay', 0)

                    # 执行操作
                    try:
                        if op['type'] == 'mouse_click':
                            button = mouse.Button.left if 'left' in op['button'] else mouse.Button.right
                            if op['pressed']:
                                pyautogui.click(op['x'], op['y'])
                                print(f"🖱️ 点击：({op['x']}, {op['y']})")

                        elif op['type'] == 'mouse_scroll':
                            pyautogui.scroll(op['dy'] * 3, op['x'], op['y'])
                            print(f"🖱️ 滚轮：({op['x']}, {op['y']})")

                        elif op['type'] == 'key_press':
                            key = self.parse_key(op['key'])
                            if key:
                                pyautogui.keyDown(key)
                                print(f"⌨️ 按下：{key}")

                        elif op['type'] == 'key_release':
                            key = self.parse_key(op['key'])
                            if key:
                                pyautogui.keyUp(key)
                                print(f"⌨️ 释放：{key}")

                    except Exception as e:
                        print(f"⚠️ 操作执行错误：{e}")

                if self.is_playing and loop < loop_count - 1:
                    print("⏸️ 循环间暂停1秒...")
                    time.sleep(1)

        except Exception as e:
            print(f"❌ 回放错误：{e}")

        finally:
            self.is_playing = False
            print("⏹️ 回放结束")

    def parse_key(self, key_str):
        """解析按键字符串"""
        # 处理特殊键
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

        # 处理普通字符键
        if len(key_str) == 3 and key_str.startswith("'") and key_str.endswith("'"):
            return key_str[1:-1]

        return None

    def start_playing(self):
        """开始回放"""
        if self.is_recording:
            print("⚠️ 正在录制中，无法回放")
            return

        if not self.operations:
            if not self.load_operations():
                return

        # 询问循环次数
        try:
            loop_input = input("\n输入循环次数（直接回车默认1次）：").strip()
            loop_count = int(loop_input) if loop_input else 1
        except:
            loop_count = 1

        # 在新线程中回放，避免阻塞
        play_thread = threading.Thread(target=self.play_operations, args=(loop_count,))
        play_thread.daemon = True
        play_thread.start()

    def stop_all(self):
        """停止所有操作"""
        if self.is_recording:
            self.stop_recording()
        if self.is_playing:
            self.is_playing = False
            print("⏹️ 已停止回放")

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

        print("\n" + "="*60)
        print("🔧 鼠标键盘录制回放工具")
        print("="*60)
        print("热键说明：")
        print("  F9  - 开始/停止录制")
        print("  F10 - 开始回放")
        print("  F12 - 退出程序")
        print("="*60)
        print("使用步骤：")
        print("1. 先录制一次完整操作（F9开始，F9停止）")
        print("2. 程序自动保存录制")
        print("3. 按F10回放（可设置循环次数）")
        print("="*60)

    def run(self):
        """主程序"""
        self.start_listeners()

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            print("\n👋 程序退出")


if __name__ == "__main__":
    recorder = AutoRecorder()
    recorder.run()
