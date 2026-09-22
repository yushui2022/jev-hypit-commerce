"""Rebuild the published 26-second Hypit film and apply its brand overlays."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

PRODUCTION = Path(__file__).resolve().parent
ROOT = PRODUCTION.parents[1]
CLI = ROOT / 'node_modules/@hypit/hypit/bin/hypit.mjs'


def verify_assets():
    for item in json.loads((PRODUCTION / 'assets-manifest.json').read_text()):
        path = PRODUCTION / item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Missing or changed release asset: {item["path"]}')
    print('All 107 release assets verified.')


def run(*args):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-assets', action='store_true')
    args = parser.parse_args()
    if args.check_assets:
        verify_assets()
        return
    output = ROOT / 'output/hd-fast'
    output.mkdir(parents=True, exist_ok=True)
    run('npm', 'run', 'build')
    author = PRODUCTION / 'runs/main.svrun'
    run('node', CLI, 'check', author)
    build = subprocess.Popen(['node', str(CLI), 'build', str(author), '--follow'],
                             cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = []
    for line in build.stdout:
        print(line, end='', flush=True)
        lines.append(line)
    if build.wait():
        raise RuntimeError('Hypit build failed; inspect the log above.')
    ids = re.findall(r'bld_[A-Za-z0-9_]+', ''.join(lines))
    if not ids:
        raise RuntimeError('Hypit did not return a build ID.')
    base = output / 'base.mp4'
    run('node', CLI, 'get', ids[-1], '--output', 'final.video', '--to', base)
    for brand, width, bottom in [('guanyi', 170, 30), ('yeadon', 145, 25)]:
        run('ffmpeg', '-y', '-i', base, '-i', PRODUCTION / f'assets/branding/{brand}.png',
            '-filter_complex', f'[1:v]scale={width}:-1[logo];[0:v][logo]overlay=W-w-35:H-h-{bottom}[v]',
            '-map', '[v]', '-map', '0:a?', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium',
            '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', output / f'{brand}-hd.mp4')
    print(f'Finished videos: {output}')


if __name__ == '__main__':
    main()
