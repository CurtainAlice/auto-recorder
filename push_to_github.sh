#!/bin/bash
# 推送代码到GitHub的脚本

# 替换为你的GitHub用户名
GITHUB_USERNAME="你的用户名"

echo "=========================================="
echo "  推送代码到GitHub"
echo "=========================================="
echo ""
echo "请先在GitHub上创建仓库 auto-recorder"
echo ""

# 设置Git用户信息（可选）
# git config user.name "你的名字"
# git config user.email "你的邮箱"

# 添加remote
git remote add origin https://github.com/$GITHUB_USERNAME/auto-recorder.git

# 推送
git branch -M main
git push -u origin main

echo ""
echo "=========================================="
echo "  推送完成！"
echo "=========================================="
echo ""
echo "接下来："
echo "1. 打开 https://github.com/$GITHUB_USERNAME/auto-recorder"
echo "2. 点击 Actions 选项卡"
echo "3. 点击 Build Windows EXE"
echo "4. 点击 Run workflow"
echo "5. 等待5-10分钟打包完成"
echo "6. 在 Artifacts 下载 exe 文件"
