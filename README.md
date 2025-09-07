# Scash Miner v1.8.1 - GitHub Release

Scash Miner是一个为SRBMiner-Multi挖矿软件创建的用户友好的可视化操作界面，使用户能够方便地配置挖矿参数并一键启动挖矿进程，无需手动编辑批处理文件。

## 🎯 v1.8.1 重要修复

### 🔧 针对性修复
- ✅ **增强Devfee错误检测**: 扩展了devfee相关错误的检测关键词匹配，包含完整错误信息
- 💬 **优化提示信息**: 当检测到"Couldn't get active devfee pools - check your internet/firewall!"等错误时显示更详细的说明
- 💡 **教育意义增强**: 明确解释什么是devfee（开发费）及其对用户挖矿的实际影响
- 💪 **稳定性保障**: 绝对确保devfee网络问题不会导致挖矿程序退出
- 🛡️ **用户友好**: 提供清晰的解决建议，但强调可以放心继续挖矿

### 🔍 针对性解决方案
- **问题**: 用户反馈"[22:39:33] [2025-09-07 22:39:33] Couldn't get active devfee pools - check your internet/firewall!"错误导致挖矿退出
- **解决**: 增强错误检测关键词，包含完整错误信息匹配
- **效果**: 检测到此类错误时只显示友好提示，绝不终止挖矿进程
- **保障**: 用户挖矿收益不受任何影响，SRBMiner自己处理devfee问题

## 功能特性

- 提供直观的图形用户界面(GUI)用于配置挖矿参数
- 支持修改钱包地址、矿工名称、CPU核心数和矿池地址
- 实现一键挖矿功能
- 绿色版设计，无需安装，解压即可运行
- 包含项目相关链接和捐款地址信息
- 实时显示挖矿状态和日志输出（预计5分钟内显示）
- 添加软件logo，增强视觉体验（紫色主题色）
- 优化日志系统，采用多线程实时捕获技术
- 修复 Worker Name 在矿池中的显示问题
- 使用智能 wallet.worker 格式
- 界面紧凑优化，适配小分辨率屏幕
- **新增**: 专门针对devfee错误的智能处理机制

## 系统要求

- Windows 64位操作系统
- 需要下载 SRBMiner-Multi v2.5.2

## 项目链接

- GitHub项目: https://github.com/Pow-King/Scash-Miner
- 中文交流TG: https://t.me/SatoshiCashNetwork
- 社区矿池: https://scash.work
- 区块浏览器: https://scash.tv
- 社区钱包: https://scash.app
- 锄头版本: https://github.com/doktor83/SRBMiner-Multi/releases/tag/2.5.2

## 项目文件说明

- **main.py**: 主程序代码
- **Scash-Miner.exe**: 绿色版可执行文件（v1.8.1）
- **config.json**: 配置文件
- **requirements.txt**: Python依赖库列表
- **README.md**: 项目说明文档
- **scash-logo.png**: 软件logo文件
- **scash-logo.ico**: 程序图标文件
- **启动 Scash-Miner.bat**: 绿色版智能启动脚本
- **SRBMiner-MULTI.exe**: 挖矿核心程序（需单独下载）

## 捐款地址

如果您觉得这个工具对您有帮助，欢迎捐款支持开发：

- **SCASH捐款地址**: scash1qtvj3eryz8p46e9nu7zzn7yfg49j7lkns4t2698
- **BSC USDT（BEP20）捐款地址**: 0x16ff0b3a4d53d6ed4367d9916492643e26661724

## 注意事项

- 本工具仅作为SRBMiner-Multi的前端界面，不修改原始挖矿软件功能
- 用户需自行确保计算机满足挖矿硬件要求
- 请确保有足够的散热和电源供应
- 挖矿有风险，用户需自行承担相关责任

## 使用说明

### 🚀 快速开始

1. 下载 SRBMiner-Multi v2.5.2:
   https://github.com/doktor83/SRBMiner-Multi/releases/tag/2.5.2
   
2. 将下载的 SRBMiner-MULTI.exe 放到此目录

3. 双击"启动 Scash-Miner.bat"运行程序
   或直接双击 Scash-Miner.exe

### 📋 配置说明

- **钱包地址**：改成你的SatoshiCash钱包地址
- **矿工名称**：设置你的矿工标识名称  
- **CPU核心数**：建议设置为CPU核心数-1
- **矿池地址**：点击"点击填写"按钮自动填入

### 从源代码运行

1. 确保已安装Python 3.8或更高版本
2. 安装依赖：`pip install -r requirements.txt`
3. 运行程序：`python main.py`

## 配置参数说明

- **钱包地址**：您的SatoshiCash钱包地址，用于接收挖矿收益
- **矿工名称**：您的矿工标识，将显示在矿池统计信息中
- **CPU核心数**：挖矿使用的CPU核心数量
- **矿池地址**：挖矿矿池的地址，格式为`stratum+tcp://服务器地址:端口`

## 🎯 Devfee 说明

### 什么是 Devfee？
Devfee（开发费）是SRBMiner-Multi挖矿软件内置的一种支持开发者的机制。挖矿软件会定期尝试连接到开发者的矿池进行短暂的挖矿，作为对软件开发和维护的支持。

### 对您的影响
- **收益影响**: Devfee通常只占总挖矿时间的很小比例（通常1-2%），对您的收益影响微乎其微
- **网络要求**: Devfee池可能需要特定的网络条件才能访问
- **错误处理**: 即使devfee池连接失败，也不会影响您的正常挖矿作业

### v1.8.1 的改进
- **智能检测**: 自动识别devfee相关的连接错误
- **友好提示**: 清晰解释错误原因和影响
- **稳定运行**: 确保devfee错误不会意外终止您的挖矿程序
- **放心挖矿**: 您可以安心继续挖矿，收益不受影响

## 技术架构

### 技术选型
- 前端: Python + Tkinter（GUI）
- 后端: SRBMiner-MULTI.exe（外部挖矿程序）
- 图像处理: Pillow (PIL)
- 配置文件: JSON
- 打包工具: PyInstaller

### 构建命令
```bash
# 安装依赖
pip install -r requirements.txt

# 打包命令
pyinstaller --onefile --windowed --icon=scash-logo.ico --clean --name="Scash-Miner" main.py
```

### 部署要求
- 确保 SRBMiner-MULTI.exe 与 Scash-Miner.exe 在同一目录
- 绿色版无需安装，解压即可运行

## 开源协议

本项目基于MIT开源协议，您可以自由使用、修改和分发。

## 开发者信息

- **开发者**: Scash 社区爱好者
- **发布日期**: 2025年9月7日
- **版本**: v1.8.1

---

**如遇问题请检查：**
1. SRBMiner-MULTI.exe 是否存在且版本正确(v2.5.2)
2. 钱包地址是否正确
3. 网络连接是否正常
4. 是否需要启用VPN访问矿池

**关于Devfee错误：**
- 看到"Couldn't get active devfee pools"等错误是正常的
- 这不会影响您的挖矿收益
- 程序会继续运行，无需担心
- 如需改善可考虑启用VPN或调整防火墙设置