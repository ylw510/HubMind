# 加速 pip 安装的方法

## 方法 1: 使用国内镜像源（推荐）

### 临时使用（单次安装）
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 永久配置（推荐）

创建或编辑 `~/.pip/pip.conf` (Linux/Mac) 或 `%APPDATA%\pip\pip.ini` (Windows):

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
timeout = 120
```

### 常用国内镜像源

- 清华大学: https://pypi.tuna.tsinghua.edu.cn/simple
- 阿里云: https://mirrors.aliyun.com/pypi/simple
- 中科大: https://pypi.mirrors.ustc.edu.cn/simple
- 豆瓣: https://pypi.douban.com/simple

## 方法 2: 使用快速安装脚本

```bash
cd backend
./install_deps.sh
```

## 方法 3: 增加超时时间

```bash
pip install --timeout=120 -r requirements.txt
```

## 方法 4: 使用缓存

```bash
pip install --cache-dir ~/.pip/cache -r requirements.txt
```
