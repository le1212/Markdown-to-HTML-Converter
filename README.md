# Markdown to HTML Converter

一个将Markdown文件转换为精美HTML文档的工具，支持多种编辑器。

## 功能特性

- ✅ 右键菜单快速转换
- ✅ 命令面板命令支持
- ✅ 快捷键支持 (Ctrl+Shift+H)
- ✅ 批量转换所有Markdown文件
- ✅ 保存时自动转换
- ✅ HTML预览功能
- ✅ 自定义输出目录
- ✅ 支持多种编辑器

## 编辑器支持

| 编辑器 | 支持程度 | 配置文件位置 |
|--------|----------|--------------|
| **VS Code** | ✅ 原生扩展 | 根目录 |
| **JetBrains 系列** | ✅ External Tools | `editors/jetbrains/` |
| **Sublime Text** | ✅ Build System | `editors/sublime-text/` |
| **Vim/Neovim** | ✅ 插件配置 | `editors/vim/` |
| **Notepad++** | ⚠️ 运行命令 | `editors/notepad++/` |
| **命令行** | ✅ 直接运行 | `python/convert.py` |

## 安装

### VS Code

#### 从VSIX文件安装

1. 下载 `.vsix` 文件
2. 打开VS Code
3. 按 `Ctrl+Shift+P` 打开命令面板
4. 输入 `Extensions: Install from VSIX...`
5. 选择下载的 `.vsix` 文件

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/le1212/Markdown-to-HTML-Converter.git

# 进入目录
cd Markdown-to-HTML-Converter

# 安装依赖
npm install

# 编译
npm run compile

# 打包
npm run package

# 安装
code --install-extension md-to-html-converter-1.0.0.vsix
```

### JetBrains 系列 (IntelliJ IDEA, PyCharm, WebStorm, etc.)

详细配置请查看 [editors/jetbrains/README.md](editors/jetbrains/README.md)

**快速配置：**

1. `File → Settings → Tools → External Tools`
2. 添加新工具：
   - Program: `python`
   - Arguments: `"$ProjectFileDir$/python/convert.py" "$FilePath$"`

### Sublime Text

详细配置请查看 [editors/sublime-text/README.md](editors/sublime-text/README.md)

**快速配置：**

1. 将 `editors/sublime-text/MarkdownToHTML.sublime-build` 复制到 `Packages/User/`
2. 打开 `.md` 文件，按 `Ctrl+B` 转换

### Vim/Neovim

详细配置请查看 [editors/vim/README.md](editors/vim/README.md)

**快速配置：**

```vim
" 添加到 .vimrc 或 init.vim
source /path/to/editors/vim/md-to-html.vim
```

### Notepad++

详细配置请查看 [editors/notepad++/README.md](editors/notepad++/README.md)

**快速配置：**

1. 按 `F5` 打开运行对话框
2. 输入：`python "C:\path\to\convert.py" "$(FULL_CURRENT_PATH)"`
3. 保存并设置快捷键

### 命令行

```bash
# 转换单个文件
python python/convert.py your-file.md

# 批量转换
python python/convert.py file1.md file2.md file3.md
```

## 使用方法

### VS Code

| 方式 | 操作 |
|------|------|
| **右键菜单** | 在 `.md` 文件上右键 → "Markdown转HTML: 转换当前文件" |
| **命令面板** | `Ctrl+Shift+P` → 输入 "Markdown转HTML" |
| **快捷键** | `Ctrl+Shift+H` |

### 其他编辑器

请查看对应编辑器的配置说明文档。

## 配置选项

### VS Code 设置

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
- Visual Studio Code 1.74.0+ (仅VS Code扩展需要)

## 许可证

MIT License
