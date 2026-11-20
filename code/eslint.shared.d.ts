import type { Linter, Rule } from 'eslint';

export const localPlugin: {
  rules: Record<string, Rule.RuleModule>;
};

export const sharedRules: Linter.RulesRecord;
