"""
Main entry point for Render deployment
"""
import sys
import os

# 确保能找到 backend 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
