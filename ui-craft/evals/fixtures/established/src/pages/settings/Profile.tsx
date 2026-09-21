import { useState } from "react";
import { PageHeader } from "../../components/PageHeader";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Field } from "../../components/ui/Field";

export function ProfileSettings() {
  const [name, setName] = useState("林晓");
  const [email, setEmail] = useState("lin@maplebooks.app");
  const [saved, setSaved] = useState(false);

  return (
    <>
      <PageHeader title="个人资料" description="这些信息会显示在你开出的发票上。" />
      <form
        className="flex flex-col gap-6"
        onSubmit={(event) => {
          event.preventDefault();
          setSaved(true);
          window.setTimeout(() => setSaved(false), 2500);
        }}
      >
        <Card title="基本信息">
          <div className="flex flex-col gap-5">
            <Field
              id="name"
              label="姓名"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
              helper="将作为发票上的开票人。"
            />
            <Field
              id="email"
              label="邮箱"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>
        </Card>
        <div className="flex items-center gap-4">
          <Button type="submit">保存更改</Button>
          <p role="status" aria-live="polite" className="text-sm text-success">
            {saved ? "已保存" : ""}
          </p>
        </div>
      </form>
    </>
  );
}
