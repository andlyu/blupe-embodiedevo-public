"""Align the native agent budget with the owner's remaining physical lease."""
import math

def native_seconds(status,requested,now):
    started=status.get('run_started_at');duration=status.get('run_duration_s')
    if type(started) not in (int,float) or type(duration) not in (int,float) or not math.isfinite(started) or not math.isfinite(duration):
        raise ValueError('Physical lease start and duration are required')
    remaining=duration-(now-started)
    # Camera/environment startup and native cleanup must finish within the lease.
    seconds=math.floor(min(requested,remaining-20))
    if seconds<15:raise TimeoutError('Insufficient physical lease remains for a native session and cleanup')
    return seconds
