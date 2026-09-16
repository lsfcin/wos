export function findRecentSession(claudeDir: any): any;
export function parseSession(filePath: any): {
    outputTokens: number;
    cacheReadTokens: number;
    turns: number;
    model: any;
};
export function findCompressedPairs(dirs: any): {
    name: any;
    dir: any;
    originalSize: any;
    compressedSize: any;
}[];
export function summarizeCompressed(pairs: any): {
    count: any;
    bytesSaved: number;
    tokensSaved: number;
} | null;
export function aggregateHistory(historyPath: any, sinceMs: any): {
    sessions: number;
    outputTokens: number;
    estSavedTokens: number;
    estSavedUsd: number;
};
