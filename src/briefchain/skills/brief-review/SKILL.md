---
name: brief-review
description: |
  Minimal requirement review skill. Checks whether a product requirement contains all four essential dimensions and whether each is reasonable. Triggers when the user asks to review, check, or verify a requirement's quality and completeness. Use keywords: "检查需求", "需求检查", "review要求", "检查PRD", "需求够不够清楚", or when the user pastes a requirement and asks "这个需求写得怎么样".
agent_created: true
---

# Req Check — 极简需求检查

## Purpose

Quickly check whether a product requirement is structurally complete and logically sound. Only four dimensions are checked — if all pass, the requirement is considered ready for development handoff.

## When to Use

- User says "帮我检查这个需求"
- User pastes a requirement and asks "够不够清楚" or "还缺什么"
- User wants a quick structural review before writing a full PRD

## The Four Dimensions

For each requirement, check the following four dimensions in order. Provide structured feedback: what is present, what is missing, and what is problematic.

### 1. Why — 问题陈述

**What to check:**
- Is the problem clearly stated? What user pain or business need is being addressed?
- Is the background sufficient? Can the reader understand the context without additional explanation?
- Is the "why" separated from the "what"? (Problem description should not read like a solution prescription.)

**Red flags:**
- Vague problem: "提升用户体验" without explaining what is bad about the current experience
- Solution disguised as problem: "我们需要一个弹窗" — that is already a solution
- Missing context: No mention of who experiences the problem or under what circumstances

### 2. What — 需求内容

**What to check:**
- Is the core requirement clearly described?
- Are edge cases covered? Check at minimum:
  - Empty state (first-time use, no data)
  - Error state (network failure, invalid input, timeout)
  - Boundary conditions (max/min values, large data volumes, concurrency)
  - Reverse operations (undo, delete, restore)
- Is each behavior unambiguous? No "快速", "友好", "灵活", or other non-quantifiable adjectives.

**Red flags:**
- Only happy path described
- "通常", "大概", "等" used without full enumeration
- Two developers could read the same sentence and implement different things

### 3. Goals — 目标与边界

**What to check:**
- Are goals measurable? Each goal should have a baseline and a target value.
- Are non-goals explicitly listed? At minimum 2-3 items that this requirement explicitly will NOT do.
- Do goals distinguish between user outcomes and business outcomes?

**Red flags:**
- Goals describe output, not outcome (e.g. "build a notification system" vs "reduce missed deadline rate by 30%")
- No non-goals — scope boundary is undefined, inviting scope creep
- Goals are unmeasurable (e.g. "make users happier")

### 4. Hypothesis — 核心假设

**What to check:**
- Is there an explicit hypothesis connecting the solution to the expected outcome?
- Format: "We believe that [doing X] will result in [outcome Y], and we will know this is true when [metric Z] changes."
- Is the hypothesis falsifiable? A good hypothesis can be disproven by data.

**Red flags:**
- No hypothesis at all — the requirement is based on opinion, not reasoning
- Hypothesis is untestable: "users will like it" — how do you measure "like"?
- Hypothesis conflates correlation with causation

## Output Format

After checking, output a structured summary:

```
## 需求检查结果

### 1. Why — 问题陈述
- 现状：[present / missing / needs clarification]
- 问题：[summary of findings]

### 2. What — 需求内容
- 现状：[present / missing / needs clarification]
- 边界场景：[which edge cases are covered / missing]
- 歧义：[any ambiguous terms found]

### 3. Goals — 目标与边界
- 现状：[present / missing / needs clarification]
- 非目标现状：[present / missing]
- 可衡量性：[measurable / not measurable]

### 4. Hypothesis — 核心假设
- 现状：[present / missing / needs clarification]
- 可证伪性：[falsifiable / not falsifiable]

### 结论
- 可交付：[yes / no / with fixes]
- 缺失项：[list of missing items]
- 建议：[actionable suggestions]
```

## Principles

1. Be concise — this is a minimal check, not a full PRD review
2. Each dimension is binary: present (and reasonable) or not
3. If all four are present and reasonable, the requirement passes
4. When something is missing, suggest what to add — do not write it for the user unless asked
5. Do not add extra dimensions beyond the four. Keep it minimal.
