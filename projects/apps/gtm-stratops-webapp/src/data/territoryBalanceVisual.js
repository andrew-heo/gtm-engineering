const beforeCounts = {
  AM_1: 28,
  AM_10: 26,
  AM_2: 30,
  AM_3: 25,
  AM_4: 27,
  AM_5: 28,
  AM_6: 29,
  AM_7: 29,
  AM_8: 25,
  AM_9: 26,
}

const afterCounts = {
  AM_1: 28,
  AM_10: 28,
  AM_2: 28,
  AM_3: 27,
  AM_4: 27,
  AM_5: 27,
  AM_6: 27,
  AM_7: 27,
  AM_8: 27,
  AM_9: 27,
}

const owners = Object.keys(beforeCounts)

export const territoryBalanceVisual = {
  summary: [
    { label: 'Before range', value: '5 accounts' },
    { label: 'After range', value: '1 account' },
    { label: 'MRR range', value: '-53%' },
    { label: 'Q1 skew', value: '-88%' },
  ],
  before: owners.map((owner) => ({
    owner,
    accounts: beforeCounts[owner],
    delta: afterCounts[owner] - beforeCounts[owner],
  })),
  after: owners.map((owner) => ({
    owner,
    accounts: afterCounts[owner],
    delta: afterCounts[owner] - beforeCounts[owner],
  })),
}
