#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一API响应格式管理器
确保所有API返回统一的JSON格式
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from flask import jsonify

class APIResponse:
    """统一API响应格式管理器"""
    
    @staticmethod
    def success(data: Optional[Dict[str, Any]] = None, 
                message: str = "操作成功", 
                request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            "status": True,
            "message": message,
            "msg": message,
            "code": 0,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id or str(uuid.uuid4()),
            "error": "",
            "data": data or {}
        }
    
    @staticmethod
    def error(message: str = "操作失败", 
              code: int = 1,
              error_detail: str = "",
              data: Optional[Dict[str, Any]] = None,
              request_id: Optional[str] = None) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "status": False,
            "message": message,
            "msg": message,
            "code": code,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id or str(uuid.uuid4()),
            "error": error_detail or message,
            "data": data or {}
        }
    
    @staticmethod
    def success_json(data: Optional[Dict[str, Any]] = None, 
                     message: str = "操作成功", 
                     request_id: Optional[str] = None,
                     status_code: int = 200):
        """创建成功响应的Flask jsonify对象"""
        response_data = APIResponse.success(data, message, request_id)
        response = jsonify(response_data)
        response.status_code = status_code
        # 确保返回UTF-8编码的JSON
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    
    @staticmethod
    def error_json(message: str = "操作失败", 
                   code: int = 1,
                   error_detail: str = "",
                   data: Optional[Dict[str, Any]] = None,
                   request_id: Optional[str] = None,
                   status_code: int = 500):
        """创建错误响应的Flask jsonify对象"""
        response_data = APIResponse.error(message, code, error_detail, data, request_id)
        response = jsonify(response_data)
        response.status_code = status_code
        # 确保返回UTF-8编码的JSON
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
    
    @staticmethod
    def from_exception(exception: Exception, 
                      message: str = "系统错误",
                      code: int = 500,
                      request_id: Optional[str] = None,
                      status_code: int = 500):
        """从异常创建错误响应"""
        error_detail = f"{exception.__class__.__name__}: {str(exception)}"
        return APIResponse.error_json(
            message=message,
            code=code,
            error_detail=error_detail,
            request_id=request_id,
            status_code=status_code
        )
