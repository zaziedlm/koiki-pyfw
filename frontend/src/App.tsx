import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Home from "@/app/page";
import LoginPage from "@/app/auth/login/page";
import RegisterPage from "@/app/auth/register/page";
import SamlCallbackPage from "@/app/auth/saml/callback/page";
import DashboardPage from "@/app/dashboard/page";
import TasksPage from "@/app/dashboard/tasks/page";
import SsoCallbackPage from "@/app/sso/callback/page";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/auth/login" element={<LoginPage />} />
        <Route path="/auth/register" element={<RegisterPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/dashboard/tasks" element={<TasksPage />} />
        <Route path="/sso/callback" element={<SsoCallbackPage />} />
        <Route path="/auth/saml/callback" element={<SamlCallbackPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
