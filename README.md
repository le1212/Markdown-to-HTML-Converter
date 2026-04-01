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

### 界面特性

- 🎨 现代化扁平设计
- 🌙 深色/浅色模式切换（自动保存偏好）
- 📑 侧边栏目录导航（可折叠）
- 🔍 目录搜索功能
- 📱 响应式设计（适配移动端）
- ⬆️ 返回顶部按钮

### Markdown支持

- ✅ 标题（H1-H6，自动生成目录）
- ✅ 段落和换行
- ✅ 粗体、斜体、粗斜体
- ✅ 有序列表、无序列表
- ✅ 代码块（带语法高亮）
- ✅ 行内代码
- ✅ 引用块（便签风格）
- ✅ 表格
- ✅ 链接和图片
- ✅ 水平线
- ✅ HTML标签

### 代码高亮

使用 Prism.js 支持 300+ 种编程语言的语法高亮：

- JavaScript / TypeScript
- Python
- Java / Kotlin
- C / C++ / C#
- Go / Rust
- HTML / CSS
- SQL
- Shell / Bash
- 以及更多...

## 项目结构

```
md-to-html-converter/
├── python/
│   └── convert.py          # Python转换脚本
├── src/
│   └── extension.ts        # VS Code扩展代码
├── editors/
│   ├── jetbrains/          # JetBrains配置
│   ├── sublime-text/       # Sublime Text配置
│   ├── vim/                # Vim/Neovim配置
│   ├── notepad++/          # Notepad++配置
│   └── atom/               # Atom配置
├── package.json            # 扩展配置
├── tsconfig.json           # TypeScript配置
├── README.md               # 说明文档
└── LICENSE                 # MIT许可证
```

## 常见问题

### Q: 转换后中文显示乱码？

A: 确保您的Markdown文件使用UTF-8编码保存。

### Q: 代码块没有语法高亮？

A: 需要在网络环境下才能加载Prism.js。如果离线使用，可以下载Prism.js到本地。

### Q: 如何自定义HTML样式？

A: 修改 `python/convert.py` 中的CSS样式即可。

### Q: 支持哪些Markdown扩展语法？

A: 目前支持标准Markdown语法，暂不支持GFM扩展语法（如任务列表、删除线等）。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 更新日志

### v1.0.0 (2024-04-01)

- ✨ 初始版本发布
- ✅ VS Code扩展支持
- ✅ 多编辑器配置支持
- ✅ 深色/浅色模式切换
- ✅ 侧边栏目录导航
- ✅ 代码语法高亮
- ✅ 目录搜索功能

## 依赖

- Python 3.6+
- Visual Studio Code 1.74.0+ (仅VS Code扩展需要)

## 许可证

[MIT License](LICENSE)

## 作者

le1212

## 链接

- [GitHub仓库](https://github.com/le1212/Markdown-to-HTML-Converter)
- [问题反馈](https://github.com/le1212/Markdown-to-HTML-Converter/issues)
