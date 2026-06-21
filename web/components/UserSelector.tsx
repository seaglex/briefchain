"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/auth";

interface User {
  id: string;
  name: string;
}

interface UserSelectorProps {
  selectedUserId: string | null;
  onSelect: (userId: string) => void;
}

export default function UserSelector({ selectedUserId, onSelect }: UserSelectorProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadUsers() {
      const result = await apiFetch<{ items: User[] }>("/api/users");
      setLoading(false);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      setUsers(result.data.items || []);
    }
    loadUsers();
  }, []);

  if (loading) {
    return <div className="text-3">加载用户中...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (users.length === 0) {
    return <div className="text-3">暂无可选用户</div>;
  }

  return (
    <div className="user-list">
      {users.map((user) => (
        <div
          key={user.id}
          className={`user-list-item ${selectedUserId === user.id ? "selected" : ""}`}
          onClick={() => onSelect(user.id)}
        >
          {user.name}
        </div>
      ))}
    </div>
  );
}
