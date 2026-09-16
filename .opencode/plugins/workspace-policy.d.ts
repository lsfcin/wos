export function WorkspacePolicy({ client }: {
    client: any;
}): Promise<{
    "tool.execute.before"?: undefined;
    "tool.execute.after"?: undefined;
    "experimental.session.compacting"?: undefined;
} | {
    "tool.execute.before": (input: any, output: any) => Promise<void>;
    "tool.execute.after": (input: any, output: any) => Promise<void>;
    "experimental.session.compacting": () => Promise<void>;
}>;
