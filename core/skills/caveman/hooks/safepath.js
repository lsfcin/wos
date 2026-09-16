// caveman — symlink-safe path resolution shared by every flag-file writer
//
// The flag paths are predictable (~/.claude/.caveman-active, .caveman-history.jsonl),
// so a local attacker with write access to that directory could plant a symlink and
// have our writes clobber an arbitrary file, or have our reads slurp a secret.
//
// Legitimate symlinked config dirs must still work (`ln -s /opt/shared ~/.claude`), so
// a symlinked PARENT is resolved and ownership-checked; only a symlinked TARGET FILE is
// refused outright — that is the actual clobber vector.
//
// Ownership check is uid-based on Unix. Windows has no uid, so it falls back to
// requiring the resolved path to live under the user's home directory.

const fs = require('fs');
const path = require('path');
const os = require('os');

// 0 is a valid no-op flag value where the platform lacks O_NOFOLLOW (Windows).
const O_NOFOLLOW = typeof fs.constants.O_NOFOLLOW === 'number' ? fs.constants.O_NOFOLLOW : 0;

function debugLog(label, message) {
  if (process.env.CAVEMAN_DEBUG === '1') {
    process.stderr.write(`[caveman] ${label}: ${message}\n`);
  }
}

// Resolve a directory that may itself be a symlink, verifying the caller owns the
// target. Returns the real directory path, or null if it must not be written to.
function resolveSafeDir(dir, label) {
  try {
    const lstat = fs.lstatSync(dir);
    if (!lstat.isSymbolicLink()) return dir;

    const realDir = fs.realpathSync(dir);
    const realStat = fs.statSync(realDir);
    if (!realStat.isDirectory()) {
      debugLog(label, `symlink target ${realDir} is not a directory`);
      return null;
    }

    if (typeof process.getuid === 'function') {
      if (realStat.uid !== process.getuid()) {
        debugLog(label, `symlink target ${realDir} owned by uid ${realStat.uid}, not current user ${process.getuid()}`);
        return null;
      }
      return realDir;
    }

    const normalizedReal = path.resolve(realDir).toLowerCase();
    const normalizedHome = path.resolve(os.homedir()).toLowerCase();
    if (!normalizedReal.startsWith(normalizedHome + path.sep) && normalizedReal !== normalizedHome) {
      debugLog(label, `symlink target ${normalizedReal} is outside home directory ${normalizedHome}`);
      return null;
    }
    return realDir;
  } catch (e) {
    return null;
  }
}

// True when the path is safe to write: it is absent, or a real file. A symlink here
// is the clobber vector and is always refused.
function isWritableTarget(realPath) {
  try {
    return !fs.lstatSync(realPath).isSymbolicLink();
  } catch (e) {
    return e.code === 'ENOENT';
  }
}

// Prepare `filePath` for a symlink-safe write: create the parent, resolve it, and
// verify the target. Returns the real path to open, or null to abort.
function prepareTarget(filePath, label) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
  const realDir = resolveSafeDir(dir, label);
  if (realDir === null) return null;
  const realPath = path.join(realDir, path.basename(filePath));
  return isWritableTarget(realPath) ? realPath : null;
}

// Open, run `write(fd)`, always close. Permissions are forced to 0600 after the
// write because the umask can widen the mode passed to open().
function withFd(targetPath, flags, write) {
  let fd;
  try {
    fd = fs.openSync(targetPath, flags, 0o600);
    write(fd);
    try { fs.fchmodSync(fd, 0o600); } catch (e) { /* best-effort on Windows */ }
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}

module.exports = { O_NOFOLLOW, debugLog, resolveSafeDir, isWritableTarget, prepareTarget, withFd };
