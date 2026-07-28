import type { CSSProperties, ReactNode } from "react";
import Image from "next/image";
import { MarketingHeader } from "@/components/marketing-shell";

const cascadeSteps = [
  {
    number: "01",
    name: "Ground",
    decision: "Accept context",
    detail: "Fix the evidence baseline before exploration begins.",
  },
  {
    number: "02",
    name: "Explore",
    decision: "Generate diversity",
    detail: "Route work across models without confusing variety for quality.",
  },
  {
    number: "03",
    name: "Validate",
    decision: "Apply gates",
    detail: "Test every critical channel; one failed channel can hold the run.",
  },
  {
    number: "04",
    name: "Repair",
    decision: "Bound attempts",
    detail: "Make reason-coded corrections, cap retries, and validate again.",
  },
  {
    number: "05",
    name: "Calibrate",
    decision: "Measure confidence",
    detail: "Separate heuristic condition from calibrated operational confidence.",
  },
  {
    number: "06",
    name: "Approve",
    decision: "Release or review",
    detail: "Route consequential or uncertain work to accountable humans.",
  },
];

const platformResponsibilities = [
  "Identity, tenancy, policy, and scoped access",
  "Multi-provider model routing and failover",
  "Usage, cost, versioning, and rate enforcement",
  "Append-only audit events and evidence bundles",
];

const engineResponsibilities = [
  "Durable specialist-agent cascade control",
  "Adaptive, bounded, reason-coded repair",
  "Weakest-link validation and acceptance gates",
  "Human review when evidence or consequence demands it",
];

function BlueprintCorners() {
  return (
    <>
      <i className="corner cornerTl" aria-hidden="true" />
      <i className="corner cornerTr" aria-hidden="true" />
      <i className="corner cornerBl" aria-hidden="true" />
      <i className="corner cornerBr" aria-hidden="true" />
    </>
  );
}

function Blueprint({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`blueprint ${className}`}>
      <BlueprintCorners />
      {children}
    </div>
  );
}

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </svg>
  );
}

function HeroVisual() {
  return (
    <Blueprint className="heroVisual">
      <Image
        src="/images/salti8-acrylic-architecture.webp"
        alt="Abstract acrylic architecture in SALTI8 terracotta and slate, representing governed layers of AI execution."
        fill
        priority
        sizes="(max-width: 1020px) 100vw, 48vw"
      />
      <div className="heroVisualShade" aria-hidden="true" />
      <div className="heroVisualTopline">
        <span>Execution envelope</span>
        <span>Rev 08</span>
      </div>
      <div className="heroVisualLabel">
        <span>Layer8 Adaptive</span>
        <strong>Govern · route · prove</strong>
      </div>
      <div className="heroVisualStatus">
        <i aria-hidden="true" />
        Policy boundary active
      </div>
    </Blueprint>
  );
}

