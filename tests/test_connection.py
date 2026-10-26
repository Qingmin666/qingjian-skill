import importlib.util
import json
from pathlib import Path
import unittest

path=Path(__file__).parents[1]/"skills/qingjian/scripts/check_connection.py"
spec=importlib.util.spec_from_file_location("probe",path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Response:
    def __init__(self,obj):self.obj=obj;self.headers={"MCP-Session-Id":"synthetic-session"}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,size):return json.dumps(self.obj).encode()

class FakeOpener:
    def __init__(self,fail=False):self.calls=[];self.fail=fail
    def open(self,req,timeout):
        body=json.loads(req.data);self.calls.append(body)
        method=body["method"]
        if method=="notifications/initialized":return Response({})
        result={}
        if method=="initialize":result={"protocolVersion":"2025-11-25"}
        elif method=="tools/list":result={"tools":[{"name":"qingjian_info"}]}
        elif method=="tools/call":result={"isError":self.fail,"structuredContent":{"revision":"rev","localDate":"2026-10-26","timeZone":"Asia/Shanghai"}}
        else:raise AssertionError(method)
        return Response({"jsonrpc":"2.0","id":body["id"],"result":result})

class Check(unittest.TestCase):
    def test_readonly_and_no_secrets(self):
        fake=FakeOpener();result=module.probe({"enabled":True,"token":"SYNTHETIC_TOKEN","port":49321},fake)
        self.assertTrue(result["success"])
        self.assertNotIn("SYNTHETIC_TOKEN",json.dumps(result))
        calls=[b["params"]["name"] for b in fake.calls if b["method"]=="tools/call"]
        self.assertEqual(calls,["qingjian_info"])
    def test_disabled(self):
        with self.assertRaises(ValueError):module.probe({"enabled":False})
    def test_remote_requires_tls(self):
        with self.assertRaises(ValueError):module.probe({"enabled":True,"token":"test","remote":True,"publicUrl":"http://invalid/mcp"})
    def test_tool_error_is_failure(self):
        with self.assertRaises(ValueError):module.probe({"enabled":True,"token":"test","port":49321},FakeOpener(True))

if __name__=="__main__":unittest.main()
