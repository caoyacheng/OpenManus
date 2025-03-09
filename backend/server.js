const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 5001;

// 中间件
app.use(cors());
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '../frontend/build')));

// 创建日志目录
const logsDir = path.join(__dirname, 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir);
}

// 执行命令并返回结果的API
app.post('/api/execute', (req, res) => {
  const { input } = req.body;
  
  if (!input) {
    return res.status(400).json({ message: '请提供输入内容' });
  }
  
  // 创建唯一的日志文件名
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const logFile = path.join(logsDir, `execution-${timestamp}.log`);
  
  console.log(`执行命令: ${input}`);
  console.log(`日志文件: ${logFile}`);
  
  // 创建日志写入流
  const logStream = fs.createWriteStream(logFile, { flags: 'a' });
  
  // 记录命令到日志
  logStream.write(`执行命令: ${input}\n`);
  logStream.write(`时间: ${new Date().toISOString()}\n\n`);
  
  // 执行命令
  const child = exec(input, {
    maxBuffer: 1024 * 1024 * 10, // 10MB buffer
  });
  
  let logs = '';
  let result = '';
  
  // 收集标准输出
  child.stdout.on('data', (data) => {
    logs += data;
    logStream.write(`[STDOUT] ${data}`);
  });
  
  // 收集标准错误
  child.stderr.on('data', (data) => {
    logs += data;
    logStream.write(`[STDERR] ${data}`);
  });
  
  // 命令执行完成
  child.on('close', (code) => {
    result = `命令执行完成，退出码: ${code}`;
    logStream.write(`\n${result}\n`);
    logStream.end();
    
    res.json({
      logs,
      result
    });
  });
  
  // 处理错误
  child.on('error', (error) => {
    const errorMsg = `执行错误: ${error.message}`;
    logStream.write(`\n${errorMsg}\n`);
    logStream.end();
    
    res.status(500).json({
      logs,
      result: errorMsg,
      error: true
    });
  });
});

// 获取所有日志文件的API
app.get('/api/logs', (req, res) => {
  fs.readdir(logsDir, (err, files) => {
    if (err) {
      return res.status(500).json({ message: '无法读取日志目录' });
    }
    
    const logFiles = files
      .filter(file => file.endsWith('.log'))
      .map(file => ({
        name: file,
        path: `/api/logs/${file}`,
        created: fs.statSync(path.join(logsDir, file)).birthtime
      }))
      .sort((a, b) => b.created - a.created);
    
    res.json(logFiles);
  });
});

// 获取特定日志文件内容的API
app.get('/api/logs/:filename', (req, res) => {
  const { filename } = req.params;
  const logFile = path.join(logsDir, filename);
  
  if (!fs.existsSync(logFile)) {
    return res.status(404).json({ message: '日志文件不存在' });
  }
  
  fs.readFile(logFile, 'utf8', (err, data) => {
    if (err) {
      return res.status(500).json({ message: '无法读取日志文件' });
    }
    
    res.send(data);
  });
});

// 处理React路由
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/build', 'index.html'));
});

// 启动服务器
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
  console.log(`API端点: http://localhost:${PORT}/api/execute`);
  console.log(`日志目录: ${logsDir}`);
});
