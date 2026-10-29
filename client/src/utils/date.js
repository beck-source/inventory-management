// Parse a plain 'YYYY-MM-DD' string as a LOCAL date. `new Date('YYYY-MM-DD')`
// is parsed as UTC midnight, which renders one day early in timezones behind
// UTC (e.g. PDT). Falls back to the default parser for other formats.
export function parseLocalDate(dateString) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(dateString))
  if (match) {
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  }
  return new Date(dateString)
}
