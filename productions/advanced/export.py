"""Render the advanced film from its archived media without model calls."""
from pathlib import Path
import subprocess,re,uuid
ROOT=Path(__file__).resolve().parents[2]
PROD=ROOT/'productions/advanced'
CLI=ROOT/'node_modules/@hypit/hypit/bin/hypit.mjs'
NAMES=['perfume','speaker','tumbler','bag']

def run(*args):subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
def prepare():
 dest=ROOT/'output/advanced';dest.mkdir(parents=True,exist_ok=True)
 for name in NAMES:
  target=dest/(name+'-30fps.mp4')
  source=PROD/('assets/sources' if name=='tumbler' else 'assets/ugc')/(name+'.mp4')
  if not target.exists() or target.stat().st_mtime<source.stat().st_mtime:
   run('ffmpeg','-v','error','-y','-i',source,'-t','10','-vf','fps=30,scale=720:1280:flags=lanczos,tpad=stop_mode=clone:stop_duration=2','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',target)
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
 temp.replace(dest/'advanced-guanyi.mp4')
 print('Video:',dest/'advanced-guanyi.mp4')
if __name__=='__main__':main()
