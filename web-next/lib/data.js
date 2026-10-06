// Single source of truth for v1. Later generated from postgres.
export const callers = [
  { handle: 'pumporacle', chains: ['solana'], rank: 'I', calls: 41, green: 3, red: 38, avg: -93,
    seal: 'CONDEMNED', kind: 'guilty',
    verdict: "Calls like he's paid per post. 38 of 41 picks rugged, worst was $DUMP at −99.8% in four hours. Nothing green in three months.",
    worst: { coin: '$DUMP', then: '$0.041', now: '$0.00008', ret: '−99.8%', good: false },
    log: [['$DUMP · oct 1', '−99.8%', false], ['$RUGPOT · sep 28', '−97%', false], ['$MOONBAG · sep 21', '+34%', true]] },
  { handle: 'Cryptoceleb1', chains: ['solana'], rank: 'II', calls: 23, green: 4, red: 19, avg: -81,
    seal: 'CONDEMNED', kind: 'guilty', since: 'JUL 2026',
    verdict: 'Promoted $SUNUSI twice — once on the way up, once on the way down. Only green call in four months was a lucky bounce. Verdict: fade everything.',
    worst: { coin: '$SUNUSI', then: '$3.7M mcap', now: '$32k', ret: '−99%', good: false },
    log: [['$SUNUSI · jul 13', '−99%', false], ['$TIWICAT · jun 30', '−100%', false], ['$BODYSCAN · jul 02', '−98%', false], ['$1000PDF · aug 11', '−79%', false], ['$PredictAI · aug 09', '−93%', false], ['$GTAN · aug 02', '+18%', true]] },
  { handle: 'solanashillz', chains: ['solana'], rank: 'III', calls: 27, green: 6, red: 21, avg: -64,
    seal: 'CONDEMNED', kind: 'guilty',
    verdict: 'Volume shiller — 27 calls and almost nothing survived. Follows whatever is already pumping and calls the top with eerie consistency.',
    worst: { coin: '$RUGPOT', then: '$1.1M mcap', now: '$30k', ret: '−97%', good: false },
    log: [['$RUGPOT · sep 25', '−97%', false], ['$FADEME · sep 12', '−91%', false]] },
  { handle: 'Tally__DE', chains: ['solana'], rank: 'IV', calls: 18, green: 11, red: 7, avg: 62,
    seal: 'UNDECIDED', kind: 'clean',
    verdict: "Solid more often than not, but the reds are violent — when wrong, spectacularly wrong. Size down and you'll survive following.",
    worst: { coin: '$DIP', then: '$0.9M mcap', now: '$0.1M', ret: '−88%', good: false },
    log: [['$ORBIT · sep 15', '+410%', true], ['$DIP · sep 09', '−88%', false]] },
  { handle: 'chartdruid', chains: ['solana'], rank: 'V', calls: 12, green: 9, red: 3, avg: 88,
    seal: 'VINDICATED', kind: 'clean',
    verdict: 'Patient entries, posted exits, small reds. The quietest good record on the board.',
    worst: { coin: '$LOOM', then: '$0.3M mcap', now: '$1.2M', ret: '+290%', good: true },
    log: [['$LOOM · sep 20', '+290%', true], ['$SLIP · sep 05', '−41%', false]] },
  { handle: 'degenreck', chains: ['solana'], rank: 'VI', calls: 31, green: 22, red: 9, avg: 140,
    seal: 'VINDICATED', kind: 'clean',
    verdict: 'The one to watch. 22 of 31 green, calls early, exits posted. $VAULT at +620% is the best tracked call on the board.',
    worst: { coin: '$VAULT', then: '$0.2M mcap', now: '$1.4M', ret: '+620%', good: true },
    log: [['$VAULT · sep 18', '+620%', true], ['$FALL · sep 02', '−52%', false]] },
  { handle: 'hoodtrenches', chains: ['robinhood'], rank: 'VII', calls: 9, green: 6, red: 3, avg: 74,
    seal: 'UNDECIDED', kind: 'clean',
    verdict: 'Early on the Robinhood field — small sample, mostly green, watching to see if it holds as more callers arrive.',
    worst: { coin: '$ROBINHOOD', then: '$0.4M mcap', now: '$1.4M', ret: '+250%', good: true },
    log: [['$ROBINHOOD · sep 28', '+250%', true], ['$ARBOR · sep 30', '−38%', false]] },
];

export const coins = {
  SUNUSI: {
    coin: '$SUNUSI', mint: '2vvw...VWpump', chain: 'SOLANA',
    dead: true, delta: '−99%', peak: '$3.7M', now: '$32k',
    touchers: [
      { handle: 'Cryptoceleb1', note: 'called jul 13, near the very top', timing: 'CALLED TOP', top: true },
      { handle: 'solanashillz', note: 'called jul 14, on the way down', timing: 'CALLED TOP', top: true },
      { handle: 'pumporacle', note: 'called jul 12, just before peak', timing: 'CALLED TOP', top: true },
    ],
    note: "Three tracked callers, three tops called. Nobody on record touched $SUNUSI at the bottom — because nobody credible ever does.",
  },
};

export const X_URL = 'https://x.com/Urdheim';

export const fmtAvg = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v) + '%';
