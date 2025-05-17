"""
内容生成使用的Pydantic模型定义
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class XiaohongshuContent(BaseModel):
    """小红书内容的结构化模型"""
    title: str = Field(description="小红书文章的标题，10-15字，吸引人的核心爆点")
    headline: str = Field(description="小红书文章的副标题，15-25字，补充标题并引发好奇")
    content: str = Field(description="小红书文章的正文内容，要求至少500字，包含详细的政策解读、枫人院独家视角、夸张推理、脑洞补充、实用建议、独家观点、情绪张力，结尾有互动语气和号召性用语")
    image_keywords: List[str] = Field(description="3-5个用于生成封面图片的关键词，要有代表性和视觉冲击力")
    cover_prompt: str = Field(description="用于生成封面图的详细描述，结合标题和关键词，强调视觉冲击力和吸引力")

class WeiboContent(BaseModel):
    """微博内容的结构化模型"""
    content: str = Field(description="微博正文内容，140字以内，吸引人的爆点，包含政策要点和个人观点")
    hashtags: List[str] = Field(description="2-3个相关话题标签")
    image_prompt: Optional[str] = Field(None, description="配图提示，用于生成相关图片")

class StructuredNewsAnalysis(BaseModel):
    """结构化的新闻分析"""
    title: str = Field(description="分析标题")
    key_points: List[str] = Field(description="关键要点列表")
    analysis: str = Field(description="详细分析")
    implications: str = Field(description="政策影响和意义")
    recommendations: Optional[List[str]] = Field(None, description="建议列表")

class ContentItem(BaseModel):
    """内容项模型"""
    title: str = Field(description="内容标题")
    headline: str = Field(description="内容摘要")
    content: str = Field(description="正文内容")
    image_keywords: List[str] = Field(default_factory=list, description="图片关键词")
    questions: List[str] = Field(default_factory=list, description="互动问题")
    url: Optional[str] = Field(default=None, description="原文URL")
    original_image_url: Optional[str] = Field(default=None, description="原始图片URL")
    imgur_url: Optional[str] = Field(default=None, description="Imgur图片URL")
    final_image_path: Optional[str] = Field(default=None, description="最终图片本地路径")
    types: List[str] = Field(default_factory=lambda: ["移民资讯"], description="内容类型")
    tags: List[str] = Field(default_factory=list, description="内容标签")
    
    class Config:
        arbitrary_types_allowed = True 