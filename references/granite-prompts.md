# Granite 4.1 prompts — copy-paste, Ollama-ready

Granite 4.1 8B is a non-thinking, instruction-following, structured-output model.
Prompt it the opposite of how you prompt Claude: no open reasoning, one task,
a strict output contract, an example, temperature 0. Don't ask it to "think
through" — ask it to emit a shape. These are the runtime prompts the SMB pipeline
embeds when it routes to Granite; paste them into `ollama run` first to validate.

Run all at temperature 0: `ollama run granite4.1:8b --temperature 0` or set
`"options": {"temperature": 0}` on the API call.

---

## PROMPT 1 — Stale-memory compression (the leg itself)

System:
```
You compress stale agent memory into a durable summary. You preserve only
reusable procedures, constraints, and decisions. You drop greetings, chit-chat,
one-off context, and anything not reusable. You never invent facts. You output
ONLY the summary in the exact template. No preamble. Hard cap: 120 tokens.
```
User:
```
TEMPLATE (fill, keep headers, omit a section if empty):
PROCEDURES:
- <imperative step>
CONSTRAINTS:
- <rule that must always hold>
DECISIONS:
- <choice made and the reason>

MEMORY TO COMPRESS:
<<<
{stale_memory_text}
>>>
```

## PROMPT 2 — Skill description generator (~100-token, keyword-routed)

System:
```
You write the `description` field for an agentskills.io SKILL.md. It must state
WHAT the skill does and WHEN to use it, packed with trigger keywords a router
will match. 1 to 3 sentences. Plain text only, no markdown, no quotes, no
preamble. 60 to 100 tokens. Start with a verb.
```
User:
```
SKILL BODY:
<<<
{skill_body_markdown}
>>>
Write the description now.
```

## PROMPT 3 — Distillation pre-pass → strict JSON

Cheap local pre-extraction before (optional) Opus distillation. Granite 4.1 does
structured JSON well; enforce the schema and reject prose.

System:
```
You extract reusable knowledge from a conversation into JSON. Output ONLY valid
JSON matching the schema. No markdown fences, no commentary. Use [] for empty
arrays. Do not invent content not present in the text.
```
User:
```
SCHEMA:
{
  "entities": [string],
  "procedures": [string],   // imperative steps, durable only
  "constraints": [string],  // rules that must always hold
  "evidence": [string],     // short verbatim-ish support snippets
  "causal": [string],       // "X because Y" durable cause links
  "abstract": string        // one sentence, <= 20 words
}

CONVERSATION:
<<<
{conversation_text}
>>>
```

---

## Ollama test harness

Quick CLI sanity check:
```
ollama run granite4.1:8b "Reply with the single word: ready"
```

API call (what the pipeline uses — no key, local only):
```
curl http://localhost:11434/api/chat -d '{
  "model": "granite4.1:8b",
  "stream": false,
  "options": {"temperature": 0},
  "messages": [
    {"role": "system", "content": "Reply with valid JSON only."},
    {"role": "user", "content": "Return {\"ok\": true}"}
  ]
}'
```

Fallback under memory pressure — swap one string:
```
"model": "granite4.1:3b"
```

## Why temperature 0 + strict template matters here

The eval needs the *same input* to produce a *stable* before/after. A
non-deterministic compressor poisons the delta. Temperature 0 + a fixed template
makes Granite's leg reproducible, which is exactly what the Lane 2 before/after
metric and the ADLC "observe" loop require.
