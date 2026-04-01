#!/usr/bin/env python3
"""
将Markdown文件转换为带侧边栏目录的HTML文件
用法：python convert-md-to-html.py 工作.md
"""

import sys
import os
import re
import io
from pathlib import Path

def escape_html(text):
    """转义HTML特殊字符"""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))

def generate_heading_id(text, index=None, existing_ids=None):
    """生成标题ID，确保唯一性"""
    # 支持中文，将空格和标点转换为-
    heading_id = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', text.lower())
    heading_id = re.sub(r'[-\s]+', '-', heading_id)
    heading_id = heading_id.strip('-')

    if not heading_id:
        heading_id = f'heading-{index if index is not None else 0}'

    # 检查唯一性 - 如果existing_ids为None，创建一个本地集合
    local_ids = existing_ids if existing_ids is not None else set()

    base_id = heading_id
    counter = 1
    while heading_id in local_ids:
        heading_id = f'{base_id}-{counter}'
        counter += 1

    # 如果传入了existing_ids，更新它
    if existing_ids is not None:
        existing_ids.add(heading_id)

    return heading_id

# 预编译正则表达式以提高性能
INLINE_PATTERNS = {
    'code': re.compile(r'`([^`]+)`'),
    'bold_italic_star': re.compile(r'(?<!\*)\*\*\*(?!\*)(.+?)(?<!\*)\*\*\*(?!\*)'),
    'bold_italic_underscore': re.compile(r'(?<!_)___(?!_)(.+?)(?<!_)___(?!_)'),
    'bold_star': re.compile(r'(?<!\*)\*\*(?!\*)(.+?)(?<!\*)\*\*(?!\*)'),
    'bold_underscore': re.compile(r'(?<!_)__(?!_)(.+?)(?<!_)__(?!_)'),
    'italic_star': re.compile(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)'),
    'italic_underscore': re.compile(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)'),
    'image': re.compile(r'!\[([^\]]*)\]\(([^)]+)\)'),
    'link': re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
}

def process_inline_formatting(text):
    """处理行内Markdown格式"""
    if not text:
        return text

    # 使用占位符保护代码片段，避免被其他格式处理干扰
    code_placeholders = {}
    placeholder_counter = [0]

    def save_code(match):
        placeholder = f"\x00CODE{placeholder_counter[0]}\x00"
        code_placeholders[placeholder] = f'<code>{escape_html(match.group(1))}</code>'
        placeholder_counter[0] += 1
        return placeholder

    # 先处理代码，使用占位符替换
    processed = INLINE_PATTERNS['code'].sub(save_code, text)

    # 处理图片：![alt](src) - 在链接之前处理
    processed = INLINE_PATTERNS['image'].sub(r'<img src="\2" alt="\1" class="markdown-image">', processed)

    # 处理链接：[text](url)
    processed = INLINE_PATTERNS['link'].sub(r'<a href="\2" class="markdown-link">\1</a>', processed)

    # 处理粗斜体组合：***text*** 或 ___text___
    # 使用循环处理嵌套情况
    for _ in range(3):  # 最多处理3层嵌套
        new_processed = INLINE_PATTERNS['bold_italic_star'].sub(r'<strong><em>\1</em></strong>', processed)
        new_processed = INLINE_PATTERNS['bold_italic_underscore'].sub(r'<strong><em>\1</em></strong>', new_processed)
        if new_processed == processed:
            break
        processed = new_processed

    # 处理粗体：**text** 或 __text__
    for _ in range(3):  # 最多处理3层嵌套
        new_processed = INLINE_PATTERNS['bold_star'].sub(r'<strong>\1</strong>', processed)
        new_processed = INLINE_PATTERNS['bold_underscore'].sub(r'<strong>\1</strong>', new_processed)
        if new_processed == processed:
            break
        processed = new_processed

    # 处理斜体：*text* 或 _text_
    for _ in range(3):  # 最多处理3层嵌套
        new_processed = INLINE_PATTERNS['italic_star'].sub(r'<em>\1</em>', processed)
        new_processed = INLINE_PATTERNS['italic_underscore'].sub(r'<em>\1</em>', new_processed)
        if new_processed == processed:
            break
        processed = new_processed

    # 恢复代码占位符
    for placeholder, code_html in code_placeholders.items():
        processed = processed.replace(placeholder, code_html)

    return processed

def extract_headings(markdown_content):
    """从Markdown内容中提取标题，忽略代码块中的内容"""
    headings = []
    lines = markdown_content.split('\n')
    existing_ids = set()
    in_code_block = False

    for i, line in enumerate(lines):
        # 检测代码块开始/结束
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue

        # 如果在代码块内，跳过标题检测
        if in_code_block:
            continue

        # 匹配 # 标题
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            # 使用辅助函数生成唯一ID
            heading_id = generate_heading_id(text, len(headings), existing_ids)

            headings.append({
                'level': level,
                'text': text,
                'id': heading_id,
                'line_number': i
            })

    return headings

def generate_toc_html(headings):
    """生成侧边栏目录HTML - 树形结构，支持折叠"""
    if not headings:
        return '<div class="toc-empty">暂无目录</div>'

    def build_nested_list(items, current_level=1, index=0):
        """递归构建嵌套列表"""
        result_parts = []
        n = len(items)

        while index < n:
            item = items[index]
            level = item['level']

            if level < current_level:
                # 返回上一层
                break
            elif level == current_level:
                # 检查是否有子项：查找后面是否有更高层级的标题
                has_children = False
                for j in range(index + 1, n):
                    if items[j]['level'] > current_level:
                        has_children = True
                    elif items[j]['level'] <= current_level:
                        # 遇到同级或更高级标题，停止查找
                        break

                # 构建当前列表项
                item_html = f'<li class="toc-level-{level}">\n'

                # 转义标题文本
                escaped_text = escape_html(item['text'])

                if has_children:
                    # 有子项，添加折叠按钮
                    item_html += f'  <div class="toc-item">\n'
                    item_html += f'    <button class="toc-toggle" aria-label="折叠/展开">\n'
                    item_html += f'      <i class="fas fa-chevron-right"></i>\n'
                    item_html += f'    </button>\n'
                    item_html += f'    <a href="#{item["id"]}">{escaped_text}</a>\n'
                    item_html += f'  </div>\n'
                else:
                    # 没有子项，直接添加链接
                    item_html += f'  <a href="#{item["id"]}">{escaped_text}</a>\n'

                index += 1

                # 如果有子项，递归处理子项
                if has_children:
                    item_html += '<ul class="toc-children">\n'
                    sub_result, new_index = build_nested_list(items, current_level + 1, index)
                    item_html += sub_result
                    item_html += '</ul>\n'
                    index = new_index

                item_html += '</li>\n'
                result_parts.append(item_html)
            else:
                # 当前标题层级高于当前层级，说明是子项
                # 递归处理子项
                sub_result, new_index = build_nested_list(items, current_level + 1, index)
                result_parts.append(sub_result)
                index = new_index

        return ''.join(result_parts), index

    html = '<nav class="toc">\n<ul>\n'
    nested_html, _ = build_nested_list(headings)
    html += nested_html
    html += '</ul>\n</nav>'
    return html

