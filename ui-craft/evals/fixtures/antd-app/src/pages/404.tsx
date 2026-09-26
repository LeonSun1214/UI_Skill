import { Button, Result } from 'antd';

export default function NotFound() {
  return <Result status="404" title="404" extra={<Button type="primary" href="/">Back home</Button>} />;
}
