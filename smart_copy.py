"""
智能表格复制工具
功能：从网页表格复制数据到Excel，每次最多100条
"""
import time
import pyperclip
import openpyxl
from datetime import datetime
import os
import re


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

    def paste_to_excel(self, data):
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
        print("功能：从网页表格复制数据到Excel，每次最多100条")
        print("="*60)

        while True:
            print("\n选择模式：")
            print("1. 手动复制模式")
            print("2. 查看统计")
            print("3. 退出")

            choice = input("\n请输入选项：").strip()

            if choice == '1':
                self.manual_copy_mode()
            elif choice == '2':
                self.show_summary()
            elif choice == '3':
                break
            else:
                print("❌ 无效选项")

        print(f"\n👋 程序退出，Excel文件已保存在：{self.excel_file}")


if __name__ == "__main__":
    tool = SmartCopyTool()
    tool.run()
