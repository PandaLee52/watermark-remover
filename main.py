"""
Main entry point for Render deployment
"""
import os

# 直接从 backend.app 导入
from backend.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
