"""Prepare arbitrary product-avatar pairs and export a real Hypit MP4."""
import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
from xml.sax.saxutils import quoteattr
ROOT=Path(__file__).resolve().parent
CLI=ROOT/'node_modules/@hypit/hypit/bin/hypit.mjs'

def run(*args):
    subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
def hypit(*args):run('node',CLI,*args)

def setup():
    chrome=os.environ.get('CHROME_PATH')
    if not chrome:
        candidates=['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser']
        chrome=next((x for x in candidates if Path(x).exists()),None)
    if not chrome:raise ValueError('Chrome/Chromium not found. Set CHROME_PATH to its executable.')
    runtime={'format':'hypit.runtime-local@1','dataRoot':'.hypit/runtimes/local','credentials':{'platform':{'use':'@hypit/credential-store-platform'}},'endpoints':{'media.local':{'use':'@hypit/provider-media-local'},'hyperframes.local':{'use':'@hypit/provider-hyperframes-local','config':{'chromePath':chrome,'workers':2}}}}
    (ROOT/'hypit.runtime.json').write_text(json.dumps(runtime,indent=2))
    hypit('runtime','use','hypit.runtime.json')
    hypit('packages','install','@fontsource-variable/inter@5.3.0')
    hypit('packages','install','@fontsource-variable/noto-sans-sc@5.3.0')
    hypit('runtime','up','--endpoint','media.local','--endpoint','hyperframes.local')

def prepare(source,output,url):
    source=Path(source).resolve();data=json.loads(source.read_text());pairs=data.get('pairs')
    if not isinstance(pairs,list) or not 1<=len(pairs)<=200:raise ValueError('Storyboard must contain 1–200 pairs')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    images=output/'images';images.mkdir(exist_ok=True);assets=[];elements=[]
    for i,pair in enumerate(pairs):
        for kind in ('product','avatar'):
            raw=pair[kind].get('image','');path=(source.parent/raw).resolve()
            if not raw or not path.is_file():raise ValueError(f'Missing {kind} image: {raw}')
            if path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):raise ValueError('Use PNG, JPEG or WebP images')
            name=f'{kind}{i}';dest=images/(name+path.suffix.lower());shutil.copyfile(path,dest)
            media=' media-type="image/svg+xml"' if path.suffix.lower()=='.svg' else ''
            assets.append(f'<asset:Image id="{name}" src={quoteattr("./images/"+dest.name)}{media}/>')
        elements.append(f'<scene:Message id="pair{i}" sender={quoteattr(pair["avatar"].get("id","avatar"))} text={quoteattr(pair["product"].get("name","product"))} side="left" at="{i}f" product-image={{product{i}}} avatar-image={{avatar{i}}}/>')
    xml='''<?svml using="@hypit/markup@1"?><svml>
<import as="time" from="@hypit/timeline-author@1"/><import as="spatial" from="@hypit/spatial@1"/>
<import as="fonts" from="@hypit/fonts-open@1"/><import as="asset" from="@hypit/media@1"/>
<import as="scene" from="@yeadon/commerce-scene@1"/><import as="film" from="@hypit/film@1"/>
<import as="render" from="@hypit/render-hyperframes@1"/><import as="look" source="./main.svs"/>
<time:Clock id="clock" frame-rate="30"/><time:Timeline id="program" clock={clock} end="15s"/>
<spatial:Canvas id="canvas" width="1280" height="720"/>
<fonts:Stack id="font" family="inter" weight="600" style="normal"><fonts:Fallback family="noto-sans-sc" weight="600" style="normal"/></fonts:Stack>
'''+''.join(assets)+f'<scene:Scene id="matching" timeline={{program.timeline}} canvas={{canvas}} font={{font}} during="program" title={quoteattr(url)}>'+''.join(elements)+'''</scene:Scene>
<film:Film id="main" canvas={canvas} timeline={program.timeline} appearance={look.film.main}><film:Track source={matching.track}/></film:Film>
<render:Video id="final" composition={main.composition} timeline={program.timeline}/></svml>'''
    (output/'main.svml').write_text(xml);(output/'main.svs').write_text('<?svml using="@hypit/svs@1"?><sheet version="1">film.main {background:#faf5f8;}</sheet>')
    (output/'main.svrun').write_text('<?svml using="@hypit/run-markup@1"?><svrun version="1"><author source="./main.svml"/><target output="final.video"/></svrun>')
    return output/'main.svrun'

def build(source,output,url):
    run('npm','run','build');author=prepare(source,output,url)
    hypit('check',author)
    result=subprocess.run(['node',str(CLI),'build',str(author),'--follow'],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    print(result.stdout)
    if result.returncode:raise ValueError('Hypit build failed; see output above')
    ids=re.findall(r'bld_[A-Za-z0-9_]+',result.stdout)
    if not ids:raise ValueError('Build ID not found in Hypit response')
    hypit('get',ids[-1],'--output','final.video','--to',Path(output).resolve()/'video.mp4')

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('setup');sub.add_parser('demo')
    for verb in ('prepare','build'):
        cmd=sub.add_parser(verb);cmd.add_argument('storyboard',type=Path);cmd.add_argument('--output',type=Path,default=ROOT/'output/custom');cmd.add_argument('--repo-url',default='github.com/Yeadon8888/jev-hypit-commerce')
    args=p.parse_args()
    if args.command=='setup':setup()
    elif args.command=='demo':build(ROOT/'examples/storyboard.json',ROOT/'output/demo','github.com/Yeadon8888/jev-hypit-commerce')
    elif args.command=='prepare':print(prepare(args.storyboard,args.output,args.repo_url))
    else:build(args.storyboard,args.output,args.repo_url)
if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,subprocess.CalledProcessError) as e:print('Error:',e,file=sys.stderr);sys.exit(1)
