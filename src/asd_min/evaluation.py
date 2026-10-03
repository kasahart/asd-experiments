# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
"""Invoke reader-provided official evaluator only after their terms review.
No evaluator source or truth CSV is included in this distribution.
"""
from pathlib import Path
import csv
import json
import math
import subprocess
import sys
from .runner import MACHINES,digest
REVISION = 'f6a94a2b5e614a9626c9d1ccff6df0705e6aaa75'


def validate(system):
    system=Path(system)
    expected=set()
    for machine in MACHINES:
        for prefix in ('anomaly_score','decision_result'):
            name=f'{prefix}_{machine}_section_00_test.csv';expected.add(name)
            with (system/name).open() as f: rows=list(csv.reader(f))
            if len(rows)!=200 or any(len(r)!=2 for r in rows): raise ValueError(name)
            if {r[0] for r in rows}!={f'section_00_{i:04d}.wav' for i in range(200)}: raise ValueError('Filename mismatch')
            for _,value in rows:
                x=float(value)
                if not math.isfinite(x) or (prefix=='decision_result' and x not in (0,1)): raise ValueError('Invalid score')
    if {p.name for p in system.glob('anomaly_score_*.csv')} | {p.name for p in system.glob('decision_result_*.csv')} != expected:
        raise ValueError('Unexpected submission files')
    return expected


def evaluate(system,evaluator,output,terms_reviewed=False):
    if not terms_reviewed: raise ValueError('Review evaluator conditions yourself first; see docs/rights.md')
    system,evaluator,output=map(lambda x:Path(x).resolve(),(system,evaluator,output))
    validate(system)
    revision=subprocess.check_output(['git','-C',str(evaluator),'rev-parse','HEAD'],text=True).strip()
    if revision!=REVISION: raise ValueError('Wrong evaluator revision')
    if subprocess.check_output(['git','-C',str(evaluator),'status','--porcelain'],text=True).strip():
        raise ValueError('Evaluator must be unmodified and clean')
    if output.exists(): raise ValueError('Refusing to overwrite')
    output.mkdir(parents=True)
    stage=output/'teams'/'reader';stage.mkdir(parents=True)
    (stage/system.name).symlink_to(system,target_is_directory=True)
    command=[sys.executable,str(evaluator/'dcase2026_task2_evaluator.py'),
        '--teams_root_dir',str(output/'teams'),'--dir_depth','2','--result_dir',str(output/'results'),
        '--out_all','True','--additional_result_dir',str(output/'additional')]
    receipt={'revision':REVISION,'status':'running','submission_sha256':{p.name:digest(p) for p in system.glob('*score_*.csv')}}
    try:
        with (output/'evaluator.log').open('w') as log:
            subprocess.run(command,cwd=evaluator,stdout=log,stderr=subprocess.STDOUT,check=True)
        receipt['status']='succeeded'
    except Exception:
        receipt['status']='failed';raise
    finally:
        (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return output/'results'/f'{system.name}_result.csv'
