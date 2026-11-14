"""Usage: python3 scripts/06_deploy_amplify_zip.py APP_ID main path/to/dist-root.zip"""
import sys
import subprocess
import zipfile
from pathlib import Path
import boto3

if len(sys.argv)!=4:
    raise SystemExit('Usage: python3 scripts/06_deploy_amplify_zip.py APP_ID BRANCH ZIP')
app,branch,zipname=sys.argv[1:]
path=Path(zipname).expanduser()
if not path.is_file(): raise SystemExit('ZIP not found')
with zipfile.ZipFile(path) as z:
    if 'index.html' not in z.namelist(): raise SystemExit('ZIP must have index.html at root')
api=boto3.client('amplify',region_name='us-east-1')
job=api.create_deployment(appId=app,branchName=branch)
subprocess.run(['curl','--fail','--silent','--show-error','-X','PUT',
                '-H','Content-Type: application/zip', '--upload-file',str(path),job['zipUploadUrl']],check=True)
api.start_deployment(appId=app,branchName=branch,jobId=job['jobId'])
print('Deployment job:',job['jobId'])
