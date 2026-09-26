import { PageContainer, ProTable } from '@ant-design/pro-components';
import { Button } from 'antd';
import UpdateForm from './components/UpdateForm';

export default function TableList() {
  return (
    <PageContainer>
      <ProTable rowKey="key" search={{ labelWidth: 120 }} toolBarRender={() => [<Button key="new" type="primary">New</Button>]} columns={[]} />
      <UpdateForm />
    </PageContainer>
  );
}
