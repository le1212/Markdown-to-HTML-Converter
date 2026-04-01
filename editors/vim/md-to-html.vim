" Markdown to HTML Converter
" 将此文件内容添加到你的 .vimrc 或 init.vim 中

" 配置 Python 脚本路径
" 请将下面的路径修改为实际的脚本路径
let g:md_to_html_converter_path = expand('<sfile>:p:h') . '/../python/convert.py'

" 转换当前文件
function! MdToHtml#Convert()
    let l:file = expand('%:p')
    if l:file =~ '\.md$'
        let l:cmd = 'python ' . shellescape(g:md_to_html_converter_path) . ' ' . shellescape(l:file)
        let l:output = system(l:cmd)
        if v:shell_error == 0
            echohl SuccessMsg
            echo '转换成功: ' . expand('%:r') . '.html'
            echohl None
        else
            echohl ErrorMsg
            echo '转换失败: ' . l:output
            echohl None
        endif
    else
        echohl ErrorMsg
        echo '当前文件不是Markdown文件'
        echohl None
    endif
endfunction

" 转换并预览
function! MdToHtml#ConvertAndPreview()
    call MdToHtml#Convert()
    let l:html_file = expand('%:r') . '.html'
    if filereadable(l:html_file)
        if has('win32')
            silent execute '!start ' . shellescape(l:html_file)
        elseif has('mac')
            silent execute '!open ' . shellescape(l:html_file)
        else
            silent execute '!xdg-open ' . shellescape(l:html_file)
        endif
    endif
endfunction

" 转换目录下所有Markdown文件
function! MdToHtml#ConvertAll()
    let l:dir = expand('%:p:h')
    let l:cmd = 'python -c "import os; import subprocess; [subprocess.run([\"python\", \"' . g:md_to_html_converter_path . '\", os.path.join(root, f)]) for root, dirs, files in os.walk(\"' . l:dir . '\") for f in files if f.endswith(\".md\")]\"'
    call system(l:cmd)
    echo '批量转换完成'
endfunction

" 命令定义
command! MdToHtml call MdToHtml#Convert()
command! MdToHtmlPreview call MdToHtml#ConvertAndPreview()
command! MdToHtmlAll call MdToHtml#ConvertAll()

" 快捷键映射
" F5: 转换当前文件
" F6: 转换并预览
" <Leader>ma: 转换所有文件
autocmd FileType markdown nnoremap <buffer> <F5> :MdToHtml<CR>
autocmd FileType markdown nnoremap <buffer> <F6> :MdToHtmlPreview<CR>
autocmd FileType markdown nnoremap <buffer> <Leader>ma :MdToHtmlAll<CR>

" 自动转换（保存时）
" 如需启用，取消下面的注释
" autocmd BufWritePost *.md call MdToHtml#Convert()
