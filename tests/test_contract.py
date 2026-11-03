import importlib.util,json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
spec=importlib.util.spec_from_file_location('bench',Path(__file__).parents[1]/'bench.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class Contracts(unittest.TestCase):
 def test_prediction_ids_and_empty(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'p.jsonl';selected=[{'video_id':'a'}]
   for data in [[{'video_id':'a','caption':''}],[{'video_id':'b','caption':'x'}],[{'video_id':'a','caption':'x'}]*2]:
    b.jsonl(p,data)
    with self.assertRaises(ValueError):b.predictions(p,selected)
 def test_estimated_scores_have_equal_weight(self):
  rs=[{'video_id':'a','dimensions':{'x':{'score':100},'y':{'score':50,'confidence':0}}},{'video_id':'b','dimensions':{'x':{'score':0},'y':{'score':0}}}]
  r=b.aggregate(rs,['x','y']);self.assertEqual(r['overall'],37.5);self.assertEqual(r['dimensions']['y']['n'],2);self.assertEqual(r['dimensions']['y']['estimated_n'],1)
  rs[0]['dimensions']['y']['confidence']=.9
  self.assertEqual(b.aggregate(rs,['x','y'])['overall'],37.5)
 def test_confidence_only_for_insufficient_evidence(self):
  e={'x':['witness'],'y':None}
  good={'dimensions':{'x':{'score':80,'reason_zh':'supported'},'y':{'score':50,'reason_zh':'neutral fallback','confidence':0}}}
  b.valid_score(good,e)
  for d,change in [('x',{'confidence':.9}),('y',{'confidence':None}),('y',{'score':None}),('y',{'score':0})]:
   bad=json.loads(json.dumps(good));bad['dimensions'][d].update(change)
   with self.assertRaises(ValueError):b.valid_score(bad,e)
  del good['dimensions']['y']['confidence']
  with self.assertRaises(ValueError):b.valid_score(good,e)
 def test_confidence_range_and_partial_estimate(self):
  for c in [True,-.1,1.1,float('nan'),float('inf'),'0.2']:
   with self.assertRaises(ValueError):b.valid_score({'dimensions':{'x':{'score':60,'confidence':c,'reason_zh':'partial'}}},{'x':None})
  b.valid_score({'dimensions':{'x':{'score':60,'confidence':.2,'reason_zh':'partial'}}},{'x':None})
 def test_all_insufficient_still_numeric(self):
  dims=list(b.load(b.ROOT/'protocol.json')['dimension_labels'])
  b.valid_app({'evidence_ids':dict.fromkeys(dims,None),'rationale_zh':dict.fromkeys(dims,'no evidence')},{},dims)
  scores={'dimensions':{d:{'score':50,'confidence':0,'reason_zh':'neutral fallback'} for d in dims}}
  b.valid_score(scores,dict.fromkeys(dims,None))
  self.assertEqual(b.aggregate([{'video_id':'a',**scores}],dims)['overall'],50)
 def test_aggregate_rejects_legacy_null(self):
  with self.assertRaises(ValueError):b.aggregate([{'video_id':'a','dimensions':{'x':{'score':None}}}],['x'])
 def test_range_and_applicability(self):
  for value in [True,101,-1,None]:
   with self.assertRaises(ValueError):b.valid_score({'dimensions':{'x':{'score':value,'reason_zh':'r'}}},{'x':['witness']})
 def test_bad_evidence(self):
  for ids in [['L9999'],['L0000']]:
   with self.assertRaises(ValueError):b.valid_app({'evidence_ids':{'x':ids},'rationale_zh':{'x':'r'}},{'L0000':'event_1_frame_start = [1]'},['x'])
 def test_video_integrity(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'v.mp4';p.write_bytes(b'bad')
   with self.assertRaises(ValueError):b.verify_video(p,{'bytes':3,'sha256':'wrong','video_id':'x'})
 def test_cache_identity(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'cache.json';b.save(p,{'identity':'old','response':{}})
   with self.assertRaises(ValueError):b.checked(p,'prompt',{},'model','url','fake',lambda x:None)
 def test_frozen_evidence_binds_to_exact_reference(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);caption='observed = "hand presses block"';sha=b.digest(caption.encode())
   refs={'a':{'gold_caption':caption,'sha256':sha}}
   frozen={'video_id':'a','reference_sha256':sha,'evidence_ids':{'x':['L0000']},'rationale_zh':{'x':'visible'}}
   b.save(root/'protocol.json',{'fixture':'frozen evidence protocol'});b.jsonl(root/'applicability.jsonl',[frozen]);b.save(root/'dataset.lock.json',{'applicability_protocol_sha256':b.hash_file(root/'protocol.json'),'metadata_sha256':{'applicability.jsonl':b.hash_file(root/'applicability.jsonl')}})
   with patch.object(b,'ROOT',root):
    self.assertEqual(b.frozen_applicability(root,refs,['x'])['a']['evidence_ids']['x'],['L0000'])
    changed='observed = "different fact"'
    with self.assertRaisesRegex(ValueError,'stale'):b.frozen_applicability(root,{'a':{'gold_caption':changed,'sha256':b.digest(changed.encode())}},['x'])
    b.save(root/'protocol.json',{'fixture':'changed evidence protocol'})
    with self.assertRaisesRegex(ValueError,'protocol mismatch'):b.frozen_applicability(root,refs,['x'])
    b.save(root/'protocol.json',{'fixture':'frozen evidence protocol'})
    frozen['evidence_ids']['x']=None;b.jsonl(root/'applicability.jsonl',[frozen])
    with self.assertRaisesRegex(ValueError,'checksum'):b.frozen_applicability(root,refs,['x'])
 def test_schema_repair_and_resume(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'cache.json'
   with patch.object(b,'api',side_effect=[({'ok':False},{}),({'ok':True},{})]) as api:
    validator=lambda x:b.require(x['ok'],'invalid witness ID')
    self.assertTrue(b.checked(p,'prompt',{},'model','url','fake',validator)['ok'])
    self.assertIn('invalid witness ID',api.call_args_list[1].args[0])
    self.assertTrue(b.checked(p,'prompt',{},'model','url','fake',validator)['ok'])
    self.assertEqual(api.call_count,2)
if __name__=='__main__':unittest.main()
