"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/auth";
import type {
  KanbanColumnConfig,
  KanbanConfig,
  KanbanConfigResponse,
  KanbanTemplateDetailResponse,
  KanbanTemplateListItem,
} from "@/lib/kanban";

interface KanbanConfigFormProps {
  initialConfig: KanbanConfigResponse;
  initialTemplates: KanbanTemplateListItem[];
}

export default function KanbanConfigForm({
  initialConfig,
  initialTemplates,
}: KanbanConfigFormProps) {
  const router = useRouter();
  const [config, setConfig] = useState<KanbanConfig>(initialConfig.kanban);
  const [columns, setColumns] = useState<KanbanColumnConfig[]>(initialConfig.columns);
  const [templates] = useState<KanbanTemplateListItem[]>(initialTemplates);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number>(
    initialConfig.kanban.kanban_template_id
  );
  const [group, setGroup] = useState(initialConfig.kanban.group);
  const [doneVisibleDays, setDoneVisibleDays] = useState(
    initialConfig.kanban.done_visible_days
  );
  const [isPublic, setIsPublic] = useState(false);
  const [templateName, setTemplateName] = useState("");
  const [isColumnsModified, setIsColumnsModified] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateColumn(index: number, patch: Partial<KanbanColumnConfig>) {
    setColumns((prev) =>
      prev.map((col, i) => (i === index ? { ...col, ...patch } : col))
    );
    setIsColumnsModified(true);
  }

  async function handleTemplateChange(templateId: number) {
    setSelectedTemplateId(templateId);
    const result = await apiFetch<KanbanTemplateDetailResponse>(
      `/api/kanban-templates/${templateId}`
    );
    if (result.ok) {
      setColumns(result.data.columns);
      setIsColumnsModified(false);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);

    const configResult = await apiFetch(`/api/kanbans/${config.kanban_id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: config.name,
        kanban_template_id: selectedTemplateId,
        group,
        done_visible_days: doneVisibleDays,
      }),
    });

    if (!configResult.ok) {
      setSaving(false);
      setError(configResult.message);
      return;
    }

    if (isColumnsModified) {
        const columnsResult = await apiFetch(`/api/kanbans/${config.kanban_id}/columns`, {
          method: "PUT",
          body: JSON.stringify({
            name: isPublic ? templateName : "",
            kanban_template_mode: "simple",
            is_public: isPublic ? true : false,
            columns: columns.map((col) => ({
              column_id: col.column_id,
              status_key: col.status_key,
              name: col.name,
              color: col.color,
              is_hidden: col.is_hidden,
              position: col.position,
            })),
          }),
        });
        if (!columnsResult.ok) {
          setError(columnsResult.message);
          return;
        }
    }

    setSaving(false);

    router.push("/kanban");
  }

  return (
    <div className="card" style={{ maxWidth: 720 }}>
      {error && <div className="error-message mb-16">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">看板名称</label>
          <input
            value={config.name}
            onChange={(e) => setConfig((c) => ({ ...c, name: e.target.value }))}
            disabled={saving}
          />
        </div>

        <div className="form-group">
          <label className="form-label">
            模板
            {isColumnsModified && (
              <span className="text-3 ml-8">（正在修改）</span>
            )}
          </label>
          <select
            value={String(selectedTemplateId)}
            onChange={(e) => handleTemplateChange(parseInt(e.target.value, 10))}
            disabled={saving}
          >
            {templates.map((t) => (
              <option
                key={t.kanban_template_id}
                value={String(t.kanban_template_id)}
              >
                {t.name || "private"}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">泳道分组</label>
          <select value={group} onChange={(e) => setGroup(e.target.value as typeof group)} disabled={saving}>
            <option value="none">无</option>
            <option value="assignee">执行人</option>
            <option value="priority">优先级</option>
            <option value="brief">Brief</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">done 显示天数</label>
          <input
            type="number"
            min={1}
            value={doneVisibleDays}
            onChange={(e) => setDoneVisibleDays(parseInt(e.target.value, 10))}
            disabled={saving}
          />
        </div>

        <div className="form-group">
          <label className="form-label">列配置</label>
          <div className="kanban-config-columns">
            <div className="kanban-config-column kanban-config-column-header">
              <span className="text-3">名称</span>
              <span className="text-3">颜色</span>
              <span className="text-3">状态</span>
              <span className="text-3">Hidden</span>
            </div>
            {columns.map((col, index) => (
              <div key={col.column_id ?? col.status_key} className="kanban-config-column">
                <input
                  type="text"
                  value={col.name}
                  onChange={(e) => updateColumn(index, { name: e.target.value })}
                  disabled={saving}
                />
                <input
                  type="color"
                  value={col.color || "#cccccc"}
                  onChange={(e) => updateColumn(index, { color: e.target.value })}
                  disabled={saving}
                />
                <span className="text-3">{col.status_key}</span>
                <input
                  type="checkbox"
                  checked={col.is_hidden}
                  onChange={(e) => updateColumn(index, { is_hidden: e.target.checked })}
                  disabled={saving}
                />
              </div>
            ))}
          </div>
        </div>

        {isColumnsModified && (
          <div className="form-group flex" style={{ flexDirection: "column", gap: 8 }}>
            <label className="flex items-center cursor-pointer" style={{ gap: 8 }}>
              <input
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={saving}
                style={{ width: "auto" }}
              />
              <span> 保存为公开模板</span>
            </label>
            {isPublic && (
              <input
                type="text"
                placeholder="模板名称"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
                disabled={saving}
              />
            )}
          </div>
        )}

        <div className="flex gap-8">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "保存中..." : "保存"}
          </button>
          <button type="button" className="btn" onClick={() => router.push("/kanban")} disabled={saving}>
            取消
          </button>
        </div>
      </form>
    </div>
  );
}
