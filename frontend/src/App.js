import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [userInput, setUserInput] = useState('');
  const [logs, setLogs] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!userInput.trim()) {
      setError('请输入内容');
      return;
    }

    setLoading(true);
    setError('');
    setLogs('');
    setResult('');

    try {
      // 假设后端API端点为/api/execute
      const response = await axios.post('/api/execute', { input: userInput });
      
      // 假设后端返回的数据格式为 { logs: '...', result: '...' }
      setLogs(response.data.logs || '');
      setResult(response.data.result || '');
    } catch (err) {
      console.error('Error:', err);
      setError(err.response?.data?.message || '请求失败，请稍后再试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>OpenManus 前端界面</h1>
      </div>

      <div className="input-section">
        <h2>输入</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="userInput">请输入您的命令或查询：</label>
            <textarea
              id="userInput"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="在此输入..."
              required
            />
          </div>
          <button type="submit" disabled={loading}>
            {loading ? '处理中...' : '提交'}
          </button>
        </form>
        {error && <div className="error">{error}</div>}
      </div>

      <div className="output-section">
        <h2>输出</h2>
        {loading && <div className="loading">正在处理您的请求，请稍候...</div>}
        
        {logs && (
          <div>
            <h3>日志输出：</h3>
            <div className="log-output">{logs}</div>
          </div>
        )}
        
        {result && (
          <div>
            <h3>结果：</h3>
            <div className="result-output">{result}</div>
          </div>
        )}
        
        {!loading && !logs && !result && (
          <div className="empty-state">
            提交请求后，日志和结果将显示在这里
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
