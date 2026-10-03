# SPDX-License-Identifier: MIT
# Copyright (c) 2026 kasahart
import argparse
import csv
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description='ASD experiments: article 2 B0/B1/W1/SS')
    sub=parser.add_subparsers(dest='command',required=True)
    view=sub.add_parser('results',help='View saved experiment results; no inference or rescoring')
    view.add_argument('--file',type=Path,default=Path('results/summary-with-ss.csv'))
    infer=sub.add_parser('infer',help='New features and normal references per condition')
    infer.add_argument('--input',type=Path,required=True)
    infer.add_argument('--checkpoint',type=Path,required=True)
    infer.add_argument('--output',type=Path,required=True)
    infer.add_argument('--conditions',nargs='+',choices=['b0','b1','w1','ss'],default=['b0','b1','w1','ss'])
    infer.add_argument('--device',default='cpu')
    infer.add_argument('--machine',choices=['BlowerDustCollector','Sander','SewingMachine','ToothBrush','ToyDrone'])
    infer.add_argument('--limit',type=int,help='Smoke only; never an article score')
    infer.add_argument('--dry-run',action='store_true',help='Validate inventory and show count; no checkpoint loading')
    ev=sub.add_parser('evaluate',help='Requires reader-provided evaluator and resolved terms')
    ev.add_argument('--system',type=Path,required=True)
    ev.add_argument('--evaluator',type=Path,required=True)
    ev.add_argument('--output',type=Path,required=True)
    ev.add_argument('--terms-reviewed',action='store_true')
    args=parser.parse_args()
    if args.command=='results':
        with args.file.open() as f:
            for row in csv.DictReader(f): print(f"{row['condition'].upper()}: {100*float(row['official_score']):.3f} (stored experiment result; no computation in this command)")
    elif args.command=='infer':
        from .runner import plan,run,MACHINES
        machines=(args.machine,) if args.machine else MACHINES
        if args.dry_run:
            files=plan(args.input,machines,args.limit)
            print(json.dumps({m:{s:len(p) for s,p in v.items()} for m,v in files.items()},indent=2))
        else:
            print(json.dumps(run(args.input,args.checkpoint,args.output,args.conditions,args.device,machines,args.limit),indent=2))
    else:
        from .evaluation import evaluate
        print(evaluate(args.system,args.evaluator,args.output,args.terms_reviewed))

if __name__=='__main__': main()
