"""
DataWorks电子表格数据自动复制到Excel工具
功能：通过热键触发，自动从网页表格复制数据到Excel文件
"""
import time
import pyperclip
import openpyxl
from datetime import datetime
import os
import sys

# 导入Windows相关库
try:
    import pyautogui
    import keyboard
    HAS_GUI = True
except:
    HAS_GUI = False
    print("警告：未安装GUI库，将使用手动输入模式")

class DataWorksCopyTool:
    def __init__(self):
        self.copied_count = 0
        self.batch_size = 100  # 每次最多复制100条
        self.excel_file = None
        self.wb = None
        self.ws = None
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
        os.makedirs(self.output_dir, exist_ok=True)
        self.init_excel()

    def init_excel(self):
        """初始化Excel文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'DataWorks数据_{timestamp}.xlsx'
        self.excel_file = os.path.join(self.output_dir, filename)
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.ws.title = '数据'
        self.current_row = 1
        self.save_excel()
        print(f"Excel文件已创建：{self.excel_file}")

    def save_excel(self):
        """保存Excel文件"""
        self.wb.save(self.excel_file)

    def paste_to_excel(self, data):
        """将数据粘贴到Excel"""
        lines = data.strip().split('\n')
        count = 0

        for line in lines:
            if line.strip():
                # 尝试按Tab分割（网页表格通常用Tab分隔）
                if '\t' in line:
                    cells = line.split('\t')
                else:
                    # 如果没有Tab，按多个空格分割
                    cells = line.split()

                if cells:
                    for col_idx, cell in enumerate(cells, 1):
                        self.ws.cell(row=self.current_row, column=col_idx, value=cell.strip())
                    self.current_row += 1
                    count += 1

        self.copied_count += count
        self.save_excel()
        return count

    def manual_copy_mode(self):
        """手动复制模式 - 用户手动复制，程序监听剪贴板"""
        print("\n" + "="*50)
        print("📋 手动复制模式")
        print("="*50)
        print("操作步骤：")
        print("1. 在DataWorks中选择要复制的行（最多100行）")
        print("2. Ctrl+C 复制")
        print("3. 在此窗口按 Enter 粘贴到Excel")
        print("4. 输入 'quit' 退出程序")
        print("="*50)

        while True:
            try:
                cmd = input("\n按 Enter 粘贴，输入 quit 退出：").strip()
                if cmd.lower() == 'quit':
                    break

                # 获取剪贴板内容
                data = pyperclip.paste()
                if data:
                    count = self.paste_to_excel(data)
                    print(f"✅ 成功粘贴 {count} 条数据")
                    print(f"📊 已复制总数：{self.copied_count} 条")
                else:
                    print("⚠️  剪贴板为空，请先复制数据")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 错误：{e}")

        print(f"\n📊 总共复制了 {self.copied_count} 条数据")
        print(f"📁 Excel文件保存在：{self.excel_file}")

    def auto_copy_mode(self, start_row, end_row):
        """自动复制模式 - 模拟鼠标键盘操作"""
        if not HAS_GUI:
            print("❌ 自动复制模式需要GUI库，请使用手动模式")
            return

        print(f"\n🚀 自动复制模式：第 {start_row} 行 到第 {end_row} 行")
        print("3秒后开始，请确保DataWorks窗口在前台...")
        time.sleep(3)

        try:
            # 获取屏幕分辨率
            screen_width, screen_height = pyautogui.size()
            print(f"屏幕分辨率：{screen_width} x {screen_height}")

            # 这里需要根据实际页面位置调整
            # 提示用户先手动定位第一个单元格的位置
            print("\n请先手动点击表格的第一个单元格，然后按 Enter 继续...")
            input()

            # 获取当前鼠标位置作为起始点
            start_x, start_y = pyautogui.position()
            print(f"起始位置：({start_x}, {start_y})")

            # 模拟选择多行并复制
            # 注意：这里需要根据实际表格的行高调整
            row_height = 25  # 假设每行25像素，需要根据实际情况调整

            # 点击起始行
            pyautogui.click(start_x, start_y)
            time.sleep(0.2)

            # 按住Shift选择到结束行
            end_y = start_y + (end_row - start_row) * row_height
            pyautogui.keyDown('shift')
            pyautogui.click(start_x, end_y)
            pyautogui.keyUp('shift')
            time.sleep(0.3)

            # 复制
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)

            # 粘贴到Excel
            count = self.paste_to_excel(pyperclip.paste())
            print(f"✅ 成功复制 {count} 条数据")

        except Exception as e:
            print(f"❌ 自动复制失败：{e}")
            print("请使用手动复制模式")

    def run(self):
        """主程序"""
        print("="*60)
        print("🔧 DataWorks电子表格数据复制工具")
        print("="*60)
        print("功能：从网页表格复制数据到Excel，每次最多100条")
        print("="*60)

        while True:
            print("\n选择模式：")
            print("1. 手动复制模式（推荐）")
            print("2. 自动复制模式（需要定位）")
            print("3. 查看统计")
            print("4. 退出")

            choice = input("\n请输入选项 (1-4)：").strip()

            if choice == '1':
                self.manual_copy_mode()
            elif choice == '2':
                try:
                    start = int(input("起始行号："))
                    end = int(input("结束行号："))
                    if end - start + 1 > self.batch_size:
                        print(f"⚠️  超过{self.batch_size}条限制，自动截断")
                        end = start + self.batch_size - 1
                    self.auto_copy_mode(start, end)
                except ValueError:
                    print("❌ 请输入有效的数字")
            elif choice == '3':
                print(f"\n📊 统计信息：")
                print(f"已复制总数：{self.copied_count} 条")
                print(f"Excel文件：{self.excel_file}")
            elif choice == '4':
                break
            else:
                print("❌ 无效选项")

        print(f"\n👋 程序退出，Excel文件已保存在：{self.excel_file}")


if __name__ == "__main__":
    tool = DataWorksCopyTool()
    tool.run()
