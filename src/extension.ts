import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn } from 'child_process';

let outputChannel: vscode.OutputChannel;

export function activate(context: vscode.ExtensionContext) {
    outputChannel = vscode.window.createOutputChannel('Markdown to HTML Converter');
    
    outputChannel.appendLine('Markdown to HTML Converter 扩展已激活');

    // 注册转换当前文件命令
    const convertCommand = vscode.commands.registerCommand('mdToHtml.convert', async (uri?: vscode.Uri) => {
        const fileUri = uri || vscode.window.activeTextEditor?.document.uri;
        if (!fileUri) {
            vscode.window.showErrorMessage('请先打开一个Markdown文件');
            return;
        }
        
        const filePath = fileUri.fsPath;
        if (!filePath.endsWith('.md')) {
            vscode.window.showErrorMessage('只能转换Markdown文件（.md）');
            return;
        }
        
        await convertFile(filePath);
    });

    // 注册转换所有文件命令
    const convertAllCommand = vscode.commands.registerCommand('mdToHtml.convertAll', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            vscode.window.showErrorMessage('请先打开一个工作区');
            return;
        }
        
        const mdFiles = await vscode.workspace.findFiles('**/*.md', '**/node_modules/**');
        if (mdFiles.length === 0) {
            vscode.window.showInformationMessage('未找到Markdown文件');
            return;
        }
        
        const choice = await vscode.window.showWarningMessage(
            `找到 ${mdFiles.length} 个Markdown文件，是否全部转换？`,
            '确定',
            '取消'
        );
        
        if (choice === '确定') {
            let successCount = 0;
            let failCount = 0;
            
            for (const fileUri of mdFiles) {
                try {
                    await convertFile(fileUri.fsPath);
                    successCount++;
                } catch {
                    failCount++;
                }
            }
            
            vscode.window.showInformationMessage(
                `转换完成：成功 ${successCount} 个，失败 ${failCount} 个`
            );
        }
    });

    // 注册预览命令
    const previewCommand = vscode.commands.registerCommand('mdToHtml.preview', async (uri?: vscode.Uri) => {
        const fileUri = uri || vscode.window.activeTextEditor?.document.uri;
        if (!fileUri) {
            vscode.window.showErrorMessage('请先打开一个Markdown文件');
            return;
        }
        
        const filePath = fileUri.fsPath;
        if (!filePath.endsWith('.md')) {
            vscode.window.showErrorMessage('只能预览Markdown文件（.md）');
            return;
        }
        
        const htmlPath = filePath.replace(/\.md$/, '.html');
        
        // 如果HTML文件不存在，先转换
        if (!fs.existsSync(htmlPath)) {
            await convertFile(filePath);
        }
        
        // 在浏览器中预览
        const previewUri = vscode.Uri.parse(htmlPath);
        await vscode.env.openExternal(previewUri);
    });

    // 监听保存事件
    const saveListener = vscode.workspace.onDidSaveTextDocument(async (document) => {
        const config = vscode.workspace.getConfiguration('mdToHtml');
        if (config.get<boolean>('autoConvertOnSave') && document.fileName.endsWith('.md')) {
            await convertFile(document.fileName);
        }
    });

    context.subscriptions.push(convertCommand, convertAllCommand, previewCommand, saveListener);
}

async function convertFile(filePath: string): Promise<void> {
    const config = vscode.workspace.getConfiguration('mdToHtml');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    const outputDir = config.get<string>('outputDirectory') || '';
    const showNotification = config.get<boolean>('showNotification') ?? true;
    
    // 获取Python脚本路径
    const extensionPath = vscode.extensions.getExtension('le1212.md-to-html-converter')?.extensionPath;
    const scriptPath = extensionPath 
        ? path.join(extensionPath, 'python', 'convert.py')
        : path.join(__dirname, '..', 'python', 'convert.py');
    
    // 构建输出路径
    let outputPath = filePath;
    if (outputDir) {
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(filePath));
        if (workspaceFolder) {
            // 确保输出目录存在
            const outputDirPath = path.join(workspaceFolder.uri.fsPath, outputDir);
            if (!fs.existsSync(outputDirPath)) {
                fs.mkdirSync(outputDirPath, { recursive: true });
            }
            outputPath = path.join(outputDirPath, path.basename(filePath));
        } else {
            // 文件不在工作区内，使用相对路径
            const outputDirPath = path.join(path.dirname(filePath), outputDir);
            if (!fs.existsSync(outputDirPath)) {
                fs.mkdirSync(outputDirPath, { recursive: true });
            }
            outputPath = path.join(outputDirPath, path.basename(filePath));
        }
    }
    
    outputChannel.appendLine(`正在转换: ${filePath}`);
    outputChannel.appendLine(`Python路径: ${pythonPath}`);
    outputChannel.appendLine(`脚本路径: ${scriptPath}`);
    
    return new Promise((resolve, reject) => {
        const timeoutMs = 30000; // 30秒超时
        let timeoutId: NodeJS.Timeout | null = null;

        const childProcess = spawn(pythonPath, [scriptPath, filePath], {
            cwd: path.dirname(filePath),
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
        });
        
        let stdout = '';
        let stderr = '';
        
        childProcess.stdout.on('data', (data: Buffer) => {
            stdout += data.toString();
            outputChannel.append(data.toString());
        });
        
        childProcess.stderr.on('data', (data: Buffer) => {
            stderr += data.toString();
            outputChannel.append(data.toString());
        });
        
        // 设置超时
        timeoutId = setTimeout(() => {
            if (childProcess.pid) {
                outputChannel.appendLine('转换超时，正在终止进程...');
                childProcess.kill('SIGTERM');
                const errorMsg = '转换超时（30秒）';
                outputChannel.appendLine(errorMsg);
                vscode.window.showErrorMessage(errorMsg);
                reject(new Error(errorMsg));
            }
        }, timeoutMs);

        const cleanup = () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
                timeoutId = null;
            }
        };

        childProcess.on('close', (code: number | null) => {
            cleanup();

            if (code === 0) {
                const htmlPath = outputPath.replace(/\.md$/, '.html');
                outputChannel.appendLine(`转换成功: ${htmlPath}`);

                if (showNotification) {
                    vscode.window.showInformationMessage(
                        `转换成功: ${path.basename(htmlPath)}`,
                        '打开文件',
                        '打开文件夹'
                    ).then(choice => {
                        if (choice === '打开文件') {
                            vscode.commands.executeCommand('vscode.open', vscode.Uri.file(htmlPath));
                        } else if (choice === '打开文件夹') {
                            vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(htmlPath));
                        }
                    }, (err: Error) => {
                        outputChannel.appendLine(`显示通知时出错: ${err.message}`);
                    });
                }
                resolve();
            } else {
                // 优先使用stderr，如果stderr为空但有stdout，则使用stdout
                const errorOutput = stderr.trim() || stdout.trim();
                const errorMsg = errorOutput
                    ? `转换失败: ${errorOutput}`
                    : `转换失败: Python进程退出代码 ${code}`;
                outputChannel.appendLine(errorMsg);
                vscode.window.showErrorMessage(errorMsg);
                reject(new Error(errorMsg));
            }
        });

        childProcess.on('error', (err: Error) => {
            cleanup();
            const errorMsg = `执行Python失败: ${err.message}`;
            outputChannel.appendLine(errorMsg);
            vscode.window.showErrorMessage(errorMsg);
            reject(err);
        });
    });
}

export function deactivate() {
    outputChannel.appendLine('Markdown to HTML Converter 扩展已停用');
    outputChannel.dispose();
}
