"use client";

import { FormEvent, useState } from "react";

type SubmissionState =
  | { kind: "idle"; message: "" }
  | { kind: "pending"; message: "Submitting your pilot request…" }
  | { kind: "success"; message: string }
  | { kind: "error"; message: string };

function responseError(payload: unknown): string {
  if (
    payload &&
    typeof payload === "object" &&
    "detail" in payload &&
    typeof payload.detail === "string"
  ) {
    return payload.detail;
  }
  return "Your request could not be submitted. Check the form and try again.";
}

export function PilotApplicationForm({
  apiBaseUrl,
}: {
  apiBaseUrl?: string;
}) {
  const [submission, setSubmission] = useState<SubmissionState>({
    kind: "idle",
    message: "",
  });
  const normalizedApiBaseUrl = apiBaseUrl?.replace(/\/+$/, "");

  async function submitApplication(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);

    setSubmission({
      kind: "pending",
      message: "Submitting your pilot request…",
    });

    try {
      if (!normalizedApiBaseUrl) {
        throw new Error(
          "Pilot intake is not configured for this build. Add the public API URL in Hostinger and rebuild.",
        );
      }

      const response = await fetch(
        `${normalizedApiBaseUrl}/v1/pilot-applications`,
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            contact_name: formData.get("contact_name"),
            work_email: formData.get("work_email"),
            company: formData.get("company"),
            role: formData.get("role") || null,
            use_case: formData.get("use_case"),
            timeline: formData.get("timeline") || null,
            source: "website-pilot",
            consent_to_contact:
              formData.get("consent_to_contact") === "accepted",
            website: formData.get("website") || "",
          }),
        },
      );
      const payload = (await response.json().catch(() => null)) as
        | { message?: string }
        | null;
      if (!response.ok) {
        throw new Error(responseError(payload));
      }

      form.reset();
      setSubmission({
        kind: "success",
        message:
          payload?.message ??
          "Thanks. SALTI8 will review your pilot request.",
      });
    } catch (reason: unknown) {
      setSubmission({
        kind: "error",
        message:
          reason instanceof Error
            ? reason.message
            : "The pilot service could not be reached. Try again shortly.",
      });
    }
  }

  const pending = submission.kind === "pending";

  return (
    <section
      id="pilot-application"
      className="pilotApplication"
      aria-labelledby="pilot-application-title"
    >
      <div>
        <p className="eyebrow">Start the conversation</p>
        <h2 id="pilot-application-title">Request pilot access.</h2>
        <p>
          Tell SALTI8 about one workflow, its failure cost, and the operating
          team responsible for it. A focused pilot starts with a specific
          outcome—not a generic platform rollout.
        </p>
      </div>

      <form onSubmit={submitApplication} aria-busy={pending}>
        <div className="formGrid">
          <label>
            Contact name
            <input
              name="contact_name"
              type="text"
              minLength={2}
              maxLength={120}
              autoComplete="name"
              required
            />
          </label>
          <label>
            Work email
            <input
              name="work_email"
              type="email"
              maxLength={254}
              autoComplete="email"
              required
            />
          </label>
          <label>
            Company
            <input
              name="company"
              type="text"
              minLength={2}
              maxLength={160}
              autoComplete="organization"
              required
            />
          </label>
          <label>
            Role <span>(optional)</span>
            <input
              name="role"
              type="text"
              maxLength={120}
              autoComplete="organization-title"
            />
          </label>
          <label>
            Evaluation timeline <span>(optional)</span>
            <select name="timeline" defaultValue="">
              <option value="">Select a timeline</option>
              <option value="immediate">Immediate</option>
              <option value="30_days">Within 30 days</option>
              <option value="60_90_days">Within 60–90 days</option>
              <option value="exploring">Exploring</option>
            </select>
          </label>
        </div>

        <label>
          Workflow and failure mode
          <textarea
            name="use_case"
            minLength={20}
            maxLength={2000}
            rows={7}
            placeholder="Describe the workflow, what can fail, and how you measure a safe outcome."
            required
          />
        </label>

        <label className="honeypot" aria-hidden="true">
          Website
          <input
            name="website"
            type="text"
            autoComplete="off"
            tabIndex={-1}
          />
        </label>

        <label className="consentField">
          <input
            name="consent_to_contact"
            type="checkbox"
            value="accepted"
            required
          />
          <span>
            I agree that SALTI8 may contact me about this pilot request.
          </span>
        </label>

        {submission.message ? (
          <p
            className={`formMessage formMessage-${submission.kind}`}
            role={submission.kind === "error" ? "alert" : "status"}
            aria-live={submission.kind === "error" ? "assertive" : "polite"}
          >
            {submission.message}
          </p>
        ) : null}

        <button
          className="button buttonPrimary"
          type="submit"
          disabled={pending}
        >
          {pending ? "Submitting…" : "Request pilot access"}
        </button>
      </form>
    </section>
  );
}
