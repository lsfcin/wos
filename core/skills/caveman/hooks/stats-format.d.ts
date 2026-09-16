export function formatHistory({ sessions, outputTokens, estSavedTokens, estSavedUsd, since }: {
    sessions: any;
    outputTokens: any;
    estSavedTokens: any;
    estSavedUsd: any;
    since: any;
}): string;
export function formatShare({ outputTokens, turns, mode, model }: {
    outputTokens: any;
    turns: any;
    mode: any;
    model: any;
}): string;
export function formatStats({ outputTokens, cacheReadTokens, turns, mode, model, sessionPath, compressed }: {
    outputTokens: any;
    cacheReadTokens: any;
    turns: any;
    mode: any;
    model: any;
    sessionPath: any;
    compressed: any;
}): string;
