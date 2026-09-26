import { PageContainer } from '@ant-design/pro-components';
import { Button, Card, Table } from 'antd';

export default function Users() {
  return (
    <PageContainer extra={<Button type="primary">Invite</Button>}>
      <Card>
        <Table rowKey="id" columns={[{ title: 'Name', dataIndex: 'name' }]} dataSource={[]} />
      </Card>
    </PageContainer>
  );
}
