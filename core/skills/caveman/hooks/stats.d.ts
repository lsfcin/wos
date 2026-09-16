#!/usr/bin/env node
declare const _exports: {
    formatHistory({ sessions, outputTokens, estSavedTokens, estSavedUsd, since }: {
        sessions: any;
        outputTokens: any;
        estSavedTokens: any;
        estSavedUsd: any;
        since: any;
    }): string;
    formatShare({ outputTokens, turns, mode, model }: {
        outputTokens: any;
        turns: any;
        mode: any;
        model: any;
    }): string;
    formatStats({ outputTokens, cacheReadTokens, turns, mode, model, sessionPath, compressed }: {
        outputTokens: any;
        cacheReadTokens: any;
        turns: any;
        mode: any;
        model: any;
        sessionPath: any;
        compressed: any;
    }): string;
    findRecentSession(claudeDir: any): any;
    parseSession(filePath: any): {
        outputTokens: number;
        cacheReadTokens: number;
        turns: number;
        model: any;
    };
    findCompressedPairs(dirs: any): {
        name: any;
        dir: any;
        originalSize: any;
        compressedSize: any;
    }[];
    summarizeCompressed(pairs: any): {
        count: any;
        bytesSaved: number;
        tokensSaved: number;
    } | null;
    aggregateHistory(historyPath: any, sinceMs: any): {
        sessions: number;
        outputTokens: number;
        estSavedTokens: number;
        estSavedUsd: number;
    };
    priceForModel(model: any): string | number | null;
    formatUsd(amount: any): string;
    deriveSavings({ outputTokens, mode, model }: {
        outputTokens: any;
        mode: any;
        model: any;
    }): {
        ratio: null;
        price: string | number | null;
        estNormal: null;
        estSavedTokens: number;
        estSavedUsd: number;
    } | {
        ratio: any;
        price: string | number | null;
        estNormal: number;
        estSavedTokens: number;
        estSavedUsd: number;
    };
    parseDuration(spec: any): number | null;
    humanizeTokens(n: any): string;
    COMPRESSION: typeof import("./stats-pricing").COMPRESSION;
    MODEL_OUTPUT_PRICE_PER_M: (string | number)[][];
};
export = _exports;
