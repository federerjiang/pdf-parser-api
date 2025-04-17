# PDF解析API服务

这是一个基于FastAPI和marker-pdf库构建的PDF解析API服务，能够从PDF文件中提取文本内容并进行格式化输出。

## 功能特点

- 支持PDF文件的文本提取
- 支持OCR识别（光学字符识别）
- 支持多种输出格式（Markdown、JSON、HTML）
- 支持Base64编码的PDF输入
- 支持多语言OCR识别
- REST API接口，易于集成

## 环境要求

- Python 3.10+
- Docker (可选，用于容器化部署)

## 安装与运行

### 本地运行

1. 克隆项目
   ```bash
   git clone https://github.com/yourusername/pdf-parser-api.git
   cd pdf-parser-api
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 运行服务
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```

### Docker部署

1. 构建Docker镜像
   ```bash
   docker build -t pdf-parser-api .
   ```

2. 运行Docker容器
   ```bash
   docker run -p 8000:8000 pdf-parser-api
   ```

3. 使用Docker Compose部署
   ```bash
   docker-compose up -d
   ```

## API使用说明

服务启动后，可以通过以下方式访问API：

- API文档: http://localhost:8000/docs 或 http://localhost:8000/redoc
- 健康检查: http://localhost:8000/v1/health

### 主要API端点

#### 1. 解析Base64编码的PDF

```
POST /v1/convert
```

请求体:
```json
{
  "pdf_base64": "base64编码的PDF文件内容"
}
```

响应:
```json
{
  "success": true,
  "output": "提取的文本内容",
  "images": {
    "image1": "base64编码的图片1",
    "image2": "base64编码的图片2"
  },
  "metadata": {
    "页数": 5,
    "其他元数据": "值"
  }
}
```

## 配置选项

- `force_ocr`: 是否强制对所有页面使用OCR（默认为false）
- `paginate_output`: 是否在输出中按页分隔（默认为false）
- `languages`: OCR识别支持的语言列表
- `output_format`: 输出格式，可以是markdown、json或html（默认为markdown）

## 测试

项目包含自动化测试脚本，用于测试API服务的各项功能：

```bash
# 运行测试
./tests/run_tests.sh

# 使用pytest运行详细测试
./tests/run_tests.sh --with-pytest
```

测试前，请确保：
1. API服务已在本地启动（localhost:8000）
2. 在tests目录中放置了测试用的example.pdf文件

更多测试相关信息，请参阅 [tests/README.md](tests/README.md)。

## 许可证

MIT许可证