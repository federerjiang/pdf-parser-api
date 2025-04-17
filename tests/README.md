# API测试指南

本目录包含用于测试PDF解析API服务的测试脚本和相关文件。

## 测试文件说明

- `test_api.py` - API测试主脚本
- `requirements-test.txt` - 测试所需的Python依赖
- `run_tests.sh` - 测试运行脚本
- `example.pdf` - 测试用的示例PDF文件（需要自行提供）

## 运行测试

确保本地API服务已启动并运行在 http://localhost:8000 上。

### 方法1：使用提供的脚本

```bash
# 直接运行测试
./tests/run_tests.sh

# 使用pytest运行测试（生成更详细的报告）
./tests/run_tests.sh --with-pytest
```

### 方法2：手动运行

```bash
# 安装测试依赖
pip install -r tests/requirements-test.txt

# 运行测试
python tests/test_api.py

# 或使用pytest运行
pytest tests/test_api.py -v
```

## 测试功能

1. **健康检查测试** - 验证API服务是否正常运行
2. **PDF转换测试** - 测试PDF转换功能是否正常工作
3. **无效输入测试** - 验证API对无效输入的处理
4. **性能测试** - 测量API响应时间并记录结果

## 注意事项

- 确保在测试目录中放置名为`example.pdf`的测试PDF文件
- 性能测试结果将保存在`tests/performance_results.txt`文件中
- 所有测试都依赖于本地运行的API服务（localhost:8000） 