# Agentic Rule: Avoid Premature Over-Engineering

## Rule ID: `AVOID_PREMATURE_OPTIMIZATION`

## Context
This rule was created after an AI agent over-specified a health tech product by creating comprehensive technical specifications before validating core user hypotheses. The agent jumped to enterprise-scale solutions when the user explicitly requested starting with the "smallest testable systems."

## Core Principle
**"Build the minimum viable solution that tests the core hypothesis, not the minimum viable enterprise platform."**

## Mandatory Pre-Work Checklist

Before writing ANY technical specifications or architecture documents, AI agents MUST complete this checklist:

### ✅ Hypothesis Validation First
- [ ] **Identify the ONE core hypothesis to test** (not multiple assumptions)
- [ ] **Define success/failure criteria** for the hypothesis
- [ ] **Confirm the smallest possible test** that could validate/invalidate it
- [ ] **Ask: "What's the simplest way to test this assumption?"**

### ✅ Constraint Acknowledgment
- [ ] **Explicitly state current constraints** (budget, time, team size, users)
- [ ] **Design FOR constraints, not DESPITE them**
- [ ] **Ask: "How can constraints drive creativity?"**
- [ ] **Challenge every assumption about needed complexity**

### ✅ Off-the-Shelf Priority
- [ ] **List available tools/APIs/libraries** that solve this problem
- [ ] **Default to existing solutions** unless custom is absolutely necessary
- [ ] **Ask: "What would a no-code solution look like?"**
- [ ] **Justify custom development** with clear reasoning

### ✅ Scale Reality Check
- [ ] **Define current user count** (often 1 user initially)
- [ ] **Design for 10x current users, not 1000x**
- [ ] **Ask: "What problems exist only at scale we don't have?"**
- [ ] **Postpone scalability until it's a proven problem**

## Red Flag Patterns to Avoid

### 🚫 Architecture Astronomy
- Creating microservices for <100 users
- Designing database sharding before database exists
- Planning for multi-region deployment in MVP phase
- Choosing technologies for "eventual scale"

### 🚫 Specification Paralysis
- Writing detailed specs before user validation
- Covering edge cases that may never exist
- Documenting features before confirming user need
- Creating compliance frameworks before compliance requirements

### 🚫 Technology Tourism
- Selecting new/complex tools to showcase knowledge
- Building custom solutions when SaaS alternatives exist
- Implementing enterprise patterns for startup problems
- Optimizing for problems that don't exist yet

## Forcing Functions

### The "Simplicity Challenge"
Before proposing ANY solution, complete this sentence:
*"The simplest possible way to test [hypothesis] is [solution] using [existing tool/service]."*

### The "One Week Rule"
Ask: *"Could a competent developer build and deploy this solution in one week using existing tools?"*
- If NO: Simplify further
- If YES: Proceed with proposal

### The "Manual First" Test
Ask: *"Could we test this hypothesis manually before building any software?"*
- If YES: Start there
- If NO: Question if the hypothesis is specific enough

## Implementation Guidelines

### Phase 1: Manual/No-Code Validation
- Use spreadsheets, forms, manual processes
- Leverage existing SaaS tools (Notion, Airtable, Zapier)
- Focus on user workflow, not system architecture
- Collect real data from real users (even if it's just founder)

### Phase 2: Minimal Automation
- Identify the ONE most painful manual step
- Automate only that step using existing APIs/tools
- Keep everything else manual
- Measure impact of automation

### Phase 3: Selective Custom Development
- Build custom solutions only for validated, unique value propositions
- Use managed services for everything else
- Maintain ability to pivot quickly
- Document technical debt for future resolution

## Decision Framework

When faced with technical decisions, use this priority order:

1. **Manual Process**: Can humans do this initially?
2. **Existing Tool**: Does a SaaS/API/library solve this?
3. **Simple Custom**: Can we build something basic in <1 week?
4. **Complex Custom**: Only if validated user need and no alternatives

## Example Applications

### ❌ Wrong Approach (Over-Engineering)
User: "I want to track my symptoms and get AI insights"
Agent: *Creates comprehensive microservices architecture with custom databases, security layers, compliance frameworks, and scalable AI pipeline*

### ✅ Right Approach (Hypothesis-Driven)
User: "I want to track my symptoms and get AI insights"
Agent: 
1. **Hypothesis**: "AI can provide valuable health insights from symptom descriptions"
2. **Test**: Google Form → Manual review + OpenAI API call → Email response
3. **Success Criteria**: User finds insights valuable and actionable
4. **Duration**: 1 day to set up, 1 week to test

## Enforcement Mechanisms

### Pre-Development Questions
Before writing specifications, AI agents must answer:
1. What specific hypothesis are we testing?
2. What's the manual version of this solution?
3. What existing tools could solve 80% of this problem?
4. How would we test this with 1 user before building anything?
5. What would success look like in 1 week vs 1 year?

### Code Review Checklist
- [ ] Does this solve a validated user problem?
- [ ] Is this the simplest solution that could work?
- [ ] Are we using existing tools/services where possible?
- [ ] Can we pivot/change direction easily?
- [ ] Are we optimizing for current constraints, not imagined ones?

## Success Metrics

This rule is successful when:
- Time from idea to user feedback < 1 week
- User validation happens before technical specifications
- Off-the-shelf tools are preferred over custom development
- Solutions are designed for current scale, not anticipated scale
- Pivoting/changing direction remains easy and fast

## Violation Consequences

When this rule is violated:
- Development time increases exponentially
- User feedback is delayed or absent
- Assumptions remain unvalidated
- Pivot costs become prohibitive
- Technical debt overwhelms product development

## Regular Reviews

Monthly ask:
- Are we building for real problems or imagined ones?
- What assumptions have we validated vs assumed?
- How quickly can we change direction?
- What percentage of our effort is custom vs leveraging existing tools?

---

**Remember: The goal is to learn fast, not build perfectly. Perfect solutions to wrong problems are worthless. Imperfect solutions to real problems are invaluable.**