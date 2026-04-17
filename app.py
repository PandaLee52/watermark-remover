from flask import Flask, request, jsonify, send_file
import subprocess, uuid, os, tempfile
from pathlib import Path

app = Flask(__name__)
UPLOAD = Path(tempfile.gettempdir()) / 'uploads'
OUTPUT = Path(tempfile.gettempdir()) / 'outputs'
UPLOAD.mkdir(exist_ok=True)
OUTPUT.mkdir(exist_ok=True)
tasks = {}

@app.route('/')
def home():
    return '''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>去水印</title></head>
<body style="font-family:Arial;max-width:800px;margin:50px auto;padding:20px">
<h1 style="text-align:center">🎬 视频去水印工具</h1>
<div style="border:2px dashed #007bff;padding:40px;text-align:center;cursor:pointer;border-radius:10px" onclick="document.getElementById('f').click()">
<p style="font-size:18px">📁 点击上传视频</p><input type="file" id="f" accept="video/*" onchange="upload(this.files[0])" style="display:none">
</div><div id="r" style="margin-top:20px;padding:20px;background:#f5f5f5;border-radius:10px;display:none"></div>
<script>
async function upload(file){if(!file)return;document.getElementById('r').style.display='block';document.getElementById('r').innerHTML='<p>上传中...</p>';
const fd=new FormData();fd.append('video',file);try{const res=await fetch('/api/upload',{method:'POST',body:fd});const d=await res.json();
if(d.success){document.getElementById('r').innerHTML='<p>✅ 上传成功</p><button onclick="remove(\\''+d.tid+'\\')" style="background:#007bff;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer">去除水印</button>';
}else{document.getElementById('r').innerHTML='<p>错误:'+d.error+'</p>';}}catch(e){document.getElementById('r').innerHTML='<p>失败:'+e.message+'</p>';}}
async function remove(tid){document.getElementById('r').innerHTML+='<p>处理中...</p>';
try{const res=await fetch('/api/remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tid:tid})});const d=await res.json();
if(d.success){document.getElementById('r').innerHTML+='<p>✅ 完成</p><a href="/api/download/'+tid+'" download><button style="background:#28a745;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer">下载视频</button></a>';
}else{document.getElementById('r').innerHTML+='<p>错误:'+d.error+'</p>';}}catch(e){document.getElementById('r').innerHTML+='<p>失败:'+e.message+'</p>';}}
</script></body></html>'''

@app.route('/health')
def health():
    return jsonify({'status':'ok'})

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'success':False,'error':'No file'}),400
    f=request.files['video']
    tid=str(uuid.uuid4())
    p=UPLOAD/f'{tid}_{f.filename}'
    f.save(p)
    tasks[tid]={'input':str(p),'output':None}
    return jsonify({'success':True,'tid':tid})

@app.route('/api/remove', methods=['POST'])
def remove():
    tid=(request.json or{}).get('tid')
    if not tid or tid not in tasks:
        return jsonify({'success':False,'error':'Not found'}),404
    inp=tasks[tid]['input']
    out=OUTPUT/f'{tid}_out.mp4'
    try:
        r=subprocess.run(['ffmpeg','-i',inp,'-vf','delogo=x=10:y=10:w=100:h=50','-c:a','copy','-y',str(out)],capture_output=True,timeout=300)
        if r.returncode==0:
            tasks[tid]['output']=str(out)
            return jsonify({'success':True})
        return jsonify({'success':False,'error':'FFmpeg error'}),500
    except Exception as e:
        return jsonify({'success':False,'error':str(e)}),500

@app.route('/api/download/<tid>')
def download(tid):
    if tid not in tasks or not tasks[tid].get('output'):
        return jsonify({'success':False,'error':'Not ready'}),404
    return send_file(tasks[tid]['output'],mimetype='video/mp4')

if __name__=='__main__':
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)))