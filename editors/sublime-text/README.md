# Sublime Text 配置说明

## 安装步骤

### 方法1：手动安装

1. 打开 Sublime Text
2. 菜单：`Preferences → Browse Packages...`
3. 在打开的目录中创建文件夹 `md-to-html-converter`
4. 将以下文件复制到该文件夹：
   - `MarkdownToHTML.sublime-build`
   - `python/` 目录（从项目根目录复制）
5. 重启 Sublime Text

### 方法2：使用 Package Control（推荐）

1. 安装 [Package Control](https://packagecontrol.io/)
2. `Ctrl+Shift+P` 打开命令面板
3. 输入 `Package Resource Viewer: Open Resource`
4. 选择 `User` → 创建 `MarkdownToHTML.sublime-build`

## 使用方法

### 转换单个文件

1. 打开 `.md` 文件
2. 按 `Ctrl+B` (Windows/Linux) 或 `Cmd+B` (macOS)
3. 或菜单：`Tools → Build`
4. 选择 `MarkdownToHTML` 构建系统

### 转换所有文件

1. 按 `Ctrl+Shift+B`
2. 选择 `MarkdownToHTML - Convert All`

## 设置默认构建系统

1. 打开 `.md` 文件
2. 菜单：`Tools → Build System → MarkdownToHTML`
3. 勾选后，打开 `.md` 文件时自动使用此构建系统

## 自定义快捷键

1. 菜单：`Preferences → Key Bindings`
2. 添加以下配置：

```json
[
    {
        "keys": ["ctrl+shift+h"],
        "command": "build",
        "context": [
            {
                "key": "selector",
                "operator": "equal",
                "operand": "text.html.markdown"
            }
        ]
    }
]
```

## 配置输出目录

修改 `MarkdownToHTML.sublime-build`：

```json
{
    "cmd": ["python", "${packages}/md-to-html-converter/python/convert.py", "$file", "--output", "$folder/html"],
    "selector": "text.html.markdown",
    "working_dir": "$file_path"
}
```
