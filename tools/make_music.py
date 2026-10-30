"""Synthesize an original, copyright-free background track for the reel.

Lo-fi beat at 100 BPM (Am - F - C - G), soft pad, bass, pluck arpeggio,
and a whoosh into each slide change. Pure stdlib, writes 16-bit mono WAV.
"""
import array
import math
import random
import sys
import wave

SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT

CHORDS = [  # (bass, [pad notes])
    (110.00, [220.00, 261.63, 329.63]),  # Am
    (87.31, [174.61, 220.00, 261.63]),   # F
    (130.81, [196.00, 261.63, 329.63]),  # C
    (98.00, [196.00, 246.94, 293.66]),   # G
]


def render(length, transitions):
    n = int(length * SR)
    out = [0.0] * n
    rnd = random.Random(7)
    two_pi = 2 * math.pi

    def add(start, dur, fn, gain):
        s = int(start * SR)
        for i in range(max(0, s), min(n, s + int(dur * SR))):
            out[i] += gain * fn((i - s) / SR)

    bars = int(length / BAR) + 1
    for b in range(bars):
        t0 = b * BAR
        bass, pad = CHORDS[b % len(CHORDS)]
        # pad: detuned sines with slow attack/release
        for f in pad:
            add(t0, BAR, lambda t, f=f: (math.sin(two_pi * f * t) + math.sin(two_pi * f * 1.004 * t))
                * min(1, t / 0.4) * min(1, (BAR - t) / 0.4), 0.035)
        # bass on beats 1 and 3
        for k in (0, 2):
            add(t0 + k * BEAT, BEAT * 1.8, lambda t, f=bass: math.sin(two_pi * f * t) * math.exp(-t * 2.2), 0.22)
        # pluck arpeggio on 8ths, one octave up
        arp = [p * 2 for p in pad]
        for k in range(8):
            f = arp[[0, 1, 2, 1][k % 4]]
            add(t0 + k * BEAT / 2, 0.45, lambda t, f=f: (math.sin(two_pi * f * t) + 0.3 * math.sin(two_pi * 2 * f * t))
                * math.exp(-t * 9), 0.05)
        for k in range(4):
            beat = t0 + k * BEAT
            if k in (0, 2):  # kick
                add(beat, 0.35, lambda t: math.sin(two_pi * (50 * t + 70 * (1 - math.exp(-t * 30)) / 30))
                    * math.exp(-t * 9), 0.45)
            else:  # soft snare/clap
                add(beat, 0.2, lambda t: (rnd.random() * 2 - 1) * math.exp(-t * 25), 0.10)
            for h in (0, 0.5):  # hi-hat
                prev = [0.0]

                def hat(t, prev=prev):
                    x = rnd.random() * 2 - 1
                    y, prev[0] = x - prev[0], x
                    return y * math.exp(-t * 60)
                add(beat + h * BEAT, 0.08, hat, 0.035)

    # whoosh rising into each slide change
    for tr in transitions:
        state = [0.0]

        def whoosh(t, state=state, dur=0.6):
            state[0] += 0.15 * ((rnd.random() * 2 - 1) - state[0])
            return state[0] * math.sin(math.pi * t / dur) ** 2
        add(tr - 0.45, 0.6, whoosh, 0.9)

    # fades + normalise
    peak = max(abs(x) for x in out) or 1
    pcm = array.array("h")
    for i, x in enumerate(out):
        t = i / SR
        env = min(1, t / 0.8, (length - t) / 1.5)
        pcm.append(int(max(-1, min(1, x / peak * 0.85 * max(env, 0))) * 32767))
    return pcm


def main(path, length, transitions):
    pcm = render(length, transitions)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), [float(x) for x in sys.argv[3:]])
