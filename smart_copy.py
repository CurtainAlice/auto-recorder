"""
智能表格复制工具
功能：识别网页表格序号，自动复制指定范围的数据到Excel
"""
import time
import pyperclip
import openpyxl
from datetime import datetime
import os
import sys
import re

# 导入屏幕识别库
try:
    import pyautogui
    import pytesseract
    from PIL import Image, ImageGrab
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("提示：安装 OCR 库可启用自动识别功能")
    print("pip install pytesseract pillow")


class SmartCopyTool:
    def __init__(self):
        self.copied_count = 0
        self.current_row = 1
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

        # 添加表头
        headers = ['序号', '车牌号', '车辆ID', '车架号', '其他数据']
        for col, header in enumerate(headers, 1):
            self.ws.cell(row=1, column=col, value=header)
        self.current_row = 2

        self.save_excel()
        print(f"Excel文件已创建：{self.excel_file}")

    def save_excel(self):
        """保存Excel"""
        self.wb.save(self.excel_file)

    def paste_to_excel(self, data, start_seq=1):
        """将复制的数据粘贴到Excel"""
        lines = data.strip().split('\n')
        count = 0

        for line in lines:
            if not line.strip():
                continue

            # 尝试按Tab分割
            if '\t' in line:
                cells = line.split('\t')
            else:
                # 按空格分割，但保留车牌号等含空格的数据
                cells = re.split(r'\s{2,}', line)
                if len(cells) == 1:
                    cells = line.split()

            if cells:
                # 清理每个单元格
                cells = [cell.strip() for cell in cells if cell.strip()]

                # 写入Excel
                for col_idx, cell in enumerate(cells, 1):
                    self.ws.cell(row=self.current_row, column=col_idx, value=cell)

                self.current_row += 1
                count += 1

        self.copied_count += count
        self.save_excel()
        return count

    def get_clipboard_data(self):
        """获取剪贴板数据"""
        try:
            data = pyperclip.paste()
            return data
        except:
            return ""

    def screen_capture_region(self, x1, y1, x2, y2):
        """截取屏幕区域"""
        if not HAS_OCR:
            print("❌ OCR功能未安装")
            return ""

        try:
            # 截取指定区域
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))

            # 使用OCR识别文字
            text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng')
            return text
        except Exception as e:
            print(f"❌ 截图识别失败：{e}")
            return ""

    def find_row_by_number(self, row_number):
        """根据行号找到屏幕上的位置"""
        if not HAS_OCR:
            print("❌ OCR功能未安装，请手动定位")
            return None

        print(f"\n🔍 正在查找第 {row_number} 行...")

        # 获取屏幕尺寸
        screen_width, screen_height = pyautogui.size()

        # 截取整个屏幕进行OCR
        screenshot = ImageGrab.grab()
        text = pytesseract.image_to_string(screenshot, lang='chi_sim+eng')

        # 查找行号
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if str(row_number) in line:
                print(f"✅ 找到行号 {row_number}")
                # 返回大概的y坐标（需要根据实际情况调整）
                y_pos = int((i / len(lines)) * screen_height)
                return y_pos

        print(f"⚠️ 未找到行号 {row_number}")
        return None

    def auto_copy_by_range(self, start_row, end_row):
        """根据行号范围自动复制"""
        if not HAS_OCR:
            print("❌ 自动复制需要OCR功能")
            print("请安装：pip install pytesseract pillow")
            print("还需要安装Tesseract OCR引擎")
            return

        print(f"\n🚀 自动复制：第 {start_row} 行 到第 {end_row} 行")
        print("="*50)
        print("操作步骤：")
        print("1. 程序会自动定位起始行")
        print("2. 按住Shift选择到结束行")
        print("3. Ctrl+C复制")
        print("="*50)

        # 等待用户准备好
        input("\n请确保DataWorks窗口在前台，然后按 Enter 继续...")

        # 查找起始行位置
        start_y = self.find_row_by_number(start_row)
        if start_y is None:
            print("❌ 无法自动定位，请使用手动模式")
            return

        # 获取屏幕宽度，假设表格在屏幕左侧
        screen_width, _ = pyautogui.size()
        x_pos = 100  # 假设序号列在x=100的位置

        print(f"\n📍 起始位置：({x_pos}, {start_y})")
        print("3秒后开始操作...")
        time.sleep(3)

        try:
            # 点击起始行
            pyautogui.click(x_pos, start_y)
            time.sleep(0.2)

            # 查找结束行位置
            end_y = self.find_row_by_number(end_row)
            if end_y is None:
                # 如果找不到结束行，根据行数估算
                row_height = 25  # 假设每行25像素
                end_y = start_y + (end_row - start_row) * row_height
                print(f"⚠️ 使用估算位置：{end_y}")

            # 按住Shift点击结束行
            pyautogui.keyDown('shift')
            pyautogui.click(x_pos, end_y)
            pyautogui.keyUp('shift')
            time.sleep(0.3)

            # 复制
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.5)

            # 获取剪贴板内容
            data = self.get_clipboard_data()
            if data:
                count = self.paste_to_excel(data, start_row)
                print(f"\n✅ 成功复制 {count} 条数据")
                print(f"📊 已复制总数：{self.copied_count} 条")
            else:
                print("❌ 复制失败，剪贴板为空")

        except Exception as e:
            print(f"❌ 操作失败：{e}")

    def manual_copy_mode(self):
        """手动复制模式"""
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

                data = self.get_clipboard_data()
                if data:
                    count = self.paste_to_excel(data)
                    print(f"✅ 成功粘贴 {count} 条数据")
                    print(f"📊 已复制总数：{self.copied_count} 条")
                else:
                    print("⚠️ 剪贴板为空，请先复制数据")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 错误：{e}")

        self.show_summary()

    def show_summary(self):
        """显示汇总信息"""
        print("\n" + "="*50)
        print("📊 汇总信息")
        print("="*50)
        print(f"已复制总数：{self.copied_count} 条")
        print(f"Excel文件：{self.excel_file}")
        print("="*50)

    def run(self):
        """主程序"""
        print("="*60)
        print("🔧 智能表格复制工具")
        print("="*60)
        print("功能：识别网页表格序号，自动复制数据到Excel")
        print("="*60)

        while True:
            print("\n选择模式：")
            print("1. 手动复制模式（推荐）")
            if HAS_OCR:
                print("2. 自动复制模式（需要OCR）")
            print("3. 查看统计")
            print("4. 退出")

            choice = input("\n请输入选项：").strip()

            if choice == '1':
                self.manual_copy_mode()
            elif choice == '2' and HAS_OCR:
                try:
                    start = int(input("起始行号："))
                    end = int(input("结束行号："))
                    if end - start + 1 > 100:
                        print("⚠️ 超过100条限制，自动截断到100条")
                        end = start + 99
                    self.auto_copy_by_range(start, end)
                except ValueError:
                    print("❌ 请输入有效的数字")
            elif choice == '3':
                self.show_summary()
            elif choice == '4':
                break
            else:
                print("❌ 无效选项")

        print(f"\n👋 程序退出，Excel文件已保存在：{self.excel_file}")


if __name__ == "__main__":
    tool = SmartCopyTool()
    tool.run()
