export interface MessageAttributeRow {
  name: string
  dataType: string
  customType: string
  value: string
}

const NUMBER_PATTERN = /^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$/
const BASE64_PATTERN = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/

export function getMessageAttributesError(attributes: MessageAttributeRow[]): string | undefined {
  if (attributes.length > 10) return 'You can add up to 10 message attributes.'
  const names = new Set<string>()
  for (const [index, attr] of attributes.entries()) {
    const prefix = `Attribute ${index + 1}: `
    if (!/^[a-zA-Z0-9_.-]{1,256}$/.test(attr.name)
      || /^(aws|amazon)\./i.test(attr.name)
      || attr.name.startsWith('.') || attr.name.endsWith('.') || attr.name.includes('..')) {
      return `${prefix}use a name of 1-256 letters, numbers, underscores, hyphens or periods; no AWS./Amazon. prefix, leading/trailing period or consecutive periods.`
    }
    if (names.has(attr.name)) return `${prefix}attribute names must be unique.`
    names.add(attr.name)
    if (attr.dataType.length + (attr.customType ? attr.customType.length + 1 : 0) > 256) {
      return `${prefix}data type including the custom type must not exceed 256 characters.`
    }
    if (!attr.value) return `${prefix}a value is required.`
    if (attr.dataType === 'Number' && !NUMBER_PATTERN.test(attr.value)) return `${prefix}enter a valid number.`
    if (attr.dataType === 'Binary' && !BASE64_PATTERN.test(attr.value)) return `${prefix}enter valid Base64, including padding when required.`
  }
}
