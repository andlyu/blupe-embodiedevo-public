export function operatorIdAllowed(userId, configuredIds = '') {
  if (typeof userId !== 'string' || !userId.trim()) return false;
  const allowed = new Set(
    String(configuredIds)
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean),
  );
  return allowed.has(userId.trim());
}
