import {
  businessPriceLabel,
  teamPriceLabel,
} from "@/lib/public-pricing";

/**
 * A diagram rendered inside a content section.
 *
 * Dimensions are required. The static export runs with
 * `images.unoptimized: true`, so the browser gets a plain <img>; without an
 * intrinsic aspect ratio every diagram causes a layout shift, which is both a
 * Core Web Vitals (CLS) penalty and a genuinely worse reading experience.
 *
 * `srcSmall` is a half-width WebP used below 900px so mobile does not download
 * a 1376px asset.
 */
export type SectionFigure = {
  src: string;
  srcSmall?: string;
  alt: string;
  caption: string;
  width: number;
  height: number;
};

export type ContentSection = {
  heading: string;
  body: string[];
  points?: string[];
  figure?: SectionFigure;
};

export type Faq = {
  question: string;
  answer: string;
};

export type Source = {
  label: string;
  url: string;
};

export type SeoPage = {
  slug: string;
  title: string;
  description: string;
  eyebrow: string;
  heading: string;
  lead: string;
  keywords: string[];
  sections: ContentSection[];
  faqs: Faq[];
  related: string[];
  sources?: Source[];
  lastVerified?: string;
  lastUpdated?: string;
  noindex?: boolean;
  /** Overrides the default social card for pages with their own artwork. */
  ogImage?: string;
  /** Lead illustration rendered directly beneath the page hero. */
  heroFigure?: SectionFigure;
};

const DIAGRAM_WIDTH = 1376;
const DIAGRAM_HEIGHT = 736;

function diagram(
  name: string,
  alt: string,
  caption: string,
): SectionFigure {
  return {
    src: `/images/${name}.webp`,
    srcSmall: `/images/${name}-sm.webp`,
    alt,
    caption,
    width: DIAGRAM_WIDTH,
    height: DIAGRAM_HEIGHT,
  };
}