def enhanced_markdown_to_html(markdown_text, heading_id_map=None):
    """增强的Markdown到HTML转换，支持更多元素
    heading_id_map: 可选的标题ID映射，键为行号，值为ID
    """
    # 预处理：将文本按行分割
    lines = markdown_text.split('\n')
    result_lines = []
    i = 0
    n = len(lines)

    # 预编译一些常用的正则表达式以提高性能
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
    list_pattern = re.compile(r'^(\s*)([*-]|\d+[\.\)])\s+(.+)$')
    hr_pattern = re.compile(r'^[-*_]{3,}$')
    table_row_pattern = re.compile(r'^\s*\|')

    # 状态变量
    in_code_block = False
    code_block_language = ''
    code_block_content = []
    in_blockquote = False
    blockquote_lines = []

    # 列表状态
    list_stack = []  # 存储列表类型和缩进级别

    # 用于确保标题ID唯一性的集合
    heading_ids = set()

    while i < n:
        line = lines[i].rstrip()

        # 计算缩进（空格数）
        indent = 0
        while indent < len(line) and line[indent] == ' ':
            indent += 1
        line = line[indent:]  # 移除前导空格

        # 1. 代码块处理
        if line.startswith('```'):
            # 结束任何未关闭的列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

            if not in_code_block:
                # 开始代码块
                in_code_block = True
                code_block_language = line[3:].strip() or 'text'
                code_block_content = []
            else:
                # 结束代码块
                in_code_block = False
                code_content = '\n'.join(code_block_content)
                # 转义HTML特殊字符
                code_content = escape_html(code_content)
                # 添加语言标签
                language_label = code_block_language if code_block_language != 'text' else ''
                result_lines.append(f'<div class="code-block">')
                if language_label:
                    result_lines.append(f'  <div class="code-language">{escape_html(language_label)}</div>')
                result_lines.append(f'  <pre><code class="language-{escape_html(code_block_language)}">{code_content}</code></pre>')
                result_lines.append(f'</div>')
            i += 1
            continue

        if in_code_block:
            # 使用原始行，保留缩进，但移除开头的 ``` 行中的标记符
            raw_line = lines[i]
            code_block_content.append(raw_line)
            i += 1
            continue

        # 2. 引用块处理
        if line.startswith('>'):
            # 结束任何未关闭的列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

            if not in_blockquote:
                in_blockquote = True
                blockquote_lines = []

            # 处理引用行
            if line.startswith('> '):
                # 有内容的引用行
                blockquote_lines.append(line[2:].strip())
            elif line.strip() == '>':
                # 空引用行，作为段落分隔
                blockquote_lines.append('')

            i += 1

            # 继续收集连续的引用行
            while i < n and lines[i].lstrip().startswith('>'):
                line = lines[i].lstrip()
                if line.startswith('> '):
                    blockquote_lines.append(line[2:].strip())
                elif line.strip() == '>':
                    blockquote_lines.append('')
                i += 1

            # 结束引用块
            in_blockquote = False

            # 构建引用内容，保留原始换行结构
            # 处理引用块内的行内格式并保留换行
            processed_lines = []
            for content in blockquote_lines:
                if content == '':
                    # 空行表示段落分隔
                    processed_lines.append('')
                else:
                    # 处理行内格式（链接、加粗、斜体等）
                    processed_content = process_inline_formatting(content)
                    processed_lines.append(processed_content)

            # 将处理后的内容按段落分组
            quote_parts = []
            current_part = []

            for line in processed_lines:
                if line == '':
                    if current_part:
                        # 将当前段落的多行用<br>连接
                        quote_parts.append('<br>'.join(current_part))
                        current_part = []
                else:
                    current_part.append(line)

            if current_part:
                # 将当前段落的多行用<br>连接
                quote_parts.append('<br>'.join(current_part))

            if quote_parts:
                # 每个段落用<p>标签包裹
                paragraphs_html = ''.join([f'<p>{part}</p>' for part in quote_parts])
                result_lines.append(f'<blockquote>{paragraphs_html}</blockquote>')

            continue
        elif in_blockquote:
            # 结束引用块（当遇到非引用行时）
            in_blockquote = False
            # 使用相同的逻辑处理引用块内容
            processed_lines = []
            for content in blockquote_lines:
                if content == '':
                    processed_lines.append('')
                else:
                    processed_content = process_inline_formatting(content)
                    processed_lines.append(processed_content)

            quote_parts = []
            current_part = []

            for line in processed_lines:
                if line == '':
                    if current_part:
                        quote_parts.append('<br>'.join(current_part))
                        current_part = []
                else:
                    current_part.append(line)

            if current_part:
                quote_parts.append('<br>'.join(current_part))

            if quote_parts:
                paragraphs_html = ''.join([f'<p>{part}</p>' for part in quote_parts])
                result_lines.append(f'<blockquote>{paragraphs_html}</blockquote>')
            continue

        # 3. 标题处理
        heading_match = heading_pattern.match(line)
        if heading_match:
            # 结束任何未关闭的列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            # 为标题生成ID
            # 优先使用heading_id_map中的ID，确保与目录一致
            if heading_id_map and i in heading_id_map:
                heading_id = heading_id_map[i]
                # 添加到集合中以确保唯一性
                if heading_id in heading_ids:
                    # 如果ID已存在，生成一个唯一的
                    heading_id = generate_heading_id(text, i, heading_ids)
                else:
                    heading_ids.add(heading_id)
            else:
                # 后备方案：使用generate_heading_id，传入heading_ids集合确保唯一性
                heading_id = generate_heading_id(text, i, heading_ids)
            # 转义标题文本中的HTML特殊字符
            escaped_text = escape_html(text)
            result_lines.append(f'<h{level} id="{heading_id}">{escaped_text}</h{level}>')
            i += 1
            continue

        # 4. 列表处理（统一处理有序和无序列表）
        # 匹配：- 项目, * 项目, 1. 项目, 1) 项目
        list_match = list_pattern.match(line)
        if list_match:
            list_type = 'ul' if list_match.group(2) in ['*', '-'] else 'ol'

            # 处理列表缩进
            if not list_stack:
                # 开始新列表
                result_lines.append(f'<{list_type}>')
                list_stack.append((list_type, indent))
            elif indent > list_stack[-1][1]:
                # 增加缩进，开始嵌套列表
                result_lines.append(f'<{list_type}>')
                list_stack.append((list_type, indent))
            elif indent < list_stack[-1][1]:
                # 减少缩进，结束列表
                while list_stack and indent < list_stack[-1][1]:
                    result_lines.append('</' + list_stack.pop()[0] + '>')
                # 如果当前缩进级别没有列表，开始新列表
                if not list_stack or list_stack[-1][1] != indent:
                    result_lines.append(f'<{list_type}>')
                    list_stack.append((list_type, indent))
            elif list_type != list_stack[-1][0]:
                # 相同缩进但不同类型，结束旧列表开始新列表
                result_lines.append('</' + list_stack.pop()[0] + '>')
                result_lines.append(f'<{list_type}>')
                list_stack.append((list_type, indent))

            # 收集多行列表项内容
            list_item_lines = [list_match.group(3).strip()]
            i += 1

            # 检查后续行是否属于同一个列表项（有缩进但不是新的列表项）
            while i < n:
                next_line = lines[i].rstrip()
                next_indent = 0
                while next_indent < len(next_line) and next_line[next_indent] == ' ':
                    next_indent += 1

                # 如果是空行，检查下一行是否还是列表项的一部分
                if not next_line.strip():
                    # 检查下一行是否还是当前列表项的延续
                    if i + 1 < n:
                        next_next_line = lines[i + 1].rstrip()
                        next_next_indent = 0
                        while next_next_indent < len(next_next_line) and next_next_line[next_next_indent] == ' ':
                            next_next_indent += 1

                        # 如果下一行有足够的缩进，继续当前列表项
                        if next_next_indent > indent:
                            list_item_lines.append('')  # 添加空行作为段落分隔
                            i += 1
                            continue
                    # 否则结束当前列表项
                    break

                # 如果是新的列表项或标题等，结束当前列表项
                if (list_pattern.match(next_line) or
                    heading_pattern.match(next_line) or
                    next_line.startswith('>') or
                    next_line.startswith('```') or
                    hr_pattern.match(next_line) or
                    (next_line.strip().startswith('|') and '|' in next_line[1:])):
                    break

                # 如果缩进大于当前列表项的缩进，属于同一个列表项
                if next_indent > indent:
                    list_item_lines.append(next_line[next_indent:].strip())
                    i += 1
                else:
                    # 缩进不够，结束当前列表项
                    break

            # 处理列表项内容，保留换行结构
            # 对每行内容处理行内格式，然后按段落分组
            processed_lines = []
            for list_line in list_item_lines:
                if list_line == '':
                    processed_lines.append('')
                else:
                    processed_line = process_inline_formatting(list_line)
                    processed_lines.append(processed_line)

            # 将处理后的内容按段落分组（空行分隔）
            list_item_parts = []
            current_part = []

            for line in processed_lines:
                if line == '':
                    if current_part:
                        list_item_parts.append('<br>'.join(current_part))
                        current_part = []
                else:
                    current_part.append(line)

            if current_part:
                list_item_parts.append('<br>'.join(current_part))

            # 如果有多个段落，用<p>标签包裹每个段落
            if len(list_item_parts) > 1:
                list_item_html = ''.join([f'<p>{part}</p>' for part in list_item_parts])
                result_lines.append(f'<li>{list_item_html}</li>')
            else:
                list_item_html = list_item_parts[0] if list_item_parts else ''
                result_lines.append(f'<li>{list_item_html}</li>')
            continue

        # 5. 水平线
        if hr_pattern.match(line):
            # 结束任何未关闭的列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

            result_lines.append('<hr>')
            i += 1
            continue

        # 6. 表格（增强支持）
        if table_row_pattern.match(line) and '|' in line[1:]:
            # 结束任何未关闭的列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

            # 表格开始
            table_lines = []
            # 收集表格行
            while i < n and table_row_pattern.match(lines[i]):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                # 生成表格
                table_html = ['<table>']
                alignments = []  # 存储每列的对齐方式

                for row_idx, row in enumerate(table_lines):
                    # 分割单元格，保留空单元格但去除首尾空格
                    cells = [cell.strip() for cell in row.split('|')[1:-1]]
                    if not cells:
                        continue

                    # 第二行通常是分隔线，用于确定对齐方式
                    if row_idx == 1:
                        # 解析对齐方式
                        for cell in cells:
                            cell_clean = cell.replace('-', '').replace(':', '').strip()
                            if cell_clean == '':
                                # 检查对齐方式
                                if cell.startswith(':') and cell.endswith(':'):
                                    alignments.append('center')
                                elif cell.startswith(':'):
                                    alignments.append('left')
                                elif cell.endswith(':'):
                                    alignments.append('right')
                                else:
                                    alignments.append('left')  # 默认左对齐
                            else:
                                # 如果不是分隔线，则作为普通行处理
                                alignments = ['left'] * len(cells)  # 重置为默认对齐
                                break
                        # 如果是分隔线，跳过不添加到表格中
                        if all(cell.replace('-', '').replace(':', '').strip() == '' for cell in cells):
                            continue

                    tag = 'th' if row_idx == 0 else 'td'
                    table_html.append('<tr>')

                    for col_idx, cell in enumerate(cells):
                        # 处理表格单元格中的格式
                        processed_cell = process_inline_formatting(cell)

                        # 添加对齐样式
                        style = ''
                        if col_idx < len(alignments):
                            if alignments[col_idx] == 'center':
                                style = ' style="text-align: center;"'
                            elif alignments[col_idx] == 'right':
                                style = ' style="text-align: right;"'
                            elif alignments[col_idx] == 'left':
                                style = ' style="text-align: left;"'

                        table_html.append(f'<{tag}{style}>{processed_cell}</{tag}>')

                    table_html.append('</tr>')

                table_html.append('</table>')
                result_lines.append('\n'.join(table_html))
            continue

        # 7. 普通段落
        if line.strip():
            # 结束任何未关闭的列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

            # 处理行内格式
            processed_line = process_inline_formatting(line)
            result_lines.append(f'<p>{processed_line}</p>')
        elif not line.strip() and list_stack:
            # 空行结束所有列表
            while list_stack:
                result_lines.append('</' + list_stack.pop()[0] + '>')

        i += 1

    # 处理未结束的块
    if in_blockquote:
        # 使用相同的逻辑处理未结束的引用块
        processed_lines = []
        for content in blockquote_lines:
            if content == '':
                processed_lines.append('')
            else:
                processed_content = process_inline_formatting(content)
                processed_lines.append(processed_content)

        quote_parts = []
        current_part = []

        for line in processed_lines:
            if line == '':
                if current_part:
                    quote_parts.append('<br>'.join(current_part))
                    current_part = []
            else:
                current_part.append(line)

        if current_part:
            quote_parts.append('<br>'.join(current_part))

        if quote_parts:
            paragraphs_html = ''.join([f'<p>{part}</p>' for part in quote_parts])
            result_lines.append(f'<blockquote>{paragraphs_html}</blockquote>')

    # 结束任何未关闭的列表
    while list_stack:
        result_lines.append('</' + list_stack.pop()[0] + '>')

    html = '\n'.join(result_lines)
    return html

