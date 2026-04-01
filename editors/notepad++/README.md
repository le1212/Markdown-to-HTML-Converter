# Notepad++ 配置说明

## 安装步骤

1. 打开 Notepad++
2. 菜单：`运行 → 运行...` (或按 `F5`)
3. 输入以下命令：

```
python "C:\path\to\convert.py" "$(FULL_CURRENT_PATH)"
```

4. 点击 `保存...` 按钮
5. 输入名称：`Markdown转HTML`
6. 设置快捷键（如 `Ctrl+Shift+H`）

## 使用方法

1. 打开 `.md` 文件
2. 按 `F5` 或菜单：`运行 → 运行...`
3. 选择 `Markdown转HTML`
4. 或使用设置的快捷键

## 高级配置

### 使用 NppExec 插件（推荐）

1. 安装 NppExec 插件：`插件 → 插件管理 → 搜索 NppExec → 安装`
2. 重启 Notepad++
3. 按 `F6` 打开 NppExec 执行框
4. 输入以下脚本：

```
// 转换当前Markdown文件
python "C:\path\to\convert.py" "$(FULL_CURRENT_PATH)"
// 显示输出文件
NPP_OPEN $(CURRENT_DIRECTORY)\$(NAME_PART).html
```

5. 点击 `Save...` 保存脚本为 `Markdown to HTML`

### 设置自动转换

在 NppExec 中创建以下脚本：

```
// 保存时自动转换
NPP_SAVE
python "C:\path\to\convert.py" "$(FULL_CURRENT_PATH)"
```

然后在 `插件 → NppExec → Advanced Options` 中设置：
- 勾选 `Place to the Macros submenu`
- 在 `Associated script` 中选择保存的脚本
- 在 `Item name` 中输入名称

### 批量转换

创建批处理脚本 `convert_all.bat`：

```batch
@echo off
for /r %%f in (*.md) do (
    echo Converting: %%f
    python "C:\path\to\convert.py" "%%f"
)
echo Done!
pause
```

然后在 NppExec 中运行：

```
cmd /c "C:\path\to\convert_all.bat"
```

## 快捷键设置

1. 菜单：`设置 → 管理快捷键...`
2. 选择 `Run commands` 标签
3. 找到保存的命令
4. 双击修改快捷键
