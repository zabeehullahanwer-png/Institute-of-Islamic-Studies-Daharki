#!/usr/bin/env python3
"""Student Journey (donor video) — one-off build for this project.

raw.mp4 (368x496 WhatsApp clip) -> final 1080x1920 vertical:
  intro card -> framed video with bilingual subtitles + highlight chips -> closing card.
Run from repo root or anywhere:  python3 projects/2026-11-07-student-journey/build.py
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FONTS = os.path.join(ROOT, "brand", "fonts")
brand = json.load(open(os.path.join(ROOT, "brand", "brand.json"), encoding="utf-8"))

W, H = 1080, 1920
VID_W, VID_H, VID_Y = 960, 1294, 200          # 368x496 scaled, framed
SUB_TOP = VID_Y + VID_H                        # bottom band starts here
END = 48.70                                    # trailing silence trimmed
INTRO, OUTRO = 3.6, 5.0

GREEN, GOLD = brand["colors"]["primary"], brand["colors"]["accent"]
UR, EN, AR = "Noto Nastaliq Urdu", "Poppins SemiBold", "Noto Naskh Arabic"

# (start, end, urdu, english) — speech was Urdu / Arabic / English; both lines always shown
SUBS = [
    (0.08, 2.70, "السلام علیکم ورحمۃ اللہ وبرکاتہ", "Peace and blessings be upon you"),
    (2.80, 4.55, "میں شاہد ہوں", "I am Shahid"),
    (4.60, 9.10, "جب میں اس ادارے میں آیا تو بالکل صفر سے آغاز کیا", "When I joined this institution, I started from zero."),
    (9.20, 12.50, "لیکن اس جگہ نے میری زندگی بدل دی", "But this place changed my life."),
    (12.55, 16.60, "انہوں نے مجھے نورانی قاعدہ کے پہلے حرف سے پڑھایا", "They taught me from the very first letter of the Noorani Qaida"),
    (16.65, 19.10, "یہاں تک کہ میں نے قرآنِ کریم حفظ کر لیا", "until I completed memorising the Holy Quran."),
    (19.20, 23.10, "یہاں صرف دین ہی نہیں، اسکول کی تعلیم بھی دی گئی", "Not only religion — school education was given too."),
    (23.20, 27.20, "میں نے کے جی سے شروع کیا، آج میں آٹھویں جماعت میں ہوں", "I started in KG; today I am in Grade 8."),
    (27.30, 31.40, "ساتھ ہی الحمدللہ، عالم کورس کے دوسرے سال میں ہوں", "Alhamdulillah, I am also in the 2nd year of the Alim course."),
    (31.45, 35.10, "عالمِ دین بننے کا میرا خواب پورا ہو رہا ہے", "My dream of becoming a scholar is coming true."),
    (35.20, 39.65, "یہاں رہائش، کتابوں اور تعلیم کا تمام خرچ بالکل مفت ہے", "Here, our living, books and Quran education are completely free."),
    (39.70, 42.80, "یہ ادارہ ایک خاندان کی طرح ہمارا خیال رکھتا ہے", "This institution cares for us like a family."),
    (43.65, 47.10, "مجھے خوبصورت مستقبل دینے کا بہت شکریہ", "Thank you so much for giving me a beautiful future."),
    (47.15, 48.60, "بہت بہت شکریہ", "Thank you very much"),
]

# highlight chips on the video (start, end, urdu, english)
CHIPS = [
    (16.70, 21.0, "حافظِ قرآن", "Hafiz-e-Quran"),
    (23.30, 27.2, "کے جی سے آٹھویں جماعت", "KG → Grade 8"),
    (27.40, 34.8, "عالم کورس · سالِ دوم", "Alim Course · Year 2"),
    (35.30, 42.6, "رہائش · کتب · تعلیم — مفت", "100% Free for Students"),
]


def c(hexcol, alpha="00"):
    h = hexcol.lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def t(sec):
    sec = max(sec, 0)
    return f"{int(sec // 3600)}:{int(sec % 3600 // 60):02d}:{sec % 60:05.2f}"


def ass(path, events):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,{EN},40,{c('#FFFFFF')},{c('#FFFFFF')},{c('#000000','80')},{c('#000000','80')},0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(events) + "\n")


def ev(start, end, tags, text, layer=1):
    return f"Dialogue: {layer},{t(start)},{t(end)},Base,,0,0,0,,{{{tags}}}{text}"


def card_events(dur, lines):
    out = []
    for i, (y, font, size, col, text, extra) in enumerate(lines):
        d = 0.15 + i * 0.18
        out.append(ev(d, dur, f"\\an5\\pos({W // 2},{y})\\fn{font}\\fs{size}\\c{c(col)}\\bord0\\shad0"
                              f"\\fad(450,350){extra}", text))
    return out


def gold_rule(y, width, start, end):
    x0, x1 = (W - width) // 2, (W + width) // 2
    return ev(start, end, f"\\an7\\pos(0,0)\\p1\\c{c(GOLD)}\\bord0\\shad0\\fad(450,350)",
              f"m {x0} {y} l {x1} {y} l {x1} {y + 3} l {x0} {y + 3}", layer=0)


def run(cmd):
    print("+", " ".join(cmd[:6]), "...")
    subprocess.run(cmd, check=True)


def bg_input(dur):
    # deep green vertical gradient
    return ["-f", "lavfi", "-i",
            f"gradients=s={W}x{H}:d={dur}:r=30:c0=0x0E6B45:c1=0x05311F:x0=540:y0=0:x1=540:y1={H}:nb_colors=2"]


def esc(p):
    return p.replace(":", "\\:").replace("'", "\\'")


def render_card(name, dur, events):
    a = os.path.join(HERE, f"{name}.ass")
    ass(a, events)
    out = os.path.join(HERE, f"{name}.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *bg_input(dur),
         "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={dur}",
         "-filter_complex",
         f"[0:v]ass='{esc(a)}':fontsdir='{esc(FONTS)}',fade=t=in:st=0:d=0.4,"
         f"fade=t=out:st={dur - 0.4}:d=0.4,format=yuv420p[v]",
         "-map", "[v]", "-map", "1:a", "-t", str(dur), *ENC, out])
    return out


ENC = ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-r", "30"]


def main_events():
    e = []
    # header band
    e.append(ev(0, END, f"\\an5\\pos({W // 2},56)\\fn{EN}\\fs30\\fsp6\\c{c(GOLD)}\\bord0", "STUDENT JOURNEY"))
    e.append(ev(0, END, f"\\an5\\pos({W // 2},128)\\fn{UR}\\fs84\\c{c('#FFFFFF')}\\bord0", "طالب علم کا تعلیمی سفر"))
    # subtitles (bottom band, never over the face)
    for s, en_, ur, eng in SUBS:
        e.append(ev(s, en_, f"\\an5\\q0\\pos({W // 2},{SUB_TOP + 150})\\fn{UR}\\fs92\\c{c('#FFFFFF')}\\bord0\\fad(120,120)", ur))
        e.append(ev(s, en_, f"\\an5\\q0\\pos({W // 2},{SUB_TOP + 330})\\fn{EN}\\fs38\\c{c(GOLD)}\\bord0\\fad(120,120)", eng))
    # footer
    e.append(ev(0, END, f"\\an5\\pos({W // 2},{H - 34})\\fn{EN}\\fs24\\fsp2\\c{c('#FFFFFF', '60')}\\bord0",
                brand["name_en"].upper()))
    # highlight chips: gold panel at bottom-right of the video (clear of the face), slides in
    cw, ch = 600, 210
    for s_, e_, ur, eng in CHIPS:
        x1, y0 = (W + VID_W) // 2 - 24, VID_Y + VID_H - ch - 30
        x0 = x1 - cw
        mv = lambda y: f"\\move({x0 + 70},{y},{x0},{y},0,260)"
        e.append(ev(s_, e_, f"\\an7{mv(y0)}\\p1\\c{c(GOLD)}\\bord0\\shad4\\4c{c('#000000','90')}\\fad(260,220)",
                    f"m 0 0 l {cw} 0 l {cw} {ch} l 0 {ch}", layer=2))
        e.append(ev(s_, e_, f"\\an7{mv(y0 + ch - 54)}\\p1\\c{c(GREEN)}\\bord0\\shad0\\fad(260,220)",
                    f"m 0 0 l {cw} 0 l {cw} 54 l 0 54", layer=3))
        cx = cw // 2
        e.append(ev(s_, e_, f"\\an5\\move({x0 + 70 + cx},{y0 + 76},{x0 + cx},{y0 + 76},0,260)\\fn{UR}\\fs76"
                            f"\\c{c(GREEN)}\\bord0\\shad0\\fad(260,220)", ur, layer=4))
        e.append(ev(s_, e_, f"\\an5\\move({x0 + 70 + cx},{y0 + ch - 27},{x0 + cx},{y0 + ch - 27},0,260)\\fn{EN}"
                            f"\\fs30\\c{c('#FFFFFF')}\\bord0\\shad0\\fad(260,220)", eng, layer=4))
    return e


def render_main():
    a = os.path.join(HERE, "main.ass")
    ass(a, main_events())
    out = os.path.join(HERE, "main.mp4")
    border = 6
    fc = ";".join([
        # video: upscale cleanly, gentle denoise, tiny grade + sharpen
        f"[1:v]trim=0:{END},setpts=PTS-STARTPTS,hqdn3d=2:2:4:4,"
        f"scale={VID_W}:{VID_H}:flags=lanczos,eq=contrast=1.04:saturation=1.06:brightness=0.01,"
        f"unsharp=5:5:0.6,setsar=1[vid]",
        f"color=c={GOLD}:s={VID_W + 2 * border}x{VID_H + 2 * border}:d={END}:r=30[frame]",
        f"[frame][vid]overlay={border}:{border}[fv]",
        f"[0:v][fv]overlay={(W - VID_W) // 2 - border}:{VID_Y - border}:shortest=1,"
        f"ass='{esc(a)}':fontsdir='{esc(FONTS)}',format=yuv420p[v]",
        # audio: clean + loudness for phones
        f"[1:a]atrim=0:{END},asetpts=PTS-STARTPTS,highpass=f=90,lowpass=f=11000,afftdn=nr=10:nf=-35,"
        f"acompressor=threshold=-22dB:ratio=2.5:attack=15:release=200,"
        f"loudnorm=I=-15:TP=-1.5:LRA=9,aresample=48000,"
        f"afade=t=in:st=0:d=0.15,afade=t=out:st={END - 0.4}:d=0.4[a]",
    ])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *bg_input(END),
         "-i", os.path.join(HERE, "raw.mp4"), "-filter_complex", fc,
         "-map", "[v]", "-map", "[a]", "-t", str(END), *ENC, out])
    return out


def main():
    intro = render_card("intro", INTRO, card_events(INTRO, [
        (640, EN, 34, GOLD, "STUDENT JOURNEY", "\\fsp8"),
        (800, UR, 140, "#FFFFFF", "طالب علم کا تعلیمی سفر", ""),
        (965, EN, 38, "#FFFFFF", "An Educational Journey with", ""),
        (1150, UR, 100, GOLD, brand["name_ur"], ""),
        (1300, EN, 36, "#FFFFFF", brand["name_en"], ""),
    ]) + [gold_rule(1040, 260, 0.5, INTRO)])
    main_v = render_main()
    outro = render_card("outro", OUTRO, card_events(OUTRO, [
        (700, UR, 112, "#FFFFFF", "آپ کا تعاون، ان کا روشن مستقبل", ""),
        (860, EN, 42, GOLD, "Your support builds their future", ""),
        (1080, UR, 96, "#FFFFFF", brand["name_ur"], ""),
        (1225, EN, 34, "#FFFFFF", brand["name_en"], ""),
        (1295, EN, 28, GOLD, "Daharki · Sindh · Pakistan", "\\fsp3"),
    ]) + [gold_rule(960, 260, 0.6, OUTRO)])

    final = os.path.join(HERE, "IIS-Daharki_Student-Journey_Shahid.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", intro, "-i", main_v, "-i", outro,
         "-filter_complex", "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]",
         "-map", "[v]", "-map", "[a]", *ENC, "-movflags", "+faststart", final])
    print("Done:", final)


if __name__ == "__main__":
    main()
