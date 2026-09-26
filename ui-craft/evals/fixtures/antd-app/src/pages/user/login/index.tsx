import { LoginForm, ProFormText } from '@ant-design/pro-components';

export default function Login() {
  return (
    <LoginForm title="Harbor Admin" subTitle="Sign in to continue">
      <ProFormText name="username" placeholder="Username" rules={[{ required: true }]} />
      <ProFormText.Password name="password" placeholder="Password" rules={[{ required: true }]} />
    </LoginForm>
  );
}
