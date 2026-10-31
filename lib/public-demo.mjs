export const PUBLIC_DEMO_OWNER = 'public-demo';

const privateEmailKey = /(?:^|_)(?:email|email_address)$/i;
const emailAddress = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;

/** Public run details omit contact fields and redact email addresses in text. */
export function publicDemoPayload(value) {
  if (Array.isArray(value)) return value.map(publicDemoPayload);
  if (typeof value === 'string') return value.replace(emailAddress, '[private email]');
  if (!value || typeof value !== 'object') return value;

  const sanitized = Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => !privateEmailKey.test(key))
      .map(([key, entry]) => [key, publicDemoPayload(entry)]),
  );

  // Preserve the operator's reviewed physical diagnosis when an older worker
  // reported its generic upstream simulator_failed wrapper.
  if (sanitized.kind === 'hardware' && sanitized.report?.outcomes && sanitized.report?.reviews) {
    const reviewed = sanitized.report.reviews.find((review) =>
      review?.outcome === 'failure' && typeof review.note === 'string'
      && /safety guardrails/i.test(review.note) && /rejected before motion/i.test(review.note),
    );
    const jointLimit = reviewed?.note?.match(/\b([a-z0-9_]+_outside_limits)\b/i)?.[1];
    if (jointLimit) {
      if (typeof sanitized.report.summary === 'string') {
        sanitized.report.summary = sanitized.report.summary.replace(
          /\bsimulator_failed\b/g,
          `YAM Safety Guardrails rejected the trajectory before motion (${jointLimit})`,
        );
      }
      sanitized.report.outcomes = sanitized.report.outcomes.map((outcome) =>
        outcome?.reason === 'simulator_failed'
          ? { ...outcome, reason: `hardware_safety_guardrail_rejected (${jointLimit})` }
          : outcome,
      );
    }
  }

  return sanitized;
}
