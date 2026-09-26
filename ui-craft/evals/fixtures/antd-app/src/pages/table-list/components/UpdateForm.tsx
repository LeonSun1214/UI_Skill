import { ModalForm, ProFormText } from '@ant-design/pro-components';

export default function UpdateForm() {
  return (
    <ModalForm title="Update rule" trigger={<a>Edit</a>}>
      <ProFormText name="name" label="Name" />
    </ModalForm>
  );
}
