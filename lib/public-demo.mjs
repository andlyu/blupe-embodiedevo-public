export const PUBLIC_DEMO_OWNER = 'public-demo';

const privateEmailKey = /(?:^|_)(?:email|email_address)$/i;
const emailAddress = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;

/** Public run details omit contact fields and redact email addresses in text. */
export function publicDemoPayload(value) {
  if (Array.isArray(value)) return value.map(publicDemoPayload);
  if (typeof value === 'string') return value.replace(emailAddress, '[private email]');
  if (!value || typeof value !== 'object') return value;

  return Object.fromEntries(
    Object.entries(value)
      .filter(([key]) => !privateEmailKey.test(key))
      .map(([key, entry]) => [key, publicDemoPayload(entry)]),
  );
}
