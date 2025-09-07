import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import json
import os
import sys
import threading
import time
import platform
import socket
import re

# 尝试导入PIL库，如果失败则设置标志
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: 未找到PIL库，将无法显示logo图片。您可以通过 'pip install Pillow' 安装。")

class ScashMinerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Scash Miner")
        self.root.geometry("1000x650")  # 缩小窗口尺寸，确保小分辨率显示完整
        self.root.resizable(True, True)
        
        # 设置中文字体支持
        self.setup_fonts()
        
        # 挖矿进程控制
        self.mining_process = None
        self.is_mining = False
        self.mining_thread = None
        self.log_queue = []  # 日志队列，用于在主线程中更新UI
        self.log_lock = threading.Lock()  # 用于保护日志队列的锁
        self.pre_network_test_passed = False  # 启动前网络检测是否通过
        
        # 读取配置文件
        self.config = self.load_config()
        
        # 加载和设置软件图标
        if PIL_AVAILABLE:
            self.load_app_icon()
        
        # 创建主界面
        self.create_widgets()
        
        # 初始化配置输入框
        self.init_config_fields()
        
        # 启动日志更新定时器
        self.update_log_display()
        
        # 设置窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_fonts(self):
        # 确保中文正常显示
        if sys.platform.startswith('win'):
            # Windows系统默认支持中文字体
            pass
    
    def load_app_icon(self):
        """加载应用图标并确保正确显示"""
        # 优先使用scash-logo.png作为窗口图标
        icon_formats = ["scash-logo.png", "logo.ico", "logo.png", "logo.gif"]
        icon_path = None
        
        # 首先检查当前工作目录
        for format_name in icon_formats:
            if os.path.exists(format_name):
                icon_path = format_name
                break
        
        # 如果找不到图标，尝试检查常见位置
        if not icon_path:
            common_paths = [".", os.path.dirname(os.path.abspath(__file__))]
            if hasattr(sys, '_MEIPASS'):
                common_paths.append(sys._MEIPASS)
            if platform.system() == 'Windows' and hasattr(sys, 'frozen'):
                common_paths.append(os.path.dirname(sys.executable))
            
            for path in common_paths:
                for format_name in icon_formats:
                    full_path = os.path.join(path, format_name)
                    if os.path.exists(full_path):
                        icon_path = full_path
                        break
                if icon_path:
                    break
        
        # 尝试使用PIL加载图标
        try:
            if PIL_AVAILABLE and icon_path:
                try:
                    # 加载并调整图像大小作为窗口图标
                    self.icon_image = Image.open(icon_path)
                    # 为窗口图标创建合适的尺寸（32x32像素）
                    icon_resized = self.icon_image.copy()
                    icon_resized.thumbnail((32, 32), Image.Resampling.LANCZOS)
                    
                    # 设置为窗口图标
                    self.icon_photo = ImageTk.PhotoImage(icon_resized)
                    self.root.iconphoto(True, self.icon_photo)
                    self.log_message(f"成功设置窗口图标: {icon_path}")
                    
                    # 如果是ico格式，同时尝试使用iconbitmap
                    if icon_path.lower().endswith('.ico'):
                        try:
                            self.root.iconbitmap(icon_path)
                        except:
                            pass
                    return True
                except Exception as e:
                    self.log_message(f"加载窗口图标时出错: {str(e)}")
            elif icon_path:
                # 如果没有PIL库，尝试使用tkinter的基本方法
                self.log_message("未找到PIL库，尝试使用基本方法加载图标")
                if icon_path.lower().endswith('.ico'):
                    try:
                        self.root.iconbitmap(icon_path)
                        return True
                    except Exception as e:
                        self.log_message(f"加载图标失败: {str(e)}")
            
            # 如果找不到图标文件，记录日志
            if not icon_path:
                self.log_message("未找到窗口图标文件，使用默认图标")
        except Exception as e:
            self.log_message(f"加载窗口图标时发生异常: {str(e)}")
        
        return False if not icon_path else True
    
    def load_config(self):
        """优先从config.json加载配置，如果不存在则创建默认配置"""
        config_path = "config.json"
        
        # 默认配置，与项目规范文档一致，增加新的优化参数
        default_config = {
            "wallet_address": "scash1qtvj3eryz8p46e9nu7zzn7yfg49j7lkns4t2698",
            "worker_name": "x",
            "cpu_threads": "20",
            "pool_address": "stratum+tcp://scash.work:9601",
            "use_tls": True,
            "use_keepalive": True,
            "use_wallet_worker_format": True,
            "retry_time": "30",
            "send_stales": False
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 确保所有必要的配置项都存在，添加新参数
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                self.log_message(f"读取配置文件失败: {str(e)}")
                # 即使读取失败，也尝试创建一个新的配置文件
                try:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(default_config, f, ensure_ascii=False, indent=4)
                    self.log_message("已创建新的配置文件")
                except Exception as e2:
                    self.log_message(f"创建配置文件失败: {str(e2)}")
                return default_config
        else:
            # 如果配置文件不存在，创建默认配置文件
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
                self.log_message("已创建默认配置文件")
            except Exception as e:
                self.log_message(f"创建默认配置文件失败: {str(e)}")
            return default_config
    
    def save_config(self):
        config_path = "config.json"
        try:
            # 获取当前配置以保持新参数
            current_config = self.load_config()
            
            # 更新用户修改的参数（移除TLS和Keepalive）
            current_config.update({
                "wallet_address": self.wallet_entry.get(),
                "worker_name": self.worker_entry.get(),
                "cpu_threads": self.threads_entry.get(),
                "pool_address": self.pool_entry.get(),
                "use_wallet_worker_format": self.wallet_worker_var.get()
            })
            
            # 移除TLS和Keepalive配置（因为影响挖矿）
            current_config.pop('use_tls', None)
            current_config.pop('use_keepalive', None)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, ensure_ascii=False, indent=4)
            self.log_message("配置已保存")
            messagebox.showinfo("成功", "配置已保存")
        except Exception as e:
            self.log_message(f"保存配置文件失败: {str(e)}")
            messagebox.showerror("错误", f"保存配置文件失败: {str(e)}")
    
    def on_closing(self):
        """处理窗口关闭事件，确保挖矿进程被正确停止"""
        try:
            if self.is_mining and self.mining_process:
                # 如果正在挖矿，先问用户是否确认关闭
                result = messagebox.askyesno(
                    "确认关闭",
                    "挖矿程序正在运行中，关闭GUI将同时停止挖矿。\n\n确认要关闭吗？"
                )
                if not result:
                    return  # 用户取消关闭
                
                # 用户确认关闭，停止挖矿进程
                self.log_message("📴 用户关闭GUI，正在停止挖矿进程...")
                self.is_mining = False
                
                # 停止挖矿进程
                if self.mining_process and self.mining_process.poll() is None:
                    try:
                        # 尝试优雅地终止进程
                        self.mining_process.terminate()
                        self.mining_process.wait(timeout=2)
                        self.log_message("✅ 挖矿进程已优雅停止")
                    except subprocess.TimeoutExpired:
                        # 如果超时，强制终止
                        try:
                            self.mining_process.kill()
                            self.log_message("⚠️ 挖矿进程已强制终止")
                        except Exception as e:
                            self.log_message(f"❌ 终止进程失败: {str(e)}")
                    except Exception as e:
                        self.log_message(f"❌ 停止进程时出错: {str(e)}")
                
                # 使用taskkill命令清理所有相关进程
                try:
                    result = subprocess.run(["taskkill", "/F", "/IM", "SRBMiner-MULTI.exe", "/T"],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           text=True, check=False, timeout=5)
                    if result.returncode == 0:
                        self.log_message("🧹 已清理所有SRBMiner-MULTI进程")
                    else:
                        if "not found" not in result.stderr:
                            self.log_message(f"⚠️ 清理进程时出现问题: {result.stderr.strip()}")
                except Exception as e:
                    self.log_message(f"❌ 执行taskkill命令失败: {str(e)}")
            
            # 关闭窗口
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            self.log_message(f"❌ 关闭窗口时出错: {str(e)}")
            # 即使出错也要关闭窗口
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
    
    def test_pool_connectivity(self, pool_address):
        """测试矿池连通性，返回(is_reachable, test_results)"""
        try:
            # 解析矿池地址
            if pool_address.startswith('stratum+tcp://'):
                pool_url = pool_address.replace('stratum+tcp://', '')
            else:
                pool_url = pool_address
            
            if ':' in pool_url:
                host, port = pool_url.split(':', 1)
                port = int(port)
            else:
                host = pool_url
                port = 4444  # 默认端口
            
            test_results = {
                'host': host,
                'port': port,
                'ping_success': False,
                'socket_success': False,
                'dns_success': False,
                'error_messages': []
            }
            
            self.log_message(f"🔍 开始测试矿池连通性: {host}:{port}")
            
            # 1. DNS解析测试
            try:
                socket.gethostbyname(host)
                test_results['dns_success'] = True
                self.log_message(f"✅ DNS解析成功: {host}")
            except socket.gaierror as e:
                test_results['error_messages'].append(f"DNS解析失败: {str(e)}")
                self.log_message(f"❌ DNS解析失败: {host} - {str(e)}")
            
            # 2. Ping测试
            try:
                ping_cmd = ['ping', '-n', '3', host] if platform.system().lower() == 'windows' else ['ping', '-c', '3', host]
                
                # 隐藏cmd窗口的配置
                startupinfo = None
                creationflags = 0
                if platform.system().lower() == 'windows':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    creationflags = subprocess.CREATE_NO_WINDOW
                
                result = subprocess.run(
                    ping_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    startupinfo=startupinfo,
                    creationflags=creationflags
                )
                
                if result.returncode == 0:
                    test_results['ping_success'] = True
                    # 提取ping的平均响应时间
                    if platform.system().lower() == 'windows':
                        # Windows ping输出解析
                        if '平均' in result.stdout or 'Average' in result.stdout:
                            avg_time = re.search(r'\d+ms', result.stdout.split('平均')[-1] or result.stdout.split('Average')[-1])
                            if avg_time:
                                self.log_message(f"✅ Ping成功: 平均响应时间 {avg_time.group()}")
                            else:
                                self.log_message(f"✅ Ping成功: {host}")
                        else:
                            self.log_message(f"✅ Ping成功: {host}")
                    else:
                        self.log_message(f"✅ Ping成功: {host}")
                else:
                    ping_error = result.stderr.strip() or result.stdout.strip()
                    test_results['error_messages'].append(f"Ping失败: {ping_error}")
                    self.log_message(f"❌ Ping失败: {host} - {ping_error}")
                    
            except subprocess.TimeoutExpired:
                test_results['error_messages'].append("Ping超时")
                self.log_message(f"❌ Ping超时: {host}")
            except Exception as e:
                test_results['error_messages'].append(f"Ping错误: {str(e)}")
                self.log_message(f"❌ Ping错误: {host} - {str(e)}")
            
            # 3. TCP连接测试
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)  # 5秒超时
                result = sock.connect_ex((host, port))
                
                if result == 0:
                    test_results['socket_success'] = True
                    self.log_message(f"✅ TCP连接成功: {host}:{port}")
                else:
                    error_msg = f"TCP连接失败: 端口 {port} 不可达"
                    test_results['error_messages'].append(error_msg)
                    self.log_message(f"❌ {error_msg}")
                
                sock.close()
                
            except socket.timeout:
                test_results['error_messages'].append("TCP连接超时")
                self.log_message(f"❌ TCP连接超时: {host}:{port}")
            except Exception as e:
                test_results['error_messages'].append(f"TCP连接错误: {str(e)}")
                self.log_message(f"❌ TCP连接错误: {host}:{port} - {str(e)}")
            
            # 判断总体连通性
            is_reachable = test_results['dns_success'] and (test_results['ping_success'] or test_results['socket_success'])
            
            if is_reachable:
                self.log_message(f"✅ 矿池网络连通性测试通过: {pool_address}")
            else:
                self.log_message(f"❌ 矿池网络连通性测试失败: {pool_address}")
                self.log_message(f"⚠️ 错误详情: {"; ".join(test_results['error_messages'])}")
            
            return is_reachable, test_results
            
        except Exception as e:
            self.log_message(f"❌ 矿池连通性测试异常: {str(e)}")
            return False, {'error': str(e)}
    
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 移除logo和标题显示，直接进入配置区域
        # 添加复制到剪贴板功能
        def copy_to_clipboard(text):
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # 保持剪贴板内容
            self.log_message(f"已复制到剪贴板: {text}")
        
        # 创建配置区域和控制区域的分割
        left_frame = ttk.LabelFrame(main_frame, text="配置参数", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 配置区域
        # 钱包地址
        ttk.Label(left_frame, text="钱包地址:\n(Wallet Address)", font=("SimHei", 10)).grid(row=0, column=0, sticky=tk.NW, pady=5)
        self.wallet_entry = ttk.Entry(left_frame, width=35)  # 进一步减小宽度到35
        self.wallet_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # 矿工名称
        ttk.Label(left_frame, text="矿工名称:\n(Worker Name)", font=("SimHei", 10)).grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.worker_entry = ttk.Entry(left_frame, width=35)  # 进一步减小宽度到35
        self.worker_entry.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # CPU核心数
        ttk.Label(left_frame, text="CPU核心数:\n(CPU Threads)", font=("SimHei", 10)).grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.threads_entry = ttk.Entry(left_frame, width=35)  # 进一步减小宽度到35
        self.threads_entry.grid(row=2, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # 矿池地址
        ttk.Label(left_frame, text="矿池地址:\n(Pool Address)", font=("SimHei", 10)).grid(row=3, column=0, sticky=tk.NW, pady=5)
        self.pool_entry = ttk.Entry(left_frame, width=35)  # 进一步减小宽度到35
        self.pool_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=(5, 0))
        
        # 矿池地址提示（移动到输入框下方）
        pool_tip_frame = tk.Frame(left_frame)
        pool_tip_frame.grid(row=4, column=1, sticky=tk.W, pady=(2, 5), padx=(5, 0))
        
        pool_tip_label = tk.Label(pool_tip_frame, text="社区矿池地址: stratum+tcp://scash.work:9601", 
                                 font=('SimHei', 9), cursor="hand2", fg="#8B00FF")
        pool_tip_label.pack(side=tk.LEFT)
        pool_tip_label.bind("<Button-1>", lambda e: self._auto_fill_pool_address())
        
        # 点击填写按钮
        fill_button = tk.Button(pool_tip_frame, text="点击填写", font=('SimHei', 8), 
                               cursor="hand2", fg="#8B00FF", bg="white", relief="flat",
                               command=self._auto_fill_pool_address)
        fill_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # 高级配置选项（只保留Wallet.Worker格式）
        advanced_frame = ttk.LabelFrame(left_frame, text="高级配置 (Advanced Settings)", padding="5")
        advanced_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(10, 5))
        
        # 高级配置提示
        advanced_tip_label = tk.Label(advanced_frame, text="高级配置默认即可", 
                                     font=('SimHei', 9), fg="#8B00FF")
        advanced_tip_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 只保留Wallet.Worker格式选项
        self.wallet_worker_var = tk.BooleanVar(value=True)
        self.wallet_worker_check = ttk.Checkbutton(advanced_frame, 
                                                  text="使用Wallet.Worker格式 (Use Wallet.Worker Format)\n推荐：可在矿池显示矿工名称", 
                                                  variable=self.wallet_worker_var)
        self.wallet_worker_check.pack(anchor=tk.W, pady=2)
        
        # 配置列的权重，使输入框可以自动拉伸
        left_frame.columnconfigure(1, weight=1)
        
        # 保存配置按钮
        self.save_button = ttk.Button(left_frame, text="保存配置", command=self.save_config)
        self.save_button.grid(row=6, column=0, columnspan=2, pady=10)
        
        # 项目信息区域
        project_frame = ttk.LabelFrame(left_frame, text="项目信息", padding="10")
        project_frame.grid(row=7, column=0, columnspan=2, sticky=tk.NSEW, pady=(10, 0))
        
        # 添加可点击的链接和地址标签（使用紫色主题色）
        # GitHub项目地址
        github_label = ttk.Label(project_frame, text="GitHub项目: https://github.com/Pow-King/Scash-Miner", 
                                font=('SimHei', 9), cursor="hand2", foreground="#8B00FF")
        github_label.pack(anchor=tk.W, pady=1)
        github_label.bind("<Button-1>", lambda e: copy_to_clipboard("https://github.com/Pow-King/Scash-Miner"))
        
        github_eng_label = ttk.Label(project_frame, text="(Project Repository)", 
                                    font=('Arial', 8), foreground="gray")
        github_eng_label.pack(anchor=tk.W, padx=(15, 0))
        
        tg_label = ttk.Label(project_frame, text="中文交流TG: https://t.me/SatoshiCashNetwork", 
                           font=('SimHei', 9), cursor="hand2", foreground="#8B00FF")
        tg_label.pack(anchor=tk.W, pady=1)
        tg_label.bind("<Button-1>", lambda e: copy_to_clipboard("https://t.me/SatoshiCashNetwork"))
        
        tg_eng_label = ttk.Label(project_frame, text="(Chinese Community Telegram)", 
                               font=('Arial', 8), foreground="gray")
        tg_eng_label.pack(anchor=tk.W, padx=(15, 0))
        
        pool_label = ttk.Label(project_frame, text="社区矿池: https://scash.work", 
                             font=('SimHei', 9), cursor="hand2", foreground="#8B00FF")
        pool_label.pack(anchor=tk.W, pady=1)
        pool_label.bind("<Button-1>", lambda e: copy_to_clipboard("https://scash.work"))
        
        pool_eng_label = ttk.Label(project_frame, text="(Community Mining Pool)", 
                                font=('Arial', 8), foreground="gray")
        pool_eng_label.pack(anchor=tk.W, padx=(15, 0))
        
        explorer_label = ttk.Label(project_frame, text="区块浏览器: https://scash.tv", 
                                 font=('SimHei', 9), cursor="hand2", foreground="#8B00FF")
        explorer_label.pack(anchor=tk.W, pady=1)
        explorer_label.bind("<Button-1>", lambda e: copy_to_clipboard("https://scash.tv"))
        
        explorer_eng_label = ttk.Label(project_frame, text="(Block Explorer)", 
                                    font=('Arial', 8), foreground="gray")
        explorer_eng_label.pack(anchor=tk.W, padx=(15, 0))
        
        # 直接显示SCASH捐款地址，移除社区钱包和锄头版本以节省空间
        donation_label = ttk.Label(project_frame, text="SCASH捐款地址: scash1qtvj3eryz8p46e9nu7zzn7yfg49j7lkns4t2698", 
                                 font=('SimHei', 9), cursor="hand2", foreground="#8B00FF")
        donation_label.pack(anchor=tk.W, pady=1)
        donation_label.bind("<Button-1>", lambda e: copy_to_clipboard("scash1qtvj3eryz8p46e9nu7zzn7yfg49j7lkns4t2698"))
        
        donation_eng_label = ttk.Label(project_frame, text="(SCASH Donation Address)", 
                                    font=('Arial', 8), foreground="gray")
        donation_eng_label.pack(anchor=tk.W, padx=(15, 0))
        
        # BSC USDT捐款地址
        usdt_donation_label = ttk.Label(project_frame, text="BSC USDT（BEP20）捐款地址: 0x16ff0b3a4d53d6ed4367d9916492643e26661724", 
                                       font=('SimHei', 9), cursor="hand2", foreground="#8B00FF")
        usdt_donation_label.pack(anchor=tk.W, pady=1)
        usdt_donation_label.bind("<Button-1>", lambda e: copy_to_clipboard("0x16ff0b3a4d53d6ed4367d9916492643e26661724"))
        
        usdt_donation_eng_label = ttk.Label(project_frame, text="(BSC BEP20 USDT Donation Address)", 
                                          font=('Arial', 8), foreground="gray")
        usdt_donation_eng_label.pack(anchor=tk.W, padx=(15, 0))
        
        # 控制区域
        control_frame = ttk.LabelFrame(right_frame, text="控制\n(Control)", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 开始挖矿按钮
        self.start_button = ttk.Button(control_frame, text="开始挖矿 (Start Mining)", command=self.start_mining)
        self.start_button.pack(fill=tk.X, pady=5)
        
        # 停止挖矿按钮
        self.stop_button = ttk.Button(control_frame, text="停止挖矿 (Stop Mining)", command=self.stop_mining, state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, pady=5)
        
        # 重启挖矿按钮
        self.restart_button = ttk.Button(control_frame, text="重启挖矿 (Restart Mining)", command=self.restart_mining, state=tk.DISABLED)
        self.restart_button.pack(fill=tk.X, pady=5)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(right_frame, text="挖矿状态\n(Mining Status)", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 挖矿状态标签
        self.status_var = tk.StringVar(value="未挖矿")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("SimHei", 12))
        self.status_label.pack(pady=10)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(right_frame, text="挖矿日志\n(Mining Log)", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=40, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 创建菜单
        self.create_menu()
    
    def create_menu(self):
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        
        # 创建帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="项目信息", command=self.show_project_info)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        # 设置菜单栏
        self.root.config(menu=menubar)
    
    def show_about(self):
        messagebox.showinfo("关于", "Scash Miner\n版本: v1.8.1\n\n这是一个用于SatoshiCash挖矿的可视化工具，\n基于SRBMiner-Multi开发。\n\n由Scash社区爱好者开发")
    
    def show_project_info(self):
        # 创建信息窗口
        info_window = tk.Toplevel(self.root)
        info_window.title("项目信息")
        info_window.geometry("900x700")  # 进一步扩大窗口尺寸，确保内容完整显示
        info_window.resizable(True, True)
        
        # 窗口居中显示
        info_window.transient(self.root)
        info_window.grab_set()
        
        # 创建主框架和状态框架
        main_frame = ttk.Frame(info_window)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态显示框架（用于显示复制提示）
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=20, pady=(15, 0))
        
        # 复制状态标签 - 增大字体，更醒目的提示
        self.copy_status_label = ttk.Label(status_frame, text="", font=("SimHei", 12, "bold"), foreground="#00AA00")
        self.copy_status_label.pack(anchor=tk.E)
        
        # 内容框架 - 增加内边距
        frame = ttk.Frame(main_frame, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加标题 - 增大字体
        title_label = ttk.Label(frame, text="SatoshiCash Miner 项目信息", 
                               font=("SimHei", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 复制到剪贴板功能（添加明显提示）
        def copy_to_clipboard_info(text):
            info_window.clipboard_clear()
            info_window.clipboard_append(text)
            info_window.update()
            
            # 显示复制成功提示 - 更醒目的提示文字
            self.copy_status_label.config(text="✅ 已复制到剪贴板")
            # 3秒后清除提示
            info_window.after(3000, lambda: self.copy_status_label.config(text=""))
        
        # 添加链接信息（使用紫色主题色）- 增加内边距
        links_frame = ttk.LabelFrame(frame, text="项目链接", padding="15")
        links_frame.pack(fill=tk.X, pady=(0, 15))
        
        # GitHub项目链接 - 增大字体和行间距
        github_label = tk.Label(links_frame, text="GitHub项目: https://github.com/Pow-King/Scash-Miner",
                               font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        github_label.pack(anchor=tk.W, pady=5)
        github_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("https://github.com/Pow-King/Scash-Miner"))
        
        # TG群链接
        tg_label = tk.Label(links_frame, text="中文交流TG: https://t.me/SatoshiCashNetwork",
                           font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        tg_label.pack(anchor=tk.W, pady=5)
        tg_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("https://t.me/SatoshiCashNetwork"))
        
        # 社区矿池
        pool_label = tk.Label(links_frame, text="社区矿池: https://scash.work",
                             font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        pool_label.pack(anchor=tk.W, pady=5)
        pool_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("https://scash.work"))
        
        # 区块浏览器
        explorer_label = tk.Label(links_frame, text="区块浏览器: https://scash.tv",
                                 font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        explorer_label.pack(anchor=tk.W, pady=5)
        explorer_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("https://scash.tv"))
        
        # 社区钱包
        wallet_label = tk.Label(links_frame, text="社区钱包: https://scash.app",
                               font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        wallet_label.pack(anchor=tk.W, pady=5)
        wallet_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("https://scash.app"))
        
        # 锄头版本
        version_label = tk.Label(links_frame, text="锄头版本: https://github.com/doktor83/SRBMiner-Multi/releases/tag/2.5.2",
                                font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        version_label.pack(anchor=tk.W, pady=5)
        version_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("https://github.com/doktor83/SRBMiner-Multi/releases/tag/2.5.2"))
        
        # 捐款信息 - 增加内边距
        donation_frame = ttk.LabelFrame(frame, text="捐款支持", padding="15")
        donation_frame.pack(fill=tk.X, pady=(0, 15))
        
        donation_label = tk.Label(donation_frame, text="SCASH捐款地址: scash1qtvj3eryz8p46e9nu7zzn7yfg49j7lkns4t2698",
                                 font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        donation_label.pack(anchor=tk.W, pady=5)
        donation_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("scash1qtvj3eryz8p46e9nu7zzn7yfg49j7lkns4t2698"))
        
        # BSC USDT捐款地址
        usdt_donation_label = tk.Label(donation_frame, text="BSC USDT（BEP20）捐款地址: 0x16ff0b3a4d53d6ed4367d9916492643e26661724",
                                     font=('SimHei', 12), cursor="hand2", fg="#8B00FF")
        usdt_donation_label.pack(anchor=tk.W, pady=5)
        usdt_donation_label.bind("<Button-1>", lambda e: copy_to_clipboard_info("0x16ff0b3a4d53d6ed4367d9916492643e26661724"))
        
        # 提示信息 - 更明显的提示
        tip_label = ttk.Label(frame, text="💡 点击以上任意链接或地址可复制到剪贴板", 
                             font=('SimHei', 11), foreground="#666666")
        tip_label.pack(pady=(15, 0))
    
    def init_config_fields(self):
        # 初始化配置输入框
        self.wallet_entry.insert(0, self.config["wallet_address"])
        self.worker_entry.insert(0, self.config["worker_name"])
        self.threads_entry.insert(0, self.config["cpu_threads"])
        self.pool_entry.insert(0, self.config["pool_address"])
        
        # 初始化高级配置选项（只保留Wallet.Worker格式）
        self.wallet_worker_var.set(self.config.get('use_wallet_worker_format', True))
    
    def _auto_fill_pool_address(self):
        """自动填写社区矿池地址"""
        self.pool_entry.delete(0, tk.END)
        self.pool_entry.insert(0, "stratum+tcp://scash.work:9601")
        self.log_message("已自动填写社区矿池地址")
    
    def log_message(self, message):
        # 使用线程安全的方式添加日志消息到队列
        with self.log_lock:
            self.log_queue.append(message)
    
    def update_log_display(self):
        # 在主线程中更新日志显示
        with self.log_lock:
            # 获取队列中的所有消息并清空队列
            messages = self.log_queue.copy()
            self.log_queue.clear()
        
        if messages:
            self.log_text.config(state=tk.NORMAL)
            for message in messages:
                # 插入消息到日志显示区域
                self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
                
                # 特别标记重要信息
                important_keywords = [
                    'connected', 'disconnected', 'difficulty', 'hashrate', 'hash rate', 
                    'accepted', 'rejected', 'cpu result', 'job received', 'shares',
                    'pool', 'algorithm', 'error', 'failed', 'success'
                ]
                
                warning_keywords = ['error', 'failed', 'rejected', 'disconnected']
                success_keywords = ['accepted', 'connected', 'initialized']
                
                message_lower = message.lower()
                
                # 获取最后一行的位置
                last_line_start = self.log_text.index(tk.END + "-2l")
                last_line_end = self.log_text.index(tk.END + "-1l")
                
                # 根据关键词应用不同的颜色标签
                if any(keyword in message_lower for keyword in warning_keywords):
                    self.log_text.tag_add("warning", last_line_start, last_line_end)
                elif any(keyword in message_lower for keyword in success_keywords):
                    self.log_text.tag_add("success", last_line_start, last_line_end)
                elif any(keyword in message_lower for keyword in important_keywords):
                    self.log_text.tag_add("important", last_line_start, last_line_end)
                elif 'h/s' in message_lower:  # 哈希率信息
                    self.log_text.tag_add("hashrate", last_line_start, last_line_end)
            
            # 自动滚动到最新的日志
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        # 设置日志文本框的标签样式
        self.log_text.tag_config("important", foreground="blue", font=('SimHei', 9, 'bold'))
        self.log_text.tag_config("warning", foreground="red", font=('SimHei', 9, 'bold'))
        self.log_text.tag_config("success", foreground="green", font=('SimHei', 9, 'bold'))
        self.log_text.tag_config("hashrate", foreground="purple", font=('SimHei', 9, 'bold'))
        
        # 每50毫秒更新一次日志显示（提高实时性）
        self.root.after(50, self.update_log_display)
    
    def start_mining(self):
        # 验证输入参数
        if not self.validate_inputs():
            return
        
        # 重置网络检测标志
        self.pre_network_test_passed = False
        
        # 开始挖矿前更新按钮状态
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.restart_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        
        # 开始挖矿线程
        self.is_mining = True
        self.mining_thread = threading.Thread(target=self._mining_thread_func)
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def _mining_thread_func(self):
        try:
            # 获取配置参数
            wallet_address = self.wallet_entry.get()
            worker_name = self.worker_entry.get()
            cpu_threads = self.threads_entry.get()
            pool_address = self.pool_entry.get()
            
            # 获取GUI中的优化参数配置（移除TLS和Keepalive）
            use_wallet_worker_format = self.wallet_worker_var.get()
            
            # 加载配置文件获取其他参数
            config = self.load_config()
            retry_time = config.get('retry_time', '30')
            send_stales = config.get('send_stales', False)
            
            # 日志记录开始挖矿的线程信息
            self.log_message(f"开始挖矿线程: {threading.current_thread().name}")
            
            # ⭐ 在启动挖矿前先进行网络连通性测试
            self.log_message("🔍 开始启动前网络检测...")
            is_reachable, test_results = self.test_pool_connectivity(pool_address)
            
            if not is_reachable:
                # 网络不可达，立即提示VPN问题
                self.pre_network_test_passed = False
                self.log_message("❌ 矿池网络不可达，无法开始挖矿")
                self.log_message("⚠️ 请检查以下问题:")
                self.log_message("1. 是否已经启用VPN网络")
                self.log_message("2. VPN是否连接正常")
                self.log_message("3. 防火墙设置是否阻止连接")
                
                # 显示立即的VPN警告
                self._show_immediate_vpn_warning(test_results)
                
                # 停止挖矿并重置状态
                self.is_mining = False
                self.status_var.set("矿池连接失败")
                self.reset_buttons()
                return
            
            # 网络连通性测试通过，继续启动挖矿
            self.pre_network_test_passed = True
            self.log_message("✅ 矿池网络可达，开始启动挖矿程序...")
            
            # 构建钱包地址，根据配置决定是否使用 wallet.worker 格式
            if use_wallet_worker_format and worker_name.strip():
                # 使用 wallet.worker 格式（推荐）
                full_wallet_address = f"{wallet_address}.{worker_name}"
                self.log_message(f"💼 使用 wallet.worker 格式: {full_wallet_address}")
                password_param = "x"  # 传统密码参数用默认值
            else:
                # 使用传统的分离格式
                full_wallet_address = wallet_address
                password_param = worker_name if worker_name.strip() else "x"
                self.log_message(f"💼 使用传统格式: wallet={full_wallet_address}, password={password_param}")
            
            # 构建挖矿命令，移除TLS和Keepalive参数
            cmd = [
                "SRBMiner-MULTI.exe",
                "--algorithm", "randomscash",
                "--pool", pool_address,
                "--wallet", full_wallet_address,
                "--password", password_param,
                "--cpu-threads", cpu_threads,
                "--randomx-use-largepages",
                "--send-stales", str(send_stales).lower(),
                "--retry-time", retry_time,
                "--gpu-off"
            ]
            
            self.log_message(f"开始挖矿: {' '.join(cmd)}")
            self.status_var.set("挖矿中")
            
            # 使用固定的日志文件
            log_file_path = "mining_log.txt"
            self.log_message(f"挖矿日志将于5分钟左右显示在界面上")
            
            # 启动挖矿进程，隐藏cmd窗口，并配置输出捕获
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # 隐藏窗口
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 在Windows上，使用优化的进程创建参数
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NO_WINDOW
            
            # 使用优化的参数启动进程，确保实时捕获输出
            self.mining_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将标准错误也重定向到标准输出
                text=True,
                bufsize=0,  # 无缓冲模式，实时捕获输出
                universal_newlines=True,
                shell=False,
                startupinfo=startupinfo,
                creationflags=creationflags,
                close_fds=True
            )
            
            # 记录进程启动信息
            self.log_message(f"挖矿进程已启动，PID: {self.mining_process.pid}")
            
            # 启动连接监测线程
            connection_thread = threading.Thread(target=self._monitor_mining_connection)
            connection_thread.daemon = True
            connection_thread.start()
            
            # 启动日志读取线程
            log_thread = threading.Thread(target=self._read_mining_output, args=(log_file_path,))
            log_thread.daemon = True
            log_thread.start()
            
            # 等待进程结束或被停止
            while self.is_mining and self.mining_process.poll() is None:
                time.sleep(0.1)  # 检查进程状态
            
            # 进程结束后的处理
            if self.mining_process and self.mining_process.poll() is not None:
                self.log_message(f"挖矿进程结束，退出代码: {self.mining_process.returncode}")
                if self.is_mining:  # 如果不是主动停止的
                    self.status_var.set("挖矿意外停止")
                    self.reset_buttons()
                    
        except Exception as e:
            self.log_message(f"挖矿过程中发生错误: {str(e)}")
            print(f"详细错误: {repr(e)}")
            import traceback
            traceback.print_exc()
            self.status_var.set("挖矿已停止")
            self.reset_buttons()
    
    def _read_mining_output(self, log_file_path):
        """独立线程读取挖矿输出，确保实时性"""
        try:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                # 添加时间戳标记新的挖矿会话开始
                session_start = f"\n=== 挖矿会话开始于 {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n"
                log_file.write(session_start)
                log_file.flush()
                
                self.log_message("开始捕获挖矿输出，预计5分钟显示挖矿日志")
                
                while self.is_mining and self.mining_process and self.mining_process.poll() is None:
                    try:
                        # 使用非阻塞方式读取输出
                        import select
                        import io
                        
                        if sys.platform == 'win32':
                            # Windows下直接读取，设置小的超时时间
                            try:
                                # 使用非阻塞读取模式
                                import msvcrt
                                import os
                                
                                # 尝试读取一行
                                line = self.mining_process.stdout.readline()
                                if line:
                                    line = line.strip()
                                    if line:  # 只处理非空行
                                        # 在GUI中显示日志（线程安全）
                                        self.log_message(line)
                                        # 立即写入日志文件
                                        log_file.write(f"[{time.strftime('%H:%M:%S')}] {line}\n")
                                        log_file.flush()  # 强制刷新到磁盘
                                        
                                        # 强制GUI更新（在主线程中执行）
                                        self.root.after_idle(lambda: None)
                                else:
                                    # 没有输出时短暂休眠
                                    time.sleep(0.001)  # 1毫秒
                            except Exception as read_error:
                                if "temporarily unavailable" not in str(read_error).lower():
                                    self.log_message(f"读取输出异常: {str(read_error)}")
                                time.sleep(0.01)
                        else:
                            # 非Windows系统使用select
                            ready, _, _ = select.select([self.mining_process.stdout], [], [], 0.1)
                            if ready:
                                line = self.mining_process.stdout.readline()
                                if line:
                                    line = line.strip()
                                    if line:
                                        self.log_message(line)
                                        log_file.write(f"[{time.strftime('%H:%M:%S')}] {line}\n")
                                        log_file.flush()
                                        
                    except Exception as e:
                        error_msg = str(e)
                        if "temporarily unavailable" not in error_msg.lower() and "broken pipe" not in error_msg.lower():
                            self.log_message(f"读取输出时出错: {error_msg}")
                        time.sleep(0.01)
                
                # 添加时间戳标记挖矿会话结束
                session_end = f"=== 挖矿会话结束于 {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n"
                log_file.write(session_end)
                log_file.flush()
                
        except Exception as e:
            self.log_message(f"日志读取线程异常: {str(e)}")
    
    def _monitor_mining_connection(self):
        """监测挖矿连接状态，检测是否需要VPN"""
        connection_timeout = 120  # 2分钟超时
        start_time = time.time()
        connection_established = False
        vpn_warning_shown = False
        cpu_activity_detected = False
        
        self.log_message("🔍 开始监测矿池连接状态...")
        
        while self.is_mining and self.mining_process and self.mining_process.poll() is None:
            current_time = time.time()
            elapsed_time = current_time - start_time
            
            # 检查是否已经连接成功
            if not connection_established:
                # 检查日志中是否有连接成功的标志
                try:
                    if os.path.exists("mining_log.txt"):
                        with open("mining_log.txt", 'r', encoding='utf-8') as f:
                            log_content = f.read().lower()
                            
                            # 更严格的连接成功检测 - 只有当真正开始挖矿时才认为成功
                            real_mining_indicators = [
                                'job received', 'new job', 'difficulty set to',
                                'share accepted', 'accepted share', 'cpu result',
                                'hash rate', 'hashrate', 'h/s', 'mh/s', 'kh/s',
                                'randomscash algorithm', 'mining started',
                                '接受任务', '开始挖矿', '哈希率',
                                'result accepted', 'shares: '
                            ]
                            
                            # 检查是否真正开始挖矿（有实际工作输出）
                            if any(indicator in log_content for indicator in real_mining_indicators):
                                connection_established = True
                                cpu_activity_detected = True
                                self.log_message("✅ 矿池连接成功，已开始正常挖矿作业")
                                break
                            
                            # 检查连接失败的标志
                            connection_error_indicators = [
                                'connection failed', 'connection refused', 'connection timeout',
                                'failed to connect', 'unable to connect', 'network unreachable',
                                'host unreachable', 'connection reset', 'socket error',
                                'getaddrinfo failed', 'name resolution failed', 'dns lookup failed',
                                'connection timed out', 'no route to host', 'network is unreachable',
                                'pool connection error', 'pool not reachable', 'connect error',
                                '连接失败', '连接被拒绝', '连接超时', '网络不可达',
                                'error: failed to', 'cannot connect to', 'connection lost'
                            ]
                            
                            # 检查devfee相关错误（特殊处理）
                            devfee_error_indicators = [
                                'couldn\'t get active devfee pools', 'devfee pool connection failed',
                                'devfee pool error', 'devfee network error', 'devfee pools - check your internet',
                                'devfee pools - check your firewall', 'couldn\'t get active devfee pools - check your internet/firewall!',
                                'devfee connection failed', 'devfee - check your internet', 'devfee - check your firewall',
                                'couldn\'t connect to devfee', 'devfee pools unreachable', 'devfee timeout'
                            ]
                            
                            # 检查是否有devfee相关错误
                            if any(error in log_content for error in devfee_error_indicators):
                                if not vpn_warning_shown:
                                    vpn_warning_shown = True
                                    self.log_message("⚠️ 检测到SRBMiner的devfee池连接问题")
                                    self.log_message("💡 这是开发费功能，连接失败不会影响您的挖矿收益")
                                    self.log_message("🔧 提示：可以启用VPN或检查防火墙设置，但不影响正常挖矿")
                                    self.log_message("📌 重要：程序会继续运行，SRBMiner会自己处理这个问题")
                                    self.log_message("✅ 您的挖矿收益不会受到任何影响，请放心继续挖矿")
                                # 特别注意：devfee错误绝对不能导致挖矿退出，继续监控
                            
                            # 检查是否有明确的连接错误（仅提示，不终止挖矿）
                            elif any(error in log_content for error in connection_error_indicators):
                                if not vpn_warning_shown:
                                    vpn_warning_shown = True
                                    self.log_message("🚫 检测到连接错误，可能是网络波动或该矿池需要VPN")
                                    self.log_message("💡 提示：如果连接问题持续，建议检查VPN设置或等待网络恢复")
                                    # 不再主动终止挖矿，让SRBMiner自己处理网络问题
                                # 继续监控而不是break
                                
                except Exception as e:
                    pass  # 忽略读取错误
            
            time.sleep(5)  # 每5秒检查一次
    
    def _show_vpn_warning(self):
        """显示VPN警告信息（仅提示，不终止挖矿）"""
        current_pool = self.pool_entry.get().strip()
        warning_msg = (
            "⚠️ 矿池连接警告\n\n"
            "检测到可能的连接问题，但继续运行挖矿程序\n"
            "（SRBMiner会自动处理网络波动和重连）\n\n"
            "🔍 可能的原因：\n"
            "1. 网络临时波动（通常会自动恢复）\n"
            "2. 矿池需要VPN网络才能访问\n"
            "3. 本地网络限制或防火墙阻止\n"
            "4. 矿池服务器维护或不可用\n\n"
            "💡 建议：\n"
            "- 如果是临时网络问题，请等待自动恢复\n"
            "- 如果问题持续，可考虑启用VPN或更换矿池\n"
            "- 避免频繁重启，让挖矿程序自行处理\n\n"
            f"📝 当前矿池: {current_pool}\n"
            f"🕰 检测时间: {time.strftime('%H:%M:%S')}"
        )
        
        self.log_message(warning_msg)
        # 移除弹窗和主动停止挖矿的逻辑，只记录日志
    
    def _show_immediate_vpn_warning(self, test_results):
        """立即显示VPN警告，用于启动前网络测试失败"""
        current_pool = self.pool_entry.get().strip()
        
        # 生成详细的错误信息
        error_details = ""
        if 'error_messages' in test_results and test_results['error_messages']:
            error_details = "\n".join(test_results['error_messages'])
        
        warning_msg = (
            "🔴 无法连接到矿池\n\n"
            f"📝 矿池地址: {current_pool}\n"
            f"🕰 测试时间: {time.strftime('%H:%M:%S')}\n\n"
            "🔍 网络测试结果:\n"
            f"DNS解析: {'✅ 成功' if test_results.get('dns_success') else '❌ 失败'}\n"
            f"Ping测试: {'✅ 成功' if test_results.get('ping_success') else '❌ 失败'}\n"
            f"TCP连接: {'✅ 成功' if test_results.get('socket_success') else '❌ 失败'}\n\n"
        )
        
        if error_details:
            warning_msg += f"❌ 错误详情:\n{error_details}\n\n"
        
        warning_msg += (
            "🔧 解决方案:\n"
            "1. ⭐ 先启用VPN网络后再尝试挖矿\n"
            "2. 检查VPN是否正常连接\n"
            "3. 检查防火墙设置\n"
            "4. 尝试更换其他矿池地址"
        )
        
        self.log_message(warning_msg)
        
        # 在主线程中显示弹窗
        def show_immediate_warning_dialog():
            try:
                result = messagebox.showerror(
                    "矿池连接失败", 
                    f"无法连接到指定矿池！\n\n"
                    f"矿池地址: {current_pool}\n\n"
                    "🔍 网络测试结果:\n"
                    f"DNS解析: {'✅' if test_results.get('dns_success') else '❌'}\n"
                    f"Ping测试: {'✅' if test_results.get('ping_success') else '❌'}\n"
                    f"TCP连接: {'✅' if test_results.get('socket_success') else '❌'}\n\n"
                    "🔧 建议解决方案:\n"
                    "1. 先启用VPN网络后再尝试\n"
                    "2. 检查VPN连接状态\n"
                    "3. 检查防火墙设置"
                )
            except Exception as e:
                pass  # 忽略弹窗错误
        
        # 使用after在主线程中调用
        self.root.after(100, show_immediate_warning_dialog)

    def stop_mining(self):
        # 停止挖矿
        self.log_message("开始停止挖矿操作")
        self.is_mining = False
        
        success = False  # 记录是否成功停止
        
        # 等待线程状态变更
        if hasattr(self, 'mining_thread') and self.mining_thread and self.mining_thread.is_alive():
            self.log_message(f"挖矿线程状态: 仍在运行中，等待停止...")
        
        # 终止主挖矿进程
        if self.mining_process is not None:
            try:
                proc_id = self.mining_process.pid if hasattr(self.mining_process, 'pid') else "未知"
                self.log_message(f"尝试终止挖矿进程 (PID: {proc_id})")
                
                if self.mining_process.poll() is None:
                    try:
                        # 尝试优雅地终止进程
                        self.mining_process.terminate()
                        # 等待进程终止，最多等待3秒
                        self.mining_process.wait(timeout=3)
                        self.log_message("挖矿进程已优雅终止")
                        success = True
                    except subprocess.TimeoutExpired:
                        # 如果超时，强制终止进程
                        try:
                            self.mining_process.kill()
                            self.log_message("挖矿进程已被强制终止")
                            success = True
                        except Exception as e:
                            self.log_message(f"终止挖矿进程失败: {str(e)}")
                else:
                    self.log_message(f"挖矿进程已结束，退出代码: {self.mining_process.returncode}")
                    success = True
            except Exception as e:
                self.log_message(f"处理挖矿进程时出错: {str(e)}")
        else:
            self.log_message("没有活跃的挖矿进程")
            success = True
        
        # 如果上面的方法都失败，尝试使用taskkill命令
        if not success:
            try:
                self.log_message("尝试使用taskkill命令强制清理SRBMiner-MULTI进程")
                # 使用taskkill命令强制终止所有相关进程
                result = subprocess.run(["taskkill", "/F", "/IM", "SRBMiner-MULTI.exe", "/T"], 
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                       text=True, check=False)
                
                if result.returncode == 0:
                    self.log_message("成功清理SRBMiner-MULTI进程")
                    if result.stdout.strip():
                        self.log_message(f"清理结果: {result.stdout.strip()}")
                else:
                    # 返回代码不为0可能表示没有找到进程或其他错误
                    if "ERROR: The process \"SRBMiner-MULTI.exe\" not found" in result.stderr:
                        self.log_message("没有找到运行中的SRBMiner-MULTI进程（已经停止）")
                    else:
                        self.log_message(f"清理进程时出现问题: {result.stderr.strip()}")
                        
            except Exception as e:
                self.log_message(f"执行taskkill命令时出错: {str(e)}")
        
        # 重置挖矿进程引用
        self.mining_process = None
        
        # 更新状态和按钮
        self.status_var.set("挖矿已停止")
        self.reset_buttons()
    
    def restart_mining(self):
        # 重启挖矿
        self.stop_mining()
        # 等待1秒后重新开始挖矿
        self.root.after(1000, self.start_mining)
    
    def reset_buttons(self):
        # 重置按钮状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.NORMAL)
    
    def validate_inputs(self):
        # 验证钱包地址
        wallet_address = self.wallet_entry.get().strip()
        if not wallet_address.startswith("scash"):
            messagebox.showerror("错误", "钱包地址格式不正确，应该以'scash'开头")
            return False
        
        # 验证矿工名称
        worker_name = self.worker_entry.get().strip()
        if not worker_name:
            messagebox.showerror("错误", "矿工名称不能为空")
            return False
        
        # 验证CPU核心数
        try:
            threads = int(self.threads_entry.get().strip())
            if threads <= 0:
                messagebox.showerror("错误", "CPU核心数必须大于0")
                return False
        except ValueError:
            messagebox.showerror("错误", "CPU核心数必须是数字")
            return False
        
        # 验证矿池地址
        pool_address = self.pool_entry.get().strip()
        if not pool_address.startswith("stratum+tcp://"):
            messagebox.showerror("错误", "矿池地址格式不正确，应该以'stratum+tcp://'开头")
            return False
        
        return True

if __name__ == "__main__":
    # 打印调试信息
    print(f"Python版本: {platform.python_version()}")
    print(f"操作系统: {platform.system()} {platform.release()} {platform.architecture()}")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python解释器路径: {sys.executable}")
    print(f"是否打包: {'是' if hasattr(sys, 'frozen') else '否'}")
    if hasattr(sys, '_MEIPASS'):
        print(f"MEIPASS路径: {sys._MEIPASS}")
    
    # 检查scash-logo.png文件是否存在
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_paths = [
        'scash-logo.png',
        os.path.join(os.getcwd(), 'scash-logo.png'),
        os.path.join(script_dir, 'scash-logo.png')
    ]
    
    for i, logo_path in enumerate(logo_paths):
        print(f"检查logo文件 {i+1}: {logo_path}, 存在: {os.path.exists(logo_path)}")
        if os.path.exists(logo_path):
            print(f"文件大小: {os.path.getsize(logo_path)} 字节")
            try:
                # 尝试直接打开图片以测试完整性
                if PIL_AVAILABLE:
                    with Image.open(logo_path) as img:
                        print(f"图片信息: {img.format}, {img.size}, {img.mode}")
            except Exception as e:
                print(f"打开图片失败: {str(e)}")
    
    root = tk.Tk()
    app = ScashMinerGUI(root)
    root.mainloop()