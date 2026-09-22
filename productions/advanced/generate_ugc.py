"""Generate four reference-driven UGC clips through TokensFactory; keys stay in memory."""
import concurrent.futures, getpass, json, os, subprocess, time
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
CACHE=ROOT/'output/advanced-generation';CACHE.mkdir(parents=True,exist_ok=True)
KEY=os.environ.get('TOKENSFACTORY_API_KEY') or getpass.getpass('TokensFactory API key: ')
RAW='https://raw.githubusercontent.com/Yeadon8888/jev-hypit-commerce/main/'
SCENES=[
 (3,'perfume','A stylish apartment with soft afternoon window light. The creator picks up the amber square perfume bottle, turns their head slightly toward the window then back to camera, rotates the bottle once to show the front, and sets it beside a small handbag.', 'A little finishing touch before heading out. Here is the bottle up close. Which scent is your everyday pick?'),
 (39,'speaker','A real home desk with a laptop and plant. The creator holds the exact black speaker phone stand, places a phone on it, turns slightly to check the screen, then looks back with a natural smile. Keep the speaker and stand geometry consistent.', 'Here is a simple desk setup idea. Phone up here, speaker underneath. Take a closer look at this little stand.'),
 (46,'tumbler','A bright lived-in kitchen. The creator lifts the exact handled tumbler from the counter, shows the lid and straw without removing parts, turns their head slightly toward camera, and takes a small casual sip.', 'A quick look at my grab-and-go setup. Handle, straw, and room for ice. Which color would you choose?'),
 (82,'bag','A softly lit apartment entryway. The creator wears the exact striped padded cloud crossbody bag, slightly turns their shoulders and head to show the side silhouette, then holds the bag closer to camera and smiles.', 'This striped bag adds a playful touch to a simple outfit. Here is the shape up close. How would you style it?')]

def request(method,path,payload=None):
 config='header = "Authorization: Bearer '+KEY+'"\n'
 cmd=['curl','-sS','--max-time','150','--config','-','-A','Mozilla/5.0','-X',method,'https://tokensfactory.cc'+path]
 if payload is not None:
  f=CACHE/(str(payload.get('_name','request'))+'.request.json');body={k:v for k,v in payload.items() if not k.startswith('_')};f.write_text(json.dumps(body));cmd+=['-H','Content-Type: application/json','--data-binary','@'+str(f)]
 r=subprocess.run(cmd,input=config,text=True,capture_output=True)
 if r.returncode:raise RuntimeError('Network request failed: '+str(r.returncode))
 try:return json.loads(r.stdout)
 except ValueError:raise RuntimeError('Non-JSON response from media service')

def make(scene):
 idx,name,direction,dialogue=scene;taskfile=CACHE/(name+'.task.json');output=BASE/'assets/ugc'/(name+'.mp4')
 if output.exists():
  probe=subprocess.run(['ffprobe','-v','error',str(output)],capture_output=True)
  if probe.returncode==0:return name+' already downloaded'
 prompt=f'''Create a 10 second vertical 9:16 American English TikTok UGC product showcase. Image 1 is the exact fictional adult creator identity; preserve facial identity, hair and natural appearance. Image 2 is the exact product; preserve its color, shape, proportions and recognizable packaging. {direction} Shoot on a smartphone at eye level with natural daylight, subtle handheld movement, realistic skin and hands. Begin with direct eye contact and a small natural head turn. Use two or three motivated jump cuts between medium shot and product close-up. Friendly conversational American English delivery, exact dialogue: "{dialogue}" Clean synchronized spoken audio and quiet room tone; no music. No subtitles, overlays or new logos. Retain the product's real printed label where visible. No exaggerated performance or fabricated efficacy claims. Show one creator and one product only.'''
 payload={'model':'veo-omni-flash','prompt':prompt,'duration':10,'aspect_ratio':'9:16','Ingredients_images':[RAW+f'productions/advanced/assets/references/creator-{idx:03d}.png',RAW+f'productions/hd-fast/assets/products/{idx:03d}.webp'],'_name':name}
 (BASE/'prompts').mkdir(exist_ok=True);(BASE/'prompts'/(name+'.json')).write_text(json.dumps({k:v for k,v in payload.items() if not k.startswith('_')},ensure_ascii=False,indent=2))
 if taskfile.exists():r=json.loads(taskfile.read_text())
 else:
  r=request('POST','/v1/videos',payload);taskfile.write_text(json.dumps(r))
 taskid=r.get('id') or r.get('task_id')
 if not taskid:raise RuntimeError(name+' submission failed: '+json.dumps(r)[:500])
 print(name,'task',taskid,flush=True)
 for attempt in range(180):
  r=request('GET','/v1/videos/'+taskid);taskfile.write_text(json.dumps(r));status=r.get('status') or r.get('state')
  if attempt%3==0:print(name,status,flush=True)
  if status=='failed':raise RuntimeError(name+' failed: '+json.dumps(r.get('error')))
  if status=='completed':
   urls=(r.get('metadata') or {}).get('result_urls') or []
   url=r.get('video_url') or r.get('url') or (urls[0] if urls else None)
   if not url:raise RuntimeError(name+' completed without URL')
   download=['curl','-fL','--retry','2','-sS','-A','Mozilla/5.0',url,'-o',str(output)]
   config=''
   if url.startswith('https://tokensfactory.cc/'):
    download+=['--config','-'];config='header = \"Authorization: Bearer '+KEY+'\"\n'
   subprocess.run(download,input=config,text=True,check=True)
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(output)]))
   (BASE/'assets/ugc'/(name+'.provenance.json')).write_text(json.dumps({'model':payload['model'],'task_id':taskid,'result_url':url,'product_index':idx,'probe':probe},ensure_ascii=False,indent=2))
   print(name,'complete',probe['format']['duration'],flush=True);return name
  time.sleep(20)
 raise RuntimeError(name+' still pending; resume the same task later')

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  failed=[]
  for f in concurrent.futures.as_completed([pool.submit(make,s) for s in SCENES]):
   try:print('RESULT',f.result(),flush=True)
   except Exception as e:failed.append(str(e));print('ERROR',str(e),flush=True)
  if failed:raise SystemExit(1)
