# Prompts Library

A collection of reusable prompt templates for Claude Code. Every prompt follows the structured XML format: `<context>` → `<rule>` → `<input>` → `<output>`.

## How to use

Copy a prompt template, fill in the `<input>` section with your specific request, and paste it into Claude Code.

## Templates

| Name | Domain | File | What it does |
|---|---|---|---|
| *(no templates yet — add yours here)* | | | |

## Prompt structure

All templates follow this four-block structure:

```xml
<context>
  Background — what system, codebase, or domain is involved.
  What already exists and what the goal is.
</context>

<rule>
  Constraints and conventions Claude must follow.
  Grouped into named sections (e.g., Naming, Structure, Performance).
</rule>

<input>
  The specific request.
  Modes, variants, or examples of valid inputs.
</input>

<output>
  The exact format Claude must respond with.
  Step-by-step order, required sections, and what to omit.
</output>
```
