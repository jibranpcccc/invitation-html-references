from pathlib import Path
import json,base64,io,hashlib
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import pymupdf
R=Path(__file__).resolve().parents[1];OUT=R;QA=R/'qa-local';QA.mkdir(exist_ok=True);results={};fail=[]
def dec(s):return np.array(Image.open(io.BytesIO(base64.b64decode(s.split(',',1)[1]))).convert('RGBA'))
with sync_playwright() as p:
 b=p.chromium.launch()
 for slug in ['whale-birthday','pumpkin-gender-reveal']:
  context=b.new_context(offline=True,accept_downloads=True,viewport={'width':1440,'height':1100});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto((OUT/slug/'Editor.html').as_uri());page.wait_for_function('InvitationEditor.ready');z={};cfg=page.evaluate('CONFIG')
  def reset():page.locator('#reset').click()
  def put(key,patch):page.evaluate('([key,patch])=>{Object.assign(fields.find(f=>f.key===key),patch);updateInputs();render()}',[key,patch])
  def pixels():return dec(page.evaluate("canvas.toDataURL('image/png')"))
  # Wrap changes must invalidate the cached raster; valid wrapping may recover an overflow.
  put('date',{'text':'Saturday, September 25, 2027','size':15,'wrap':False});a=pixels();off=page.evaluate('issues');put('date',{'wrap':True});bb=pixels();on=page.evaluate('issues');z['wrap_changes_pixels']=bool(np.any(a!=bb));z['wrap_off_issues']=off;z['wrap_on_issues']=on
  if not z['wrap_changes_pixels'] and not (off and on):fail.append(slug+' wrap inert')
  # Multiline underline and line-height controls.
  reset();multikey='date' if slug=='whale-birthday' else 'venue';multitext='May\n2027' if slug=='whale-birthday' else 'Sea\nHall';multisize=8 if slug=='whale-birthday' else 9;put(multikey,{'text':multitext,'wrap':True,'size':multisize,'lineHeight':1,'underline':True});a=pixels();ia=page.evaluate('issues');Image.fromarray(a).save(QA/(slug+'-multiline-underline.png'));put(multikey,{'lineHeight':1.5});bb=pixels();z['line_height_changes_pixels']=bool(np.any(a!=bb));z['multiline_underline_issues']=ia
  if not z['line_height_changes_pixels'] or ia:fail.append(slug+' multiline styles')
  z['underline_each_field']=[]
  for f in cfg['defaults']:
   reset();before=pixels();put(f['key'],{'underline':True});changed=int(np.any(before!=pixels(),axis=2).sum());z['underline_each_field'].append({'key':f['key'],'changed_pixels':changed,'issues':page.evaluate('issues')});
   if not changed:fail.append(slug+' underline '+f['key'])
  # Every color picker has an independent visible effect when its effect is enabled.
  key='name' if slug=='whale-birthday' else 'date';idx=next(i for i,f in enumerate(cfg['defaults']) if f['key']==key);z['color_controls']=[]
  for control in ['outline','shadowColor','palette0','palette1','palette2']:
   reset();put(key,{'outlineWidth':.5,'shadow':.5,'mode':'palette','palette':['#9b1540','#14599c','#23793a']});page.locator('details').evaluate_all('(es)=>es.forEach(e=>e.open=true)');page.locator('#selected').select_option(str(idx));a=pixels();page.locator('#'+control).evaluate('(e)=>{e.value="#ff6600";e.dispatchEvent(new Event("input",{bubbles:true}))}');page.evaluate('()=>new Promise(requestAnimationFrame)');changed=int(np.any(a!=pixels(),axis=2).sum());z['color_controls'].append({'control':control,'changed_pixels':changed});
   if not changed:fail.append(slug+' color '+control)
  # Stress input cannot allocate an unbounded canvas or silently disappear as valid.
  reset();put(key,{'text':'W'*160,'size':120});z['stress_blocked']=bool(page.evaluate('issues'));z['stress_message']=page.evaluate('issues');
  if not z['stress_blocked']:fail.append(slug+' stress not blocked')
  reset();state=page.evaluate('({product:CONFIG.id,version:1,fields:structuredClone(fields)})');state['fields'][0].update(text='Nate\u2019s' if key=='name' else 'June 1',underline=True,italic=True,bold=True);path=QA/(slug+'-final-settings.json');path.write_text(json.dumps(state),encoding='utf-8');page.locator('#loadSettings').set_input_files(str(path));page.wait_for_function('fields[0].underline');style=pixels();
  with page.expect_download() as ev:page.locator('#saveHtml').click()
  saved=QA/(slug+'-final-personalized.html');ev.value.save_as(str(saved));q=context.new_page();q.goto(saved.as_uri());q.wait_for_function('InvitationEditor.ready');z['final_personalized_exact']=bool(np.array_equal(style,dec(q.evaluate("canvas.toDataURL('image/png')"))));q.close();
  if not z['final_personalized_exact']:fail.append(slug+' final personalized')
  # Final actual downloads after the final code edit.
  reset()
  for id,target in [('png',OUT/slug/'Preview.png'),('pdf',QA/(slug+'-Final.pdf'))]:
   with page.expect_download() as ev:page.locator('#'+id).click()
   ev.value.save_as(str(target))
  im=Image.open(OUT/slug/'Preview.png');doc=pymupdf.open(QA/(slug+'-Final.pdf'));pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),alpha=False);arr=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3);z['pdf_matches_png_exactly']=bool(np.array_equal(arr,np.array(im.convert('RGB'))));z['png_size']=im.size;z['png_dpi']=im.info.get('dpi');z['pdf_points']=[doc[0].rect.width,doc[0].rect.height];z['html_sha256']=hashlib.sha256((OUT/slug/'Editor.html').read_bytes()).hexdigest();z['png_sha256']=hashlib.sha256((OUT/slug/'Preview.png').read_bytes()).hexdigest();z['errors']=errors
  if errors or not z['pdf_matches_png_exactly']:fail.append(slug+' final export/runtime')
  results[slug]=z;context.close();print(slug,'supplementary complete',flush=True)
 b.close()
(QA/'supplemental-results.json').write_text(json.dumps({'products':results,'failures':fail},indent=2),encoding='utf-8');print('FAILURES',fail)
# Native field crops for visual inspection.
main=json.loads((QA/'results.json').read_text(encoding='utf-8'))
for slug in ['whale-birthday','pumpkin-gender-reveal']:
 defaults=main['products'][slug]['fields'];files=sorted(QA.glob(slug+'-blank-*.png'));tiles=[]
 for fn in files:
  im=Image.open(fn).convert('RGB');region=(340,1175,1210,1485) if 'blank-name' in fn.name else (365,1590,1065,1865) if slug=='whale-birthday' else (350,1100,1200,1655);crop=im.crop(region);tiles.append((fn.stem,crop))
 cw=max(t[1].width for t in tiles)+20;ch=max(t[1].height for t in tiles)+35;cols=2;rows=(len(tiles)+1)//2;sheet=Image.new('RGB',(cw*cols,ch*rows),'#ddd');dr=ImageDraw.Draw(sheet)
 for i,(label,crop) in enumerate(tiles):x=(i%2)*cw+10;y=(i//2)*ch+5;dr.text((x,y),label,fill='black');sheet.paste(crop,(x,y+25))
 sheet.save(QA/(slug+'-blank-review.jpg'),quality=96)

if fail: raise SystemExit(1)