export const seoPages: SeoPage[] = [
  {
    slug: "architecture",
    title: "Adaptive Spatial Intelligence: The Layer8 Control Architecture",
    description:
      "How Layer8, SALTI, and B-HDSR combine into one closed-loop control architecture that turns generative output into validated, repairable, auditable infrastructure.",
    eyebrow: "Control architecture",
    heading: "From generative guesses to living, validated infrastructure.",
    lead:
      "Most AI systems are open loops: a model generates, the same model approves its own work, and the output ships. This page walks through the alternative — a closed-loop architecture that separates exploration, validation, repair, and human review into distinct, inspectable stages, and explains what each layer is actually responsible for.",
    keywords: [
      "adaptive spatial intelligence",
      "closed-loop AI architecture",
      "AI validation and repair",
      "governed adaptability",
      "multi-agent workflow architecture",
      "AI control plane architecture",
      "B-HDSR",
      "SALTI engine",
    ],
    lastUpdated: "July 29, 2026",
    ogImage: "/images/og/salti8-architecture.png",
    heroFigure: diagram(
      "salti8-adaptive-spatial-intelligence",
      "Split illustration: a grey wireframe engineering drawing on the left transitions into a luminous, layered terrain of flowing teal and amber channels on the right, representing the shift from static generative output to living validated infrastructure.",
      "Adaptive spatial intelligence — from generative guesses to living, validated infrastructure",
    ),
    sections: [
      {
        heading: "The problem: open-loop generation cannot be trusted",
        body: [
          "In an open-loop system, input goes to a generator and the generator's output goes straight to production. There is no independent check between the two. When the model is right, nothing is wasted. When it is wrong, the failure is silent — the output looks structurally plausible, passes casual review, and only surfaces as a defect much later, usually in front of a user or an auditor.",
          "The fix is not a better prompt or a larger model. It is architectural. A closed loop separates the act of generating from the act of accepting, and gives each stage its own failure behaviour: exploration produces candidates, validation tests them against independent criteria, and repair is routed by the specific reason validation failed rather than by a blind retry.",
          "Systems built this way are deliberately incomplete, uncertain, modular, degradable, and repairable. Those are not weaknesses to engineer away — they are the properties that let a system survive contact with real inputs.",
        ],
        points: [
          "Generation is a step, not a verdict",
          "Validation is independent of the model that generated the work",
          "Repair is reason-coded and bounded, never an unbounded retry loop",
          "Human review is a routed outcome, not an afterthought",
        ],
        figure: diagram(
          "salti8-governed-adaptability-loop",
          "Diagram comparing an open-loop pipeline — input to generator to output, ending in a failure state — with a closed-loop architecture in which exploration feeds validation, and validation feeds reason-routed repair back into the loop.",
          "Open-loop generation versus a closed loop with validation and reason-routed repair",
        ),
      },
      {
        heading: "The biological heuristic: structures built to be repaired",
        body: [
          "A beaver dam is not engineered to be impermeable. It is engineered to leak in controlled ways, shed sacrificial material under load, distribute stress across interlocking branches, and accumulate new material where pressure is highest. It survives floods precisely because it does not attempt to be perfect.",
          "The same four properties map directly onto software architecture. Controlled porosity becomes modular data flow through declared interfaces instead of a monolithic black box. Distributed load paths become multi-channel validation, where geometry, semantics, and physics are each tested independently. Sacrificial elements become isolated candidate workspaces, so a failed generation never overwrites a canonical accepted asset. Material recruitment becomes evidence accumulation — new sensor data and human review raise confidence over time rather than being discarded.",
          "This is why the architecture treats partial failure as normal operating state. A single failed validation channel holds the run; it does not collapse the system.",
        ],
        figure: diagram(
          "salti8-repair-first-structures",
          "Cutaway diagram of a beaver dam annotated with four physical resilience properties — controlled porosity, distributed load paths, sacrificial elements, and material recruitment — each mapped to a digital equivalent: modular data flow, multi-channel validation, isolated candidate workspaces, and evidence accumulation.",
          "Four physical resilience properties and their direct software equivalents",
        ),
      },
      {
        heading: "Three layers, three distinct questions",
        body: [
          "The architecture separates into three layers, and the cleanest way to understand the split is by the question each layer answers. Layer8 answers who, what, where, and under which policy a workflow executes. SALTI answers whether exploration was sufficient, whether the resulting condition is acceptable, and whether stated confidence is calibrated. B-HDSR answers which failure mode is currently controlling and whether present capacity still exceeds present load.",
          "Keeping these boundaries visible is what makes the system auditable. When something goes wrong you can say which layer made the decision, on what evidence, and under which policy version — instead of pointing at a single opaque model and guessing.",
          "It also makes adoption incremental. A team can run Layer8 alone as a governed multi-provider gateway, then add SALTI's evaluative stages only where the consequence of a silent failure justifies the extra latency and cost.",
        ],
        points: [
          "B-HDSR — resilience intelligence: which failure mode controls, and does capacity exceed load",
          "SALTI — evaluative intelligence: is exploration sufficient, is condition acceptable, is confidence calibrated",
          "Layer8 — operational intelligence: who, what, where, and under which policy execution happens",
        ],
        figure: diagram(
          "salti8-governed-adaptability-architecture",
          "Exploded isometric diagram of three stacked layers: B-HDSR resilience intelligence on top, SALTI evaluative intelligence in the middle, and Layer8 operational intelligence at the base, each annotated with the question it answers.",
          "The three-layer control stack and the question each layer answers",
        ),
      },
      {
        heading: "Layer8: the operational substrate",
        body: [
          "Layer8 is the substrate everything else runs on. It cryptographically establishes who can request work and isolates project boundaries, so a tenant's context, credentials, and outputs cannot leak across the boundary. It dispatches jobs to specialist tools rather than routing everything through a single monolithic model.",
          "The digital thread is the part that matters most for accountability. Every state transition — the input, the model selected, the policy applied, the validation result, the repair reason, the approving human — is written to an immutable event ledger. That ledger is what makes a decision reconstructable months later, and what makes rollback a defined operation instead of an archaeology project.",
          "Policy enforcement runs continuously alongside it: least privilege by default, explicit provider restrictions, and gated approvals that must clear before an asset is delivered.",
        ],
        points: [
          "Identity and tenancy — cryptographically scoped access and project isolation",
          "Modular routing — dispatch to specialist tools, not one monolithic model",
          "The digital thread — an immutable event ledger connecting inputs, models, decisions, and outputs",
          "Policy enforcement — least privilege, provider restrictions, and explicitly gated approvals",
        ],
        figure: diagram(
          "salti8-layer8-operational-substrate",
          "Diagram of the Layer8 routing hub at the centre, connected to identity, storage, compute, and validator nodes, above a horizontal chain of immutable ledger events representing the digital thread.",
          "Layer8 routing hub, its connected subsystems, and the immutable event ledger beneath",
        ),
      },
      {
        heading: "What this buys you in practice",
        body: [
          "The practical outcome is that failure becomes visible early and cheap, rather than late and expensive. A validation channel that fails holds the run and emits a reason code. Repair is attempted a bounded number of times against that specific reason. If repair does not clear the gate, the work is routed to a human with the full decision context attached — not dumped as a raw model response for someone to re-derive from scratch.",
          "Confidence is reported as a calibrated number rather than a model's self-assessment, which means an operations team can set a threshold and mean it. And because every stage writes to the digital thread, an audit does not depend on anyone remembering what happened.",
          "None of this removes human judgement. It concentrates human judgement on the decisions that actually need it.",
        ],
      },
    ],
    faqs: [
      {
        question: "What is adaptive spatial intelligence?",
        answer:
          "Adaptive spatial intelligence describes systems that treat spatial and geometric output as living infrastructure to be continuously validated and repaired, rather than as a one-shot generative result. Instead of accepting a model's first output, the system explores candidates, validates them across independent channels such as geometry, semantics, and physics, repairs specific failures, and accumulates evidence over time.",
      },
      {
        question: "What is the difference between open-loop and closed-loop AI architecture?",
        answer:
          "In an open loop, a single model both generates and effectively approves its own work, so failures are silent. In a closed loop, exploration, validation, repair, and human review are separate stages with separate failure behaviour, so a failed check holds the run and routes a reason-coded correction instead of shipping a plausible-looking defect.",
      },
      {
        question: "What does B-HDSR stand for and what does it do?",
        answer:
          "B-HDSR is the resilience-intelligence layer of the architecture. It determines which failure mode is currently controlling a workflow and whether present capacity still exceeds present load, which is what allows the system to degrade in a controlled way rather than fail all at once.",
      },
      {
        question: "Do I have to adopt all three layers at once?",
        answer:
          "No. Layer8 can run on its own as a governed multi-provider gateway with tenant isolation, routing, and an audit ledger. SALTI's evaluative stages and B-HDSR's resilience logic are added where the consequence of a silent failure justifies the additional latency and cost.",
      },
      {
        question: "Why is the architecture compared to a beaver dam?",
        answer:
          "A beaver dam survives floods because it is porous, sheds sacrificial material, distributes load across interlocking branches, and recruits new material under pressure — it is built to be repaired rather than to be perfect. Those four properties map directly onto modular data flow, isolated candidate workspaces, multi-channel validation, and evidence accumulation in software.",
      },
    ],
    related: [
      "salti-b-engine",
      "ai-governance",
      "governed-ai-agents",
      "spatial-intelligence",
    ],
  },
  {
    slug: "ai-gateway",
    title: "AI Gateway for Governed Model Execution",
    description:
      "Route, secure, observe, validate, and govern AI model traffic through one multi-provider AI gateway with durable workflows and auditable evidence.",
    eyebrow: "Multi-provider AI infrastructure",
    heading: "An AI gateway built for decisions—not just requests.",
    lead:
      "Layer8 Adaptive gives platform teams one governed execution envelope for model access, policy, routing, validation, repair, approvals, usage, and provenance. It handles the ordinary gateway work while adding controls for agentic workflows that cannot be treated like stateless API calls.",
    keywords: [
      "AI gateway",
      "LLM gateway",
      "multi-provider AI gateway",
      "enterprise AI gateway",
      "AI API gateway",
    ],
    sections: [
      {
        heading: "Control every provider through one policy layer",
        body: [
          "Applications authenticate once while Layer8 applies tenant, scope, rate, residency, model, and cost policy before a request reaches a provider. Provider credentials remain behind the control plane instead of spreading across applications and agent tools.",
          "Routing can account for model capability, health, latency, budget, and data-handling requirements. Fallback is explicit and observable, so resilience does not become silent model substitution.",
        ],
        points: [
          "Scoped API keys and tenant isolation",
          "Provider routing, failover, budgets, and quotas",
          "Normalized request, response, and streaming contracts",
          "Tenant-partitioned cache keys and structured audit records",
        ],
      },
      {
        heading: "Extend the gateway from transport to governed execution",
        body: [
          "A conventional LLM proxy ends when a model returns text. Layer8 can continue through specialist validation, bounded repair, calibrated gates, and human approval using the SALTI-B Engine.",
          "That separation matters: the gateway owns secure execution, while the engine owns workflow control. Teams can adopt routing first and add deeper governance only where risk and value justify it.",
        ],
      },
      {
        heading: "Built for AI-first operations with accountable release",
        body: [
          "AI-first does not mean approval-free. Routine work can proceed automatically within measured policy. Uncertain, high-consequence, or poorly evidenced work can be held for human review with the full decision context attached.",
        ],
      },
    ],
    faqs: [
      {
        question: "What is an AI gateway?",
        answer:
          "An AI gateway is a control layer between applications and AI providers. It centralizes authentication, model routing, rate limits, observability, cost controls, policy, and provider integrations.",
      },
      {
        question: "How is Layer8 different from a basic LLM proxy?",
        answer:
          "Layer8 adds durable cascade execution, independent validation, bounded repair, human approval, tenant governance, and provenance beyond request forwarding.",
      },
      {
        question: "Can Layer8 route to multiple AI providers?",
        answer:
          "Yes. The architecture supports policy-driven routing and fallback across approved providers while keeping credentials and audit data tenant-aware.",
      },
    ],
    related: ["llm-routing", "ai-governance", "salti-b-engine", "integrations"],
  },
  {
    slug: "llm-routing",
    title: "LLM Routing, Failover, and Model Policy",
    description:
      "Route LLM requests by capability, health, cost, latency, residency, and policy with observable failover across approved AI providers.",
    eyebrow: "Model routing and resilience",
    heading: "Use the right model without hard-wiring your product to one.",
    lead:
      "Layer8 Adaptive separates application contracts from provider decisions. Platform teams can govern which models are eligible, how fallback works, what each tenant may use, and when a routing change requires review.",
    keywords: [
      "LLM routing",
      "AI model router",
      "LLM failover",
      "multi-model routing",
      "AI provider routing",
    ],
    sections: [
      {
        heading: "Routing that respects more than price",
        body: [
          "The cheapest model is not automatically the correct model. Routing policy can combine declared capability, measured health, latency, budget, regional restrictions, model allowlists, and task-specific requirements.",
          "Each decision should identify the policy and provider version used. That creates an operational record when behavior changes after a model or route update.",
        ],
      },
      {
        heading: "Failover without silent semantic drift",
        body: [
          "Provider failover can preserve availability, but substituting a model can change quality, tool support, safety behavior, and data handling. Layer8 records fallback and can require revalidation or human review when the substitute changes the risk profile.",
        ],
        points: [
          "Timeout and health-aware provider fallback",
          "Per-tenant model and region allowlists",
          "Cost and quota boundaries",
          "Validation after consequential route changes",
        ],
      },
      {
        heading: "One contract for applications and agents",
        body: [
          "A normalized API keeps provider-specific details behind the gateway while still allowing capabilities such as streaming and tool use to be declared explicitly. Applications gain portability without pretending every model behaves identically.",
        ],
      },
    ],
    faqs: [
      {
        question: "What is LLM routing?",
        answer:
          "LLM routing selects an AI model or provider for a request using policy such as task capability, availability, cost, latency, geography, and tenant permissions.",
      },
      {
        question: "Does model failover guarantee equivalent output?",
        answer:
          "No. Different models can behave differently. Layer8 makes fallback visible and can trigger validation or approval when equivalence has not been established.",
      },
    ],
    related: ["ai-gateway", "integrations", "ai-governance"],
  },
  {
    slug: "ai-governance",
    title: "AI Governance, Audit Logs, and Provenance",
    description:
      "Apply enforceable AI policy, tenant isolation, audit logs, evidence bundles, approvals, and versioned provenance to model and agent workflows.",
    eyebrow: "Policy that executes",
    heading: "AI governance belongs in the request path.",
    lead:
      "Policies that live only in documents cannot control production traffic. Layer8 Adaptive evaluates identity, scope, tenant, model, data, cost, validation, and approval rules as part of execution—and records the evidence behind the outcome.",
    keywords: [
      "AI governance",
      "AI audit logs",
      "AI provenance",
      "enterprise AI policy",
      "AI compliance controls",
    ],
    sections: [
      {
        heading: "Move governance from guidance to enforcement",
        body: [
          "Layer8 places authorization and policy before provider routing. Disallowed models, scopes, regions, or workloads are rejected before secrets or data reach an external service.",
          "Policy decisions are versioned so a later reviewer can determine which rules governed a request at that moment—not merely which rules exist today.",
        ],
      },
      {
        heading: "Reconstruct the decision, not just the prompt",
        body: [
          "Useful provenance includes request identity, tenant, policy, provider, model, validation results, repair reasons, approval actions, timestamps, integrity metadata, and artifact references. Sensitive prompt logging remains separately controlled.",
        ],
        points: [
          "Structured request and workflow records",
          "Versioned policy and module references",
          "Reason-coded validation and repair",
          "Exportable evidence bundles",
        ],
      },
      {
        heading: "Make truthful security and compliance claims",
        body: [
          "Layer8 provides technical controls that can support a compliance program. It does not turn an organization compliant by itself. Public claims should identify implemented controls and independently verified certifications separately.",
        ],
      },
    ],
    faqs: [
      {
        question: "What is AI governance?",
        answer:
          "AI governance is the set of policies, controls, responsibilities, evidence, and review processes used to manage how AI systems are selected, operated, monitored, and changed.",
      },
      {
        question: "Does Layer8 log prompts by default?",
        answer:
          "The architecture keeps prompt logging separately configurable because prompts can contain sensitive data. Operational metadata and provenance can be recorded without indiscriminately storing prompt content.",
      },
    ],
    related: ["security", "human-in-the-loop-ai", "ai-gateway"],
  },
  {
    slug: "governed-ai-agents",
    title: "Governed AI Agents and Durable Workflows",
    description:
      "Run governed AI agents through durable state, bounded retries, independent validation, approval gates, and complete workflow provenance.",
    eyebrow: "Agentic systems under control",
    heading: "Give agents freedom inside explicit operating boundaries.",
    lead:
      "Layer8 Adaptive treats agent work as a durable, inspectable process rather than a chain of prompts hidden inside application code. The SALTI-B Engine controls exploration, validation, repair, confidence, and escalation.",
    keywords: [
      "governed AI agents",
      "AI agent governance",
      "durable AI workflows",
      "agent orchestration",
      "enterprise AI agents",
    ],
    sections: [
      {
        heading: "Durable state instead of fragile prompt chains",
        body: [
          "Each run has an identity, versioned definition, state, events, artifacts, retry limits, and final disposition. Workers can recover from interruption without repeating billable or consequential steps blindly.",
        ],
      },
      {
        heading: "Separate generation from validation",
        body: [
          "An agent should not be the sole judge of its own output. Specialist validators can inspect different failure channels, and a weakest-link gate can hold the run when one critical channel fails.",
        ],
        points: [
          "Bounded tool and model execution",
          "Independent specialist validators",
          "Reason-coded repair operators",
          "Human escalation with evidence attached",
        ],
      },
      {
        heading: "Measure automation by safe completion",
        body: [
          "The useful metric is not how often a human disappears from the loop. It is how often the system completes correctly within policy, how quickly it recovers from known failures, and how effectively it escalates the rest.",
        ],
      },
    ],
    faqs: [
      {
        question: "What is a governed AI agent?",
        answer:
          "A governed AI agent operates within enforceable permissions, tool boundaries, budgets, validation rules, audit requirements, and escalation paths.",
      },
      {
        question: "Why use durable workflows for agents?",
        answer:
          "Durable state allows agent runs to survive timeouts and worker failures, avoid duplicate actions, preserve evidence, and resume from known checkpoints.",
      },
    ],
    related: ["salti-b-engine", "human-in-the-loop-ai", "ai-governance"],
  },
  {
    slug: "human-in-the-loop-ai",
    title: "AI-First Workflows with Human Oversight",
    description:
      "Automate routine AI work first while routing uncertain, consequential, or weakly evidenced decisions to accountable human reviewers.",
    eyebrow: "AI first · humans where they matter",
    heading: "Automation handles the flow. Humans own consequential release.",
    lead:
      "Layer8 Adaptive supports AI-first execution without pretending that every decision should be autonomous. Measured policy determines when work may proceed and when a reviewer must inspect the evidence, correction history, and remaining uncertainty.",
    keywords: [
      "human in the loop AI",
      "AI-first workflow",
      "human AI oversight",
      "AI approval workflow",
      "responsible AI automation",
    ],
    sections: [
      {
        heading: "Use humans for judgment, not routine forwarding",
        body: [
          "Routine, low-risk work can pass automatically when required gates succeed. Review queues should concentrate human attention on consequential actions, novel failure modes, missing evidence, and confidence below the approved threshold.",
        ],
      },
      {
        heading: "Give reviewers decision-ready context",
        body: [
          "A reviewer needs more than the final output. Layer8 can present the originating request, policy, providers, validation channels, failed gates, repair attempts, evidence, and the precise action awaiting approval.",
        ],
        points: [
          "Risk- and confidence-based escalation",
          "Explicit approve, reject, and request-repair actions",
          "Reviewer identity and timestamp capture",
          "No silent release after approval expires",
        ],
      },
      {
        heading: "Improve automation without hiding failure",
        body: [
          "Review outcomes become labeled operational evidence. Teams can learn which workflows are ready for broader automation while preserving the ability to roll back policies and thresholds.",
        ],
      },
    ],
    faqs: [
      {
        question: "What does human in the loop mean for AI?",
        answer:
          "It means a person reviews or authorizes defined AI decisions, especially when consequences, uncertainty, or policy require accountable judgment.",
      },
      {
        question: "Is Layer8 human-first or AI-first?",
        answer:
          "Execution is AI-first for work that satisfies policy and validation. Humans remain responsible for consequential release, exceptions, and decisions that exceed approved confidence or evidence boundaries.",
      },
    ],
    related: ["governed-ai-agents", "ai-governance", "salti-b-engine"],
  },
  {
    slug: "salti-b-engine",
    title: "SALTI-B Engine for Adaptive AI Control",
    description:
      "Explore the SALTI-B Engine: a durable AI control sequence for grounding, exploration, validation, bounded repair, confidence, and approval.",
    eyebrow: "Core orchestration technology",
    heading: "A control engine for AI workflows that must recover visibly.",
    lead:
      "The SALTI-B Engine governs how Layer8 Adaptive explores alternatives, measures condition, records damage, attempts bounded repair, applies acceptance gates, and routes uncertain work to humans.",
    keywords: [
      "SALTI-B Engine",
      "AI orchestration engine",
      "adaptive AI control",
      "AI validation engine",
      "bounded AI repair",
    ],
    sections: [
      {
        heading: "Six stages, one durable decision record",
        body: [
          "Grounding establishes the working evidence. Exploration produces candidates. Validation tests critical channels. Repair addresses reason-coded failures within limits. Calibration estimates operational confidence. Approval releases or escalates the result.",
        ],
      },
      {
        heading: "Weakest-link gates protect critical channels",
        body: [
          "Averages can hide a decisive failure. SALTI-B can evaluate critical validation channels with minimum or weakest-link logic, preventing strong performance elsewhere from compensating for a failed safety, evidence, or constraint channel.",
        ],
      },
      {
        heading: "Recovery is measured—not assumed",
        body: [
          "The Beaver Engineering Amplified Vector (BEAV) compares repair and capture rates with loss and decay. It is a design metric that requires domain calibration, not a certified engineering result or a substitute for accountable review.",
        ],
      },
      {
        heading: "Temperature is control state—not truth",
        body: [
          "The SALTI (Smith Agent Loop Temperature Indicator) expresses closed-loop controller behavior such as exploration pressure within the SALTI-B Engine. It is not a physical measurement, calibrated probability, or correctness guarantee. The interface and API must preserve those semantic boundaries.",
        ],
      },
    ],
    faqs: [
      {
        question: "What does the SALTI-B Engine do?",
        answer:
          "It controls durable AI workflow stages, including grounding, exploration, validation, bounded repair, confidence handling, and human approval.",
      },
      {
        question: "Can SALTI-B work with different AI providers?",
        answer:
          "Yes. Provider execution is handled through Layer8, allowing SALTI-B workflow stages to use approved models and specialist modules according to policy.",
      },
    ],
    related: ["governed-ai-agents", "ai-gateway", "human-in-the-loop-ai"],
  },
  {
    slug: "spatial-intelligence",
    title: "Governed Spatial Intelligence Workflows",
    description:
      "Apply evidence, weakest-link validation, bounded repair, and human approval to spatial AI, digital twins, infrastructure, and resilience workflows.",
    eyebrow: "Vertical intelligence",
    heading: "Spatial AI with evidence, limits, and accountable decisions.",
    lead:
      "Layer8 Adaptive extends governed execution into spatial intelligence workflows where visual plausibility cannot substitute for operational validity. Observations, plans, validations, repairs, and approvals remain traceable.",
    keywords: [
      "spatial intelligence AI",
      "governed spatial AI",
      "AI digital twins",
      "infrastructure AI",
      "disaster resilience AI",
    ],
    sections: [
      {
        heading: "Keep observation separate from inference",
        body: [
          "Unknown capacity must remain unknown instead of being converted into optimistic credit. Spatial modules can preserve evidence quality, source, timestamp, geometry, calibration, and unresolved uncertainty as first-class fields.",
        ],
      },
      {
        heading: "Validate the channels that can fail independently",
        body: [
          "Geometry, topology, accessibility, capacity, provenance, and safety can each invalidate a result. Weakest-link gates prevent an attractive aggregate score from hiding one failed critical channel.",
        ],
      },
      {
        heading: "Support experts without impersonating them",
        body: [
          "The platform can organize evidence, run calibrated modules, and route review. It is not a substitute for licensed engineering, emergency command, or domain authority where those roles are legally or operationally required.",
        ],
      },
    ],
    faqs: [
      {
        question: "What is governed spatial intelligence?",
        answer:
          "It is spatial AI executed with explicit evidence, uncertainty, validation channels, repair limits, policy, provenance, and human authority.",
      },
    ],
    related: ["salti-b-engine", "ai-governance", "human-in-the-loop-ai"],
  },
  {
    slug: "integrations",
    title: "AI Provider and Platform Integrations",
    description:
      "Connect approved AI models, identity systems, observability tools, data services, and deployment platforms through Layer8 Adaptive.",
    eyebrow: "Controlled interoperability",
    heading: "Connect the ecosystem without surrendering the control plane.",
    lead:
      "Layer8 Adaptive is designed to sit between applications and the providers, tools, and infrastructure they depend on. Integrations inherit tenant policy, credential isolation, observability, and audit requirements.",
    keywords: [
      "AI integrations",
      "LLM provider integrations",
      "multi-provider AI",
      "AI gateway integrations",
    ],
    sections: [
      {
        heading: "Model providers",
        body: [
          "Provider adapters normalize supported contracts while retaining explicit capability differences. The current backend includes OpenAI and Gemini adapters and is structured for additional approved providers.",
        ],
      },
      {
        heading: "Identity, data, and operations",
        body: [
          "The target architecture supports OIDC identity, PostgreSQL, Redis, object storage, queues, secret managers, OpenTelemetry-compatible observability, and policy-controlled specialist modules.",
        ],
      },
      {
        heading: "Integrations fail closed where required",
        body: [
          "Credential state, provider health, plugin failure, and regional constraints are operational inputs. Blocking controls remain blocking instead of silently degrading to an ungoverned path.",
        ],
      },
    ],
    faqs: [
      {
        question: "Which AI providers does Layer8 support?",
        answer:
          "The current backend includes OpenAI and Gemini adapters. Additional providers are added through a common adapter contract and must be approved by tenant policy.",
      },
    ],
    related: ["ai-gateway", "llm-routing", "security"],
  },
  {
    slug: "security",
    title: "Layer8 Adaptive Security and Trust",
    description:
      "Review Layer8 security architecture for tenant isolation, scoped access, secret handling, audit events, rate limits, encryption, and deployment boundaries.",
    eyebrow: "Security and trust",
    heading: "Security controls before model execution.",
    lead:
      "Layer8 Adaptive is designed so authentication, tenant resolution, policy, quotas, redaction, and credential isolation occur before provider routing. This page describes architectural intent and implemented controls without claiming certifications that have not been independently verified.",
    keywords: [
      "AI gateway security",
      "LLM security gateway",
      "AI tenant isolation",
      "AI audit security",
    ],
    sections: [
      {
        heading: "Tenant-aware access and data boundaries",
        body: [
          "API keys are hashed, scoped, revocable, and associated with a tenant. Runtime authorization checks tenant status and model permissions. Cache keys and persisted data must retain tenant identity to prevent cross-tenant reuse.",
        ],
      },
      {
        heading: "Secrets stay behind the control plane",
        body: [
          "Provider credentials are referenced through controlled configuration rather than returned to clients. Production deployments should use a managed secret store and separate credentials, databases, queues, and buckets by environment.",
        ],
        points: [
          "Rate and quota enforcement before provider calls",
          "Optional prompt logging with conservative defaults",
          "Signed Stripe webhooks and idempotent event processing",
          "Dependency, secret, container, and static analysis scanning",
        ],
      },
      {
        heading: "Current trust posture",
        body: [
          "SALTI8 does not currently claim SOC 2, ISO 27001, HIPAA, FedRAMP, or other third-party certification in this repository. Those claims should appear only after the relevant scope has been independently assessed.",
        ],
      },
      {
        heading: "Report a security concern",
        body: [
          "Use the SALTI8 contact form to provide a high-level description and request a secure reporting channel. Do not place credentials, customer data, working exploit code, or sensitive vulnerability details in the public contact form.",
          "Good-faith research must avoid privacy violations, data destruction, persistence, social engineering, denial of service, and access beyond what is necessary to demonstrate the issue. SALTI8 will coordinate scope and remediation directly.",
        ],
      },
    ],
    faqs: [
      {
        question: "Is Layer8 SOC 2 certified?",
        answer:
          "No certification claim is currently made. The architecture includes controls that can support a future assurance program, but certification requires independent assessment.",
      },
      {
        question: "How are API keys stored?",
        answer:
          "The backend stores a hash and prefix rather than the raw API key and supports revocation and rotation.",
      },
    ],
    related: ["ai-governance", "ai-gateway", "docs", "contact"],
  },
  {
    slug: "pricing",
    title: "Layer8 Adaptive Pricing",
    description:
      "Review Layer8 Adaptive options for development, team, business, and enterprise governed AI gateway deployments.",
    eyebrow: "Transparent platform pricing",
    heading: "Pay for governed execution—not hidden model markup.",
    lead:
      "Approved Layer8 organizations can activate Team or Business subscriptions through authenticated billing. Platform access and provider inference remain separately visible.",
    keywords: [
      "AI gateway pricing",
      "LLM gateway pricing",
      "Layer8 Adaptive pricing",
      "enterprise AI pricing",
    ],
    sections: [
      {
        heading: "Evaluation access",
        body: [
          "Approved pilot teams can evaluate API integration and sandbox workflows before activating a production subscription. Evaluation duration, tenant limits, and provider access are confirmed in writing during onboarding.",
        ],
      },
      {
        heading: `Team — ${teamPriceLabel}`,
        body: [
          "Team includes one customer organization with API access, cascade execution, audit export, provider routing, and standard pilot support. AI-provider inference, taxes, and separately contracted services are not included in the platform fee.",
          "The authenticated Stripe Checkout shows the exact recurring charge before payment. Paid access changes only after the signed webhook confirms the subscription.",
        ],
      },
      {
        heading: `Business — ${businessPriceLabel}`,
        body: [
          "Business includes the Team capabilities plus extended-retention controls, priority pilot support, and the spatial-intelligence entitlement. SSO, private networking, dedicated deployment boundaries, data residency, custom retention, and service-level commitments require a separate written order.",
        ],
      },
      {
        heading: "Cancellation, renewals, and refunds",
        body: [
          "Monthly subscriptions renew automatically until canceled. An authorized customer administrator can manage or cancel a subscription in the Stripe customer portal; cancellation takes effect at the end of the paid billing period unless the checkout or a written order states otherwise.",
          "Fees are non-refundable and are not prorated except where required by law or expressly stated in a written order. Customers keep access through the paid period after a scheduled cancellation.",
        ],
      },
    ],
    faqs: [
      {
        question: "Are AI model costs included?",
        answer:
          "Provider inference costs remain separately visible so customers can distinguish model spend from the Layer8 platform subscription.",
      },
      {
        question: "Can I purchase Layer8 Adaptive today?",
        answer:
          "Approved organizations can choose Team or Business from the customer billing screen. Layer8 verifies the signed Stripe webhook before granting paid entitlements.",
      },
      {
        question: "Can I cancel from the website?",
        answer:
          "Yes. After activation, an authorized organization administrator can open the Stripe customer portal from the billing screen and schedule cancellation at the end of the current billing period.",
      },
    ],
    related: ["pilot", "ai-gateway", "compare/portkey", "compare/litellm"],
  },
  {
    slug: "contact",
    title: "Contact SALTI8",
    description:
      "Contact SALTI8 about Layer8 Adaptive pilots, product questions, billing, privacy, security, partnerships, and governed AI execution.",
    eyebrow: "Contact",
    heading: "Talk with the team building Layer8 Adaptive.",
    lead:
      "Use the contact form for product, pilot, billing, privacy, security, or partnership questions. SALTI8 will route the request to the appropriate owner.",
    keywords: [
      "contact SALTI8",
      "Layer8 Adaptive contact",
      "AI gateway pilot",
    ],
    sections: [
      {
        heading: "Product and pilot questions",
        body: [
          "Share the organization, workflow, failure mode, and evaluation timeline so SALTI8 can determine whether a focused pilot is a fit.",
        ],
      },
      {
        heading: "Billing, privacy, and security requests",
        body: [
          "Name the request type in the message. Do not submit passwords, API keys, payment-card data, private prompts, or exploit details. SALTI8 will establish an appropriate secure follow-up channel when needed.",
        ],
      },
    ],
    faqs: [],
    related: ["pilot", "pricing", "security", "privacy"],
    lastUpdated: "July 28, 2026",
  },
  {
    slug: "privacy",
    title: "SALTI8 Privacy Notice",
    description:
      "Learn what information SALTI8 collects, why it is used, which service providers process it, and how to submit a privacy request.",
    eyebrow: "Legal",
    heading: "Privacy notice.",
    lead:
      "This notice explains how SALTI8, Inc. handles personal information for salti8.com, Layer8 Adaptive accounts, pilot applications, support, and billing.",
    keywords: [
      "SALTI8 privacy",
      "Layer8 Adaptive privacy",
      "AI gateway data privacy",
    ],
    sections: [
      {
        heading: "Information we collect",
        body: [
          "Pilot and contact forms collect the information you provide, such as name, work email, company, role, request details, timeline, and consent to be contacted. Account access can include identity, session, and organization membership information supplied through Clerk. Billing can include customer, subscription, invoice, and transaction identifiers supplied through Stripe; SALTI8 does not receive complete payment-card numbers.",
          "Layer8 may process operational metadata needed to authenticate, route, secure, meter, troubleshoot, and audit customer requests. Prompt and response handling depends on customer configuration and the approved AI providers used for a workflow. Prompt logging is disabled by default in the launch configuration.",
        ],
      },
      {
        heading: "How we use information",
        body: [
          "SALTI8 uses information to evaluate pilot requests, create and secure accounts, provide and improve the service, process subscriptions, respond to support and legal requests, prevent abuse, maintain audit and billing records, and comply with law.",
          "SALTI8 does not sell personal information. We may disclose information to service providers acting on our behalf, to customer organization administrators, when required by law, or to protect rights, safety, and service integrity.",
        ],
      },
      {
        heading: "Service providers and international processing",
        body: [
          "Launch service providers include Hostinger for the public site and DNS, Render for the API and managed infrastructure, Clerk for identity, Stripe for billing, and customer-approved AI or storage providers for configured workloads. Those providers process information under their own terms and privacy notices.",
          "Information may be processed in countries other than where it was collected. Customer-specific data location or residency commitments apply only when written into an order.",
        ],
      },
      {
        heading: "Retention, security, and choices",
        body: [
          "SALTI8 retains information only as long as reasonably necessary for the purposes described, customer instructions, dispute resolution, security, and legal or accounting obligations. Operational and content retention can vary by plan and tenant configuration.",
          "Reasonable technical and organizational safeguards are used, but no internet service can guarantee absolute security. Depending on applicable law, you may request access, correction, deletion, restriction, or a copy of personal information.",
        ],
      },
      {
        heading: "Contact and changes",
        body: [
          "Submit privacy questions or requests through the SALTI8 contact form and label the message as a privacy request. Do not include sensitive authentication or payment information. SALTI8 may update this notice as the service changes and will post the revised date on this page.",
        ],
      },
    ],
    faqs: [],
    related: ["contact", "security", "terms", "acceptable-use"],
    lastUpdated: "July 28, 2026",
  },
  {
    slug: "terms",
    title: "SALTI8 Terms of Service",
    description:
      "Review SALTI8 terms for Layer8 Adaptive accounts, subscriptions, customer data, AI outputs, acceptable use, cancellation, and service limitations.",
    eyebrow: "Legal",
    heading: "Terms of service.",
    lead:
      "These terms govern access to salti8.com and Layer8 Adaptive by SALTI8. A signed order form or services agreement controls if it conflicts with these terms.",
    keywords: [
      "SALTI8 terms",
      "Layer8 Adaptive terms",
      "AI gateway terms of service",
    ],
    sections: [
      {
        heading: "Accounts and organizations",
        body: [
          "You must provide accurate information, protect credentials, and have authority to act for the organization you join or create. Organization administrators control membership and billing. You are responsible for activity under your accounts and API keys and must notify SALTI8 promptly of suspected unauthorized use.",
          "Pilot and production access may require approval, identity configuration, an organization-to-tenant mapping, and technical onboarding. SALTI8 may reject, suspend, or limit access when necessary to protect customers, the service, or third parties.",
        ],
      },
      {
        heading: "Subscriptions, taxes, cancellation, and refunds",
        body: [
          "Paid subscriptions renew automatically for the billing period shown at Stripe Checkout until canceled. Prices exclude AI-provider usage, taxes, and separately contracted services unless stated otherwise. You authorize Stripe to charge the selected payment method for recurring fees and applicable taxes.",
          "An authorized administrator can schedule cancellation through the Stripe customer portal. Cancellation normally takes effect at the end of the current paid period. Fees are non-refundable and non-prorated except where required by law or expressly stated in a written order.",
        ],
      },
      {
        heading: "Customer data and AI workloads",
        body: [
          "As between you and SALTI8, you retain rights in data you submit. You grant SALTI8 and its processors the limited rights needed to host, transmit, secure, transform, and otherwise process that data to provide the service. You are responsible for having the rights and lawful basis needed to submit data and for configuring approved providers and retention appropriately.",
          "AI outputs can be inaccurate, incomplete, or non-unique. Layer8 controls and evidence can reduce operational risk but do not guarantee correctness, legal compliance, fitness, or professional judgment. You remain responsible for review and use of outputs, especially for consequential decisions.",
        ],
      },
      {
        heading: "Service operation and support",
        body: [
          "SALTI8 may change or discontinue preview features and may perform maintenance. Unless a written order states otherwise, the service is provided without a service-level commitment and support response times are not guaranteed.",
          "You may not bypass authorization, rate, policy, tenancy, or billing controls. Use is also subject to the Acceptable Use Policy.",
        ],
      },
      {
        heading: "Intellectual property and feedback",
        body: [
          "SALTI8 and its licensors retain rights in Layer8 Adaptive, the SALTI-B Engine, software, designs, documentation, and branding. No rights are granted except the limited, revocable right to use the service under these terms and an applicable order.",
          "If you provide feedback, you permit SALTI8 to use it without restriction or compensation, provided SALTI8 does not identify you publicly without permission.",
        ],
      },
      {
        heading: "Disclaimers and limits",
        body: [
          "To the maximum extent permitted by law, the service is provided “as is” and “as available” without implied warranties. SALTI8 is not liable for indirect, incidental, special, consequential, exemplary, or punitive damages, lost profits, or lost data.",
          "To the maximum extent permitted by law, SALTI8's aggregate liability arising from the service is limited to fees you paid SALTI8 for the service during the twelve months before the event giving rise to the claim. Some jurisdictions do not allow every exclusion or limit, so those provisions apply only to the extent permitted.",
        ],
      },
      {
        heading: "Termination and changes",
        body: [
          "Either party may end use as permitted by the subscription or written order. SALTI8 may suspend or terminate access for material breach, unlawful or unsafe use, nonpayment, or risk to the service. Provisions that by their nature should survive termination will survive.",
          "SALTI8 may update these terms prospectively. Material changes will be posted with a revised date. Continued use after an effective update constitutes acceptance where permitted by law.",
        ],
      },
    ],
    faqs: [],
    related: ["pricing", "privacy", "acceptable-use", "contact"],
    lastUpdated: "July 28, 2026",
  },
  {
    slug: "acceptable-use",
    title: "SALTI8 Acceptable Use Policy",
    description:
      "Review prohibited uses of Layer8 Adaptive, including unauthorized access, harmful content, evasion, abuse, privacy violations, and high-risk deployment.",
    eyebrow: "Legal",
    heading: "Acceptable use policy.",
    lead:
      "Layer8 Adaptive may be used only for lawful, authorized workloads that respect security, privacy, human authority, provider rules, and customer policy.",
    keywords: [
      "SALTI8 acceptable use",
      "AI gateway acceptable use policy",
      "responsible AI platform use",
    ],
    sections: [
      {
        heading: "Prohibited conduct",
        body: [
          "You may not use the service to break the law; infringe rights; facilitate malware, credential theft, unauthorized surveillance, exploitation, or fraud; access systems or data without permission; evade safety, policy, rate, tenancy, or billing controls; disrupt the service; or test security without written authorization.",
          "You may not submit data you lack the right to process, expose secrets in prompts or logs contrary to policy, misrepresent AI output as verified human or professional judgment, or use the service to make unlawful discriminatory decisions.",
        ],
      },
      {
        heading: "High-impact and regulated use",
        body: [
          "Layer8 is not a substitute for licensed, legally required, or accountable professional review. Uses involving safety, employment, housing, credit, insurance, education, healthcare, legal rights, critical infrastructure, emergency response, or other high-impact decisions require appropriate human authority, testing, documentation, and written customer controls.",
        ],
      },
      {
        heading: "Enforcement and reporting",
        body: [
          "SALTI8 may investigate suspected violations and may limit, suspend, or terminate access to protect customers, third parties, or the service. Where practical, SALTI8 will provide notice and an opportunity to correct a violation, but immediate action may be required for urgent risk.",
          "Report suspected abuse through the contact form. For a vulnerability, provide a high-level description first and wait for a secure reporting channel before sending exploit details or sensitive data.",
        ],
      },
    ],
    faqs: [],
    related: ["terms", "privacy", "security", "contact"],
    lastUpdated: "July 28, 2026",
  },
  {
    slug: "docs",
    title: "Layer8 Adaptive Documentation",
    description:
      "Start with Layer8 Adaptive architecture, authentication, inference routing, spatial endpoints, billing webhooks, and deployment documentation.",
    eyebrow: "Developer documentation",
    heading: "Build against one governed execution contract.",
    lead:
      "The current repository provides a FastAPI control and execution plane with tenant administration, scoped API keys, routing, provider adapters, cache, audit infrastructure, spatial endpoints, and Stripe billing foundations.",
    keywords: [
      "Layer8 API docs",
      "AI gateway API",
      "LLM gateway documentation",
      "SALTI-B documentation",
    ],
    sections: [
      {
        heading: "Authentication and tenancy",
        body: [
          "Administrative endpoints use a bootstrap bearer token today, while runtime inference uses tenant-scoped API keys. OIDC-backed operator identity and tenant-aware RBAC are planned before broad production exposure.",
        ],
      },
      {
        heading: "Billing and Stripe",
        body: [
          "Authenticated billing endpoints create Stripe Checkout and customer portal sessions. The signed webhook endpoint synchronizes subscriptions, invoices, and entitlements into tenant billing state.",
        ],
        points: [
          "POST /v1/billing/checkout",
          "POST /v1/billing/portal",
          "GET /v1/billing/{tenant_id}",
          "POST /v1/webhooks/stripe",
        ],
      },
      {
        heading: "Source and architecture",
        body: [
          "The public source repository contains the build plan, environment examples, database migrations, deployment manifests, tests, and the production web workspace.",
        ],
      },
    ],
    faqs: [
      {
        question: "Where is the Layer8 source repository?",
        answer:
          "The current source is at github.com/robs46859-eng/layer8.",
      },
    ],
    related: ["ai-gateway", "security", "integrations"],
  },
  {
    slug: "glossary",
    title: "AI Gateway and Agent Governance Glossary",
    description:
      "Definitions for AI gateways, LLM routing, governed agents, validation gates, bounded repair, provenance, and human-in-the-loop workflows.",
    eyebrow: "Technical glossary",
    heading: "The language of governed AI execution.",
    lead:
      "Clear terminology prevents security controls, heuristic scores, calibrated probabilities, and marketing claims from being treated as interchangeable.",
    keywords: [
      "AI gateway glossary",
      "AI governance terms",
      "LLM routing definition",
      "agent orchestration glossary",
    ],
    sections: [
      {
        heading: "AI gateway",
        body: [
          "A control layer between applications and AI providers that centralizes authentication, policy, routing, rate limits, observability, cost controls, and integrations.",
        ],
      },
      {
        heading: "Bounded repair",
        body: [
          "A reason-coded correction attempt with explicit limits, followed by validation. Bounded repair prevents an agent from looping indefinitely or quietly changing the acceptance criteria.",
        ],
      },
      {
        heading: "Weakest-link gate",
        body: [
          "An acceptance rule in which the minimum critical-channel result controls release. It is useful when success in one area cannot compensate for failure in another.",
        ],
      },
      {
        heading: "Provenance",
        body: [
          "The evidence needed to reconstruct how a result was produced, including identities, policy, versions, providers, events, validations, repairs, approvals, and artifact references.",
        ],
      },
    ],
    faqs: [],
    related: ["ai-gateway", "ai-governance", "salti-b-engine"],
  },
  {
    slug: "pilot",
    title: "Layer8 Adaptive Private Pilot",
    description:
      "Apply for a Layer8 Adaptive private pilot for governed AI gateways, multi-provider routing, durable agents, and evidence-sensitive workflows.",
    eyebrow: "Private pilot",
    heading: "Bring one workflow that cannot afford a silent failure.",
    lead:
      "SALTI8 is preparing focused pilots with platform teams that need multi-provider resilience, agent governance, independent validation, or decision provenance.",
    keywords: [
      "enterprise AI pilot",
      "AI gateway pilot",
      "governed AI platform",
    ],
    sections: [
      {
        heading: "Good pilot candidates",
        body: [
          "The strongest candidates have a defined workflow, measurable failure modes, accessible reviewers, and a reason that ordinary request logging is insufficient.",
        ],
        points: [
          "Multi-provider applications requiring governed fallback",
          "Agent workflows with costly or consequential tool actions",
          "Evidence-sensitive spatial or infrastructure analysis",
          "Teams needing audit-ready model and policy provenance",
        ],
      },
      {
        heading: "Pilot sequence",
        body: [
          "We define the workflow and acceptance channels, establish a secure tenant boundary, integrate approved providers, run labeled evaluations, calibrate gates, and review evidence before production exposure.",
        ],
      },
      {
        heading: "Commercial activation",
        body: [
          "Approved tenants receive account access before a Stripe subscription is created. This prevents anonymous payment from being mistaken for automatic access to a governed enterprise environment.",
        ],
      },
    ],
    faqs: [
      {
        question: "Why is checkout limited to approved tenants?",
        answer:
          "Layer8 requires an organization and tenant boundary before subscription entitlements can be provisioned safely.",
      },
    ],
    related: ["pricing", "security", "ai-gateway"],
  },
  {
    slug: "compare/portkey",
    title: "Layer8 Adaptive vs Portkey",
    description:
      "Compare Layer8 Adaptive and Portkey across AI gateway routing, observability, governance, durable cascades, validation, repair, and pricing.",
    eyebrow: "AI gateway comparison",
    heading: "Layer8 Adaptive vs Portkey",
    lead:
      "Portkey is an established AI gateway and observability platform. Layer8 Adaptive is being built around governed execution, durable specialist cascades, weakest-link validation, bounded repair, and evidence-backed approval.",
    keywords: [
      "Portkey alternative",
      "Layer8 vs Portkey",
      "AI gateway comparison",
    ],
    sections: [
      {
        heading: "Where Portkey is strong",
        body: [
          "Portkey publicly offers gateway routing, guardrails, observability, prompt management, logs, and enterprise controls. Its Production plan is listed at $49 per month with included recorded logs and usage-based log overages.",
        ],
      },
      {
        heading: "Where Layer8 is different",
        body: [
          "Layer8 focuses on durable execution beyond the provider response: specialist validation channels, bounded reason-coded repair, weakest-link gates, human approval, and complete decision provenance.",
        ],
      },
      {
        heading: "How to choose",
        body: [
          "Choose based on the workflow you need to govern. Teams primarily seeking a mature gateway and observability product should evaluate Portkey directly. Teams needing controlled multi-stage execution and evidence-sensitive release should evaluate Layer8 as it reaches pilot readiness.",
        ],
      },
    ],
    faqs: [],
    related: ["ai-gateway", "pricing", "compare/litellm"],
    sources: [{ label: "Portkey official pricing", url: "https://portkey.ai/pricing" }],
    lastVerified: "July 28, 2026",
  },
  {
    slug: "compare/litellm",
    title: "Layer8 Adaptive vs LiteLLM",
    description:
      "Compare Layer8 Adaptive with LiteLLM for open-source LLM proxying, model routing, enterprise controls, governed cascades, validation, and provenance.",
    eyebrow: "Open-source gateway comparison",
    heading: "Layer8 Adaptive vs LiteLLM",
    lead:
      "LiteLLM provides a widely used open-source interface and proxy across many model providers. Layer8 builds on the gateway category with durable governance and controlled workflow execution.",
    keywords: [
      "LiteLLM alternative",
      "Layer8 vs LiteLLM",
      "open source LLM gateway",
    ],
    sections: [
      {
        heading: "Where LiteLLM is strong",
        body: [
          "LiteLLM offers a free self-hosted open-source gateway with provider normalization, virtual keys, budgets, rate limits, fallback, logs, and Prometheus integration. Enterprise pricing is custom and capacity-oriented.",
        ],
      },
      {
        heading: "Where Layer8 is different",
        body: [
          "Layer8 treats gateway routing as the beginning of governed execution. The SALTI-B Engine adds durable stages, independent gates, bounded repair, approval state, and reconstructable evidence.",
        ],
      },
      {
        heading: "How to choose",
        body: [
          "LiteLLM is compelling when broad provider compatibility and self-hosted proxying are the priority. Layer8 is intended for teams whose acceptance, recovery, and approval logic must be explicit operational state.",
        ],
      },
    ],
    faqs: [],
    related: ["ai-gateway", "llm-routing", "compare/portkey"],
    sources: [{ label: "LiteLLM official pricing", url: "https://www.litellm.ai/pricing" }],
    lastVerified: "July 28, 2026",
  },
  {
    slug: "compare/openrouter",
    title: "Layer8 Adaptive vs OpenRouter",
    description:
      "Compare Layer8 Adaptive and OpenRouter for multi-model access, provider routing, platform fees, tenant governance, durable workflows, and validation.",
    eyebrow: "Gateway and aggregator comparison",
    heading: "Layer8 Adaptive vs OpenRouter",
    lead:
      "OpenRouter aggregates access to a large model and provider catalog. Layer8 Adaptive is a tenant-aware governance and execution control plane designed to sit inside an organization’s operating boundary.",
    keywords: [
      "OpenRouter alternative",
      "Layer8 vs OpenRouter",
      "multi-model AI gateway",
    ],
    sections: [
      {
        heading: "Where OpenRouter is strong",
        body: [
          "OpenRouter provides a broad model marketplace, unified API, provider routing, pay-as-you-go credits, and BYOK options. Its public pay-as-you-go platform fee is listed at 5.5 percent.",
        ],
      },
      {
        heading: "Where Layer8 is different",
        body: [
          "Layer8 is not primarily a model marketplace. It governs tenant access, provider accounts, workflow stages, validation, repair, approval, and provenance across approved infrastructure.",
        ],
      },
      {
        heading: "How to choose",
        body: [
          "OpenRouter is useful for convenient access to many models. Layer8 is intended for organizations that need policy and evidence to remain under their control while routing across their approved providers.",
        ],
      },
    ],
    faqs: [],
    related: ["ai-gateway", "llm-routing", "compare/litellm"],
    sources: [{ label: "OpenRouter official pricing", url: "https://openrouter.ai/pricing" }],
    lastVerified: "July 28, 2026",
  },
];

export const seoPageBySlug = new Map(seoPages.map((page) => [page.slug, page]));

export function pageHref(slug: string) {
  return `/${slug}/`;
}
