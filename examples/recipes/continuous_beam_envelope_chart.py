# ---
# Example:  Continuous beam — plot the moment and shear envelopes
# Feature:  continuous_beam (C01 Continuous Beam)
# Verified: yes — 2026-09-02 — envelope extremes match the C01 goldens; chart written and checked; exact on prokon-automation.exe
# ---
# The desktop program draws the bending-moment diagram on screen; a script
# can draw it too — and keep it, version it, or drop it into a report.
# Every analysis returns 22 position-by-position envelope series under
# result["envelopes"], one value per analysis position, ready to plot.
#
# Uses matplotlib, bundled with Prokon's Python runtime.

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to a file; use plt.show() in your own session
import matplotlib.pyplot as plt

import prokon.v5

# The same two-span beam as the quick-start: 2 x 6 m, 300 x 500, BS8110,
# 20 kN/m dead + 10 kN/m live per span.
result = prokon.v5.continuous_beam.analyse(
    design_code="BS8110 - 1997",
    sections=[{"n": 1, "bw": 300, "d": 500}],
    segments=[
        {"span": 1, "length": 6, "sec_left": 1},
        {"span": 2, "length": 6, "sec_left": 1},
    ],
    supports=[{"n": 1}, {"n": 2}, {"n": 3}],
    loads=[
        {"case": "Dead", "span": 1, "w_left": 20},
        {"case": "Dead", "span": 2, "w_left": 20},
        {"case": "Live", "span": 1, "w_left": 10},
        {"case": "Live", "span": 2, "w_left": 10},
    ],
    fyv=250.0, cover_top=30.0, cover_bot=40.0,
)["result"]

env = result["envelopes"]
x = env["position"]                      # m from the LEFT END of the beam
m_min = env["moment_negative"]           # kNm — minimum-moment envelope
m_max = env["moment_positive"]           # kNm — maximum-moment envelope
v_min = env["shear_negative"]            # kN
v_max = env["shear_positive"]            # kN
cap_bot = env["moment_capacity_bottom"]  # kNm — capacity, bottom steel in tension
cap_top = env["moment_capacity_top"]     # kNm — capacity, top steel in tension (negative)

# Where the supports are: each span's boundaries, read from the span rows.
support_x = [x[result["spans"][0]["first_position"] - 1]] + [
    x[span["last_position"] - 1] for span in result["spans"]
]

fig, (ax_m, ax_v) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

# ── Bending moment envelope, drawn the way engineers draw it: sagging down
ax_m.fill_between(x, m_min, m_max, alpha=0.3, label="moment envelope")
ax_m.plot(x, m_min, lw=1)
ax_m.plot(x, m_max, lw=1)
ax_m.plot(x, cap_bot, "--", lw=1, label="capacity (bottom steel)")
ax_m.plot(x, cap_top, "--", lw=1, label="capacity (top steel)")
ax_m.axhline(0.0, color="black", lw=0.8)
ax_m.invert_yaxis()                       # sagging (positive) plotted downward
ax_m.set_ylabel("moment [kNm]")
ax_m.legend(loc="upper center", ncol=3, fontsize=8)

# Annotate the governing values (these are the quick-start's numbers:
# max sagging 132.5 kNm in the spans, max hogging -198.0 kNm at support 2).
sag = result["max_sagging_moment"]
hog = result["max_hogging_moment"]
ax_m.annotate(f"{sag:.1f}", (x[m_max.index(max(m_max))], sag),
              textcoords="offset points", xytext=(0, -12), ha="center", fontsize=8)
ax_m.annotate(f"{hog:.1f}", (x[m_min.index(min(m_min))], hog),
              textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8)

# ── Shear force envelope ─────────────────────────────────────────────────
ax_v.fill_between(x, v_min, v_max, alpha=0.3, label="shear envelope")
ax_v.plot(x, v_min, lw=1)
ax_v.plot(x, v_max, lw=1)
ax_v.axhline(0.0, color="black", lw=0.8)
ax_v.set_ylabel("shear [kN]")
ax_v.set_xlabel("position along beam [m]")
ax_v.legend(loc="upper center", fontsize=8)

# Mark the supports on both panels.
for ax in (ax_m, ax_v):
    for sx in support_x:
        ax.axvline(sx, color="grey", lw=0.8, ls=":")

title = f"Continuous beam envelopes — BS8110 - 1997, {result['span_count']} spans"
fig.suptitle(title)
fig.tight_layout()

out = Path("continuous_beam_envelopes.png")
fig.savefig(out, dpi=150)
print(f"Max sagging {sag:.1f} kNm, max hogging {hog:.1f} kNm, "
      f"max shear {result['max_shear']:.1f} kN")                    # 132.5 / -198.0 / 165.0
print(f"Chart written: {out.resolve()}")