export default function Home() {
  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "SALTI8",
    url: "https://salti8.com",
    description:
      "SALTI8 develops governed AI execution infrastructure for reliable multi-provider and agent workflows.",
  };

  const softwareSchema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "Layer8 Adaptive",
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Cloud",
    creator: {
      "@type": "Organization",
      name: "SALTI8",
    },
    description:
      "A governed AI execution platform for model routing, durable cascades, bounded repair, human approval, and provenance.",
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify([organizationSchema, softwareSchema]).replace(
            /</g,
            "\\u003c",
          ),
        }}
      />

      <a className="skipLink" href="#main">
        Skip to content
      </a>

      <MarketingHeader />

      <main id="main">
        <section className="hero shell">
          <div className="heroCopy">
            <p className="eyebrow">01 · Governed execution infrastructure</p>
            <h1>
              Every AI action enters through policy.
              <span> Every decision leaves with evidence.</span>
            </h1>
            <p className="heroLead">
              Layer8 Adaptive by SALTI8 is the execution layer between your
              applications and AI providers—routing work, validating outcomes,
              bounding repair, and preserving provenance before results reach
              production.
            </p>
            <div className="heroActions">
              <a className="button buttonPrimary" href="#platform">
                Explore the platform <ArrowIcon />
              </a>
              <a className="button buttonSecondary" href="#engine">
                See the SALTI-B chain
              </a>
            </div>
            <div className="heroProof" aria-label="Platform capabilities">
              <span>Multi-provider</span>
              <span>Tenant-isolated</span>
              <span>Human-governed</span>
            </div>
          </div>
          <HeroVisual />
        </section>

        <section className="capabilityRail" aria-label="Execution guarantees">
          <div className="shell capabilityGrid">
            <div>
              <span>01</span>
              <strong>Route</strong>
              <p>Choose providers by policy, health, cost, and capability.</p>
            </div>
            <div>
              <span>02</span>
              <strong>Validate</strong>
              <p>Test critical channels independently before acceptance.</p>
            </div>
            <div>
              <span>03</span>
              <strong>Repair</strong>
              <p>Correct known failure modes without unbounded loops.</p>
            </div>
            <div>
              <span>04</span>
              <strong>Prove</strong>
              <p>Reconstruct decisions from policy, evidence, and events.</p>
            </div>
          </div>
        </section>

        <section className="section shell" id="platform">
          <div className="sectionHeading">
            <p className="eyebrow">02 · Division of responsibility</p>
            <h2>One governed envelope. Two explicit control layers.</h2>
            <p>
              Layer8 owns secure execution and operational policy. The SALTI-B
              Engine owns adaptive workflow control. Keeping those boundaries
              visible makes the system easier to audit, test, and trust.
            </p>
          </div>

          <div className="responsibilityGrid">
            <Blueprint className="responsibilityCard lightCard">
              <span className="cardIndex">L8 / 01</span>
              <p className="cardKicker">Layer8 Adaptive</p>
              <h3>The operational substrate</h3>
              <p className="cardIntro">
                Governs who may request work, where it runs, and how each
                decision is recorded.
              </p>
              <ul>
                {platformResponsibilities.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Blueprint>

            <Blueprint className="responsibilityCard darkCard">
              <span className="cardIndex">SB / 02</span>
              <p className="cardKicker">SALTI-B Engine</p>
              <h3>The adaptive controller</h3>
              <p className="cardIntro">
                Governs exploration, condition, repair, confidence, and
                accountable release.
              </p>
              <ul>
                {engineResponsibilities.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Blueprint>
          </div>
        </section>

        <section className="engineSection" id="engine">
          <div className="shell">
            <div className="sectionHeading sectionHeadingDark">
              <p className="eyebrow">03 · SALTI-B control sequence</p>
              <h2>Generation is a step—not a verdict.</h2>
              <p>
                Specialist stages turn an open-ended model response into a
                bounded, inspectable execution. Failure is routed, not hidden.
              </p>
            </div>

            <Blueprint className="cascadePlate">
              <div className="plateHeader">
                <span>SALTI-B Engine · Cascade gates</span>
                <span>Sheet 01 / 01</span>
              </div>
              <ol className="cascadeList">
                {cascadeSteps.map((step, index) => (
                  <li
                    key={step.number}
                    style={{ "--step-delay": `${index * 70}ms` } as CSSProperties}
                  >
                    <span className="stepNumber">{step.number}</span>
                    <strong>{step.name}</strong>
                    <span className="stepDecision">{step.decision}</span>
                    <p>{step.detail}</p>
                  </li>
                ))}
              </ol>
            </Blueprint>
          </div>
        </section>

        <section className="section shell" id="governance">
          <div className="governanceGrid">
            <div className="sectionHeading governanceCopy">
              <p className="eyebrow">04 · Evidence before confidence</p>
              <h2>Control that survives the audit.</h2>
              <p>
                Layer8 records the tenant, policy, provider, model, validation
                result, repair reason, approval, and version behind a decision.
                Teams can reconstruct what happened without trusting a
                screenshot or a model&apos;s memory.
              </p>
              <a className="textLink" href="/pilot/">
                Discuss a governed workflow <ArrowIcon />
              </a>
            </div>
            <Blueprint className="evidencePanel">
              <div className="evidenceHeader">
                <span>Provenance bundle</span>
                <span className="status">Complete</span>
              </div>
              <dl>
                <div>
                  <dt>Request</dt>
                  <dd>req_8a19</dd>
                </div>
                <div>
                  <dt>Policy</dt>
                  <dd>prod-governed-v3</dd>
                </div>
                <div>
                  <dt>Validation</dt>
                  <dd>5 / 5 gates</dd>
                </div>
                <div>
                  <dt>Repairs</dt>
                  <dd>1 bounded attempt</dd>
                </div>
                <div>
                  <dt>Approval</dt>
                  <dd>Human verified</dd>
                </div>
                <div>
                  <dt>Evidence</dt>
                  <dd>Hash sealed</dd>
                </div>
              </dl>
            </Blueprint>
          </div>
          <figure className="productVisual">
            <Image
              src="/images/layer8-adaptive-control-surface.webp"
              alt="Concept visualization of the Layer8 Adaptive control plane showing routed network flows and security posture panels."
              width={2000}
              height={1091}
              sizes="(max-width: 1280px) calc(100vw - 40px), 1240px"
            />
            <figcaption>
              Layer8 Adaptive · Concept interface visualization
            </figcaption>
          </figure>
        </section>

        <section className="pilotSection" id="pilot">
          <div className="shell pilotInner">
            <div>
              <p className="eyebrow">05 · Private pilot</p>
              <h2>Bring one workflow that cannot afford a silent failure.</h2>
            </div>
            <p>
              SALTI8 is preparing Layer8 Adaptive for pilot deployments with
              platform teams building multi-provider, agentic, and
              evidence-sensitive systems.
            </p>
            <a className="button buttonPrimary buttonOnDark" href="/pilot/">
              Request pilot access <ArrowIcon />
            </a>
          </div>
        </section>
      </main>

      <footer className="siteFooter">
        <div className="shell footerInner">
          <div>
            <a className="brand footerBrand" href="/">
              SALTI<span>8</span>
            </a>
            <p>Industrial precision for governed intelligence.</p>
          </div>
          <div className="footerMeta">
            <span>Layer8 Adaptive by SALTI8</span>
            <span>Powered by the SALTI-B Engine</span>
          </div>
          <p>© 2026 SALTI8 Labs</p>
        </div>
      </footer>
    </>
  );
}
