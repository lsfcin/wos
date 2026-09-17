// Shared ESLint rules for all TypeScript/JavaScript projects under code/ — R1-R6 style enforcement.

const singleReturnRule = {
  meta: {
    type: "suggestion",
    messages: { err: "Single return per function. Collect result in a variable or restructure with if/else." },
  },
  create(context) {
    const stack = [];
    function push() { stack.push(0); }
    function pop(node) {
      const count = stack.pop();
      if (count > 1) { context.report({ node, messageId: "err" }); }
    }
    return {
      FunctionDeclaration: push,
      "FunctionDeclaration:exit": pop,
      FunctionExpression: push,
      "FunctionExpression:exit": pop,
      ArrowFunctionExpression(node) {
        // Expression body = implicit return, no ReturnStatement — sentinel -1 skips counting.
        stack.push(node.body.type === "BlockStatement" ? 0 : -1);
      },
      "ArrowFunctionExpression:exit"(node) {
        const count = stack.pop();
        if (count > 1) { context.report({ node, messageId: "err" }); }
      },
      ReturnStatement() {
        if (stack.length > 0 && stack[stack.length - 1] >= 0) {
          stack[stack.length - 1]++;
        }
      },
    };
  },
};

function countCallsInSubtree(rootNode) {
  let count = 0;
  function walk(node) {
    if (!node || typeof node !== "object") { return; }
    const type = node.type;
    if (node !== rootNode && (type === "FunctionDeclaration" || type === "FunctionExpression" || type === "ArrowFunctionExpression")) {
      return;
    }
    if (type === "CallExpression" || type === "NewExpression") { count++; }
    for (const key of Object.keys(node)) {
      if (key === "parent") { continue; } // ESLint attaches parent refs; skip to avoid cycles.
      const child = node[key];
      if (Array.isArray(child)) {
        for (const item of child) {
          if (item && typeof item === "object" && item.type) { walk(item); }
        }
      } else if (child && typeof child === "object" && child.type) {
        walk(child);
      }
    }
  }
  walk(rootNode);
  return count;
}

const oneCallPerStatementRule = {
  meta: {
    type: "suggestion",
    messages: { err: "{{n}} calls in one statement. Extract each call to an intermediate variable." },
  },
  create(context) {
    function check(node) {
      const n = countCallsInSubtree(node);
      if (n > 1) { context.report({ node, messageId: "err", data: { n } }); }
    }
    return {
      ExpressionStatement: check,
      VariableDeclaration: check,
      ReturnStatement: check,
      ThrowStatement: check,
      IfStatement(node) {
        const n = countCallsInSubtree(node.test);
        if (n > 1) { context.report({ node: node.test, messageId: "err", data: { n } }); }
      },
      WhileStatement(node) {
        const n = countCallsInSubtree(node.test);
        if (n > 1) { context.report({ node: node.test, messageId: "err", data: { n } }); }
      },
    };
  },
};

function getChainDepth(node) {
  let depth = 0;
  let current = node;
  while (current.type === "MemberExpression") {
    depth++;
    current = current.object;
    while (current.type === "ChainExpression") { current = current.expression; }
  }
  return depth;
}

const maxChainDepthRule = {
  meta: {
    type: "suggestion",
    messages: { err: "Chain depth {{d}}: max is 2 (a.b.c). Extract a.b.c to an intermediate variable first." },
  },
  create(context) {
    return {
      MemberExpression(node) {
        const parent = node.parent;
        // Skip non-outermost nodes — parent MemberExpression will report instead.
        if (parent && parent.type === "MemberExpression" && parent.object === node) { return; }
        const depth = getChainDepth(node);
        if (depth > 2) { context.report({ node, messageId: "err", data: { d: depth } }); }
      },
    };
  },
};

export const localPlugin = {
  rules: {
    "single-return": singleReturnRule,
    "one-call-per-statement": oneCallPerStatementRule,
    "max-chain-depth": maxChainDepthRule,
  },
};

export const sharedRules = {
  "max-statements-per-line": ["error", { max: 1 }],
  "curly": ["error", "all"],
  "local/one-call-per-statement": "error",
  "local/single-return": "error",
  "@typescript-eslint/no-explicit-any": "error",
  "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
  "max-lines-per-function": ["error", { max: 40, skipBlankLines: true, skipComments: true }],
  "local/max-chain-depth": "error",
};
