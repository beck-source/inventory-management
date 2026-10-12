export function exportToCSV(data, filename, headers) {
  if (!data || data.length === 0) return

  // Build CSV header row
  const headerRow = headers.map(h => `"${h}"`).join(',')

  // Build CSV data rows
  const rows = data.map(row => {
    return headers.map(header => {
      const value = row[header]
      // Handle special cases: null, undefined, objects
      if (value === null || value === undefined) return '""'
      if (typeof value === 'object') return `"${JSON.stringify(value).replace(/"/g, '""')}"`
      // Escape quotes in strings
      return `"${String(value).replace(/"/g, '""')}"`
    }).join(',')
  })

  // Combine header and rows
  const csv = [headerRow, ...rows].join('\n')

  // Create blob and download
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}.csv`)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
