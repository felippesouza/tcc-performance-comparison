import fs from 'fs';

let inputData = '';
process.stdin.on('data', chunk => { inputData += chunk; });
process.stdin.on('end', () => {
    try {
        const payload = JSON.parse(inputData);
        const tool = payload.toolCall.name;
        const args = payload.toolCall.args;
        
        const allow = () => { console.log(JSON.stringify({ decision: 'allow' })); process.exit(0); };
        const deny = (reason) => { console.log(JSON.stringify({ decision: 'deny', reason })); process.exit(0); };
        
        const argsStr = JSON.stringify(args);
        if (argsStr.includes('inline-ok:')) {
            return allow();
        }

        if (tool === 'run_command') {
            const cmd = args.CommandLine || '';
            const delegable = /(^|[\s;|&(])unzip(\s|$)/.test(cmd) ||
                              /(^|[\s;|&(])tar\s+[^|]*(x|--extract)/.test(cmd) ||
                              /(^|[\s;|&(])grep\s+-[A-Za-z]*[rR]/.test(cmd) ||
                              /(^|[\s;|&(])find\s+[^|]*-exec/.test(cmd);
            if (delegable) {
                return deny("🧭 DELEGATION GATE — This shell operation dumps large output into MAIN context. Delegate first → sweeper (unzip/parse) · locator (symbol/grep). If inline is genuinely necessary, re-run with 'inline-ok: <reason>' in the command.");
            }
        }

        if (tool === 'view_file') {
            const fp = args.AbsolutePath;
            if (!fp) return allow();
            if (/\.(png|jpe?g|gif|webp|bmp|svg|pdf|ico|heic)$/i.test(fp)) return allow();
            
            try {
                const stats = fs.statSync(fp);
                if (stats.size > 60000) {
                    return deny(`🧭 DELEGATION GATE — File exceeds 60KB (${stats.size} bytes). Delegate to a locator/sweeper, or use 'inline-ok: <reason>' in toolSummary.`);
                }
            } catch (e) {
                return allow();
            }
        }

        allow();
    } catch (e) {
        console.log(JSON.stringify({ decision: 'allow' }));
    }
});
