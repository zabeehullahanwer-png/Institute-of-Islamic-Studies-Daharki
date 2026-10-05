#!/usr/bin/env python3
"""IIS Daharki video editor: raw video -> branded, professional output.

Pipeline (sab ffmpeg se):
  1. Frame: target size (landscape 16:9 / reel 9:16 / square 1:1), blurred
     background fill jab aspect ratio match na ho.
  2. Color: halka contrast/saturation/sharpen touch.
  3. Branding: logo watermark, opening title, speaker lower-third,
     closing line (Urdu text libass ke zariye, Nastaliq shaping sahi rehti hai).
  4. Audio: rumble cut, noise reduction, loudness -14 LUFS (social media standard).
  5. Optional: subtitles (.srt) burn-in, background nasheed/ambience (ducked),
     intro/outro clips jor dena.
  6. Encode: H.264 + AAC, +faststart (Facebook/YouTube/WhatsApp friendly).

Usage:
  iis_edit.py RAW.mp4 -o out.mp4 --title "..." --speaker "..." --speaker-role "..."
  iis_edit.py RAW.mp4 --format reel --trim 00:00:05-00:01:10 ...
  iis_edit.py RAW.mp4 --thumbnail thumb.jpg --title "..."   (sirf thumbnail)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
BRAND_DIR = os.path.join(ROOT, "brand")
FONTS_DIR = os.path.join(BRAND_DIR, "fonts")

FORMATS = {
    "landscape": (1920, 1080),
    "reel": (1080, 1920),
    "square": (1080, 1080),
}


def load_brand():
    with open(os.path.join(BRAND_DIR, "brand.json"), encoding="utf-8") as f:
        brand = json.load(f)
    for key in ("logo", "intro", "outro"):
        path = os.path.join(ROOT, brand.get(key, ""))
        brand[key] = path if brand.get(key) and os.path.isfile(path) else None
    return brand


def run(cmd):
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
        check=True, capture_output=True, text=True,
    ).stdout
    info = json.loads(out)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    return {
        "duration": float(info["format"].get("duration", 0)),
        "width": int(v["width"]) if v else 0,
        "height": int(v["height"]) if v else 0,
        "has_audio": a is not None,
    }


def hex_to_ass(color, alpha="00"):
    c = color.lstrip("#")
    return f"&H{alpha}{c[4:6]}{c[2:4]}{c[0:2]}".upper()


def ass_time(sec):
    sec = max(sec, 0)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def has_rtl(text):
    return any("؀" <= ch <= "ۿ" or "ݐ" <= ch <= "ݿ" for ch in text)


def esc(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def build_ass(path, w, h, dur, brand, title, subtitle, speaker, role, closing):
    """Title card, lower-third aur closing line ka ASS file banata hai."""
    primary = hex_to_ass(brand["colors"]["primary"])
    accent = hex_to_ass(brand["colors"]["accent"])
    white = hex_to_ass(brand["colors"]["text_light"])
    panel = hex_to_ass(brand["colors"]["primary"], "30")
    scale = h / 1080 if w >= h else w / 1080
    fs = lambda n: int(n * scale)

    def font_for(text):
        return brand["fonts"]["urdu"] if has_rtl(text) else brand["fonts"]["latin"]

    # Nastaliq usi point size par Latin se chhota dikhta hai, is liye Urdu text 1.35x
    def size_tag(style, text):
        size = next(st[1] for st in styles if st[0] == style)
        return f"\\fs{int(size * 1.35)}" if has_rtl(text) else ""

    styles = [
        # name, size, primary colour, outline colour, back colour, border style, outline, shadow, alignment, marginV
        ("Title", fs(96), white, panel, panel, 3, fs(28), 0, 5, 0),
        ("Sub", fs(46), accent, panel, panel, 3, fs(14), 0, 5, 0),
        ("LowerName", fs(62), white, primary, primary, 3, fs(16), 0, 1, fs(190)),
        ("LowerRole", fs(40), primary, accent, accent, 3, fs(12), 0, 1, fs(100)),
        ("Closing", fs(58), white, primary, panel, 3, fs(18), 0, 2, fs(110)),
    ]
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
    ]
    for name, size, pc, oc, bc, bs, ol, sh, al, mv in styles:
        lines.append(
            f"Style: {name},{brand['fonts']['latin']},{size},{pc},{pc},{oc},{bc},0,0,0,0,100,100,0,0,"
            f"{bs},{ol},{sh},{al},{fs(80)},{fs(80)},{mv},1"
        )
    lines += ["", "[Events]",
              "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]

    def ev(start, end, style, text, extra=""):
        if not text:
            return
        fn = font_for(text)
        lines.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,"
            f"{{\\fn{fn}{size_tag(style, text)}\\fad(400,400){extra}}}{esc(text)}"
        )

    if title:
        t_end = min(5.0, dur * 0.4)
        sub_y = int(h * 0.5 + fs(150))
        ev(0.3, t_end, "Title", title, f"\\pos({w // 2},{int(h * 0.5)})")
        ev(0.6, t_end, "Sub", subtitle, f"\\pos({w // 2},{sub_y})")
    if speaker and dur > 8:
        s0 = 6.0 if title else 1.5
        s1 = min(s0 + 7.0, dur - 1)
        ev(s0, s1, "LowerName", speaker)
        ev(s0 + 0.2, s1, "LowerRole", role)
    if closing and dur > 6:
        ev(max(dur - 4.5, 0), dur - 0.2, "Closing", closing)

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def filter_escape(path):
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def edit(args):
    brand = load_brand()
    w, h = FORMATS[args.format]
    info = probe(args.input)
    start, end = 0.0, info["duration"]
    if args.trim:
        a, b = args.trim.split("-")
        start, end = to_sec(a), to_sec(b)
    dur = end - start

    tmp = tempfile.mkdtemp(prefix="iis_")
    ass = os.path.join(tmp, "overlay.ass")
    closing = args.closing if args.closing is not None else brand["name_ur"]
    build_ass(ass, w, h, dur, brand, args.title, args.subtitle, args.speaker, args.speaker_role, closing)

    inputs = ["-ss", str(start), "-t", str(dur), "-i", args.input]
    idx = 1
    logo_idx = music_idx = None
    if brand["logo"] and not args.no_logo:
        inputs += ["-loop", "1", "-i", brand["logo"]]
        logo_idx, idx = idx, idx + 1
    if args.music:
        inputs += ["-stream_loop", "-1", "-i", args.music]
        music_idx, idx = idx, idx + 1

    grade = "eq=contrast=1.05:saturation=1.08:gamma=1.0,unsharp=5:5:0.5:5:5:0.0" if not args.no_grade else "null"
    v = [
        f"[0:v]split=2[bg][fg]",
        f"[bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=30:5,eq=brightness=-0.08[bgb]",
        f"[fg]scale={w}:{h}:force_original_aspect_ratio=decrease,setsar=1[fgs]",
        f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2,{grade},fps={args.fps},format=yuv420p[base]",
    ]
    last = "base"
    if logo_idx is not None:
        lw = int(min(w, h) * 0.12)
        v.append(f"[{logo_idx}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa=0.85[logo]")
        v.append(f"[{last}][logo]overlay=W-w-{int(lw * 0.3)}:{int(lw * 0.3)}:shortest=1[lg]")
        last = "lg"
    if args.subtitles:
        style = f"FontName={brand['fonts']['urdu']},FontSize=20,Outline=2,MarginV=40"
        v.append(f"[{last}]subtitles='{filter_escape(args.subtitles)}':fontsdir='{filter_escape(FONTS_DIR)}'"
                 f":force_style='{style}'[sb]")
        last = "sb"
    v.append(f"[{last}]ass='{filter_escape(ass)}':fontsdir='{filter_escape(FONTS_DIR)}',"
             f"fade=t=in:st=0:d=0.5,fade=t=out:st={max(dur - 0.7, 0):.2f}:d=0.7[vout]")

    a = []
    if info["has_audio"]:
        chain = "highpass=f=80,lowpass=f=12000"
        if not args.no_denoise:
            chain += ",afftdn=nr=12:nf=-30"
        a.append(f"[0:a]{chain},loudnorm=I=-14:TP=-1.5:LRA=11,"
                 f"afade=t=in:st=0:d=0.4,afade=t=out:st={max(dur - 0.7, 0):.2f}:d=0.7[voice]")
        if music_idx is not None:
            a.append(f"[{music_idx}:a]volume={args.music_volume},atrim=0:{dur:.2f}[mus]")
            a.append("[mus][voice]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]")
            a.append("[duck][voice]amix=inputs=2:normalize=0,alimiter=limit=0.9[aout]")
        else:
            a.append("[voice]anull[aout]")
    elif music_idx is not None:
        a.append(f"[{music_idx}:a]volume={args.music_volume},atrim=0:{dur:.2f},"
                 f"afade=t=out:st={max(dur - 1.5, 0):.2f}:d=1.5[aout]")

    main_out = os.path.join(tmp, "main.mp4") if (brand["intro"] or brand["outro"]) and not args.no_bumpers else args.output
    cmd = ["ffmpeg", "-hide_banner", "-y", *inputs,
           "-filter_complex", ";".join(v + a), "-map", "[vout]"]
    if a:
        cmd += ["-map", "[aout]"]
    cmd += encode_args(args) + ["-t", f"{dur:.3f}", main_out]
    run(cmd)

    if main_out != args.output:
        join_bumpers(brand, main_out, args, w, h)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Done: {args.output}")


def encode_args(args):
    return ["-c:v", "libx264", "-preset", args.preset, "-crf", str(args.crf),
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart"]


def join_bumpers(brand, main, args, w, h):
    parts = [p for p in (brand["intro"], main, brand["outro"]) if p]
    ins, fl = [], []
    for i, p in enumerate(parts):
        ins += ["-i", p]
        has_a = probe(p)["has_audio"]
        fl.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                  f"setsar=1,fps={args.fps},format=yuv420p[v{i}]")
        fl.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]" if has_a else
                  f"anullsrc=r=48000:cl=stereo,atrim=0:{probe(p)['duration']:.3f}[a{i}]")
    fl.append("".join(f"[v{i}][a{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=1[v][a]")
    run(["ffmpeg", "-hide_banner", "-y", *ins, "-filter_complex", ";".join(fl),
         "-map", "[v]", "-map", "[a]", *encode_args(args), args.output])


def thumbnail(args):
    brand = load_brand()
    w, h = (1280, 720) if args.format == "landscape" else (1080, 1920) if args.format == "reel" else (1080, 1080)
    info = probe(args.input)
    at = args.thumb_at if args.thumb_at is not None else info["duration"] * 0.3
    tmp = tempfile.mkdtemp(prefix="iis_")
    ass = os.path.join(tmp, "thumb.ass")
    build_ass(ass, w, h, 10, brand, args.title, args.subtitle, None, None, brand["name_ur"])
    ins = ["-ss", str(at), "-i", args.input]
    fl = [f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"eq=contrast=1.1:saturation=1.15:brightness=-0.05[b]"]
    last = "b"
    if brand["logo"]:
        ins += ["-i", brand["logo"]]
        lw = int(min(w, h) * 0.16)
        fl.append(f"[1:v]scale={lw}:-1[l]")
        fl.append(f"[b][l]overlay=W-w-{lw // 4}:{lw // 4}[bl]")
        last = "bl"
    # ASS events time-based hain; frame ka PTS 2s par shift karte hain taa ke title card nazar aaye
    fl.append(f"[{last}]setpts=PTS-STARTPTS+2/TB,"
              f"ass='{filter_escape(ass)}':fontsdir='{filter_escape(FONTS_DIR)}'[o]")
    run(["ffmpeg", "-hide_banner", "-y", *ins, "-filter_complex", ";".join(fl),
         "-map", "[o]", "-frames:v", "1", "-q:v", "2", args.thumbnail])
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Thumbnail: {args.thumbnail}")


def to_sec(t):
    parts = [float(p) for p in t.split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("-o", "--output")
    p.add_argument("--format", choices=FORMATS, default="landscape")
    p.add_argument("--title", default="")
    p.add_argument("--subtitle", default="")
    p.add_argument("--speaker", default="")
    p.add_argument("--speaker-role", default="")
    p.add_argument("--closing", help="aakhri line; default: institute ka Urdu naam. Khali '' = kuch nahi")
    p.add_argument("--trim", help="HH:MM:SS-HH:MM:SS")
    p.add_argument("--subtitles", help=".srt file burn karne ke liye")
    p.add_argument("--music", help="background audio (sirf halal/nasheed/ambience)")
    p.add_argument("--music-volume", type=float, default=0.12)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--crf", type=int, default=19)
    p.add_argument("--preset", default="medium")
    p.add_argument("--no-logo", action="store_true")
    p.add_argument("--no-grade", action="store_true")
    p.add_argument("--no-denoise", action="store_true")
    p.add_argument("--no-bumpers", action="store_true", help="intro/outro na lagayen")
    p.add_argument("--thumbnail", help="sirf thumbnail banayen (jpg path)")
    p.add_argument("--thumb-at", type=float, help="thumbnail ka frame (seconds)")
    args = p.parse_args()

    if args.thumbnail:
        thumbnail(args)
        return
    if not args.output:
        base, _ = os.path.splitext(args.input)
        args.output = f"{base}_IIS_{args.format}.mp4"
    edit(args)


if __name__ == "__main__":
    main()
