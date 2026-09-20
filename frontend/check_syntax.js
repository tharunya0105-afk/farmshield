// Validates the inline babel script of index.html parses (brace/paren/quote state machine).
const fs = require('fs');
const html = fs.readFileSync('index.html', 'utf8');
const m = html.match(/<script type="text\/babel">([\s\S]*?)<\/script>/);
if (!m) { console.log('NO BABEL SCRIPT FOUND'); process.exit(1); }
const src = m[1];
let stack = [], inStr = null, esc = false, inLineC = false, inBlockC = false;
for (let i = 0; i < src.length; i++) {
  const c = src[i], n = src[i + 1];
  if (inLineC) { if (c === '\n') inLineC = false; continue; }
  if (inBlockC) { if (c === '*' && n === '/') { inBlockC = false; i++; } continue; }
  if (inStr) {
    if (esc) { esc = false; continue; }
    if (c === '\\') { esc = true; continue; }
    if (c === inStr) inStr = null;
    continue;
  }
  if (c === '/' && n === '/') { inLineC = true; continue; }
  if (c === '/' && n === '*') { inBlockC = true; i++; continue; }
  if (c === '"' || c === "'" || c === '`') { inStr = c; continue; }
  if (c === '(' || c === '[' || c === '{') stack.push({ c, i });
  if (c === ')' || c === ']' || c === '}') {
    const open = stack.pop();
    if (!open || (open.c === '(' && c !== ')') || (open.c === '[' && c !== ']') || (open.c === '{' && c !== '}')) {
      console.log('MISMATCH at index', i, ':', src.slice(Math.max(0, i - 60), i + 60));
      process.exit(1);
    }
  }
}
if (inStr) { console.log('UNTERMINATED STRING'); process.exit(1); }
if (stack.length) {
  const open = stack[stack.length - 1];
  console.log('UNCLOSED', open.c, 'at index', open.i, ':', src.slice(Math.max(0, open.i - 40), open.i + 80));
  process.exit(1);
}
console.log('frontend JS structure OK,', src.length, 'chars');
