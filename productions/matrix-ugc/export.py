"""Render the advanced film from its archived media without model calls."""
from pathlib import Path
import subprocess,re,uuid
ROOT=Path(__file__).resolve().parents[2]
PROD=ROOT/'productions/matrix-ugc'
CLI=ROOT/'node_modules/@hypit/hypit/bin/hypit.mjs'
NAMES=['perfume','speaker','tumbler','bag']

def run(*args):subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
def prepare():
 import runpy
 runpy.run_path(str(ROOT/'productions/advanced/export.py'))['prepare']()
 dest=ROOT/'output/matrix-ugc';dest.mkdir(parents=True,exist_ok=True)
 return dest

def main():
 dest=prepare();run('npm','run','build');author=PROD/'runs/main.svrun'
 run('node',CLI,'check',author)
 p=subprocess.Popen(['node',str(CLI),'build',str(author),'--follow'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);lines=[]
 for line in p.stdout:print(line,end='',flush=True);lines.append(line)
 if p.wait():raise RuntimeError('Hypit render failed')
 ids=re.findall(r'bld_[A-Za-z0-9_]+',''.join(lines))
 if not ids:raise RuntimeError('Missing build ID')
 temp=dest/('export-'+uuid.uuid4().hex+'.mp4')
 run('node',CLI,'get',ids[-1],'--output','final.video','--to',temp)
 temp.replace(dest/'base.mp4')
 for brand,width,bottom in [('guanyi',170,30),('yeadon',145,25)]:
  run('ffmpeg','-v','error','-y','-i',dest/'base.mp4','-i',ROOT/f'productions/hd-fast/assets/branding/{brand}.png','-filter_complex',f'[1:v]scale={width}:-1[logo];[0:v][logo]overlay=W-w-35:H-h-{bottom}[v]','-map','[v]','-map','0:a?','-c:v','libx264','-crf','16','-preset','fast','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',dest/f'{brand}-matrix-ugc.mp4')
 print('Videos:',dest)
if __name__=='__main__':main()
