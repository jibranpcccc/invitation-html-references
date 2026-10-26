from pathlib import Path
import json,base64,io,hashlib,time,copy,re
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import pymupdf
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT;QA=ROOT/'qa-local';QA.mkdir(exist_ok=True);REPORT={'products':{},'failures':[]}
def decode(s):return np.asarray(Image.open(io.BytesIO(base64.b64decode(s.split(',',1)[1]))).convert('RGBA'))
def check(cond,label):
 if not cond:REPORT['failures'].append(label)
with sync_playwright() as p:
 b=p.chromium.launch()
 for slug in ['whale-birthday','pumpkin-gender-reveal']:
  print('Checking',slug,flush=True);d=OUT/slug;ctx=b.new_context(viewport={'width':1440,'height':1100},offline=True,accept_downloads=True);page=ctx.new_page();errors=[];network=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:network.append(r.url));page.goto((d/'Editor.html').as_uri());page.wait_for_function('InvitationEditor.ready',timeout=20000);cfg=page.evaluate('CONFIG');defaults=copy.deepcopy(cfg['defaults']);res={'baseline_issues':page.evaluate('issues'),'fields':len(defaults),'blank':[],'body':[],'controls':[],'name_matrix':[],'font_choices':[]};check(not res['baseline_issues'],slug+' default invalid')
  def reset():page.locator('#reset').click()
  def canvas():return decode(page.evaluate("canvas.toDataURL('image/png')"))
  def savepng(filename):
   im=canvas();Image.fromarray(im).save(filename);return im
  def put(key,patch):page.evaluate('([k,v])=>{Object.assign(fields.find(f=>f.key===k),v);updateInputs();render()}',[key,patch])
  baseline=savepng(QA/(slug+'-default.png'))
  clean=decode(page.evaluate("(()=>{const c=offscreen(1500,2100);c.getContext('2d').drawImage(background,0,0,1500,2100);return c.toDataURL('image/png')})()"))
  for f in defaults:
   reset();put(f['key'],{'text':''});blank=savepng(QA/(slug+'-blank-'+f['key']+'.png'));x,y,w,h=[v*1500/1060 for v in f['box']];x0,y0=int(np.floor(x)),int(np.floor(y));x1,y1=int(np.ceil(x+w)),int(np.ceil(y+h));same=bool(np.array_equal(blank[y0:y1,x0:x1],clean[y0:y1,x0:x1]));diff=np.any(blank!=baseline,axis=2);diff[y0:y1,x0:x1]=False;outside=int(diff.sum());blocked=page.locator('#png').is_disabled() and page.locator('#pdf').is_disabled();z={'field':f['key'],'clean_crop_exact':same,'other_pixels_unchanged':outside==0,'blocked':blocked,'issues':page.evaluate('issues')};res['blank'].append(z);check(same and outside==0 and blocked,slug+' blank '+f['key']);put(f['key'],{'text':f['text']});check(np.array_equal(canvas(),baseline),slug+' restore '+f['key'])
   # Verify independent bold/color for every field.
   for patch in [{'bold':True},{'fill':'#c9213a'}]:
    reset();put(f['key'],patch);im=canvas();changed=int(np.any(im!=baseline,axis=2).sum());check(changed>0,slug+' inert '+f['key']+str(patch));res['controls'].append({'field':f['key'],'patch':patch,'changed_pixels':changed,'issues':page.evaluate('issues')})
   if f['key']!='name':
    short='3 PM' if f['key']=='time' else 'Amy' if f['key']=='rsvp' else '555-0100' if f['key']=='phone' else 'Sea Hall' if f['key']=='venue' else 'June 1' if f['key']=='date' else '12 Ocean Road'
    long='10:30 AM - 11:45 PM' if f['key']=='time' else 'Saturday, September 25, 2027' if f['key']=='date' else 'The Grand Ocean View Pavilion and Celebration Garden' if f['key']=='venue' else 'RSVP: Christopher at christopher.family@example.com by September 15' if f['key']=='rsvp' else '+1 (555) 123-4567' if f['key']=='phone' else '123 Celebration Avenue, Franklin, Tennessee 37064'
    for j,v in enumerate([short,long]):
     reset();put(f['key'],{'text':v});lay=page.evaluate('layouts');issues=page.evaluate('issues');found=next((l for l in lay if l['key']==f['key']),None);z={'field':f['key'],'text':v,'issues':issues,'layout':found};res['body'].append(z);check(bool(issues) or (found is not None and found['actual']>=f['minPt']),slug+' under-minimum '+f['key']);savepng(QA/(slug+'-'+f['key']+'-'+str(j)+'.png'))
  print('Field checks complete',slug,flush=True)
  if slug=='whale-birthday':
   for j,v in enumerate(['AL','al','Al','NATE\u2019S','nate\u2019s','Nate\u2019s','CHRISTOPHER\u2019S','christopher\u2019s','Christopher\u2019s','NOEL\u2019S','gjpqy']):
    reset();put('name',{'text':v});z={'text':v,'issues':page.evaluate('issues'),'layout':page.evaluate("layouts.find(x=>x.key==='name')")};res['name_matrix'].append(z);check(not z['issues'],slug+' name '+v);savepng(QA/(slug+'-name-'+str(j)+'.png'))
   controlkey='name'
  else:controlkey='date'
  # Common styling and placement controls; use real UI input events.
  reset();page.locator('details').evaluate_all('(es)=>es.forEach(e=>e.open=true)');selectedIndex=next(i for i,f in enumerate(defaults) if f['key']==controlkey);page.locator('#selected').select_option(str(selectedIndex));page.locator('details').first.evaluate('(e)=>e.open=true');controlbase=canvas()
  cases=[('italic',True),('underline',True),('size',str(defaults[selectedIndex]['minPt'])),('spacing','1'),('align','left'),('fill','#d62240'),('mode','palette'),('outlineWidth','0.8'),('shadow','0.7')]
  if controlkey=='name':cases += [('stitch',False),('stitchColor','#ffdc00'),('grain',False)]
  for id,value in cases:
   reset();page.locator('#selected').select_option(str(selectedIndex));page.locator('details').first.evaluate('(e)=>e.open=true')
   if id in ['outlineWidth','shadow']:page.locator('#outlineWidth').evaluate('(e)=>e.closest("details").open=true')
   loc=page.locator('#'+id)
   if isinstance(value,bool):loc.set_checked(value)
   elif id in ['align','mode']:loc.select_option(value)
   else:loc.evaluate('(e,v)=>{e.value=v;e.dispatchEvent(new Event("input",{bubbles:true}))}',value)
   page.evaluate('()=>new Promise(requestAnimationFrame)');im=canvas();changed=int(np.any(im!=controlbase,axis=2).sum());z={'field':controlkey,'control':id,'value':value,'changed_pixels':changed,'issues':page.evaluate('issues')};res['controls'].append(z);check(changed>0,slug+' UI inert '+id)
  # Placement must not change rendered size. Out-of-bounds positions must block.
  reset();put(controlkey,{'text':'Amy' if controlkey=='name' else 'June 1'});before=page.evaluate('layouts.find(x=>x.key===selectedField().key)');put(controlkey,{'dx':1});after=page.evaluate('layouts.find(x=>x.key===selectedField().key)');res['placement_size_unchanged']=before['actual']==after['actual'];check(res['placement_size_unchanged'],slug+' movement resized');put(controlkey,{'dy':30});res['placement_blocks']=bool(page.evaluate('issues'));check(res['placement_blocks'],slug+' outside movement accepted')
  # No silently truncated paragraphs.
  reset();body=next(f for f in defaults if f['kind']=='body');put(body['key'],{'text':'\n'.join(['a']*13),'size':body['minPt'],'wrap':True});res['too_many_lines_blocked']=bool(page.evaluate('issues'));check(res['too_many_lines_blocked'],slug+' silent truncation')
  for j,font in enumerate(cfg['fonts']):
   reset();put(controlkey,{'font':font});z={'font':font,'issues':page.evaluate('issues')};res['font_choices'].append(z);savepng(QA/(slug+'-font-'+str(j)+'.png'))
   # Font may legitimately be rejected for fitting, but never silently fall back.
   check(page.evaluate('(f)=>document.fonts.check(`16px "${f}"`)',font),slug+' unavailable font '+font)
  # Validation atomicity and all-property load/save/reopen.
  reset();state=page.evaluate('({product:CONFIG.id,version:1,fields:structuredClone(fields)})');invalid=copy.deepcopy(state);invalid['fields'][0]['mode']='banana';z=page.evaluate('d=>{const before=JSON.stringify(fields);let blocked=false;try{const next=validatedSettings(d);fields=next}catch(e){blocked=true}return {blocked,unchanged:before===JSON.stringify(fields)}}',invalid);res['invalid_settings']=z;check(z['blocked'] and z['unchanged'],slug+' invalid settings')
  state['fields'][0].update(fill='#a52f58',bold=True,italic=True,underline=True,outline='#204839',outlineWidth=.2,shadowColor='#514875',shadow=.2,mode='palette',palette=['#ae1234','#234f8c','#157b51'],spacing=.1,dx=.2,dy=0,lineHeight=1.3)
  # Allow fit validation of styled saved HTML: choose a short first field.
  state['fields'][0]['text']='Nate\u2019s' if controlkey=='name' else 'June 1, 2027';upload=QA/(slug+'-settings.json');upload.write_text(json.dumps(state),encoding='utf-8');page.locator('#loadSettings').set_input_files(str(upload));page.wait_for_function('fields[0].fill==="#a52f58"');loaded=page.evaluate('fields');res['all_styles_loaded']=all(loaded[0].get(k)==v for k,v in state['fields'][0].items());check(res['all_styles_loaded'],slug+' style state lost');styled=canvas()
  if not page.evaluate('issues'):
   with page.expect_download() as ev:page.locator('#saveHtml').click()
   edited=QA/(slug+'-personalized.html');ev.value.save_as(str(edited));p2=ctx.new_page();p2.goto(edited.as_uri());p2.wait_for_function('InvitationEditor.ready');reopened=decode(p2.evaluate("canvas.toDataURL('image/png')"));res['personalized_html_exact']=bool(np.array_equal(styled,reopened));check(res['personalized_html_exact'],slug+' personalized html changed');p2.locator('#reset').click();check(np.array_equal(reopened,decode(p2.evaluate("canvas.toDataURL('image/png')"))),slug+' personalized reset');p2.close()
  else:check(False,slug+' styled example invalid '+str(page.evaluate('issues')))
  # Actual undo/redo through UI and selected-field reset.
  reset();first=defaults[0];page.locator('#input-'+first['key']).fill('Amy' if first['key']=='name' else 'June 1');editedText=page.locator('#input-'+first['key']).input_value();page.locator('#undo').click();u=page.locator('#input-'+first['key']).input_value();page.locator('#redo').click();rr=page.locator('#input-'+first['key']).input_value();res['undo_redo']=u==first['text'] and rr==editedText;check(res['undo_redo'],slug+' undo redo');page.locator('#resetField').click();check(page.locator('#input-'+first['key']).input_value()==first['text'],slug+' reset selected')
  # Actual final saved HTML exports with metadata.
  reset();check(not page.evaluate('issues'),slug+' reset invalid')
  for id,fn in [('png','Preview.png'),('pdf','Invitation.pdf')]:
   with page.expect_download() as ev:page.locator('#'+id).click()
   target=(d/fn) if id=='png' else QA/(slug+'-'+fn);ev.value.save_as(str(target))
  im=Image.open(d/'Preview.png');res['png']={'size':im.size,'dpi':im.info.get('dpi')};check(im.size==(1500,2100) and abs(im.info.get('dpi',(0,))[0]-300)<.01,slug+' PNG size/DPI');check(np.array_equal(np.array(im.convert('RGBA')),baseline),slug+' exported PNG mismatch')
  doc=pymupdf.open(QA/(slug+'-Invitation.pdf'));rect=doc[0].rect;res['pdf']={'pages':len(doc),'points':[rect.width,rect.height]};check(len(doc)==1 and rect.width==360 and rect.height==504,slug+' PDF size')
  pdfpix=doc[0].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),alpha=False);arr=np.frombuffer(pdfpix.samples,np.uint8).reshape(pdfpix.height,pdfpix.width,3);expected=np.array(im.convert('RGB'));res['pdf_rgb_max_difference']=int(np.abs(arr.astype(np.int16)-expected.astype(np.int16)).max()) if arr.shape==expected.shape else -1;check(res['pdf_rgb_max_difference']==0,slug+' PDF pixel mismatch')
  page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(QA/(slug+'-mobile.png')),full_page=True);res['mobile']=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');check(res['mobile']['width']==res['mobile']['scroll'],slug+' mobile overflow');res['runtime_errors']=errors;check(not errors,slug+' runtime errors');res['external_requests']=[u for u in network if not u.startswith(('file:','data:','blob:'))];check(not res['external_requests'],slug+' network dependency');res['html_sha256']=hashlib.sha256((d/'Editor.html').read_bytes()).hexdigest();REPORT['products'][slug]=res;ctx.close();print('Complete',slug,'failures',REPORT['failures'],flush=True)
 b.close()
# Actual font glyph coverage.
REPORT['fonts']={}
for key,font in cfg['fonts'].items():
 raw=base64.b64decode(font['data'].split(',',1)[1]);tt=TTFont(io.BytesIO(raw));cmap=tt.getBestCmap();missing=[c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' if ord(c) not in cmap];REPORT['fonts'][key]={'missing_english_glyphs':missing,'sha256':hashlib.sha256(raw).hexdigest()};check(not missing,'missing glyph '+key)
(QA/'results.json').write_text(json.dumps(REPORT,indent=2,ensure_ascii=False),encoding='utf-8');print('FINAL FAILURES',json.dumps(REPORT['failures']),flush=True)

if REPORT['failures']: raise SystemExit(1)
