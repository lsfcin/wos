// caveman — reads and writes of the mode flag and the lifetime history log
//
// Two files, both under $CLAUDE_CONFIG_DIR:
//   .caveman-active        single value, the active mode (rewritten atomically)
//   .caveman-history.jsonl append-only, one JSON object per session
//
// Every path goes through safepath.js. All operations silent-fail: the flag is
// best-effort state, never something a session should die over.

const fs = require('fs');
const { O_NOFOLLOW, prepareTarget, withFd } = require('./safepath');

// Hard cap on a flag read. The longest legitimate value is "wenyan-ultra" (12
// bytes); 64 leaves slack without enabling exfiltration through this channel.
const MAX_FLAG_BYTES = 64;

// Atomic, symlink-safe write: temp file + rename, so a concurrent reader never
// sees a half-written flag.
function safeWriteFlag(flagPath, content) {
  try {
    const realPath = prepareTarget(flagPath, 'safeWriteFlag');
    if (realPath === null) return;

    const tempPath = `${realPath}.${process.pid}.${Date.now()}`;
    const flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | O_NOFOLLOW;
    withFd(tempPath, flags, fd => fs.writeSync(fd, String(content)));
    fs.renameSync(tempPath, realPath);
  } catch (e) {
    // Silent fail — flag is best-effort
  }
}

// Symlink-safe, size-capped, whitelist-validated read. Returns null on any anomaly.
//
// Without the cap and the whitelist, an attacker who replaced the flag with a
// symlink to ~/.ssh/id_rsa would have every reader — statusline, per-turn
// reinforcement — either echo that content to the terminal or inject it into
// model context. `validModes` is passed in to keep this file free of policy.
function readFlag(flagPath, validModes) {
  try {
    let st;
    try {
      st = fs.lstatSync(flagPath);
    } catch (e) {
      return null;
    }
    if (st.isSymbolicLink() || !st.isFile()) return null;
    if (st.size > MAX_FLAG_BYTES) return null;

    let out;
    let fd;
    try {
      fd = fs.openSync(flagPath, fs.constants.O_RDONLY | O_NOFOLLOW);
      const buf = Buffer.alloc(MAX_FLAG_BYTES);
      const n = fs.readSync(fd, buf, 0, MAX_FLAG_BYTES, 0);
      out = buf.slice(0, n).toString('utf8');
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }

    const raw = out.trim().toLowerCase();
    return validModes.includes(raw) ? raw : null;
  } catch (e) {
    return null;
  }
}

// Symlink-safe append. O_APPEND rather than the write-and-rename above, so
// concurrent sessions add lines instead of clobbering each other.
function appendFlag(filePath, line) {
  try {
    const realPath = prepareTarget(filePath, 'appendFlag');
    if (realPath === null) return;

    const flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_APPEND | O_NOFOLLOW;
    withFd(realPath, flags, fd => fs.writeSync(fd, `${String(line).replace(/\n$/, '')}\n`));
  } catch (e) {
    // Silent fail — history is best-effort
  }
}

// Symlink-safe history read. Returns raw lines; the caller parses the JSON.
// Deliberately uncapped — history grows with use, unlike the flag.
function readHistory(filePath) {
  try {
    const st = fs.lstatSync(filePath);
    if (st.isSymbolicLink() || !st.isFile()) return [];

    let raw;
    let fd;
    try {
      fd = fs.openSync(filePath, fs.constants.O_RDONLY | O_NOFOLLOW);
      raw = fs.readFileSync(fd, 'utf8');
    } finally {
      if (fd !== undefined) fs.closeSync(fd);
    }
    return raw.split('\n').filter(line => line.trim());
  } catch (e) {
    return [];
  }
}

module.exports = { MAX_FLAG_BYTES, safeWriteFlag, readFlag, appendFlag, readHistory };
