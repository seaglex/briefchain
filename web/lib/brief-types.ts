export type BriefType = "idea" | "epic" | "feature" | "story";

export const BRIEF_TYPE_LABELS: Record<BriefType, string> = {
  idea: "Idea",
  epic: "Epic",
  feature: "Feature",
  story: "Story",
};

export const BRIEF_TYPE_OPTIONS: { value: BriefType; label: string }[] = [
  { value: "idea", label: "Idea" },
  { value: "epic", label: "Epic" },
  { value: "feature", label: "Feature" },
  { value: "story", label: "Story" },
];
