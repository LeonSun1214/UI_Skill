import { PageContainer } from '@ant-design/pro-components';
import { Card, Typography } from 'antd';

export default function Welcome() {
  return (
    <PageContainer>
      <Card>
        <Typography.Title level={2}>Welcome</Typography.Title>
        <Typography.Paragraph type="secondary">Orders, returns and stock, in one place.</Typography.Paragraph>
      </Card>
    </PageContainer>
  );
}
