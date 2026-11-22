// CloudBase 云托管部署脚本(Node 传参精确,绕开 PowerShell 5.1 引号坑)
// 用法: node scripts/deploy_cloudbase.js <envId>
// 密钥从本地 .env 与 ~/.claude/settings.json 读取,不在命令行/输出中回显。
const { execFileSync } = require('child_process');
const fs = require('fs');

const envId = process.argv[2];
if (!envId) {
  console.error('用法: node scripts/deploy_cloudbase.js <envId>');
  process.exit(1);
}

const root = 'D:/claude code projects/final-mate';

// 解析 tcb 的绝对路径(node 子进程的 PATH 可能不含 npm 全局目录)
function findTcb() {
  try {
    const out = execFileSync('where', ['tcb'], { encoding: 'utf8' });
    const lines = out.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    // Windows 上必须用 .cmd 包装(Node 才能经 cmd.exe 启动)
    const cmd = lines.find((l) => /tcb\.cmd$/i.test(l));
    return cmd || lines.find((l) => /tcb$/i.test(l)) || process.env.APPDATA + '\\npm\\tcb.cmd';
  } catch (e) { /* 继续兜底 */ }
  return process.env.APPDATA + '\\npm\\tcb.cmd';
}
const TCB = findTcb();
console.log('tcb 路径: ' + TCB);
const dotenv = fs.readFileSync(root + '/.env', 'utf8');
const m = dotenv.match(/^DEEPSEEK_API_KEY=(.+)$/m);
if (!m) { console.error('未在 .env 找到 DEEPSEEK_API_KEY'); process.exit(1); }
const settings = JSON.parse(
  fs.readFileSync(process.env.USERPROFILE + '/.claude/settings.json', 'utf8')
);
const zhihuSecret = settings.env && settings.env.ZHIHU_ACCESS_SECRET;
if (!zhihuSecret) { console.error('未在 settings.json 找到 ZHIHU_ACCESS_SECRET'); process.exit(1); }

const envParams = JSON.stringify({
  DEEPSEEK_API_KEY: m[1].trim(),
  ZHIHU_ACCESS_SECRET: zhihuSecret,
});

const args = [
  'cloudrun', 'deploy',
  '-e', envId,
  '-s', 'finalmate',
  '--source', root,
  '--port', '8000',
  '--min-num', '0',
  '--max-num', '2',
  '--open-access-types', 'OA,PUBLIC',
  '--env-params', envParams,
  '--force',
  '--wait',
];

console.log('tcb ' + args.filter((a, i) => a !== '--env-params' && args[i - 1] !== '--env-params').join(' '));
try {
  execFileSync(TCB, args, { stdio: 'inherit', cwd: root });
} catch (err) {
  // 只打错误信息,避免 Node 错误转储把密钥参数写进日志
  console.error('部署失败: ' + (err && err.message ? err.message : err));
  process.exit(1);
}
