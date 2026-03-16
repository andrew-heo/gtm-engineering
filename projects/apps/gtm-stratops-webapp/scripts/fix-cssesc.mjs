import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'

const cssescPath = path.resolve('node_modules/cssesc/cssesc.js')

if (!existsSync(cssescPath)) {
  mkdirSync(path.dirname(cssescPath), { recursive: true })
  writeFileSync(
    cssescPath,
    `'use strict'

module.exports = function cssesc(value, options = {}) {
  const input = String(value)
  const isIdentifier = Boolean(options.isIdentifier)
  let output = ''

  for (let index = 0; index < input.length; index += 1) {
    const char = input[index]
    const codePoint = input.codePointAt(index)

    if (codePoint > 0xffff) {
      index += 1
    }

    const isAsciiLetter =
      (codePoint >= 0x41 && codePoint <= 0x5a) || (codePoint >= 0x61 && codePoint <= 0x7a)
    const isDigit = codePoint >= 0x30 && codePoint <= 0x39
    const isSafeIdentifierChar =
      isAsciiLetter || isDigit || char === '-' || char === '_' || codePoint >= 0x80

    if (isIdentifier) {
      const isFirst = output.length === 0
      if (
        isSafeIdentifierChar &&
        !(isFirst && isDigit) &&
        !(isFirst && char === '-' && input.length === 1)
      ) {
        output += char
        continue
      }
    } else if (char !== '\\\\' && char !== '"' && char !== "'" && codePoint >= 0x20 && codePoint <= 0x7e) {
      output += char
      continue
    }

    const hex = codePoint.toString(16).toUpperCase()
    const next = input[index + 1] || ''
    const needsTerminator = /[0-9A-Fa-f\\s]/.test(next)
    output += '\\\\' + hex + (needsTerminator ? ' ' : '')
  }

  return output
}
`,
  )
}
