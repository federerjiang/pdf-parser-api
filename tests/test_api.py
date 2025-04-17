#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import base64
import os
import pytest
import time
import json
from pathlib import Path


# 测试配置
API_BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = os.path.join(os.path.dirname(__file__), "example.pdf")


def test_health_check():
    """测试健康检查接口"""
    response = requests.get(f"{API_BASE_URL}/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PDF Parser API"


def get_base64_pdf():
    """将测试PDF文件转换为base64编码"""
    if not os.path.exists(TEST_PDF_PATH):
        pytest.skip(f"测试PDF文件不存在: {TEST_PDF_PATH}")
    
    with open(TEST_PDF_PATH, "rb") as pdf_file:
        pdf_content = pdf_file.read()
    
    return base64.b64encode(pdf_content).decode("utf-8")


def test_convert_pdf():
    """测试PDF转换接口"""
    # 获取base64编码的PDF
    base64_pdf = get_base64_pdf()
    
    # 准备请求数据
    payload = {
        "pdf_base64": base64_pdf
    }
    
    # 发送请求
    response = requests.post(
        f"{API_BASE_URL}/v1/convert",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    # 校验响应
    assert response.status_code == 200, f"请求失败，状态码: {response.status_code}，响应内容: {response.text}"
    
    data = response.json()
    assert data["success"] is True
    assert "output" in data
    assert "images" in data
    assert "metadata" in data


def test_invalid_base64():
    """测试无效的base64输入"""
    payload = {
        "pdf_base64": "无效的base64字符串"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/v1/convert",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    # 输出响应内容用于调试
    print(f"\n无效base64测试响应: {response.status_code} - {response.text}")
    
    # 根据实际实现，验证响应
    # 可能是HTTP 422错误(验证错误)或其他状态码
    # 不要断言具体的错误状态码，只要不是200即表示测试通过
    assert response.status_code != 200
    
    # 针对不同的错误响应格式进行处理
    try:
        data = response.json()
        # 如果是JSON格式的错误响应
        if "detail" in data:
            # FastAPI验证错误的标准格式
            assert "detail" in data
            print(f"错误详情: {data['detail']}")
        elif "error" in data:
            # 自定义错误响应格式
            assert data.get("success") is False
            assert "error" in data
            print(f"错误详情: {data['error']}")
    except json.JSONDecodeError:
        # 如果响应不是JSON格式，至少确保它不是成功响应
        print("响应不是JSON格式")
        pass


def test_performance():
    """测试API性能"""
    # 获取base64编码的PDF
    base64_pdf = get_base64_pdf()
    
    # 准备请求数据
    payload = {
        "pdf_base64": base64_pdf
    }
    
    # 记录开始时间
    start_time = time.time()
    
    # 发送请求
    response = requests.post(
        f"{API_BASE_URL}/v1/convert",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    # 输出响应内容
    print("\n响应详情:")
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    try:
        print(f"响应体: {response.json()}")
    except:
        print(f"响应体: {response.text}")
    
    # 计算响应时间
    response_time = time.time() - start_time
    
    # 校验响应
    assert response.status_code == 200
    print(f"API响应时间: {response_time:.2f}秒")
    
    # 记录响应时间
    with open(os.path.join(os.path.dirname(__file__), "performance_results.txt"), "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {response_time:.2f}秒\n")


if __name__ == "__main__":
    # 直接运行测试
    print("开始测试 PDF Parser API...")
    test_health_check()
    print("✓ 健康检查测试通过")
    
    try:
        test_convert_pdf()
        print("✓ PDF转换测试通过")
    except Exception as e:
        print(f"✗ PDF转换测试失败: {str(e)}")
    
    try:
        test_invalid_base64()
        print("✓ 无效base64测试通过")
    except Exception as e:
        print(f"✗ 无效base64测试失败: {str(e)}")
    
    try:
        test_performance()
        print("✓ 性能测试通过")
    except Exception as e:
        print(f"✗ 性能测试失败: {str(e)}") 