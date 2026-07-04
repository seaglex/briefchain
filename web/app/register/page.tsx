import { Suspense } from "react";
import RegisterForm from "./RegisterForm";

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="login-page">加载中...</div>}>
      <RegisterForm />
    </Suspense>
  );
}
