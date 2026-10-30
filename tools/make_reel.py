"""Turn a sequence of 1080x1920 frames into a cross-faded reel over an original synthesized track.

With `voices` (one audio file per frame), each frame is held for as long as its voice line plays and the
music is ducked under the voice.

CLI: python tools/make_reel.py OUT.mp4 SECONDS_PER_FRAME frame1.png frame2.png ...
"""
import os
import subprocess
import sys
import tempfile
import wave

import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_music  # noqa: E402

FADE = 0.5
VOICE_LEAD = 0.3   # seconds after a frame appears before its line starts
VOICE_TAIL = 0.7   # pause after a line before the next frame
MUSIC_UNDER_VOICE = 0.15
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def audio_seconds(path):
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", "22050", wav], check=True)
        with wave.open(wav) as w:
            return w.getnframes() / w.getframerate()


def voice_durations(voices, min_secs=3.0):
    return [max(min_secs, VOICE_LEAD + audio_seconds(v) + VOICE_TAIL) for v in voices]


def build_reel(frames, durs, out_path, voices=None, zoom=False):
    length = sum(durs) - FADE * (len(durs) - 1)
    starts, offset = [0.0], 0.0
    for i in range(1, len(durs)):
        offset += durs[i - 1] - FADE
        starts.append(offset)
    offsets = starts[1:]

    with tempfile.TemporaryDirectory() as tmp:
        music = os.path.join(tmp, "music.wav")
        make_music.main(music, length, [o + FADE / 2 for o in offsets])

        cmd = [FFMPEG, "-y", "-loglevel", "error"]
        for frame, dur in zip(frames, durs):
            cmd += ["-framerate", "30", "-loop", "1", "-t", str(dur), "-i", frame]
        cmd += ["-i", music]
        for v in voices or []:
            cmd += ["-i", v]
        parts = []
        if zoom:
            # slow push-in on every frame (Ken Burns); upscale first so the motion is smooth
            for i in range(len(frames)):
                parts.append(f"[{i}:v]scale=2160:-1,zoompan=z='min(zoom+0.0006,1.06)':x='iw/2-(iw/zoom/2)'"
                             f":y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,setsar=1[z{i}]")
            inputs = [f"[z{i}]" for i in range(len(frames))]
        else:
            inputs = [f"[{i}:v]" for i in range(len(frames))]
        prev = inputs[0]
        for i, offset in enumerate(offsets, start=1):
            label = f"[v{i}]"
            parts.append(f"{prev}{inputs[i]}xfade=transition=fade:duration={FADE}:offset={offset:.2f}{label}")
            prev = label
        parts.append(f"{prev}scale=1080:1920,format=yuv420p,fps=30[vout]")

        music_in = len(durs)
        if voices:
            parts.append(f"[{music_in}:a]volume={MUSIC_UNDER_VOICE}[m]")
            mix = ["[m]"]
            for i, start in enumerate(starts[:len(voices)]):
                ms = int((start + VOICE_LEAD) * 1000)
                parts.append(f"[{music_in + 1 + i}:a]aresample=44100,aformat=channel_layouts=mono,"
                             f"adelay={ms}:all=1[vo{i}]")
                mix.append(f"[vo{i}]")
            parts.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0[aout]")
            audio_map = "[aout]"
        else:
            audio_map = f"{music_in}:a"

        cmd += ["-filter_complex", ";".join(parts), "-map", "[vout]", "-map", audio_map,
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-ac", "2",
                "-shortest", "-movflags", "+faststart", out_path]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    out, secs, frames = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
    build_reel(frames, [secs] * len(frames), out)
    print("done", out)
