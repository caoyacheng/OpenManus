import asyncio
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sys
from threading import Thread

from app.agent.manus import Manus
from app.logger import logger

# 创建Flask应用
app = Flask(__name__, 
            static_folder='frontend/static',
            template_folder='frontend/templates')
CORS(app)  # 启用CORS支持

# 创建Manus代理工厂函数
def create_agent():
    return Manus()

# 创建日志目录
logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# 存储请求状态的字典
request_status = {}

# 前端页面
@app.route('/')
def index():
    return render_template('index.html')

# 静态文件
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('frontend/static', path)

# 创建一个自定义的日志处理器类
class LogCapture:
    def __init__(self):
        self.logs = []
        self.handler_id = None
        
    def start_capture(self):
        """开始捕获日志"""
        self.logs = []
        
        # 使用loguru的sink函数来捕获日志
        def sink(message):
            # 保留完整的日志格式，包括时间戳、日志级别等
            record = message.record
            time = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            level = record["level"].name
            name = record["name"]
            function = record["function"]
            line = record["line"]
            msg = record["message"]
            
            formatted_message = f"{time} | {level:<8} | {name}:{function}:{line} - {msg}"
            self.logs.append(formatted_message)
        
        # 添加自定义处理器
        self.handler_id = logger.add(sink, level="INFO")
        
    def stop_capture(self):
        """停止捕获日志"""
        if self.handler_id is not None:
            logger.remove(self.handler_id)
            self.handler_id = None
            
    def get_logs(self):
        """获取捕获的日志"""
        return '\n'.join(self.logs)

# 创建日志捕获器实例
log_capturer = LogCapture()

# 生成唯一的请求ID
def generate_request_id():
    import uuid
    return str(uuid.uuid4())

# API端点：执行命令
@app.route('/api/execute', methods=['POST'])
def execute_command():
    data = request.json
    input_text = data.get('input', '')
    
    if not input_text:
        return jsonify({'error': '请提供输入内容'}), 400
    
    # 生成请求ID
    request_id = generate_request_id()
    
    # 初始化请求状态
    request_status[request_id] = {
        'completed': False,
        'logs': '开始处理请求...\n',
        'result': None,
        'error': None
    }
    
    # 创建一个线程来处理请求
    def process_request():
        try:
            # 创建日志捕获器
            req_log_capturer = LogCapture()
            req_log_capturer.start_capture()
            
            # 记录命令
            logger.info(f"执行命令: {input_text}")
            
            # 创建一个线程来实时更新日志
            def update_logs():
                while not request_status[request_id]['completed']:
                    # 获取当前日志
                    current_logs = req_log_capturer.get_logs()
                    
                    # 更新请求状态中的日志
                    request_status[request_id]['logs'] = current_logs
                    
                    # 每0.1秒更新一次
                    import time
                    time.sleep(0.1)
            
            # 启动日志更新线程
            log_update_thread = Thread(target=update_logs)
            log_update_thread.daemon = True  # 设置为守护线程，主线程结束时自动结束
            log_update_thread.start()
            
            # 为每个请求创建一个新的代理实例
            agent = create_agent()
            
            # 执行代理
            result = asyncio.run(agent.run(input_text))
            
            # 获取最终日志
            logs = req_log_capturer.get_logs()
            
            # 停止捕获
            req_log_capturer.stop_capture()
            
            # 更新请求状态
            request_status[request_id]['logs'] = logs
            request_status[request_id]['result'] = result
            request_status[request_id]['completed'] = True
            
        except Exception as e:
            # 记录错误
            logger.error(f"执行错误: {str(e)}")
            
            # 获取捕获的日志
            logs = req_log_capturer.get_logs() if 'req_log_capturer' in locals() else '处理请求时发生错误'
            
            # 停止捕获
            if 'req_log_capturer' in locals():
                req_log_capturer.stop_capture()
            
            # 更新请求状态
            request_status[request_id]['logs'] = logs
            request_status[request_id]['error'] = str(e)
            request_status[request_id]['completed'] = True
    
    # 启动处理线程
    Thread(target=process_request).start()
    
    # 返回请求ID
    return jsonify({
        'request_id': request_id
    })

# API端点：获取请求状态
@app.route('/api/status/<request_id>', methods=['GET'])
def get_request_status(request_id):
    if request_id not in request_status:
        return jsonify({'error': '请求ID不存在'}), 404
    
    status = request_status[request_id]
    
    # 如果请求已完成且没有错误，返回结果
    if status['completed']:
        if status['error']:
            return jsonify({
                'completed': True,
                'logs': status['logs'],
                'result': f"执行错误: {status['error']}"
            })
        else:
            return jsonify({
                'completed': True,
                'logs': status['logs'],
                'result': status['result']
            })
    
    # 如果请求未完成，返回当前状态
    return jsonify({
        'completed': False,
        'logs': status['logs']
    })

# 命令行接口
async def cli_interface():
    # 创建代理实例
    agent = create_agent()
    
    while True:
        try:
            prompt = input("Enter your prompt (or 'exit' to quit): ")
            if prompt.lower() == "exit":
                logger.info("Goodbye!")
                break
            logger.warning("Processing your request...")
            await agent.run(prompt)
        except KeyboardInterrupt:
            logger.warning("Goodbye!")
            break

