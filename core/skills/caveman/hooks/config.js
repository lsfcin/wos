// caveman — shared configuration resolver, and the façade the hooks import
//
// Resolution order for the default mode:
//   1. CAVEMAN_DEFAULT_MODE environment variable
//   2. Config file `defaultMode` field:
//      - $XDG_CONFIG_HOME/caveman/config.json (any platform, if set)
//      - ~/.config/caveman/config.json (macOS / Linux fallback)
//      - %APPDATA%\caveman\config.json (Windows fallback)
//   3. 'full'
//
// Flag-file I/O lives in flagfile.js (over safepath.js) and is re-exported here,
// so every hook keeps importing exactly one module: `require('./config')`.

const fs = require('fs');
const path = require('path');
const os = require('os');
const flagfile = require('./flagfile');

const VALID_MODES = [
  'off', 'lite', 'full', 'ultra',
  'wenyan-lite', 'wenyan', 'wenyan-full', 'wenyan-ultra',
  'commit', 'review', 'compress'
];

function getConfigDir() {
  if (process.env.XDG_CONFIG_HOME) {
    return path.join(process.env.XDG_CONFIG_HOME, 'caveman');
  }
  if (process.platform === 'win32') {
    return path.join(
      process.env.APPDATA || path.join(os.homedir(), 'AppData', 'Roaming'),
      'caveman'
    );
  }
  return path.join(os.homedir(), '.config', 'caveman');
}

function getConfigPath() {
  return path.join(getConfigDir(), 'config.json');
}

// Is the workspace's `caveman` feature switched on? Asked of core/hooks/feature_law.py rather
// than answered here, because the registry and the profile are the one home for that answer and a
// second reader of them is the drift the law modules exist to prevent.
//
// Fail-OPEN by construction: this hook is registered globally and runs in sessions that are not
// inside the workspace at all, where the law is simply absent. Absent law means unchanged
// behaviour, never a dead hook.
//
// THE INTERPRETER IS ASKED, NEVER SPELLED. This spawned the bare word `python3` until 2026-09-06,
// which on a Windows clone reaches the Microsoft Store alias: it prints an advert and exits 9009,
// so `status === 1` was false and the feature read as ON no matter what the profile said. Caveman
// could not be switched off through the registry on the one platform the bug lived on — and the
// fail-open design is what hid it, because failing open is also what a healthy absent law looks
// like. `core/run --python` prints this clone's venv interpreter (the platform boundary); an empty
// answer means no venv, which is the absent-law case and stays open.
//
// The law is NOT run through `core/run` directly: that launcher exits 1 when it cannot find an
// interpreter, the same status `--enabled` uses for "switched off", and a half-installed clone
// would silently read as a deliberate shutdown.
function featureOff() {
  try {
    const law = path.join(__dirname, '..', '..', '..', 'hooks', 'feature_law.py');
    if (!fs.existsSync(law)) return false;
    const run = path.join(__dirname, '..', '..', '..', 'run');
    const spawnSync = require('child_process').spawnSync;
    const found = spawnSync('sh', [run, '--python'], { encoding: 'utf8' });
    if (found.status !== 0) return false;
    const python = (found.stdout || '').trim();
    if (!python) return false;
    return spawnSync(python, [law, '--enabled', 'caveman']).status === 1;
  } catch (e) {
    return false;
  }
}

function getDefaultMode() {
  // 0. The workspace switch. Returning 'off' is the whole wiring: every caveman hook already
  //    handles that mode, so the feature goes dark through the path it already had.
  if (featureOff()) return 'off';

  // 1. Environment variable (highest priority)
  const envMode = process.env.CAVEMAN_DEFAULT_MODE;
  if (envMode && VALID_MODES.includes(envMode.toLowerCase())) {
    return envMode.toLowerCase();
  }

  // 2. Config file
  try {
    const config = JSON.parse(fs.readFileSync(getConfigPath(), 'utf8'));
    if (config.defaultMode && VALID_MODES.includes(config.defaultMode.toLowerCase())) {
      return config.defaultMode.toLowerCase();
    }
  } catch (e) {
    // Config file doesn't exist or is invalid — fall through
  }

  // 3. Default
  return 'full';
}

// The mode whitelist is policy and lives here, so flagfile.js takes it as an
// argument rather than importing back the other way.
function readFlag(flagPath) {
  return flagfile.readFlag(flagPath, VALID_MODES);
}

module.exports = {
  VALID_MODES,
  getConfigDir,
  getConfigPath,
  getDefaultMode,
  readFlag,
  safeWriteFlag: flagfile.safeWriteFlag,
  appendFlag: flagfile.appendFlag,
  readHistory: flagfile.readHistory
};
