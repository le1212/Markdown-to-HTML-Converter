# JetBrains IDE 配置说明

适用于：IntelliJ IDEA, PyCharm, WebStorm, PhpStorm, GoLand, Rider, CLion

## 安装步骤

### 方法1：手动配置 External Tools

1. 打开 IDE 设置：`File → Settings` (Windows/Linux) 或 `Preferences` (macOS)
2. 导航到：`Tools → External Tools`
3. 点击 `+` 添加新工具
4. 配置如下：

| 字段 | 值 |
|------|-----|
| Name | `Markdown to HTML` |
| Description | `将Markdown文件转换为HTML` |
| Program | `python` |
| Arguments | `"$ProjectFileDir$/python/convert.py" "$FilePath$"` |
| Working directory | `$FileDir$` |

5. 勾选以下选项：
   - ✅ Open console for tool output
   - ✅ Synchronize files after execution

### 方法2：导入配置文件

1. 将 `MarkdownToHTML.xml` 复制到：
   - Windows: `%APPDATA%\JetBrains\<IDE名称>\tools\`
   - macOS: `~/Library/Application Support/JetBrains/<IDE名称>/tools/`
   - Linux: `~/.config/JetBrains/<IDE名称>/tools/`

2. 重启 IDE

## 使用方法

### 转换单个文件

1. 打开 `.md` 文件
2. 右键点击编辑器 → `External Tools → Markdown to HTML`
3. 或使用快捷键：`Ctrl+Alt+T` → 选择 `Markdown to HTML`

### 转换多个文件

1. 在项目视图中选择多个 `.md` 文件
2. 右键点击 → `External Tools → Markdown to HTML`

## 设置快捷键

1. 打开设置：`File → Settings → Keymap`
2. 搜索 `External Tools`
3. 找到 `Markdown to HTML`
4. 右键点击 → `Add Keyboard Shortcut`
5. 设置快捷键（如 `Ctrl+Shift+H`）

## File Watcher 自动转换

如果需要保存时自动转换：

1. 安装 File Watchers 插件
2. 打开设置：`Tools → File Watchers`
3. 点击 `+` 添加新 watcher
4. 配置如下：

| 字段 | 值 |
|------|-----|
| Name | `Markdown to HTML` |
| File type | `Markdown` |
| Program | `python` |
| Arguments | `$ProjectFileDir$/python/convert.py $FilePath$` |
| Output paths to refresh | `$FileNameWithoutExtension$.html` |
| Working directory | $FileDir$ |

5. 勾选 `Trigger the watcher regardless of syntax errors`
