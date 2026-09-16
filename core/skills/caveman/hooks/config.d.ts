export const VALID_MODES: string[];
export function getConfigDir(): any;
export function getConfigPath(): any;
export function getDefaultMode(): any;
export function readFlag(flagPath: any): any;
import flagfile = require("./flagfile");
export declare let safeWriteFlag: typeof flagfile.safeWriteFlag;
export declare let appendFlag: typeof flagfile.appendFlag;
export declare let readHistory: typeof flagfile.readHistory;
