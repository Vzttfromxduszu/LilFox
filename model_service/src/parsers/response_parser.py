from typing import Dict, Any, Optional, List, Union
import re
import json
from dataclasses import dataclass


@dataclass
class ParsedResult:
    """解析结果类"""
    success: bool
    data: Any
    error: Optional[str] = None
    raw_content: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "raw_content": self.raw_content
        }


class ResponseParser:
    """响应解析器，用于解析大模型返回的内容"""
    
    def __init__(self):
        self.parsers = {
            "json": self.parse_json,
            "code": self.parse_code,
            "list": self.parse_list,
            "key_value": self.parse_key_value,
            "markdown": self.parse_markdown,
            "text": self.parse_text
        }
    
    def parse(self, content: str, format_type: str = "text", **kwargs) -> ParsedResult:
        """
        解析响应内容
        
        Args:
            content: 原始响应内容
            format_type: 解析格式类型 (json, code, list, key_value, markdown, text)
            **kwargs: 其他参数
            
        Returns:
            ParsedResult: 解析结果对象
        """
        parser = self.parsers.get(format_type.lower())
        if not parser:
            return ParsedResult(
                success=False,
                data=None,
                error=f"不支持的解析格式: {format_type}",
                raw_content=content
            )
        
        try:
            result = parser(content, **kwargs)
            return ParsedResult(
                success=True,
                data=result,
                raw_content=content
            )
        except Exception as e:
            return ParsedResult(
                success=False,
                data=None,
                error=str(e),
                raw_content=content
            )
    
    def parse_json(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        解析JSON格式内容
        
        Args:
            content: 原始内容
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 解析后的JSON对象
        """
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, content)
        if matches:
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        # 尝试提取花括号内的内容
        brace_pattern = r'\{[\s\S]*\}'
        matches = re.findall(brace_pattern, content)
        if matches:
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("无法解析JSON内容")
    
    def parse_code(self, content: str, language: Optional[str] = None, **kwargs) -> str:
        """
        解析代码块内容
        
        Args:
            content: 原始内容
            language: 指定语言 (可选)
            **kwargs: 其他参数
            
        Returns:
            str: 提取的代码
        """
        if language:
            pattern = rf'```{language}\s*([\s\S]*?)\s*```'
        else:
            pattern = r'```\s*([\s\S]*?)\s*```'
        
        matches = re.findall(pattern, content)
        if matches:
            return matches[0].strip()
        
        raise ValueError("未找到代码块")
    
    def parse_list(self, content: str, **kwargs) -> List[str]:
        """
        解析列表格式内容
        
        Args:
            content: 原始内容
            **kwargs: 其他参数
            
        Returns:
            List[str]: 解析后的列表
        """
        # 尝试解析JSON数组
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
        
        # 尝试提取列表项
        lines = content.strip().split('\n')
        items = []
        for line in lines:
            line = line.strip()
            if line.startswith(('-', '*', '+', '•', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                # 移除列表标记
                item = re.sub(r'^[-*•+]?\s*\d+\.?\s*', '', line)
                items.append(item.strip())
        
        if items:
            return items
        
        raise ValueError("无法解析列表内容")
    
    def parse_key_value(self, content: str, **kwargs) -> Dict[str, str]:
        """
        解析键值对格式内容
        
        Args:
            content: 原始内容
            **kwargs: 其他参数
            
        Returns:
            Dict[str, str]: 解析后的键值对字典
        """
        result = {}
        
        # 尝试解析JSON对象
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        
        # 尝试解析键值对格式
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line or '：' in line:
                if ':' in line:
                    key, value = line.split(':', 1)
                else:
                    key, value = line.split('：', 1)
                result[key.strip()] = value.strip()
        
        if result:
            return result
        
        raise ValueError("无法解析键值对内容")
    
    def parse_markdown(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        解析Markdown格式内容
        
        Args:
            content: 原始内容
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 解析后的Markdown结构
        """
        result = {
            "title": "",
            "sections": [],
            "code_blocks": [],
            "links": []
        }
        
        # 提取标题
        title_pattern = r'^#\s+(.+)$'
        title_match = re.search(title_pattern, content, re.MULTILINE)
        if title_match:
            result["title"] = title_match.group(1).strip()
        
        # 提取章节
        section_pattern = r'^#{2,4}\s+(.+)$'
        for match in re.finditer(section_pattern, content, re.MULTILINE):
            result["sections"].append(match.group(1).strip())
        
        # 提取代码块
        code_pattern = r'```[\w]*\s*([\s\S]*?)\s*```'
        for match in re.finditer(code_pattern, content):
            result["code_blocks"].append(match.group(1).strip())
        
        # 提取链接
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, content):
            result["links"].append({
                "text": match.group(1),
                "url": match.group(2)
            })
        
        return result
    
    def parse_text(self, content: str, **kwargs) -> str:
        """
        解析纯文本内容
        
        Args:
            content: 原始内容
            **kwargs: 其他参数
            
        Returns:
            str: 清理后的文本
        """
        # 移除代码块标记
        content = re.sub(r'```\w*\s*[\s\S]*?\s*```', '', content)
        
        # 移除多余的空行
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def extract_info(self, content: str, patterns: Dict[str, str]) -> Dict[str, Any]:
        """
        使用正则表达式提取特定信息
        
        Args:
            content: 原始内容
            patterns: 模式字典 {字段名: 正则表达式}
            
        Returns:
            Dict[str, Any]: 提取的信息字典
        """
        result = {}
        for key, pattern in patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                if len(matches) == 1:
                    result[key] = matches[0]
                else:
                    result[key] = matches
        return result
    
    def auto_detect_format(self, content: str) -> str:
        """
        自动检测内容格式
        
        Args:
            content: 原始内容
            
        Returns:
            str: 检测到的格式类型
        """
        content = content.strip()
        
        # 检测JSON
        if content.startswith('{') or content.startswith('['):
            try:
                json.loads(content)
                return "json"
            except json.JSONDecodeError:
                pass
        
        # 检测代码块
        if '```' in content:
            return "code"
        
        # 检测列表
        lines = content.split('\n')
        if len(lines) > 1:
            list_markers = sum(1 for line in lines if line.strip().startswith(('-', '*', '+', '•')))
            if list_markers > len(lines) * 0.5:
                return "list"
        
        # 检测Markdown
        if content.startswith('#') or '##' in content:
            return "markdown"
        
        # 检测键值对
        if ':' in content and '\n' in content:
            lines_with_colon = sum(1 for line in lines if ':' in line and line.count(':') == 1)
            if lines_with_colon > len(lines) * 0.3:
                return "key_value"
        
        return "text"
    
    def parse_with_auto_detection(self, content: str, **kwargs) -> ParsedResult:
        """
        自动检测格式并解析
        
        Args:
            content: 原始内容
            **kwargs: 其他参数
            
        Returns:
            ParsedResult: 解析结果对象
        """
        format_type = self.auto_detect_format(content)
        return self.parse(content, format_type, **kwargs)