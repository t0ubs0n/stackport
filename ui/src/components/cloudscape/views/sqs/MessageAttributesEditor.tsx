import AttributeEditor from '@cloudscape-design/components/attribute-editor'
import FormField from '@cloudscape-design/components/form-field'
import Input from '@cloudscape-design/components/input'
import Select from '@cloudscape-design/components/select'

export interface MessageAttributeRow {
  name: string
  dataType: string
  customType: string
  value: string
}

const TYPE_OPTIONS = ['String', 'Number', 'Binary'].map((value) => ({ label: value, value }))
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

export default function MessageAttributesEditor({
  attributes,
  onChange,
  disabled,
}: {
  attributes: MessageAttributeRow[]
  onChange: (attributes: MessageAttributeRow[]) => void
  disabled: boolean
}) {
  const update = (index: number, patch: Partial<MessageAttributeRow>) => {
    onChange(attributes.map((item, i) => i === index ? { ...item, ...patch } : item))
  }

  return (
    <FormField
      description="Optional metadata sent with the message. You can add up to 10 message attributes. Binary values are Base64-encoded."
      errorText={getMessageAttributesError(attributes)}
    >
      <AttributeEditor
        items={attributes}
        addButtonText="Add new attribute"
        removeButtonText="Remove"
        empty="No message attributes defined for this message."
        disableAddButton={disabled || attributes.length >= 10}
        onAddButtonClick={() => onChange([...attributes, { name: '', dataType: 'String', customType: '', value: '' }])}
        onRemoveButtonClick={({ detail }) => onChange(attributes.filter((_, index) => index !== detail.itemIndex))}
        definition={[
          {
            label: 'Attribute name',
            control: (item, index) => (
              <Input value={item.name} ariaLabel={`Attribute ${index + 1} name`} disabled={disabled}
                onChange={({ detail }) => update(index, { name: detail.value })} />
            ),
          },
          {
            label: 'Data type',
            control: (item, index) => (
              <Select options={TYPE_OPTIONS} selectedOption={TYPE_OPTIONS.find((option) => option.value === item.dataType)!}
                ariaLabel={`Attribute ${index + 1} data type`} disabled={disabled}
                onChange={({ detail }) => update(index, { dataType: detail.selectedOption.value! })} />
            ),
          },
          {
            label: 'Custom type - optional',
            control: (item, index) => (
              <Input value={item.customType} ariaLabel={`Attribute ${index + 1} custom type`} disabled={disabled}
                onChange={({ detail }) => update(index, { customType: detail.value })} />
            ),
          },
          {
            label: 'Value',
            control: (item, index) => (
              <Input value={item.value} ariaLabel={`Attribute ${index + 1} value`} disabled={disabled}
                placeholder={item.dataType === 'Binary' ? 'Base64-encoded value' : 'Value'}
                onChange={({ detail }) => update(index, { value: detail.value })} />
            ),
          },
        ]}
      />
    </FormField>
  )
}
