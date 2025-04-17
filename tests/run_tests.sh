#!/bin/bash

# 定位到脚本所在目录
cd "$(dirname "$0")"

# 安装测试依赖
# pip install -r requirements-test.txt

# 运行API测试
echo "运行API测试..."
if [ "$1" == "--with-pytest" ]; then
    # 使用pytest运行测试
    pytest test_api.py -v
else
    # 直接运行测试脚本
    python test_api.py
fi 