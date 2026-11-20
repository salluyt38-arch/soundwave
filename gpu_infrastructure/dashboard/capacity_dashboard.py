"""
GPU Processing Capacity Dashboard & Live Telemetry Inspector.
Renders real-time telemetry:
  - GPU Model & Free/Total VRAM
  - CUDA Availability & Versions
  - Active Workload vs Max Concurrency
  - Health Status, Heartbeats, and Failover Counts
  - Privacy Boundary Audit Log
"""

from typing import Any, Dict
from ..router.secure_router import SecureGPURouter


class CapacityDashboardRenderer:
    """
    Renders live JSON and HTML dashboards for GPU infrastructure monitoring.
    """

    def __init__(self, router: SecureGPURouter):
        self.router = router

    def get_json_telemetry(self) -> Dict[str, Any]:
        """Returns structured JSON for REST API consumers."""
        return self.router.get_capacity_metrics()

    def render_html_dashboard(self) -> str:
        """
        Renders an ultra-modern dark-mode HTML dashboard view for operators.
        """
        metrics = self.get_json_telemetry()
        workers = metrics.get("workers", [])

        worker_rows = ""
        for w in workers:
            health_color = "#10b981" if w["worker_health"] == "healthy" else "#ef4444"
            trust_badge = "#a855f7" if "trusted" in w["trust_level"] else "#f59e0b"
            worker_rows += f"""
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
              <td style="padding: 12px; font-weight: 700; color: #fff;">{w['worker_id']}</td>
              <td style="padding: 12px; text-transform: uppercase; font-size: 11px;"><span style="background: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 6px;">{w['provider']}</span></td>
              <td style="padding: 12px;"><span style="background: {trust_badge}22; color: {trust_badge}; border: 1px solid {trust_badge}55; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">{w['trust_level']}</span></td>
              <td style="padding: 12px; color: #cbd5e1;">{w['gpu_model']}</td>
              <td style="padding: 12px; font-family: monospace; color: #38bdf8;">{w['vram_free_mb']} / {w['vram_total_mb']} MB</td>
              <td style="padding: 12px;"><span style="color: {health_color}; font-weight: 700;">● {w['worker_health'].upper()}</span></td>
              <td style="padding: 12px; font-weight: 700;">{w['active_workload']} / {w['max_concurrency']}</td>
              <td style="padding: 12px; font-size: 11px; color: #94a3b8;">{w['heartbeat_age_sec']}s ago</td>
            </tr>
            """

        if not worker_rows:
            worker_rows = '<tr><td colspan="8" style="padding: 24px; text-align: center; color: #94a3b8;">No GPU workers registered in router pool.</td></tr>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SoundWave • GPU Capacity & Telemetry Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ background: #070913; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 24px; }}
    .card {{ background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 20px; margin-bottom: 24px; backdrop-filter: blur(12px); }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .stat-box {{ background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; }}
    .stat-val {{ font-size: 24px; font-weight: 800; color: #fff; margin-top: 4px; }}
    .stat-lbl {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }}
    th {{ padding: 12px; background: rgba(0,0,0,0.3); color: #94a3b8; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.1); }}
  </style>
</head>
<body>
  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
    <div>
      <h1 style="margin: 0; font-size: 22px; font-weight: 900; color: #fff;">⚡ SoundWave GPU Capacity & Telemetry Dashboard</h1>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #94a3b8;">Real-Time Worker Health, VRAM Allocations & Failover Telemetry</p>
    </div>
    <div>
      <span style="background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); padding: 6px 14px; border-radius: 99px; font-size: 12px; font-weight: 800;">🟢 Router Active</span>
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-box">
      <div class="stat-lbl">Active GPU Workers</div>
      <div class="stat-val">{metrics['healthy_workers']} / {metrics['total_workers']}</div>
    </div>
    <div class="stat-box">
      <div class="stat-lbl">Free VRAM Available</div>
      <div class="stat-val" style="color: #38bdf8;">{round(metrics['free_vram_mb'] / 1024, 1)} GB</div>
    </div>
    <div class="stat-box">
      <div class="stat-lbl">Total Cluster VRAM</div>
      <div class="stat-val">{round(metrics['total_vram_mb'] / 1024, 1)} GB</div>
    </div>
    <div class="stat-box">
      <div class="stat-lbl">Queued Jobs</div>
      <div class="stat-val" style="color: #fbbf24;">{metrics['queued_jobs']}</div>
    </div>
    <div class="stat-box">
      <div class="stat-lbl">Active Workload</div>
      <div class="stat-val">{metrics['active_workload']}</div>
    </div>
  </div>

  <div class="card">
    <h2 style="font-size: 16px; margin: 0 0 16px 0; color: #fff;">Registered Worker Nodes (Horizontal Pool)</h2>
    <div style="overflow-x: auto;">
      <table>
        <thead>
          <tr>
            <th>Worker ID</th>
            <th>Provider</th>
            <th>Trust Level</th>
            <th>GPU Model</th>
            <th>Free / Total VRAM</th>
            <th>Health</th>
            <th>Workload</th>
            <th>Heartbeat</th>
          </tr>
        </thead>
        <tbody>
          {worker_rows}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""
