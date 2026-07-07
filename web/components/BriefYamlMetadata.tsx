import { isoToLocalDate } from "@/lib/date";

interface BriefYamlMetadataProps {
  title: string;
  priority: string;
  estimated_man_days: number | null;
  expected_completion_at: string | null;
}

export default function BriefYamlMetadata({
  title,
  priority,
  estimated_man_days,
  expected_completion_at,
}: BriefYamlMetadataProps) {
  const lines: string[] = [];
  lines.push(`title: "${title.replace(/"/g, '\\"')}"`);
  lines.push(`priority: ${priority}`);
  lines.push(
    `estimated_man_days: ${estimated_man_days !== null ? estimated_man_days : ""}`
  );
  lines.push(
    `expected_completion_at: ${expected_completion_at ? `"${isoToLocalDate(expected_completion_at)}"` : ""}`
  );

  return (
    <div className="yaml-metadata">
      <pre className="yaml-metadata-code">{lines.join("\n")}</pre>
    </div>
  );
}
