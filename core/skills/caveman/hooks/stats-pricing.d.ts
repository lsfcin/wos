export namespace COMPRESSION {
    let full: number;
}
export const MODEL_OUTPUT_PRICE_PER_M: (string | number)[][];
export function priceForModel(model: any): string | number | null;
export function formatUsd(amount: any): string;
export function deriveSavings({ outputTokens, mode, model }: {
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
export function parseDuration(spec: any): number | null;
export function humanizeTokens(n: any): string;
