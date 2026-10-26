from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np,pymupdf,json,hashlib,datetime,re
R=Path(__file__).resolve().parents[1];repo=R;out=R/'qa-local'/'brand';out.mkdir(parents=True,exist_ok=True);record={'verified_on':'2026-10-27','source':'https://www.etsy.com/shop/NorvellaHouse','scope':'Brand header, logo, palette, support footer, document title and documentation; invitation renderer and field defaults unchanged','products':{},'failures':[]}
with sync_playwright() as p:
 b=p.chromium.launch()
 for slug in ['whale-birthday','pumpkin-gender-reveal']:
  context=b.new_context(offline=True,accept_downloads=True,viewport={'width':1440,'height':1100});page=context.new_page();errors=[];requests=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url));file=repo/slug/'Editor.html';page.goto(file.as_uri());page.wait_for_function('InvitationEditor.ready');z={'issues':page.evaluate('issues'),'title':page.title(),'brand':page.locator('.brand-wordmark').inner_text(),'logo':page.locator('.brand-logo').evaluate('(e)=>({loaded:e.complete&&e.naturalWidth===100,width:e.naturalWidth,height:e.naturalHeight})'),'support_url':page.locator('.brand-footer a').get_attribute('href'),'responsive':[]}
  print(z,flush=True);assert z['brand'].casefold()=='norvella house' and z['logo']['loaded'] and not z['issues'];assert z['support_url']==record['source'];assert 'Norvella House' in z['title']
  for width in [1440,1024,850,390,320]:
   page.set_viewport_size({'width':width,'height':1100 if width>850 else 844});measurement=page.evaluate('({viewport:innerWidth,scroll:document.documentElement.scrollWidth})');assert measurement['viewport']==measurement['scroll'],(slug,measurement);z['responsive'].append(measurement)
   if width in [1440,390]:page.screenshot(path=str(out/f'{slug}-{width}.png'),full_page=True)
  page.set_viewport_size({'width':1440,'height':1100})
  for id,target in [('png',out/(slug+'-Preview.png')),('pdf',out/(slug+'-Invitation.pdf'))]:
   with page.expect_download() as ev:page.locator('#'+id).click()
   ev.value.save_as(str(target))
  old=np.array(Image.open(repo/slug/'Preview.png').convert('RGB'));new=np.array(Image.open(out/(slug+'-Preview.png')).convert('RGB'));assert np.array_equal(old,new),'Branding altered invitation';z['invitation_pixels_unchanged']=True
  im=Image.open(out/(slug+'-Preview.png'));z['png_size']=im.size;z['png_dpi']=im.info.get('dpi');doc=pymupdf.open(out/(slug+'-Invitation.pdf'));rect=doc[0].rect;z['pdf_points']=[rect.width,rect.height];assert len(doc)==1 and rect.width==360 and rect.height==504;pix=doc[0].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),alpha=False);arr=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3);assert np.array_equal(new,arr);z['pdf_matches_png']=True
  # A personalised HTML must keep the embedded brand and remain offline.
  first=page.locator('textarea').first;first.fill('Nate’s' if slug=='whale-birthday' else 'June 1, 2027')
  with page.expect_download() as ev:page.locator('#saveHtml').click()
  saved=out/(slug+'-personalised.html');ev.value.save_as(str(saved));pg=context.new_page();pg.goto(saved.as_uri());pg.wait_for_function('InvitationEditor.ready');assert pg.locator('.brand-wordmark').inner_text().casefold()=='norvella house';assert pg.locator('.brand-logo').evaluate('(e)=>e.complete&&e.naturalWidth===100');assert not pg.evaluate('issues');z['saved_html_brand_preserved']=True;pg.close()
  first.fill('');assert page.locator('#png').is_disabled() and page.locator('#pdf').is_disabled();z['empty_required_field_blocks_exports']=True;page.locator('#reset').click();assert not page.evaluate('issues')
  z['errors']=errors;assert not errors;z['external_requests']=[u for u in requests if not u.startswith(('file:','data:','blob:'))];assert not z['external_requests'];z['html_sha256']=hashlib.sha256(file.read_bytes()).hexdigest();z['png_sha256']=hashlib.sha256((repo/slug/'Preview.png').read_bytes()).hexdigest();record['products'][slug]=z;context.close();print(slug,'brand checks passed',flush=True)
 b.close()
(repo/'verification'/'BRAND-UPDATE.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
p=repo/'verification'/'RESULTS.json';r=json.loads(p.read_text(encoding='utf-8'));r['brand_revision_record']='BRAND-UPDATE.json';r['brand_revision_note']='The latest branding-only HTML hashes and unchanged invitation export checks are in BRAND-UPDATE.json. Earlier hashes below identify the functional baseline tested before the brand header/footer update.';p.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8');print('Failures:',record['failures'])
