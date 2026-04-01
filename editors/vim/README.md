# Vim/Neovim 配置说明

## 安装步骤

### 方法1：手动安装

1. 将 `md-to-html.vim` 复制到：
   - Vim: `~/.vim/plugin/`
   - Neovim: `~/.config/nvim/plugin/`

2. 将 `python/` 目录复制到相应位置

3. 修改脚本路径：
   ```vim
   let g:md_to_html_converter_path = '/path/to/convert.py'
   ```

### 方法2：使用 vim-plug

在 `.vimrc` 或 `init.vim` 中添加：

```vim
Plug 'le1212/Markdown-to-HTML-Converter'
```

然后运行：
```vim
:PlugInstall
```

### 方法3：使用 dein.vim

```vim
call dein#add('le1212/Markdown-to-HTML-Converter')
```

### 方法4：使用 packer.nvim (Neovim)

```lua
use 'le1212/Markdown-to-HTML-Converter'
```

## 使用方法

### 命令

| 命令 | 功能 |
|------|------|
| `:MdToHtml` | 转换当前文件 |
| `:MdToHtmlPreview` | 转换并在浏览器中预览 |
| `:MdToHtmlAll` | 转换当前目录下所有文件 |

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F5` | 转换当前文件 |
| `F6` | 转换并预览 |
| `<Leader>ma` | 转换所有文件 |

## 自定义配置

### 修改快捷键

```vim
" 使用 Ctrl+H 转换
autocmd FileType markdown nnoremap <buffer> <C-h> :MdToHtml<CR>
```

### 启用保存时自动转换

```vim
autocmd BufWritePost *.md call MdToHtml#Convert()
```

### 自定义脚本路径

```vim
let g:md_to_html_converter_path = '~/scripts/convert.py'
```

## Lua 配置 (Neovim)

如果使用 Lua 配置，在 `init.lua` 中添加：

```lua
vim.g.md_to_html_converter_path = vim.fn.expand('~/.config/nvim/python/convert.py')

vim.api.nvim_create_user_command('MdToHtml', function()
    local file = vim.fn.expand('%:p')
    if file:match('%.md$') then
        local cmd = 'python ' .. vim.g.md_to_html_converter_path .. ' ' .. file
        local result = vim.fn.system(cmd)
        if vim.v.shell_error == 0 then
            print('转换成功: ' .. vim.fn.expand('%:r') .. '.html')
        else
            print('转换失败: ' .. result)
        end
    else
        print('当前文件不是Markdown文件')
    end
end, {})

vim.api.nvim_create_autocmd('FileType', {
    pattern = 'markdown',
    callback = function()
        vim.api.nvim_buf_set_keymap(0, 'n', '<F5>', ':MdToHtml<CR>', { noremap = true, silent = true })
    end
})
```
