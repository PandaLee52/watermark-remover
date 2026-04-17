"""
Flask Backend for Watermark/Subtitle Remover
"""
import os
import sys
import uuid
import logging
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = '/tmp/watermark_uploads'
OUTPUT_FOLDER = '/tmp/watermark_outputs'
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Task storage (in production, use Redis or database)
tasks = {}


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'watermark-remover',
        'version': '1.0.0',
        'endpoints': ['/health', '/upload', '/detect', '/remove', '/download/<task_id>']
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'watermark-remover',
        'version': '1.0.0'
    })


@app.route('/upload', methods=['POST'])
def upload_video():
    """Upload video file"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Save file
    video_path = os.path.join(UPLOAD_FOLDER, f"{task_id}_{file.filename}")
    file.save(video_path)
    
    # Get video info
    video_info = get_video_info(video_path)
    
    # Store task
    tasks[task_id] = {
        'video_path': video_path,
        'output_path': None,
        'regions': [],
        'status': 'uploaded',
        'video_info': video_info
    }
    
    logger.info(f"Video uploaded: {task_id}, size: {os.path.getsize(video_path)} bytes")
    
    return jsonify({
        'task_id': task_id,
        'video_info': video_info
    })


@app.route('/detect', methods=['POST'])
def detect_watermarks():
    """Detect watermarks/subtitles in video"""
    data = request.json
    
    if not data or 'task_id' not in data:
        return jsonify({'error': 'task_id required'}), 400
    
    task_id = data['task_id']
    
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    video_path = task['video_path']
    
    try:
        # 模拟检测结果（实际需要 OpenCV）
        regions = [
            {"x": 100, "y": 100, "width": 200, "height": 50},
        ]
        
        task['regions'] = regions
        task['status'] = 'detected'
        
        logger.info(f"Detected {len(regions)} regions for task {task_id}")
        
        return jsonify({
            'regions': regions,
            'count': len(regions)
        })
    
    except Exception as e:
        logger.error(f"Detection error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/remove', methods=['POST'])
def remove_watermarks():
    """Remove watermarks/subtitles from video"""
    data = request.json
    
    if not data or 'task_id' not in data:
        return jsonify({'error': 'task_id required'}), 400
    
    task_id = data['task_id']
    
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    # Get regions from request or use detected regions
    regions = data.get('regions', task['regions'])
    
    if not regions:
        return jsonify({'error': 'No regions specified'}), 400
    
    video_path = task['video_path']
    output_path = os.path.join(OUTPUT_FOLDER, f"{task_id}_output.mp4")
    
    task['status'] = 'processing'
    task['regions'] = regions
    
    try:
        # 使用 FFmpeg 处理视频
        result_path = process_with_ffmpeg(video_path, output_path, regions)
        
        task['output_path'] = result_path
        task['status'] = 'completed'
        
        logger.info(f"Processing completed for task {task_id}")
        
        return jsonify({
            'task_id': task_id,
            'status': 'completed',
            'download_url': f"/download/{task_id}"
        })
    
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        task['status'] = 'failed'
        task['error'] = str(e)
        return jsonify({'error': str(e)}), 500


def process_with_ffmpeg(video_path, output_path, regions):
    """使用 FFmpeg delogo 滤镜处理视频"""
    # 构建 delogo 滤镜链
    filter_parts = []
    for r in regions:
        x = r.get('x', 0)
        y = r.get('y', 0)
        w = r.get('width', 100)
        h = r.get('height', 50)
        filter_parts.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
    
    filter_str = ",".join(filter_parts)
    
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', filter_str,
        '-c:a', 'copy',
        '-y', output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"FFmpeg error: {result.stderr}")
    
    return output_path


@app.route('/download/<task_id>', methods=['GET'])
def download_video(task_id):
    """Download processed video"""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    if task['status'] != 'completed' or not task['output_path']:
        return jsonify({'error': 'Video not ready'}), 400
    
    output_path = task['output_path']
    
    if not os.path.exists(output_path):
        return jsonify({'error': 'Output file not found'}), 404
    
    return send_file(
        output_path,
        mimetype='video/mp4',
        as_attachment=True,
        download_name=f'processed_{task_id}.mp4'
    )


@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    """Get task status"""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'regions_count': len(task.get('regions', [])),
        'has_output': task['output_path'] is not None
    })


def get_video_info(video_path: str) -> dict:
    """Get video information using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            info = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                fps_str = video_stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    fps = eval(fps_str)
                else:
                    fps = float(fps_str)
                
                return {
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'duration': float(info.get('format', {}).get('duration', 0)),
                    'fps': fps,
                    'size': int(info.get('format', {}).get('size', 0))
                }
        
        return {}
    
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {}


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