# 主函数
def main():
    # 检查是否有命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # 命令行模式
        asyncio.run(cli_interface())
    else:
        # Web服务器模式
        # 创建前端目录
        os.makedirs('frontend/templates', exist_ok=True)
        os.makedirs('frontend/static', exist_ok=True)
        
        # 创建前端HTML文件
        if not os.path.exists('frontend/templates/index.html'):
            with open('frontend/templates/index.html', 'w') as f:
                f.write('''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenManus 前端界面</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OpenManus 前端界面</h1>
        </div>

        <div class="input-section">
            <h2>输入</h2>
            <form id="commandForm">
                <div class="form-group">
                    <label for="userInput">请输入您的命令或查询：</label>
                    <textarea id="userInput" placeholder="在此输入..." required></textarea>
                </div>
                <button type="submit" id="submitBtn">提交</button>
            </form>
            <div id="error" class="error"></div>
        </div>

        <div class="output-section">
            <h2>输出</h2>
            <div id="loading" class="loading" style="display: none;">正在处理您的请求，请稍候...</div>
            
            <div id="logSection" style="display: none;">
                <h3>日志输出：</h3>
                <div id="logs" class="log-output"></div>
            </div>
            
            <div id="resultSection" style="display: none;">
                <h3>结果：</h3>
                <div id="result" class="result-output"></div>
            </div>
            
            <div id="emptyState" class="empty-state">
                提交请求后，日志和结果将显示在这里
            </div>
        </div>
    </div>

    <script src="/static/script.js"></script>
</body>
</html>
                ''')
        
        # 创建CSS文件
        if not os.path.exists('frontend/static/style.css'):
            with open('frontend/static/style.css', 'w') as f:
                f.write('''
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
        'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
        sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    background-color: #282c34;
    color: white;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
    border-radius: 5px;
}

.input-section {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.output-section {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
}

textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    resize: vertical;
    min-height: 100px;
    font-family: inherit;
}

button {
    background-color: #4caf50;
    color: white;
    border: none;
    padding: 10px 15px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background-color: #45a049;
}

.log-output {
    background-color: #282c34;
    color: #61dafb;
    padding: 15px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 400px;
    overflow-y: auto;
}

.result-output {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid #ddd;
    border-radius: 4px;
    background-color: #f9f9f9;
    white-space: pre-wrap;
}

.loading {
    text-align: center;
    margin: 20px 0;
    font-style: italic;
    color: #666;
}

.error {
    color: #d32f2f;
    background-color: #ffebee;
    padding: 10px;
    border-radius: 4px;
    margin-top: 10px;
    display: none;
}

.empty-state {
    text-align: center;
    margin: 20px 0;
    color: #666;
}
                ''')
        
        # 创建JavaScript文件
        if not os.path.exists('frontend/static/script.js'):
            with open('frontend/static/script.js', 'w') as f:
                f.write('''
document.addEventListener('DOMContentLoaded', function() {
    const commandForm = document.getElementById('commandForm');
    const userInput = document.getElementById('userInput');
    const submitBtn = document.getElementById('submitBtn');
    const loading = document.getElementById('loading');
    const logSection = document.getElementById('logSection');
    const logs = document.getElementById('logs');
    const resultSection = document.getElementById('resultSection');
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const emptyState = document.getElementById('emptyState');

    // 添加轮询状态的功能
    let pollingInterval = null;
    let requestId = null;

    // 开始轮询状态
    function startPolling(id) {
        requestId = id;
        
        // 显示处理中状态
        loading.textContent = '正在处理您的请求，请稍候...';
        loading.style.display = 'block';
        
        // 初始显示日志区域
        logSection.style.display = 'block';
        logs.textContent = '开始处理请求...\n';
        
        // 每秒轮询一次状态
        pollingInterval = setInterval(async function() {
            try {
                const statusResponse = await fetch(`/api/status/${requestId}`);
                const statusData = await statusResponse.json();
                
                // 更新日志
                if (statusData.logs) {
                    logs.textContent = statusData.logs;
                    // 自动滚动到底部
                    logs.scrollTop = logs.scrollHeight;
                }
                
                // 如果处理完成，显示结果并停止轮询
                if (statusData.completed) {
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    
                    if (statusData.result) {
                        result.textContent = statusData.result;
                        resultSection.style.display = 'block';
                    }
                    
                    loading.style.display = 'none';
                    submitBtn.disabled = false;
                }
            } catch (err) {
                console.error('Error polling status:', err);
            }
        }, 1000);
    }

    commandForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const input = userInput.value.trim();
        if (!input) {
            error.textContent = '请输入内容';
            error.style.display = 'block';
            return;
        }

        // 重置UI
        error.style.display = 'none';
        logSection.style.display = 'none';
        resultSection.style.display = 'none';
        emptyState.style.display = 'none';
        loading.style.display = 'block';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ input }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                if (data.request_id) {
                    // 如果返回了请求ID，开始轮询状态
                    startPolling(data.request_id);
                } else {
                    // 否则直接显示结果
                    if (data.logs) {
                        logs.textContent = data.logs;
                        logSection.style.display = 'block';
                    }
                    
                    if (data.result) {
                        result.textContent = data.result;
                        resultSection.style.display = 'block';
                    }
                    
                    if (!data.logs && !data.result) {
                        emptyState.style.display = 'block';
                    }
                    
                    loading.style.display = 'none';
                    submitBtn.disabled = false;
                }
            } else {
                error.textContent = data.result || '请求失败，请稍后再试';
                error.style.display = 'block';
                
                if (data.logs) {
                    logs.textContent = data.logs;
                    logSection.style.display = 'block';
                }
                
                loading.style.display = 'none';
                submitBtn.disabled = false;
            }
        } catch (err) {
            console.error('Error:', err);
            error.textContent = '请求失败，请稍后再试';
            error.style.display = 'block';
            loading.style.display = 'none';
            submitBtn.disabled = false;
        }
    });
});
                ''')
        
        # 启动Flask应用
        print("启动Web服务器，访问 http://localhost:5001 使用前端界面")
        print("使用 Ctrl+C 停止服务器")
        app.run(debug=True, host='0.0.0.0', port=5001)

if __name__ == "__main__":
    main()
