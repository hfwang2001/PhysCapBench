"""PhysCapBench three-domain release CLI. Python 3.10+, requests, FFmpeg for generation."""
import argparse, base64, hashlib, json, math, os, re, statistics, subprocess, sys, tempfile, time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
def digest(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True).encode()
def load(path): return json.loads(Path(path).read_text())
def rows(path): return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
def save(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def jsonl(path,x):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
def require(ok,msg):
    if not ok: raise ValueError(msg)
def index(rs,key='video_id'):
    require(all(isinstance(r.get(key),str) for r in rs),'Missing string ID')
    d={r[key]:r for r in rs};require(len(d)==len(rs),'Duplicate IDs');return d
def manifest(data,limit=None,domain='all'):
    rs=rows(data/'manifest.jsonl');index(rs)
    for r in rs:
        require(re.fullmatch(r'(physcap9k_\d{5}|egodex500_\d{4}|umi500_\d{4})',r['video_id']), 'Invalid video ID')
        require(r['domain'] in ['third','ego','umi'] and r['video_file']=='videos/'+r['domain']+'/'+r['video_id']+'.mp4','Unsafe video path')
    require(len(rs)==1500,'Release requires exactly 1500 videos')
    require(all(sum(r['domain']==d for r in rs)==500 for d in ['third','ego','umi']),'Each domain requires 500 videos')
    rs=[r for r in rs if domain=='all' or r['domain']==domain]
    return sorted(rs,key=lambda r:r['video_id'])[:limit]
def hash_file(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def verify_video(p,r):
    require(p.is_file() and p.stat().st_size==r['bytes'],'Missing/wrong-size video: '+r['video_id'])
    require(hash_file(p)==r['sha256'],'Video checksum mismatch: '+r['video_id'])
def fetch_metadata(a):
    require(bool(a.repo)!=bool(a.base_url),'Supply exactly one of --repo or --base-url')
    root=('https://huggingface.co/datasets/'+a.repo+'/resolve/'+a.revision) if a.repo else a.base_url.rstrip('/')
    headers={'Authorization':'Bearer '+os.environ['HF_TOKEN']} if a.repo and os.getenv('HF_TOKEN') else {}
    for name,expected in load(ROOT/'dataset.lock.json')['metadata_sha256'].items():
        dest=a.data/name
        if not dest.exists():
            res=requests.get(root+'/'+name,headers=headers,timeout=(20,180));require(res.status_code==200,'Metadata download HTTP '+str(res.status_code))
            require(digest(res.content)==expected,'Metadata checksum mismatch: '+name)
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(res.content)
        require(hash_file(dest)==expected,'Metadata checksum mismatch: '+name)
def frozen_applicability(data,refs,dims):
    path=data/'applicability.jsonl'
    dataset=load(ROOT/'dataset.lock.json')
    require(dataset.get('applicability_protocol_sha256')==hash_file(ROOT/'protocol.json'),'Frozen applicability protocol mismatch')
    expected=dataset['metadata_sha256'].get('applicability.jsonl')
    require(expected is not None and hash_file(path)==expected,'Frozen applicability checksum mismatch')
    frozen=index(rows(path));require(set(frozen)==set(refs),'Frozen applicability/reference IDs differ')
    for vid,r in refs.items():
        require(digest(r['gold_caption'].encode())==r['sha256'],'Reference content checksum mismatch')
        require(frozen[vid]['reference_sha256']==r['sha256'],'Frozen applicability is stale for '+vid)
        lines={f'L{i:04d}':line for i,line in enumerate(r['gold_caption'].splitlines()) if line.strip()}
        valid_app({k:frozen[vid][k] for k in ['evidence_ids','rationale_zh']},lines,dims)
    return frozen
def predictions(path,selected):
    rs=rows(path);d=index(rs)
    require(set(d)=={r['video_id'] for r in selected},'Prediction IDs must exactly match evaluation subset; missing/extra IDs rejected')
    require(all(isinstance(r.get('caption'),str) and r['caption'].strip() for r in rs),'Empty or non-string caption')
    return d
def api(prompt,payload,model,base,key,json_mode=True):
    body={'model':model,'temperature':0,'max_tokens':6000,'messages':[{'role':'system','content':prompt},{'role':'user','content':payload if isinstance(payload,list) else json.dumps(payload,ensure_ascii=False)}]}
    if 'doubao' in model:body['thinking']={'type':'disabled'}
    if json_mode:body['response_format']={'type':'json_object'}
    for attempt in range(3):
        try:
            res=requests.post(base.rstrip('/')+'/chat/completions',headers={'Authorization':'Bearer '+key},json=body,timeout=(20,180))
            require(res.status_code==200,'Model endpoint HTTP '+str(res.status_code))
            value=res.json();c=value['choices'][0];require(c['finish_reason']=='stop','Truncated model response')
            text=c['message']['content'];require(isinstance(text,str) and text.strip(),'Empty model response')
            parsed=json.JSONDecoder().raw_decode(text[text.index('{'):])[0] if json_mode else text
            return parsed,{'model':model,'response_id':value.get('id'),'usage':value.get('usage')}
        except (requests.RequestException,ValueError,KeyError) as e:
            if attempt==2:raise
            time.sleep(2**attempt)
def checked(path,prompt,payload,model,base,key,validator):
    identity=digest(canonical({'prompt':prompt,'payload':payload,'model':model,'base_url':base,'temperature':0,'schema_version':1}))
    if path.exists():
        d=load(path);require(d['identity']==identity,'Cache mismatch: use a new output directory');validator(d['response']);return d['response']
    feedback='';failures=[]
    for attempt in range(4):
        response,receipt=api(prompt+feedback,payload,model,base,key)
        try:validator(response)
        except (ValueError,TypeError,KeyError) as error:
            failures.append({'response':response,'error':str(error),'receipt':receipt})
            save(path.with_suffix('.failures.json'),failures)
            feedback='\nYour previous response failed schema validation: '+str(error)+'. Return a corrected JSON object. For evidence_ids, use between 1 and 6 exact keys from reference_lines per applicable dimension; never output quotations or field names as IDs. Previous response: '+json.dumps(response,ensure_ascii=False)
            if attempt==3:raise
            continue
        save(path,{'identity':identity,'response':response,'receipt':receipt});return response
def valid_app(x,lines,dims):
    require(set(x)=={'evidence_ids','rationale_zh'},'Applicability schema mismatch')
    require(set(x['evidence_ids'])==set(x['rationale_zh'])==set(dims),'Applicability dimension mismatch')
    for d,ids in x['evidence_ids'].items():
        require(ids is None or (isinstance(ids,list) and 1<=len(ids)<=6 and all(isinstance(i,str) and i in lines for i in ids)),'Invalid evidence IDs for '+d+': '+json.dumps(ids))
        if ids is not None:require(any(' = ' in lines[i] and not re.match(r'(?:new_)?event_\d+_(?:event_id|frame_start|frame_end) =',lines[i]) for i in ids),'Dimension '+d+' uses only event IDs or frame boundaries: '+json.dumps(ids)+'. Include at least one corresponding event description or action field together with the relevant timing/relation fields, within the 6-ID limit; otherwise use null. Boundary-only evidence is invalid.')
        require(isinstance(x['rationale_zh'][d],str) and x['rationale_zh'][d].strip(),'Empty applicability rationale')
def valid_score(x,e):
    require(set(x)=={'dimensions'} and set(x['dimensions'])==set(e),'Score dimensions mismatch')
    for d,v in x['dimensions'].items():
        expected={'score','reason_zh'} | ({'confidence'} if e[d] is None else set())
        require(set(v)==expected,'Score schema mismatch for '+d+': expected '+str(sorted(expected)))
        require(type(v['score']) is int and 0<=v['score']<=100,'Invalid score: every dimension requires an integer 0..100')
        if e[d] is None:
            c=v['confidence']
            require(type(c) in (int,float) and math.isfinite(c) and 0<=c<=1,'Invalid confidence for '+d+': expected finite number 0..1')
            require(c!=0 or v['score']==50,'Zero-confidence fallback must use neutral score 50')
        require(isinstance(v['reason_zh'],str) and v['reason_zh'].strip(),'Missing rationale')
def aggregate(scores,dims):
    require(bool(scores),'No scores to aggregate')
    for r in scores:
        require(set(r['dimensions'])==set(dims),'Aggregate dimension mismatch')
        require(all(type(v['score']) is int and 0<=v['score']<=100 for v in r['dimensions'].values()),'Aggregate requires numeric scores for every dimension')
    per={r['video_id']:statistics.mean(r['dimensions'][d]['score'] for d in dims) for r in scores}
    by={}
    for d in dims:
        vals=[r['dimensions'][d]['score'] for r in scores]
        by[d]={'mean':statistics.mean(vals),'n':len(vals),'estimated_n':sum('confidence' in r['dimensions'][d] for r in scores)}
    return {'n':len(scores),'overall':statistics.mean(per.values()),'dimensions':by,'per_video':per,'aggregation':'equal_dimension_then_equal_video; confidence is not a weight','scope':'full_1500' if len(scores)==1500 else 'subset'}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['validate','download','template','generate','score']);p.add_argument('--data',type=Path,default=ROOT/'data');p.add_argument('--videos',type=Path,default=ROOT/'downloaded');p.add_argument('--limit',type=int);p.add_argument('--domain',choices=['all','third','ego','umi'],default='all');p.add_argument('--base-url',help='HTTP root containing videos/');p.add_argument('--repo',help='Hugging Face dataset org/name');p.add_argument('--revision',default='main');p.add_argument('--predictions',type=Path);p.add_argument('--out',type=Path,default=ROOT/'run');p.add_argument('--api-base',default=os.getenv('OPENAI_BASE_URL','https://ark.cn-beijing.volces.com/api/v3'));p.add_argument('--model');a=p.parse_args()
    require(a.limit is None or 1<=a.limit<=1500,'limit must be 1..1500')
    if a.command=='download':fetch_metadata(a)
    selected=manifest(a.data,a.limit,a.domain)
    if a.command=='validate':
        refs=index(rows(a.data/'references.jsonl'));anns=index(rows(a.data/'annotations.jsonl'));ids={r['video_id'] for r in manifest(a.data)}
        require(set(refs)==set(anns)==ids,'1500-way video/reference/annotation mismatch')
        for r in refs.values():require(r['gold_caption'].strip() and digest(r['gold_caption'].encode())==r['sha256'],'Reference checksum mismatch')
        for r in anns.values():require(bool(r['fields']),'Incomplete annotation')
        frozen_applicability(a.data,refs,load(ROOT/'protocol.json')['dimension_labels'])
        if a.predictions:predictions(a.predictions,selected)
        print(json.dumps({'videos':1500,'annotations':1500,'references':1500,'prediction_scope':len(selected) if a.predictions else None}));return
    if a.command=='download':
        require(bool(a.repo)!=bool(a.base_url),'Supply exactly one of --repo or --base-url')
        root=('https://huggingface.co/datasets/'+a.repo+'/resolve/'+a.revision) if a.repo else a.base_url.rstrip('/')
        headers={'Authorization':'Bearer '+os.environ['HF_TOKEN']} if a.repo and os.getenv('HF_TOKEN') else {}
        for r in selected:
            dest=a.videos/r['video_file'];dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():verify_video(dest,r);continue
            part=dest.with_suffix('.part')
            with requests.get(root+'/'+r['video_file'],headers=headers,stream=True,timeout=(20,180)) as response:
                require(response.status_code==200,'Download HTTP '+str(response.status_code))
                with part.open('wb') as f:
                    for chunk in response.iter_content(1024*1024):f.write(chunk)
            verify_video(part,r);part.replace(dest);print('downloaded',r['video_id'],flush=True)
        print('verified',len(selected));return
    if a.command=='template':
        jsonl(a.out,[{'video_id':r['video_id'],'caption':''} for r in selected]);return
    key=os.getenv('OPENAI_API_KEY') or os.getenv('ARK_API_KEY');require(bool(key),'Set OPENAI_API_KEY (or ARK_API_KEY)')
    if a.command=='generate':
        require(bool(a.model),'Supply your caption model with --model')
        caps=[]
        for r in selected:
            video=a.videos/r['video_file'];verify_video(video,r);content=[{'type':'text','text':'Describe the visible physical events in chronological order. Include objects, actions, interactions and visible changes. Do not invent hidden causes.'}]
            with tempfile.TemporaryDirectory() as td:
                for i in range(8):
                    t=(i+.5)*r['duration_seconds']/8;f=Path(td)/f'{i}.jpg'
                    subprocess.run(['ffmpeg','-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-vf','scale=768:768:force_original_aspect_ratio=decrease','-y',str(f)],check=True,capture_output=True)
                    content.extend([{'type':'text','text':f'{t:.3f} seconds'},{'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+base64.b64encode(f.read_bytes()).decode()}}])
            cap,receipt=api('You describe observed video frames. Output only an English caption.',content,a.model,a.api_base,key,False)
            caps.append({'video_id':r['video_id'],'caption':cap,'generation':receipt,'sampling':'8 uniform frames, max edge 768; reference annotations not read'})
            jsonl(a.out,caps);print('generated',r['video_id'],flush=True)
        return
    require(a.predictions is not None,'Supply --predictions');caps=predictions(a.predictions,selected)
    protocol=load(ROOT/'protocol.json');dims=protocol['dimension_labels'];model=a.model or protocol['judge_model'];refs=index(rows(a.data/'references.jsonl'));results=[]
    frozen=frozen_applicability(a.data,refs,dims)
    lock={'applicability_sha256':hash_file(a.data/'applicability.jsonl'),'protocol_sha256':hash_file(ROOT/'protocol.json'),'references_sha256':hash_file(a.data/'references.jsonl'),'predictions_sha256':hash_file(a.predictions),'ids':[r['video_id'] for r in selected],'judge_model':model,'api_base':a.api_base}
    if (a.out/'run.lock.json').exists():require(load(a.out/'run.lock.json')==lock,'Run inputs changed; use a new --out directory')
    save(a.out/'run.lock.json',lock)
    for r in selected:
        vid=r['video_id'];text=refs[vid]['gold_caption'];lines={f'L{i:04d}':l for i,l in enumerate(text.splitlines()) if l.strip()}
        require(digest(text.encode())==refs[vid]['sha256'],'Reference checksum mismatch')
        app={k:frozen[vid][k] for k in ['evidence_ids','rationale_zh']}
        save(a.out/'applicability'/f'{vid}.json',{'source':'frozen_candidate_independent_reference_audit','file_sha256':lock['applicability_sha256'],'reference_sha256':refs[vid]['sha256'],'response':app})
        e={d:None if ids is None else [lines[i] for i in ids] for d,ids in app['evidence_ids'].items()}
        score=checked(a.out/'scores'/f'{vid}.json',protocol['judge_prompt'],{'gold_caption':text,'candidate_caption':caps[vid]['caption'],'evidence':e,'reference_evidence_rationale':app['rationale_zh']},model,a.api_base,key,lambda x:valid_score(x,e))
        results.append({'video_id':vid,**score});print('scored',vid,flush=True)
    jsonl(a.out/'scores.jsonl',results);summary=aggregate(results,dims);summary['domain']=a.domain;summary['per_domain']={d:aggregate([v for v in results if next(x for x in selected if x['video_id']==v['video_id'])['domain']==d],dims) for d in ['third','ego','umi'] if any(x['domain']==d for x in selected)};save(a.out/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(1)
