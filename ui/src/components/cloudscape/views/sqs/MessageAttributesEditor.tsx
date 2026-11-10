import AttributeEditor from '@cloudscape-design/components/attribute-editor'
import FormField from '@cloudscape-design/components/form-field'
import Input from '@cloudscape-design/components/input'
import Select from '@cloudscape-design/components/select'
import { getMessageAttributesError, type MessageAttributeRow } from './message-attributes'

const TYPE_OPTIONS = ['String', 'Number', 'Binary'].map((value) => ({ label: value, value }))

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