def convert_markdown_to_html(markdown_file):
    """将Markdown文件转换为带侧边栏的HTML"""
    # 读取Markdown文件
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 '{markdown_file}' 不存在")
    except PermissionError:
        raise PermissionError(f"没有权限读取文件 '{markdown_file}'")
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(markdown_file, 'r', encoding='gbk') as f:
                markdown_content = f.read()
        except UnicodeDecodeError:
            raise UnicodeDecodeError(f"无法解码文件 '{markdown_file}'，请检查文件编码")
    except Exception as e:
        raise Exception(f"读取文件时发生错误: {e}")

    # 提取标题
    headings = extract_headings(markdown_content)

    # 创建标题ID映射，用于在enhanced_markdown_to_html中重用
    heading_id_map = {}
    for heading in headings:
        # 使用行号作为键，因为同一行不可能有多个标题
        heading_id_map[heading['line_number']] = heading['id']

    # 生成HTML
    html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#2563eb">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css">
    <style>
        /* 浅色模式变量 */
        :root {{
            --primary-color: #3b82f6;
            --primary-hover: #2563eb;
            --secondary-color: #6b7280;
            --background-color: #f8fafc;
            --sidebar-bg: #ffffff;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --radius-sm: 0.25rem;
            --radius-md: 0.375rem;
            --radius-lg: 0.5rem;
            --transition: all 0.2s ease-in-out;
            --sidebar-width: 320px;
            --content-max-width: 900px;
            --code-bg: #f1f5f9;
        }}

        /* 深色模式变量 */
        [data-theme="dark"] {{
            --primary-color: #60a5fa;
            --primary-hover: #3b82f6;
            --secondary-color: #94a3b8;
            --background-color: #0f172a;
            --sidebar-bg: #1e293b;
            --card-bg: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
            --code-bg: #1e293b;
        }}

        /* 深色模式下的 body 背景 */
        [data-theme="dark"] body {{
            background-color: #0f172a;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-primary);
            background-color: var(--background-color);
            display: flex;
            min-height: 100vh;
            font-size: 15px;
            overflow: hidden;
            transition: background-color 0.3s ease;
        }}

        /* 侧边栏 - 扁平化简约风格 */
        .sidebar {{
            width: var(--sidebar-width);
            min-width: 280px;  /* 增加最小宽度 */
            max-width: 600px;  /* 增加最大宽度，允许拖拽扩展 */
            background: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            position: fixed;
            height: 100vh;
            display: flex;
            flex-direction: column;
            z-index: 100;
            flex-shrink: 0;
            overflow: hidden; /* 防止内容溢出 */
        }}

        .sidebar-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            background: var(--sidebar-bg);
            flex-shrink: 0; /* 防止标题区域被压缩 */
        }}

        .sidebar-header h2 {{
            font-size: 1.125rem;
            color: var(--text-primary);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0;
        }}

        .sidebar-header h2 i {{
            color: var(--primary-color);
            font-size: 1rem;
        }}

        /* 搜索框样式 */
        .sidebar-search {{
            position: relative;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .sidebar-search input {{
            width: 100%;
            padding: 0.5rem 0.75rem;
            padding-right: 2.5rem;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            background: var(--background-color);
            color: var(--text-primary);
            font-size: 0.875rem;
            transition: var(--transition);
        }}

        .sidebar-search input:focus {{
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }}

        /* 深色模式下搜索框样式优化 */
        [data-theme="dark"] .sidebar-search input {{
            background: #0f172a;
            border-color: #475569;
        }}

        [data-theme="dark"] .sidebar-search input:focus {{
            box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2);
        }}

        .sidebar-search i {{
            position: absolute;
            right: 2rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            font-size: 0.875rem;
            pointer-events: none;
        }}

        .sidebar-search input:focus + i {{
            color: var(--primary-color);
        }}

        /* 搜索结果高亮 */
        .toc li.hidden {{
            display: none;
        }}

        .toc li.highlight {{
            background: rgba(59, 130, 246, 0.1);
        }}

        /* 主题切换按钮 */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            z-index: 1000;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
        }}

        .theme-toggle:hover {{
            background: var(--primary-color);
            color: white;
            transform: scale(1.1);
        }}

        /* 返回顶部按钮 */
        .back-to-top {{
            position: fixed;
            bottom: 2rem;
            right: 1rem;
            width: 2.5rem;
            height: 2.5rem;
            border-radius: 50%;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            z-index: 1000;
            transition: var(--transition);
            box-shadow: var(--shadow-sm);
            opacity: 0;
            visibility: hidden;
        }}

        .back-to-top.visible {{
            opacity: 1;
            visibility: visible;
        }}

        .back-to-top:hover {{
            background: var(--primary-color);
            color: white;
            transform: translateY(-2px);
        }}

        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem 1.5rem;
            scroll-behavior: smooth; /* 添加平滑滚动 */
        }}

        /* 目录样式 - 扁平化简约风格 */
        .toc ul {{
            list-style: none;
            padding-left: 1.5rem;
            margin: 0;
        }}

        .toc > ul {{
            padding-left: 0;
        }}

        .toc li {{
            margin: 0.25rem 0;
            position: relative;
        }}

        /* 树形结构连接线 */
        .toc ul ul {{
            position: relative;
        }}

        .toc ul ul::before {{
            content: '';
            position: absolute;
            left: 0.75rem;
            top: 0;
            bottom: 0;
            width: 1px;
            background-color: #cbd5e1;
        }}

        .toc li::before {{
            content: '';
            position: absolute;
            left: -0.75rem;
            top: 1rem;
            width: 1rem;
            height: 1px;
            background-color: #cbd5e1;
        }}

        .toc > ul > li::before {{
            display: none;
        }}

        /* 目录层级递进关系 - 树形结构 */
        .toc-level-1 {{
            font-weight: 600;
            font-size: 0.95rem;
        }}

        .toc-level-2 {{
            font-size: 0.9rem;
        }}

        .toc-level-3 {{
            font-size: 0.875rem;
        }}

        .toc-level-4 {{
            font-size: 0.85rem;
        }}

        .toc-level-5 {{
            font-size: 0.825rem;
        }}

        .toc-level-6 {{
            font-size: 0.8rem;
        }}

        .toc a {{
            display: block;
            padding: 0.5rem 0.75rem;
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: var(--radius-sm);
            transition: var(--transition);
            font-weight: inherit;
            font-size: inherit;
            position: relative;
            z-index: 1;
            background-color: var(--sidebar-bg);
            margin-left: -0.75rem;
            padding-left: 0.75rem;
            white-space: nowrap; /* 强制一行显示 */
            overflow: hidden; /* 隐藏溢出内容 */
            text-overflow: ellipsis; /* 超出部分显示省略号 */
            max-width: 100%; /* 确保不超过容器宽度 */
            word-break: keep-all; /* 防止中文字符被断开 */
        }}

        .toc a:hover {{
            color: var(--primary-color);
            background-color: rgba(59, 130, 246, 0.05);
        }}

        .toc a.active {{
            color: var(--primary-color);
            background-color: rgba(59, 130, 246, 0.1);
            font-weight: 500;
        }}

        /* 一级标题特殊样式 */
        .toc-level-1 a {{
            margin-left: 0;
            padding-left: 0.75rem;
            white-space: nowrap; /* 强制一行显示 */
            overflow: hidden; /* 隐藏溢出内容 */
            text-overflow: ellipsis; /* 超出部分显示省略号 */
            word-break: keep-all; /* 防止中文字符被断开 */
        }}

        /* 折叠功能样式 */
        .toc-item {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        .toc-toggle {{
            background: none;
            border: none;
            width: 1.25rem;
            height: 1.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--text-secondary);
            border-radius: var(--radius-sm);
            transition: var(--transition);
            padding: 0;
            flex-shrink: 0;
        }}

        .toc-toggle:hover {{
            color: var(--primary-color);
            background-color: rgba(59, 130, 246, 0.1);
        }}

        .toc-toggle i {{
            font-size: 0.75rem;
            transition: transform 0.2s ease;
        }}

        .toc-toggle.expanded i {{
            transform: rotate(90deg);
        }}

        .toc-children {{
            overflow: hidden;
            max-height: 1000px; /* 默认展开，显示所有子项 */
            opacity: 1;
            transition: max-height 0.3s ease, opacity 0.2s ease;
        }}

        .toc-children.collapsed {{
            max-height: 0;
            opacity: 0;
        }}

        /* 调整有折叠按钮的链接样式 */
        .toc-item a {{
            flex: 1;
            margin-left: 0;
            padding-left: 0;
            white-space: nowrap; /* 强制一行显示 */
            overflow: hidden; /* 隐藏溢出内容 */
            text-overflow: ellipsis; /* 超出部分显示省略号 */
            max-width: calc(100% - 2rem); /* 为折叠按钮留出空间 */
            word-break: keep-all; /* 防止中文字符被断开 */
        }}

        .toc-empty {{
            color: var(--text-secondary);
            font-style: italic;
            padding: 1rem;
            text-align: center;
            font-size: 0.875rem;
        }}

        /* 拖拽分隔线样式 */
        .resizer {{
            position: fixed;
            top: 0;
            left: var(--sidebar-width);
            width: 8px;
            height: 100vh;
            background-color: transparent;
            cursor: col-resize;
            z-index: 200;
            transition: background-color 0.2s ease, left 0.2s ease; /* 添加left过渡效果 */
        }}

        .resizer:hover, .resizer.dragging {{
            background-color: var(--primary-color);
        }}

        .resizer.at-min-boundary {{
            background-color: #ef4444 !important; /* 红色，表示达到最小边界 */
        }}

        .resizer.at-max-boundary {{
            background-color: #10b981 !important; /* 绿色，表示达到最大边界 */
        }}

        .resizer::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 2px;
            height: 40px;
            background-color: var(--border-color);
            border-radius: 1px;
        }}

        .resizer:hover::before, .resizer.dragging::before {{
            background-color: white;
        }}

        /* 拖拽时的视觉反馈 */
        body.dragging {{
            cursor: col-resize;
            user-select: none;
        }}

        /* 内容区域 - 扁平化简约风格 */
        .content {{
            flex: 1;
            padding: 2rem;
            height: 100vh;
            overflow-y: auto;
            margin-left: var(--sidebar-width);
            width: calc(100% - var(--sidebar-width));
            flex-grow: 1;
            box-sizing: border-box;
            scroll-behavior: smooth;
            background-color: var(--background-color);
            transition: background-color 0.3s ease;
        }}

        /* Markdown内容样式 - 扁平化简约风格 */
        .markdown-body {{
            line-height: 1.8;
            background: var(--card-bg);
            padding: 3rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-color);
            width: 100%;
            max-width: var(--content-max-width);
            margin: 0 auto;
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }}

        /* 深色模式下内容卡片样式优化 */
        [data-theme="dark"] .markdown-body {{
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
        }}

        .markdown-body h1 {{
            font-size: 2rem;
            margin: 1.5rem 0 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid var(--border-color);
            color: var(--text-primary);
            font-weight: 600;
        }}

        .markdown-body h2 {{
            font-size: 1.5rem;
            margin: 2rem 0 0.75rem;
            color: var(--text-primary);
            font-weight: 600;
            padding-left: 0.75rem;
            border-left: 3px solid var(--primary-color);
        }}

        .markdown-body h3 {{
            font-size: 1.25rem;
            margin: 1.5rem 0 0.5rem;
            color: var(--text-primary);
            font-weight: 600;
        }}

        .markdown-body h4 {{
            font-size: 1.125rem;
            margin: 1.25rem 0 0.5rem;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .markdown-body p {{
            margin: 1rem 0;
            color: var(--text-primary);
            font-size: 1rem;
        }}

        .markdown-body ul, .markdown-body ol {{
            margin: 1rem 0;
            padding-left: 2rem;
        }}

        .markdown-body li {{
            margin: 0.5rem 0;
            padding: 0.5rem 0.75rem;
            background: var(--sidebar-bg);
            border-radius: var(--radius-sm);
            border-left: 3px solid var(--primary-color);
        }}

        .markdown-body li strong {{
            color: var(--text-primary);
            font-weight: 600;
        }}

        .markdown-body a.markdown-link {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
            border-bottom: 1px solid transparent;
            transition: var(--transition);
        }}

        .markdown-body a.markdown-link:hover {{
            border-bottom: 1px solid var(--primary-color);
        }}

        .markdown-body code {{
            background: var(--code-bg);
            padding: 0.2rem 0.4rem;
            border-radius: var(--radius-sm);
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.875em;
            color: #dc2626;
            border: 1px solid var(--border-color);
            transition: background-color 0.3s ease, border-color 0.3s ease;
        }}

        /* 深色模式下行内代码样式 */
        [data-theme="dark"] .markdown-body code {{
            color: #f87171;
        }}

        /* 代码块容器 */
        .code-block {{
            position: relative;
            margin: 1rem 0;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            overflow: hidden;
            transition: border-color 0.3s ease;
        }}

        /* 深色模式下代码块容器 */
        [data-theme="dark"] .code-block {{
            border-color: #334155;
        }}

        /* 代码语言标签 */
        .code-language {{
            position: absolute;
            top: 0;
            left: 0;
            background: var(--primary-color);
            color: white;
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 500;
            border-bottom-right-radius: var(--radius-sm);
            z-index: 10;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .markdown-body pre {{
            background: var(--code-bg);
            padding: 2rem 1rem 1rem 1rem;
            border-radius: var(--radius-md);
            overflow-x: auto;
            margin: 0;
            border: none;
            position: relative;
            transition: background-color 0.3s ease;
        }}

        .markdown-body pre code {{
            background: transparent;
            border: none;
            padding: 0;
            color: var(--text-primary);
            font-size: 0.875em;
            display: block;
            overflow-x: auto;
        }}

        .copy-button {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s, background-color 0.2s;
            font-family: inherit;
            z-index: 20; /* 提高z-index确保在语言标签上方 */
            min-width: 60px; /* 确保按钮有足够宽度 */
        }}

        /* 移动端代码复制按钮始终可见 */
        @media (max-width: 768px) {{
            .copy-button {{
                opacity: 1;
                font-size: 0.7rem;
                padding: 0.2rem 0.5rem;
                min-width: 50px;
            }}
        }}

        .copy-button:hover {{
            background: var(--primary-hover);
        }}

        .copy-button.copied {{
            background: #10b981;
        }}

        .code-block:hover .copy-button {{
            opacity: 1;
        }}

        .markdown-body blockquote {{
            position: relative;
            margin: 1.5rem 0;
            padding: 1rem 1.25rem 1rem 3rem;
            color: var(--text-secondary);
            background: var(--sidebar-bg);
            border-radius: var(--radius-md);
            border: 1px dashed var(--border-color);
            transition: all 0.3s ease;
        }}

        .markdown-body blockquote::before {{
            content: '"';
            position: absolute;
            left: 0.75rem;
            top: 0.25rem;
            font-size: 2.5rem;
            line-height: 1;
            color: var(--primary-color);
            opacity: 0.3;
            font-family: Georgia, serif;
        }}

        .markdown-body blockquote p {{
            margin: 0.5rem 0;
        }}

        .markdown-body blockquote a {{
            color: var(--primary-color);
        }}

        /* 深色模式下引用块样式 */
        [data-theme="dark"] .markdown-body blockquote {{
            border-color: var(--border-color);
        }}

        .markdown-body hr {{
            border: none;
            height: 1px;
            background: var(--border-color);
            margin: 2rem 0;
        }}

        .markdown-body table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            border: 1px solid var(--border-color);
        }}

        .markdown-body table th {{
            background: #f8fafc;
            color: var(--text-primary);
            font-weight: 600;
            padding: 0.75rem;
            text-align: left;
            border-bottom: 2px solid var(--border-color);
        }}

        .markdown-body table td {{
            padding: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .markdown-body table tr:last-child td {{
            border-bottom: none;
        }}

        .markdown-body img.markdown-image {{
            max-width: 100%;
            height: auto;
            border-radius: var(--radius-md);
            margin: 1rem 0;
        }}

        /* 响应式设计 */
        @media (max-width: 1024px) {{
            /* 移除强制设置sidebar-width，保留用户设置的宽度 */
            /* 只调整最小和最大宽度限制 */
            .sidebar {{
                min-width: 220px; /* 调整最小宽度 */
                max-width: 500px; /* 调整最大宽度，允许拖拽扩展 */
            }}

            .sidebar-header {{
                padding: 1.25rem;
            }}

            .sidebar-content {{
                padding: 0.75rem 1.25rem;
            }}

            .resizer {{
                left: var(--sidebar-width);
            }}

            .content {{
                padding: 1.25rem;
                margin-left: var(--sidebar-width); /* 使用CSS变量 */
                width: calc(100% - var(--sidebar-width)); /* 使用CSS变量计算剩余宽度 */
            }}

            .markdown-body {{
                padding: 1.75rem;
                max-width: 1200px; /* 调整最大宽度 */
            }}
        }}

        @media (max-width: 768px) {{
            body {{
                flex-direction: column;
                overflow: auto; /* 移动端恢复滚动 */
            }}

            .sidebar {{
                width: 100%;
                height: auto;
                position: static;
                border-right: none;
                border-bottom: 1px solid var(--border-color);
                display: block;
                background: var(--sidebar-bg);
            }}

            .sidebar-header {{
                padding: 1rem 1.25rem;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            .sidebar-header::after {{
                content: '▼';
                font-size: 0.75rem;
                color: var(--text-secondary);
                transition: transform 0.3s ease;
            }}

            .sidebar-header.collapsed::after {{
                transform: rotate(-90deg);
            }}

            .sidebar-content {{
                padding: 0.75rem 1.25rem;
                overflow-y: visible;
                max-height: none;
                transition: max-height 0.3s ease, opacity 0.3s ease;
            }}

            .sidebar-content.collapsed {{
                max-height: 0;
                opacity: 0;
                padding: 0;
                overflow: hidden;
            }}

            /* 移动端隐藏拖拽分隔线 */
            .resizer {{
                display: none;
            }}

            .content {{
                margin-left: 0;
                padding: 1rem; /* 减少padding，避免双重留白 */
                width: 100%;
                height: auto;
                overflow-y: visible;
            }}

            .markdown-body {{
                padding: 1.25rem;
                box-shadow: var(--shadow-sm);
                max-width: 100%; /* 移动端使用全宽 */
            }}

            .toc {{
                /* 移除高度限制，让目录可以显示所有项 */
                /* max-height: 250px; */
                overflow-y: auto;
            }}

            /* 移动端目录链接优化 */
            .toc a {{
                white-space: normal; /* 移动端允许换行 */
                overflow: visible; /* 移动端显示完整内容 */
                text-overflow: clip; /* 移动端不使用省略号 */
            }}

            .toc-item a {{
                max-width: 100%; /* 移动端使用完整宽度 */
            }}
        }}

        @media (max-width: 480px) {{
            .content {{
                padding: 1rem;
            }}

            .markdown-body {{
                padding: 1rem;
            }}

            .markdown-body h1 {{
                font-size: 1.75rem;
            }}

            .markdown-body h2 {{
                font-size: 1.375rem;
            }}

            .markdown-body h3 {{
                font-size: 1.125rem;
            }}
        }}

        /* 滚动条样式 - 优化版：更细更不明显 */
        /* WebKit浏览器（Chrome, Safari, Edge） */
        ::-webkit-scrollbar {{
            width: 4px;  /* 更细的滚动条 */
            height: 4px;
        }}

        ::-webkit-scrollbar-track {{
            background: transparent;
        }}

        ::-webkit-scrollbar-thumb {{
            background: rgba(203, 213, 225, 0.5); /* 半透明，更不明显 */
            border-radius: 2px;
            transition: background 0.2s ease;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(148, 163, 184, 0.7); /* 悬停时稍微明显一点 */
        }}

        /* 侧边栏目录区域的滚动条特别优化 */
        /* 隐藏侧边栏滚动条 - 跨浏览器解决方案 */

        /* Chrome, Safari, Edge, Opera */
        .sidebar-content::-webkit-scrollbar {{
            width: 0px; /* 完全隐藏滚动条 */
            height: 0px;
            background: transparent; /* 透明背景 */
        }}

        .sidebar-content::-webkit-scrollbar-track {{
            background: transparent; /* 透明轨道 */
        }}

        .sidebar-content::-webkit-scrollbar-thumb {{
            background: transparent; /* 透明滑块 */
            border-radius: 0px;
        }}

        .sidebar-content::-webkit-scrollbar-thumb:hover {{
            background: transparent; /* 悬停时也透明 */
        }}

        .sidebar-content::-webkit-scrollbar-corner {{
            background: transparent; /* 角落也透明 */
        }}

        /* Firefox */
        .sidebar-content {{
            scrollbar-width: none; /* 隐藏滚动条 */
            scrollbar-color: transparent transparent; /* 滑块和轨道都透明 */
        }}

        /* IE, Edge (旧版) */
        .sidebar-content {{
            -ms-overflow-style: none; /* IE和Edge隐藏滚动条 */
        }}

        /* 打印样式 */
        @media print {{
            .sidebar {{
                display: none;
            }}

            .content {{
                margin-left: 0;
                padding: 0;
            }}

            .markdown-body {{
                box-shadow: none;
                border: none;
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <!-- 主题切换按钮 -->
    <button class="theme-toggle" id="themeToggle" title="切换主题">
        <i class="fas fa-moon"></i>
    </button>

    <!-- 返回顶部按钮 -->
    <button class="back-to-top" id="backToTop" title="返回顶部">
        <i class="fas fa-arrow-up"></i>
    </button>

    <!-- 侧边栏 -->
    <aside class="sidebar">
        <div class="sidebar-header">
            <h2><i class="fas fa-book"></i> 文档目录</h2>
        </div>
        <div class="sidebar-search">
            <input type="text" id="tocSearch" placeholder="搜索目录..." />
            <i class="fas fa-search"></i>
        </div>
        <div class="sidebar-content">
            {toc}
        </div>
    </aside>

    <!-- 拖拽分隔线 -->
    <div class="resizer" id="sidebarResizer"></div>

    <!-- 主要内容 -->
    <main class="content">
        <article class="markdown-body">
            {content}
        </article>
    </main>

    <script>
        // 简单的目录交互
        document.addEventListener('DOMContentLoaded', function() {{
            const tocLinks = document.querySelectorAll('.toc a');
            const contentElement = document.querySelector('.content');
            const resizer = document.getElementById('sidebarResizer');
            const sidebar = document.querySelector('.sidebar');
            const root = document.documentElement;
            const themeToggle = document.getElementById('themeToggle');
            const backToTop = document.getElementById('backToTop');
            const tocSearch = document.getElementById('tocSearch');

            // 搜索功能
            if (tocSearch) {{
                tocSearch.addEventListener('input', (e) => {{
                    const searchTerm = e.target.value.toLowerCase().trim();
                    const tocItems = document.querySelectorAll('.toc li');
                    
                    // 如果搜索词为空，显示所有项
                    if (searchTerm === '') {{
                        tocItems.forEach(item => {{
                            item.classList.remove('hidden');
                            item.classList.remove('highlight');
                        }});
                        document.querySelectorAll('.toc-children').forEach(children => {{
                            children.classList.remove('collapsed');
                        }});
                        document.querySelectorAll('.toc-toggle').forEach(toggle => {{
                            toggle.classList.add('expanded');
                        }});
                        return;
                    }}
                    
                    // 首先隐藏所有项
                    tocItems.forEach(item => {{
                        item.classList.add('hidden');
                        item.classList.remove('highlight');
                    }});
                    
                    // 找到匹配的项并显示它们及其所有父级
                    tocItems.forEach(item => {{
                        const link = item.querySelector('a');
                        if (link) {{
                            const text = link.textContent.toLowerCase();
                            if (text.includes(searchTerm)) {{
                                // 显示匹配项
                                item.classList.remove('hidden');
                                item.classList.add('highlight');
                                
                                // 展开并显示所有父级
                                let parent = item;
                                while (parent) {{
                                    // 显示当前元素
                                    parent.classList.remove('hidden');
                                    
                                    // 如果是 toc-children，展开它
                                    if (parent.classList && parent.classList.contains('toc-children')) {{
                                        parent.classList.remove('collapsed');
                                    }}
                                    
                                    // 如果是 li，确保它的 toggle 是展开的
                                    if (parent.tagName === 'LI') {{
                                        const toggle = parent.querySelector('.toc-toggle');
                                        if (toggle) {{
                                            toggle.classList.add('expanded');
                                        }}
                                    }}
                                    
                                    parent = parent.parentElement;
                                }}
                            }}
                        }}
                    }});
                }});
            }}

            // 主题切换功能
            const initTheme = () => {{
                const savedTheme = localStorage.getItem('theme') || 'light';
                if (savedTheme === 'dark') {{
                    document.documentElement.setAttribute('data-theme', 'dark');
                    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                }} else {{
                    document.documentElement.removeAttribute('data-theme');
                    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                }}
            }};

            themeToggle.addEventListener('click', () => {{
                const currentTheme = document.documentElement.getAttribute('data-theme');
                if (currentTheme === 'dark') {{
                    document.documentElement.removeAttribute('data-theme');
                    localStorage.setItem('theme', 'light');
                    themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                }} else {{
                    document.documentElement.setAttribute('data-theme', 'dark');
                    localStorage.setItem('theme', 'dark');
                    themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                }}
            }});

            initTheme();

            // 返回顶部功能
            backToTop.addEventListener('click', () => {{
                contentElement.scrollTo({{
                    top: 0,
                    behavior: 'smooth'
                }});
            }});

            // 显示/隐藏返回顶部按钮
            contentElement.addEventListener('scroll', () => {{
                if (contentElement.scrollTop > 300) {{
                    backToTop.classList.add('visible');
                }} else {{
                    backToTop.classList.remove('visible');
                }}
            }});

            // 侧边栏拖拽功能
            if (resizer && sidebar && window.innerWidth > 768) {{
                // 确保拖拽分隔线在大屏幕上显示
                resizer.style.display = 'block';

                let isDragging = false;
                let startX = 0;
                let startWidth = 0;

                // 获取当前侧边栏宽度
                const getSidebarWidth = () => {{
                    return parseFloat(getComputedStyle(root).getPropertyValue('--sidebar-width'));
                }};

                // 设置侧边栏宽度
                const setSidebarWidth = (width) => {{
                    // 根据当前屏幕尺寸确定边界限制
                    const minWidth = 280; // 最小宽度，保证基本功能
                    const minContentWidth = 400; // 内容区域最小宽度
                    let maxWidth = 600; // 默认最大宽度，与CSS保持一致

                    if (window.innerWidth <= 1024) {{
                        maxWidth = 500; // 在1024px以下使用较小的最大宽度
                    }}

                    // 计算实际最大宽度：不能超过屏幕宽度减去内容区域最小宽度
                    const screenMaxWidth = window.innerWidth - minContentWidth;
                    const actualMaxWidth = Math.max(minWidth, Math.min(maxWidth, screenMaxWidth)); // 确保实际最大宽度不小于最小宽度

                    // 确保宽度在合法范围内
                    const clampedWidth = Math.max(minWidth, Math.min(width, actualMaxWidth));

                    // 更新CSS变量，拖拽分隔线会自动跟随
                    root.style.setProperty('--sidebar-width', clampedWidth + 'px');

                    // 添加边界状态反馈
                    resizer.classList.remove('at-min-boundary', 'at-max-boundary');
                    if (clampedWidth <= minWidth + 5) {{ // 接近最小边界
                        resizer.classList.add('at-min-boundary');
                    }} else if (clampedWidth >= actualMaxWidth - 5) {{ // 接近最大边界
                        resizer.classList.add('at-max-boundary');
                    }}

                    // 保存到localStorage
                    try {{
                        localStorage.setItem('sidebarWidth', clampedWidth.toString());
                    }} catch (e) {{
                        console.warn('无法保存侧边栏宽度到localStorage:', e);
                    }}
                }};

                // 从localStorage恢复宽度
                try {{
                    const savedWidth = localStorage.getItem('sidebarWidth');
                    if (savedWidth) {{
                        const width = parseFloat(savedWidth);
                        if (!isNaN(width)) {{
                            // 使用setSidebarWidth函数会自动进行边界检查
                            setSidebarWidth(width);
                        }}
                    }}
                }} catch (e) {{
                    console.warn('无法从localStorage读取侧边栏宽度:', e);
                }}


                // 鼠标按下事件
                resizer.addEventListener('mousedown', (e) => {{
                    isDragging = true;
                    startX = e.clientX;
                    startWidth = getSidebarWidth();

                    // 移除过渡效果以实现实时拖拽
                    resizer.style.transition = 'none';

                    // 添加视觉反馈
                    resizer.classList.add('dragging');
                    document.body.classList.add('dragging');

                    e.preventDefault();
                }});

                // 鼠标移动事件 - 优化版本，实时更新
                const handleMouseMove = (e) => {{
                    if (!isDragging) return;

                    const deltaX = e.clientX - startX;
                    const newWidth = startWidth + deltaX;

                    // 轻量级更新：只进行边界检查和CSS更新，不保存到localStorage
                    const minWidth = 280;
                    const minContentWidth = 400;
                    let maxWidth = 600;

                    if (window.innerWidth <= 1024) {{
                        maxWidth = 500;
                    }}

                    const screenMaxWidth = window.innerWidth - minContentWidth;
                    const actualMaxWidth = Math.max(minWidth, Math.min(maxWidth, screenMaxWidth)); // 确保实际最大宽度不小于最小宽度
                    const clampedWidth = Math.max(minWidth, Math.min(newWidth, actualMaxWidth));

                    // 直接更新CSS变量，实现实时响应
                    root.style.setProperty('--sidebar-width', clampedWidth + 'px');

                    // 添加边界状态反馈
                    resizer.classList.remove('at-min-boundary', 'at-max-boundary');
                    if (clampedWidth <= minWidth + 5) {{
                        resizer.classList.add('at-min-boundary');
                    }} else if (clampedWidth >= actualMaxWidth - 5) {{
                        resizer.classList.add('at-max-boundary');
                    }}
                }};

                // 鼠标释放事件
                const handleMouseUp = () => {{
                    if (!isDragging) return;

                    isDragging = false;

                    // 恢复过渡效果
                    resizer.style.transition = '';

                    // 获取最终宽度并保存到localStorage
                    const finalWidth = parseFloat(getComputedStyle(root).getPropertyValue('--sidebar-width'));
                    if (!isNaN(finalWidth)) {{
                        // 使用完整的setSidebarWidth函数保存到localStorage
                        setSidebarWidth(finalWidth);
                    }}

                    resizer.classList.remove('dragging');
                    document.body.classList.remove('dragging');

                    // 移除边界状态类，让分隔线恢复透明
                    resizer.classList.remove('at-min-boundary', 'at-max-boundary');
                }};

                // 添加事件监听器
                document.addEventListener('mousemove', handleMouseMove);
                document.addEventListener('mouseup', handleMouseUp);

                // 防止文本选择
                resizer.addEventListener('selectstart', (e) => {{
                    if (isDragging) {{
                        e.preventDefault();
                    }}
                }});

                // 双击重置宽度
                resizer.addEventListener('dblclick', () => {{
                    setSidebarWidth(320); // 重置为默认宽度
                }});
            }}

            // 平滑滚动
            tocLinks.forEach(link => {{
                link.addEventListener('click', function(e) {{
                    e.preventDefault();
                    const href = this.getAttribute('href');
                    if (!href || !href.startsWith('#')) return;

                    const targetId = href.substring(1);
                    if (!targetId) return;

                    const targetElement = document.getElementById(targetId);
                    if (!targetElement) return;

                    // 计算相对于内容区域的滚动位置
                    const contentRect = contentElement.getBoundingClientRect();
                    const targetRect = targetElement.getBoundingClientRect();
                    const scrollTop = contentElement.scrollTop;
                    const targetTop = targetRect.top - contentRect.top + scrollTop;

                    // 使用动态偏移（视口高度的10%）
                    const offset = Math.min(100, window.innerHeight * 0.1);

                    contentElement.scrollTo({{
                        top: targetTop - offset,
                        behavior: 'smooth'
                    }});

                    // 更新活动状态
                    tocLinks.forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                }});
            }});

            // 滚动时更新活动状态 - 使用防抖优化性能
            let scrollTimeout = null;
            contentElement.addEventListener('scroll', function() {{
                // 使用防抖，避免频繁触发
                if (scrollTimeout) {{
                    clearTimeout(scrollTimeout);
                }}

                scrollTimeout = setTimeout(() => {{
                    const headings = document.querySelectorAll('.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4, .markdown-body h5, .markdown-body h6');
                    let currentActiveId = null;
                    const scrollPosition = contentElement.scrollTop + 100;

                    // 找到当前可见的标题
                    for (let i = headings.length - 1; i >= 0; i--) {{
                        const heading = headings[i];
                        // 使用动态偏移
                        const offset = Math.min(100, window.innerHeight * 0.1);
                        if (heading.offsetTop <= scrollPosition + offset) {{
                            currentActiveId = heading.id;
                            break;
                        }}
                    }}

                    // 更新活动链接
                    let activeLink = null;
                    if (currentActiveId) {{
                        tocLinks.forEach(link => {{
                            const linkId = link.getAttribute('href').substring(1);
                            if (linkId === currentActiveId) {{
                                link.classList.add('active');
                                activeLink = link;
                            }} else {{
                                link.classList.remove('active');
                            }}
                        }});
                    }}

                    // 如果找到活动链接，确保它在侧边栏中可见
                    if (activeLink) {{
                        const sidebarContent = document.querySelector('.sidebar-content');
                        if (sidebarContent) {{
                            // 使用更简单可靠的方法计算链接位置
                            // 获取链接相对于侧边栏内容区域的边界矩形
                            const linkRect = activeLink.getBoundingClientRect();
                            const sidebarRect = sidebarContent.getBoundingClientRect();

                            // 计算链接在侧边栏内容区域中的相对位置
                            const linkTopRelative = linkRect.top - sidebarRect.top + sidebarContent.scrollTop;
                            const linkBottomRelative = linkRect.bottom - sidebarRect.top + sidebarContent.scrollTop;

                            const sidebarScrollTop = sidebarContent.scrollTop;
                            const sidebarHeight = sidebarContent.clientHeight;
                            const linkHeight = activeLink.offsetHeight;

                            // 检查链接是否在侧边栏可视区域外
                            const isAboveViewport = linkTopRelative < sidebarScrollTop;
                            const isBelowViewport = linkBottomRelative > sidebarScrollTop + sidebarHeight;

                            if (isAboveViewport || isBelowViewport) {{
                                // 计算需要滚动的距离
                                let targetScrollTop;

                                if (isAboveViewport) {{
                                    // 链接在可视区域上方，滚动到链接顶部
                                    targetScrollTop = linkTopRelative - 20; // 留出20px的顶部边距
                                }} else {{
                                    // 链接在可视区域下方，滚动到链接底部可见
                                    targetScrollTop = linkBottomRelative - sidebarHeight + 20; // 留出20px的底部边距
                                }}

                                // 确保滚动位置在有效范围内
                                const maxScrollTop = sidebarContent.scrollHeight - sidebarHeight;
                                const finalScrollTop = Math.max(0, Math.min(targetScrollTop, maxScrollTop));

                                // 只有当需要滚动时才执行滚动
                                if (Math.abs(sidebarScrollTop - finalScrollTop) > 5) {{
                                    sidebarContent.scrollTo({{
                                        top: finalScrollTop,
                                        behavior: 'smooth'
                                    }});
                                }}
                            }}
                        }}
                    }}
                }}, 50); // 50ms防抖延迟
            }});

            // 初始激活第一个可见的标题
            setTimeout(() => {{
                contentElement.dispatchEvent(new Event('scroll'));
            }}, 100);

            // 代码块复制功能
            const codeBlocks = document.querySelectorAll('.code-block');
            codeBlocks.forEach(codeBlock => {{
                const pre = codeBlock.querySelector('pre');
                if (!pre) return;

                // 创建复制按钮
                const copyButton = document.createElement('button');
                copyButton.className = 'copy-button';
                copyButton.textContent = '复制';
                copyButton.setAttribute('aria-label', '复制代码');

                // 获取代码内容
                const codeElement = pre.querySelector('code');
                if (!codeElement) return;

                // 添加复制按钮到代码块容器
                codeBlock.appendChild(copyButton);

                // 复制功能
                copyButton.addEventListener('click', async () => {{
                    try {{
                        const code = codeElement.textContent;
                        await navigator.clipboard.writeText(code);

                        // 更新按钮状态
                        copyButton.textContent = '已复制';
                        copyButton.classList.add('copied');

                        // 2秒后恢复
                        setTimeout(() => {{
                            copyButton.textContent = '复制';
                            copyButton.classList.remove('copied');
                        }}, 2000);
                    }} catch (err) {{
                        console.error('复制失败:', err);
                        copyButton.textContent = '复制失败';
                        setTimeout(() => {{
                            copyButton.textContent = '复制';
                        }}, 2000);
                    }}
                }});

                // 确保代码块有足够的空间显示复制按钮
                const codePadding = parseFloat(getComputedStyle(codeElement).paddingRight) || 0;
                if (codePadding < 60) {{
                    codeElement.style.paddingRight = '60px';
                }}
            }});

            // 目录折叠功能
            const tocToggles = document.querySelectorAll('.toc-toggle');
            const tocChildren = document.querySelectorAll('.toc-children');

            // 初始化折叠状态（默认展开，所以不添加collapsed类）
            // tocChildren默认是展开的，所以不需要添加任何类
            // tocToggles默认是展开状态
            tocToggles.forEach(toggle => {{
                toggle.classList.add('expanded');
            }});

            // 折叠/展开功能
            tocToggles.forEach(toggle => {{
                toggle.addEventListener('click', function(e) {{
                    e.stopPropagation(); // 防止事件冒泡
                    const parentLi = this.closest('li');
                    if (!parentLi) return;

                    const children = parentLi.querySelector('.toc-children');
                    if (!children) return;

                    const isCollapsed = children.classList.contains('collapsed');

                    if (isCollapsed) {{
                        // 展开
                        children.classList.remove('collapsed');
                        this.classList.add('expanded');
                    }} else {{
                        // 折叠
                        children.classList.add('collapsed');
                        this.classList.remove('expanded');
                    }}
                }});
            }});

            // 点击链接时，确保父级展开
            tocLinks.forEach(link => {{
                link.addEventListener('click', function() {{
                    // 找到所有父级的折叠元素并展开
                    let parent = this.closest('li');
                    while (parent) {{
                        const toggle = parent.querySelector('.toc-toggle');
                        const children = parent.querySelector('.toc-children');

                        if (toggle && children) {{
                            children.classList.remove('collapsed');
                            toggle.classList.add('expanded');
                        }}

                        parent = parent.parentElement?.closest('li');
                    }}
                }});
            }});

            // 移动端侧边栏折叠功能
            const sidebarHeader = document.querySelector('.sidebar-header');
            const sidebarContent = document.querySelector('.sidebar-content');

            if (sidebarHeader && sidebarContent && window.innerWidth <= 768) {{
                // 初始状态：在移动端默认折叠
                sidebarHeader.classList.add('collapsed');
                sidebarContent.classList.add('collapsed');

                // 点击侧边栏标题切换折叠状态
                sidebarHeader.addEventListener('click', function() {{
                    const isCollapsed = this.classList.contains('collapsed');

                    if (isCollapsed) {{
                        // 展开
                        this.classList.remove('collapsed');
                        sidebarContent.classList.remove('collapsed');
                    }} else {{
                        // 折叠
                        this.classList.add('collapsed');
                        sidebarContent.classList.add('collapsed');
                    }}
                }});

                // 监听窗口大小变化
                window.addEventListener('resize', function() {{
                    if (window.innerWidth > 768) {{
                        // 在大屏幕上确保侧边栏展开
                        sidebarHeader.classList.remove('collapsed');
                        sidebarContent.classList.remove('collapsed');
                        // 显示拖拽分隔线
                        if (resizer) {{
                            resizer.style.display = 'block';
                        }}

                        // 重新应用用户保存的宽度
                        try {{
                            const savedWidth = localStorage.getItem('sidebarWidth');
                            if (savedWidth) {{
                                const width = parseFloat(savedWidth);
                                if (!isNaN(width)) {{
                                    // 使用setSidebarWidth函数会自动进行边界检查
                                    setSidebarWidth(width);
                                }}
                            }}
                        }} catch (e) {{
                            console.warn('无法从localStorage读取侧边栏宽度:', e);
                        }}
                    }} else {{
                        // 在小屏幕上恢复折叠状态
                        if (!sidebarHeader.classList.contains('collapsed')) {{
                            sidebarHeader.classList.add('collapsed');
                            sidebarContent.classList.add('collapsed');
                        }}
                        // 隐藏拖拽分隔线
                        if (resizer) {{
                            resizer.style.display = 'none';
                        }}
                    }}
                }});
            }}
        }});
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
</body>
</html>'''

    # 获取文件名（不带扩展名）作为标题，并转义HTML特殊字符
    title = escape_html(Path(markdown_file).stem)

    # 生成侧边栏目录
    toc_html = generate_toc_html(headings)

    # 将Markdown转换为HTML，传递标题ID映射确保一致性
    content_html = enhanced_markdown_to_html(markdown_content, heading_id_map)

    # 填充模板
    html_content = html_template.format(
        title=title,
        toc=toc_html,
        content=content_html
    )

    # 保存HTML文件 - 使用Path对象正确处理文件扩展名
    markdown_path = Path(markdown_file)
    output_file = str(markdown_path.with_suffix('.html'))
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except PermissionError:
        raise PermissionError(f"没有权限写入文件 '{output_file}'")
    except IOError as e:
        raise IOError(f"写入文件时发生错误: {e}")
    except Exception as e:
        raise Exception(f"保存文件时发生未知错误: {e}")

    print(f"转换完成！文件已保存为: {output_file}")
    print(f"提取到 {len(headings)} 个标题")

    return output_file

def main():
    # 修复编码问题：设置标准输出编码为UTF-8
    try:
        # Python 3.7+ 使用 reconfigure 方法
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # 旧版本Python的兼容性处理
        if sys.stdout.encoding != 'UTF-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) < 2:
        print("用法: python convert-md-to-html.py <markdown文件>")
        print("示例: python convert-md-to-html.py 工作.md")
        sys.exit(1)

    markdown_file = sys.argv[1]

    if not os.path.exists(markdown_file):
        print(f"错误: 文件 '{markdown_file}' 不存在")
        sys.exit(1)

    # 检查文件扩展名（不区分大小写）
    markdown_path = Path(markdown_file)
    if markdown_path.suffix.lower() != '.md':
        print(f"警告: 文件 '{markdown_file}' 的扩展名不是 .md，可能不是Markdown文件")

    try:
        output_file = convert_markdown_to_html(markdown_file)
        print(f"\n打开文件: file://{os.path.abspath(output_file)}")
        print("\n提示:")
        print("1. 在浏览器中打开上面的文件链接")
        print("2. 侧边栏会自动显示文档目录")
        print("3. 点击目录项可以跳转到对应章节")
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()