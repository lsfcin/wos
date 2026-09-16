export function python(): any;
/**
 * @param {Record<string, any>} args opencode tool args
 * @param {string} toolName opencode tool name
 * @returns {Array<Record<string, any>>}
 */
export function buildPayloads(args: Record<string, any>, toolName: string): Array<Record<string, any>>;
/**
 * @param {Record<string, any>} args opencode grep args
 * @returns {Record<string, any> | null}
 */
export function buildGrepPayload(args: Record<string, any>): Record<string, any> | null;
/**
 * @param {string} script absolute path to the hook script
 * @param {Record<string, any>} payload Claude-shape hook payload
 * @param {string} canonical value for the CLAUDE_TOOL_NAME env var
 * @param {{stdin?: boolean}} [opts] stdin true = pre-hook (stdin JSON), false = post-hook (env JSON)
 * @returns {import("node:child_process").SpawnSyncReturns<string>}
 */
export function run(script: string, payload: Record<string, any>, canonical: string, { stdin }?: {
    stdin?: boolean;
}): any;
export function warn(client: any, msg: any): Promise<void>;
export const WORKSPACE: any;
export const HOOKS: string;
export const SESSION_ID: string;
export namespace TOOL_MAP {
    namespace read {
        let canonical: string;
        let group: string;
    }
    namespace edit {
        let canonical_1: string;
        export { canonical_1 as canonical };
        let group_1: string;
        export { group_1 as group };
    }
    namespace write {
        let canonical_2: string;
        export { canonical_2 as canonical };
        let group_2: string;
        export { group_2 as group };
    }
    namespace apply_patch {
        let canonical_3: string;
        export { canonical_3 as canonical };
        let group_3: string;
        export { group_3 as group };
    }
}
