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
