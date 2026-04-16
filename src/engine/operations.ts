export type OperationFn = (input: unknown[]) => unknown[];

export const OPERATIONS: Record<string, OperationFn> = {
  source: (_) => ['1\n2\n3\n4\n5'],
  lines: (input) => (input[0] as string).split('\n').filter(Boolean),
  'map(parse_int)': (input) => input.map((x) => parseInt(x as string, 10)),
  sum: (input) => [input.reduce((a, b) => (a as number) + (b as number), 0)],
};
