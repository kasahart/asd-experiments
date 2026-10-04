"""Re-render the recording figures using Wandas 0.8.0; no model weights required."""
import hashlib, json, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import wandas as wd
from asd_min.waveform import condition_audio
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.environ.get("ASD_FIGURE_OUTPUT", ROOT / "outputs/recording-figures"))
OUTPUT.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Noto Sans CJK JP"
example = json.loads((ROOT / "configs/02-recording-example.json").read_text())
DATA_ROOT = Path(os.environ.get("ASD_DATA_ROOT", ROOT / "eval_data/raw"))
path = DATA_ROOT / example["path"]
if hashlib.sha256(path.read_bytes()).hexdigest() != example["sha256"]:
    raise ValueError("Recording SHA-256 differs from the documented example")
audio = wd.read(path)
# applyは2chの形を保つため、近接側を処理し、遠方側は参照として残します。
def subtract_near(wave, condition):
    processed = condition_audio(wave.astype(np.float32), condition)
    return np.stack([processed, wave[1]]).astype(wave.dtype)

recordings = {
    "b0": audio[0],
    "b1": audio[1],
    "w1": audio.apply(subtract_near, condition="w1")[0],
    "ss": audio.apply(subtract_near, condition="ss")[0],
}
DESCRIBE = dict(normalize=False, is_close=False, xlim=(0, 6),
                fmax=8000, ylim=(0, 8000), vmin=-100, vmax=0,
                waveform={"ylim": (-.5, .5)}, spectral={"xlim": (-100, 0)})
for condition, frame in recordings.items():
    frame.describe(**DESCRIBE, image_save=OUTPUT / f"{condition}.png")
comparison = recordings["b0"].rename_channels({0: "B0"})
for condition in ("b1", "w1", "ss"):
    comparison = comparison.concat_frame(
        recordings[condition].rename_channels({0: condition.upper()}))
ax = comparison.welch(n_fft=2048).plot(
    overlay=True, title="Power spectrum: B0 / B1 / W1 / SS (full 6 s)",
    xlim=(0, 8000), ylim=(-100, 0), ylabel="Power level [dB]")
ax.figure.text(.5, -.02, "Nishida et al. · doi:10.5281/zenodo.20151556 · CC BY-NC-SA 4.0",
               ha="center", fontsize=8)
ax.figure.savefig(OUTPUT / "spectrum.png", bbox_inches="tight")
