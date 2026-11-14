import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.api import create_app
from src.tool_agent import ToolAgent, outside_jurisdiction


class Encoder:
    def encode(self,text): return list(text)


class Pipeline:
    last_trace={}
    def search(self,query,mode='hybrid_improved',top_k=3):
        self.last_trace={'original_query':query}
        return [{'id':'e1','text':'Nguồn minh họa dùng cho kiểm thử.','source_id':'fixture','source':'fixture.pdf',
                 'page':1,'metadata':{'article':'1','clause':'1'},'score':1}]
    def expand_context(self,results): return results


class ToolTests(unittest.TestCase):
    def test_foreign_jurisdiction_does_not_exclude_overseas_vietnamese(self):
        self.assertTrue(outside_jurisdiction('Thủ tục cấp giấy tại một quốc gia khác ra sao?'))
        self.assertFalse(outside_jurisdiction('Người Việt Nam định cư ở nước ngoài có quyền gì tại Việt Nam?'))
    @patch('tiktoken.get_encoding',return_value=Encoder())
    def test_real_protocol_executes_model_tool_and_validates_final(self,_):
        bodies=[]
        def request(body):
            bodies.append(body)
            if len(bodies)==1:
                msg={'role':'assistant','content':None,'tool_calls':[{'id':'call_1','type':'function','function':{'name':'search',
                     'arguments':json.dumps({'query':'original question','mode':'bm25','top_k':3})}}]}
            else:
                msg={'role':'assistant','content':json.dumps({'answer':'Nguồn minh họa [e1].','citations':['e1'],
                     'abstained':False,'reason':'fixture','evidence_quotes':[{'id':'e1','quote':'Nguồn minh họa dùng cho kiểm thử.'}]})}
            return {'choices':[{'message':msg}],'usage':{'prompt_tokens':50,'completion_tokens':30,'total_tokens':80}}
        result=ToolAgent(Pipeline(),request=request).run('original question',mode='bm25')
        self.assertEqual(result['status'],'answered')
        self.assertEqual(result['events'][0]['executed_query'],'original question')
        self.assertEqual(bodies[0]['tools'][0]['function']['parameters']['properties']['query']['enum'],['original question'])
        self.assertTrue(any(m['role']=='tool' for m in bodies[1]['messages']))
        self.assertEqual(result['usage']['total_tokens'],160)

    @patch('tiktoken.get_encoding',return_value=Encoder())
    def test_budget_blocks_before_network(self,_):
        calls=[]
        result=ToolAgent(Pipeline(),max_cost_usd=0,request=lambda body:calls.append(body)).run('question')
        self.assertEqual(result['status'],'error');self.assertFalse(calls)

    @patch('tiktoken.get_encoding',return_value=Encoder())
    def test_autonomous_loop_stops_after_two_search_rounds(self,_):
        bodies=[]
        def request(body):
            bodies.append(body)
            if len(bodies)<3:
                msg={'role':'assistant','content':None,'tool_calls':[{'id':'c'+str(len(bodies)),'type':'function',
                     'function':{'name':'search','arguments':json.dumps({'query':'variant '+str(len(bodies)),
                                                                     'mode':'bm25','top_k':3})}}]}
            else:
                msg={'role':'assistant','content':json.dumps({'answer':'Thông tin minh họa [e1].','citations':['e1'],
                     'abstained':False,'reason':'fixture','evidence_quotes':[{'id':'e1','quote':'Nguồn minh họa dùng cho kiểm thử.'}]})}
            return {'choices':[{'message':msg}],'usage':{'total_tokens':10}}
        result=ToolAgent(Pipeline(),max_rounds=2,request=request).run('fixture question',autonomous=True)
        self.assertEqual(result['status'],'answered')
        self.assertEqual(sum(e['event']=='search' for e in result['events']),2)
        self.assertEqual(len(bodies),3)
        self.assertNotIn('tools',bodies[-1])

    def test_api_input_origin_and_fixture_query(self):
        class Agent:
            def run(self,*a,**kw): return {'status':'abstain','answer':'fixture','tool_trace_id':'fixture_test'}
        with tempfile.TemporaryDirectory() as d:
            app=create_app(root=Path(d),pipeline_factory=Pipeline,agent_factory=lambda p:Agent())
            with TestClient(app,base_url='http://127.0.0.1') as client:
                self.assertEqual(client.post('/api/query',json={'question':'   '}).status_code,422)
                self.assertEqual(client.post('/api/query',json={'question':'x','mode':'bad'}).status_code,422)
                self.assertEqual(client.post('/api/query',json={'question':'x'},headers={'Origin':'https://evil.example'}).status_code,403)
                self.assertEqual(client.get('/api/example/unknown').status_code,404)
                response=client.post('/api/query',json={'question':'fixture'})
                self.assertEqual(response.status_code,200)
                self.assertTrue((Path(d)/'runs/demo_queries/fixture_test.json').exists())


if __name__=='__main__':unittest.main()
