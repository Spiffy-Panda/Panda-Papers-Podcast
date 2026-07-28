# output/odesteer — license

## Upstream work

This folder contains audio and JSON derivatives of:

> *ODESteer: A Unified ODE-Based Steering Framework for LLM Alignment*
> Hongjue Zhao, Haosen Sun, Jiangtao Kong, Xiaochang Li, Qineng Wang, Liwei
> Jiang, Qi Zhu, Tarek Abdelzaher, Yejin Choi, Manling Li, Huajie Shao.
> arXiv:[2602.17560](https://arxiv.org/abs/2602.17560).

The original paper is © its authors and is distributed by them under
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
Nothing in this folder modifies or restricts the terms under which arXiv
distributes the original work; the authoritative source is the arXiv page
linked above.

## Derivative works in this folder

The files in this folder — `part_NN_*.wav` (synthesized audio narration),
`part_NN_*_timestamps.json` (alignment data), `dialog_part_*.json`
(two-presenter dialog scripts), and `manifest.json` (workspace index) — are
derivative works of the paper text above. They were produced by Panda
Notarianni using:

- The two-presenter dialog scripter pipeline in this repository.
- Microsoft Windows neural TTS voices (via `Windows.Media.SpeechSynthesis`).

Per the ShareAlike clause (§3(b)(1)) of the upstream license, these
derivatives are released under the **same** license:

> © 2026 Panda Notarianni. Licensed under
> [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

In practice: non-commercial reuse is fine with attribution to both the
original paper authors and this repository; commercial reuse is not
permitted; any further derivatives must also be CC BY-NC-SA 4.0.

The Microsoft neural voices themselves are subject to the Microsoft Windows
EULA, which may impose additional restrictions on commercial redistribution
of audio renderings. This notice does not override those terms — consult the
Windows EULA separately before any commercial use.
