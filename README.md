# Markdown to HTML Converter

一个将Markdown文件转换为精美HTML文档的Visual Studio Code扩展。

## 功能特性

- ✅ 右键菜单快速转换
- ✅ 命令面板命令支持
- ✅ 快捷键支持 (Ctrl+Shift+H)
- ✅ 批量转换所有Markdown文件
- ✅ 保存时自动转换
- ✅ HTML预览功能
- ✅ 自定义输出目录

## 安装

### 从VSIX文件安装

1. 下载 `.vsix` 文件
2. 打开VS Code
3. 按 `Ctrl+Shift+P` 打开命令面板
4. 输入 `Extensions: Install from VSIX...`
5. 选择下载的 `.vsix` 文件

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/your-username/md-to-html-converter.git

# 进入目录
cd md-to-html-converter

# 安装依赖
npm install

# 编译
npm run compile

# 打包
npm run package

# 安装
code --install-extension md-to-html-converter-1.0.0.vsix
```

## 使用方法

### 方法1: 右键菜单

1. 在资源管理器中右键点击 `.md` 文件
2. 选择 "Markdown转HTML: 转换当前文件"

### 方法2: 命令面板

1. 打开一个 `.md` 文件
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 输入 "Markdown转HTML" 选择相应命令

### 方法3: 快捷键

- `Ctrl+Shift+H` (Windows/Linux)
- `Cmd+Shift+H` (macOS)

## 配置选项

在VS Code设置中搜索 "Markdown to HTML" 可以配置以下选项：

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `mdToHtml.autoConvertOnSave` | 保存时自动转换 | `false` |
| `mdToHtml.outputDirectory` | 输出目录 | `""` (同目录) |
| `mdToHtml.pythonPath` | Python路径 | `"python"` |
| `mdToHtml.showNotification` | 显示通知 | `true` |

## 生成的HTML特性

- 🎨 现代化扁平设计
- 🌙 深色/浅色模式切换
- 📑 侧边栏目录导航
- 🔍 目录搜索功能
- 💻 代码语法高亮 (Prism.js)
- 📱 响应式设计
- ⬆️ 返回顶部按钮

## 依赖

- Python 3.6+
- Visual Studio Code 1.74.0+

## 许可证

MIT License
