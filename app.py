import os
from typing import Optional, Dict, Any
import traceback
import base64
import io
import logging
import uuid
import uvicorn
import tempfile
import re

from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, validator
from contextlib import asynccontextmanager

from marker.config.parser import ConfigParser
from marker.output import text_from_rendered
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 全局数据存储
class AppState:
    def __init__(self):
        self.models = None

app_state = AppState()

# 应用启动和关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载模型
    logger.info("Loading models...")
    app_state.models = create_model_dict()
    logger.info("Models loaded successfully")
    yield
    # 关闭时清理资源
    logger.info("Shutting down application...")
    app_state.models = None

# 创建 FastAPI 应用
app = FastAPI(
    title="PDF Parser API",
    description="API for parsing and extracting text from PDF files",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 验证输出格式
VALID_OUTPUT_FORMATS = ["markdown", "json", "html"]

class CommonParams(BaseModel):
    filepath: str = Field(description="The path to the PDF file to convert.")
    page_range: Optional[str] = Field(
        default=None,
        description="Page range to convert, specify comma separated page numbers or ranges. Example: 0,5-10,20"
    )
    languages: Optional[str] = Field(
        default=None,
        description="Comma separated list of languages to use for OCR. Must be either the names or codes from https://github.com/VikParuchuri/surya/blob/master/surya/recognition/languages.py."
    )
    force_ocr: bool = Field(
        default=False,
        description="Force OCR on all pages of the PDF. Can lead to worse results if you have good text in your PDFs."
    )
    paginate_output: bool = Field(
        default=False,
        description="Whether to paginate the output. If True, each page will be separated by a horizontal rule with page number."
    )
    output_format: str = Field(
        default="markdown",
        description="The format to output the text in. Can be 'markdown', 'json', or 'html'."
    )
    
    @validator("output_format")
    def validate_output_format(cls, v):
        if v not in VALID_OUTPUT_FORMATS:
            raise ValueError(f"Output format must be one of {VALID_OUTPUT_FORMATS}")
        return v
    
    @validator("filepath")
    def validate_filepath(cls, v):
        if not v:
            raise ValueError("Filepath cannot be empty")
        if not os.path.exists(v):
            raise ValueError(f"File not found: {v}")
        return v

class PDFBase64Request(BaseModel):
    pdf_base64: str = Field(description="Base64 encoded PDF file content")
    
    @validator("pdf_base64")
    def validate_base64(cls, v):
        if not v:
            raise ValueError("Base64 string cannot be empty")
        try:
            # Try to decode first few characters to validate base64
            base64.b64decode(v[:100])
            return v
        except Exception:
            raise ValueError("Invalid base64 encoded string")

class ErrorResponse(BaseModel):
    success: bool = False
    error: str

class ConversionResponse(BaseModel):
    success: bool = True
    output: str
    images: Dict[str, str]  # Base64 encoded images
    metadata: Dict[str, Any]

# TODO: 将来会实现S3上传功能
def mock_upload_to_s3(image_bytes: bytes) -> str:
    """模拟上传图片到S3并返回URL的函数"""
    # 生成随机UUID作为图片标识符
    image_id = str(uuid.uuid4())
    return f"https://example.com/images/{image_id}"

def replace_image_references(text: str, image_map: Dict[str, str]) -> str:
    """
    替换文本中的Markdown格式图片引用，将原始图片名替换为S3图片链接
    
    参数:
        text: 包含图片引用的文本
        image_map: 映射原始图片名到S3链接的词典
        
    返回:
        替换后的文本
    """
    if not text or not image_map:
        return text
    
    # 只处理markdown格式的图片引用: ![alt](image_key)
    for old_key, new_url in image_map.items():
        # 替换markdown格式的图片引用
        # 使用正则表达式匹配 ![任意内容](old_key) 模式
        text = re.sub(r'!\[(.*?)\]\(' + re.escape(old_key) + r'\)', r'![\1](' + new_url + ')', text)
    
    logger.debug(f"替换图片引用后的文本: {text[:100]}...")
    return text

async def get_models():
    """依赖注入函数，确保模型已加载"""
    if app_state.models is None:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return app_state.models

# 创建v1版本的路由
v1_router = APIRouter(prefix="/v1")

@v1_router.get("/health", status_code=200, tags=["System"])
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "PDF Parser API"}

async def process_pdf_base64(pdf_base64: str, models):
    """处理Base64编码的PDF文件"""
    try:
        # 解码base64字符串
        pdf_bytes = base64.b64decode(pdf_base64)
        
        # 创建临时文件保存PDF内容
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes)
            temp_path = temp_file.name
        
        logger.info(f"临时PDF文件已保存到: {temp_path}")
        
        try:
            # 创建参数对象，使用固定输出格式
            params = CommonParams(
                filepath=temp_path,
                output_format="markdown",  # 始终使用markdown
                page_range=None,
                languages=None,
                force_ocr=False,
                paginate_output=False
            )
            
            # 处理PDF
            options = params.model_dump()
            logger.debug(f"使用以下选项处理PDF: {options}")
            
            config_parser = ConfigParser(options)
            config_dict = config_parser.generate_config_dict()
            config_dict["pdftext_workers"] = 1  # 限制worker数量以控制资源使用
            
            converter = PdfConverter(
                config=config_dict,
                artifact_dict=models,
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer(),
                llm_service=config_parser.get_llm_service()
            )
            
            # 执行转换
            rendered = converter(temp_path)
            text, _, images = text_from_rendered(rendered)
            metadata = rendered.metadata
            
            # 编码图像
            encoded_images = {}
            for k, v in images.items():
                byte_stream = io.BytesIO()
                v.save(byte_stream, format=settings.OUTPUT_IMAGE_FORMAT)
                image_bytes = byte_stream.getvalue()
                encoded_images[k] = mock_upload_to_s3(image_bytes)
            
            # 替换文本中的图片引用
            replaced_text = replace_image_references(text, encoded_images)
            
            return ConversionResponse(
                output=replaced_text,
                images=encoded_images,
                metadata=metadata,
            )
        finally:
            # 删除临时文件
            try:
                os.unlink(temp_path)
                logger.info(f"临时PDF文件已删除: {temp_path}")
            except Exception as e:
                logger.warning(f"删除临时文件时出错: {str(e)}")
    
    except Exception as e:
        logger.error(f"处理PDF时出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@v1_router.post(
    "/convert", 
    response_model=ConversionResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    },
    tags=["PDF Processing"]
)
async def convert_pdf(request: PDFBase64Request, models=Depends(get_models)):
    """
    将Base64编码的PDF文件转换为markdown文本
    
    - 使用markdown格式输出
    - 使用服务器端默认设置进行处理
    """
    return await process_pdf_base64(request.pdf_base64, models)

# 包含v1路由
app.include_router(v1_router)

@app.get("/", status_code=301)
async def redirect_to_docs():
    """重定向到API文档"""
    return RedirectResponse("/docs")

# 异常处理程序
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"未处理的异常: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "内部服务器错误"},
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)